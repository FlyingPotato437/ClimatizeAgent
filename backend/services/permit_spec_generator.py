"""
Permit Specification Generator - End-to-End Workflow Implementation
Implements automated permit document generation with spec sheet retrieval and assembly.
"""
import logging
import asyncio
import csv
import json
import os
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import requests
import httpx
from exa_py import Exa
import pypdf
from pypdf import PdfWriter, PdfReader
import tempfile

logger = logging.getLogger(__name__)


@dataclass
class BOMComponent:
    """Represents a component from the bill of materials."""
    row: int
    part_number: str
    part_name: str
    manufacturer: str
    category: str
    qty: int
    cost_per_unit: Optional[str] = None
    total_cost: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SpecSheetResult:
    """Result of spec sheet retrieval for a component."""
    component: BOMComponent
    status: str  # 'found', 'cached', 'missing'
    pdf_path: Optional[str] = None
    source_url: Optional[str] = None
    log_message: str = ""


class PermitSpecGenerator:
    """
    Main service for generating permit documents with automated spec sheet retrieval.
    Implements the complete workflow from BOM processing to final PDF assembly.
    """
    
    def __init__(self, exa_api_key: str, firecrawl_api_key: str):
        self.exa_api_key = exa_api_key
        self.firecrawl_api_key = firecrawl_api_key
        self.exa = Exa(api_key=exa_api_key)
        
        # Setup directories
        self.project_root = Path(__file__).parent.parent.parent
        self.cache_dir = self.project_root / "assets" / "specs"
        self.output_dir = self.project_root / "output" / "permits"
        self.temp_dir = self.project_root / "temp"
        
        # Create directories if they don't exist
        for directory in [self.cache_dir, self.output_dir, self.temp_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info("Permit Spec Generator initialized")
    
    async def generate_permit_with_specs(self, 
                                       permit_pdf_path: str,
                                       bom_csv_path: str,
                                       research_notes_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Main entry point for the end-to-end permit generation workflow.
        
        Args:
            permit_pdf_path: Path to the original permit PDF (first 7 pages)
            bom_csv_path: Path to the bill of materials CSV
            research_notes_path: Optional path to research notes directory
            
        Returns:
            Dictionary with generation results and metadata
        """
        logger.info(f"Starting permit generation workflow")
        start_time = datetime.now()
        
        try:
            # Step 1: Process bill of materials
            components = self._process_bom(bom_csv_path)
            logger.info(f"Processed {len(components)} components from BOM")
            
            # Step 2: Load research notes if available
            research_context = self._load_research_notes(research_notes_path) if research_notes_path else {}
            
            # Step 3: Retrieve spec sheets for all components
            spec_results = await self._retrieve_all_spec_sheets(components, research_context)
            
            # Step 4: Assemble final permit document
            output_pdf_path = await self._assemble_permit_document(permit_pdf_path, spec_results)
            
            # Step 5: Generate results summary
            results = self._generate_results_summary(spec_results, output_pdf_path, start_time)
            
            logger.info(f"Permit generation completed in {results['processing_time']}")
            return results
            
        except Exception as e:
            logger.error(f"Permit generation failed: {e}")
            raise
    
    def _process_bom(self, bom_csv_path: str) -> List[BOMComponent]:
        """
        Process and normalize bill of materials data.
        
        Args:
            bom_csv_path: Path to BOM CSV file
            
        Returns:
            List of normalized BOM components
        """
        components = []
        
        with open(bom_csv_path, 'r', encoding='utf-8') as file:
            # Skip header rows and find the data start
            content = file.read()
            lines = content.split('\n')
            
            # Find the row with column headers
            data_start_idx = 0
            for i, line in enumerate(lines):
                if 'Row,Part Number,Part Name' in line or 'Part Number' in line:
                    data_start_idx = i + 1
                    break
            
            # Process data rows
            csv_reader = csv.reader(lines[data_start_idx:])
            for row_data in csv_reader:
                if len(row_data) >= 5 and row_data[0] and row_data[0].isdigit():
                    # Normalize component data
                    component = BOMComponent(
                        row=int(row_data[0]),
                        part_number=self._normalize_model_string(row_data[1]),
                        part_name=self._normalize_model_string(row_data[2]),
                        manufacturer=self._normalize_model_string(row_data[3]),
                        category=row_data[4] if len(row_data) > 4 else "",
                        qty=int(row_data[5]) if len(row_data) > 5 and row_data[5].isdigit() else 0,
                        cost_per_unit=row_data[6] if len(row_data) > 6 else None,
                        total_cost=row_data[7] if len(row_data) > 7 else None,
                        notes=row_data[8] if len(row_data) > 8 else None
                    )
                    components.append(component)
        
        logger.info(f"Processed {len(components)} components from BOM")
        return components
    
    def _normalize_model_string(self, model_str: str) -> str:
        """
        Normalize model strings for consistent searching.
        
        Args:
            model_str: Raw model string from BOM
            
        Returns:
            Normalized model string
        """
        if not model_str:
            return ""
        
        # Convert to lowercase, strip trademarks, remove extra spaces
        normalized = model_str.lower()
        normalized = re.sub(r'[™®©]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized)
        normalized = normalized.strip()
        
        return normalized
    
    def _load_research_notes(self, research_path: str) -> Dict[str, Any]:
        """
        Load research notes and site restrictions from the specified directory.
        
        Args:
            research_path: Path to research notes directory
            
        Returns:
            Dictionary containing research context
        """
        research_context = {}
        research_dir = Path(research_path)
        
        if research_dir.exists():
            # Load any markdown or text files
            for file_path in research_dir.glob("*.md"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    research_context[file_path.stem] = f.read()
            
            # Load any JSON files
            for file_path in research_dir.glob("*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    research_context[file_path.stem] = json.load(f)
        
        logger.info(f"Loaded research context from {len(research_context)} files")
        return research_context
    
    async def _retrieve_all_spec_sheets(self, 
                                      components: List[BOMComponent],
                                      research_context: Dict[str, Any]) -> List[SpecSheetResult]:
        """
        Retrieve spec sheets for all components using parallel processing.
        
        Args:
            components: List of BOM components
            research_context: Research notes and constraints
            
        Returns:
            List of spec sheet retrieval results
        """
        # Create semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent searches
        
        # Create tasks for all components
        tasks = [
            self._retrieve_component_spec_sheet(component, research_context, semaphore)
            for component in components
            if component.part_name and component.part_name.strip()  # Skip empty components
        ]
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return valid results
        valid_results = [r for r in results if isinstance(r, SpecSheetResult)]
        logger.info(f"Retrieved spec sheets for {len(valid_results)} components")
        
        return valid_results
    
    async def _retrieve_component_spec_sheet(self, 
                                           component: BOMComponent,
                                           research_context: Dict[str, Any],
                                           semaphore: asyncio.Semaphore) -> SpecSheetResult:
        """
        Retrieve spec sheet for a single component.
        
        Args:
            component: BOM component to find spec sheet for
            research_context: Research notes and constraints
            semaphore: Concurrency limiter
            
        Returns:
            Spec sheet retrieval result
        """
        async with semaphore:
            try:
                # Step 1: Generate search queries
                queries = self._generate_search_queries(component)
                
                # Step 2: Search with Exa.ai
                for query in queries:
                    logger.info(f"Searching for {component.part_name}: {query}")
                    
                    try:
                        # Execute search
                        search_results = self.exa.search(
                            query=query,
                            num_results=5,
                            include_domains=self._get_vendor_domains(component.manufacturer)
                        )
                        
                        # Process results
                        for result in search_results.results:
                            if result.url.endswith('.pdf'):
                                # Try to download and validate PDF
                                pdf_path = await self._download_and_validate_pdf(
                                    result.url, component
                                )
                                
                                if pdf_path:
                                    return SpecSheetResult(
                                        component=component,
                                        status='found',
                                        pdf_path=pdf_path,
                                        source_url=result.url,
                                        log_message=f"✅ {component.part_name} → vendor PDF"
                                    )
                    
                    except Exception as e:
                        logger.warning(f"Search failed for query '{query}': {e}")
                        continue
                
                # Step 3: Try fallback cache
                cached_path = self._find_cached_spec_sheet(component)
                if cached_path:
                    return SpecSheetResult(
                        component=component,
                        status='cached',
                        pdf_path=cached_path,
                        log_message=f"⚠️ {component.part_name} → cached"
                    )
                
                # Step 4: Component not found
                return SpecSheetResult(
                    component=component,
                    status='missing',
                    log_message=f"❌ {component.part_name} → missing"
                )
                
            except Exception as e:
                logger.error(f"Failed to retrieve spec sheet for {component.part_name}: {e}")
                return SpecSheetResult(
                    component=component,
                    status='missing',
                    log_message=f"❌ {component.part_name} → error: {str(e)}"
                )
    
    def _generate_search_queries(self, component: BOMComponent) -> List[str]:
        """
        Generate vendor-specific and fallback search queries for a component.
        
        Args:
            component: BOM component
            
        Returns:
            List of search queries ordered by priority
        """
        queries = []
        vendor_domain = self._get_vendor_domain(component.manufacturer)
        
        # Vendor-locked slug query
        if vendor_domain:
            if component.part_number:
                queries.append(
                    f'filetype:pdf inurl:{component.part_number} site:{vendor_domain}'
                )
            
            queries.append(
                f'filetype:pdf "{component.part_name}" datasheet site:{vendor_domain}'
            )
        
        # Generic fallback queries
        if component.part_number:
            queries.append(f'{component.part_number} datasheet filetype:pdf')
        
        queries.append(f'{component.part_name} datasheet filetype:pdf')
        queries.append(f'{component.manufacturer} {component.part_name} specification filetype:pdf')
        
        return queries
    
    def _get_vendor_domain(self, manufacturer: str) -> Optional[str]:
        """Get the primary domain for a manufacturer."""
        domain_mapping = {
            'qcells': 'qcells.com',
            'q cells': 'qcells.com',
            'enphase': 'enphase.com',
            'enphase energy inc.': 'enphase.com',
            'ironridge': 'ironridge.com',
            'solaredge': 'solaredge.com',
            'tesla': 'tesla.com',
            'sunpower': 'sunpower.com',
            'canadian solar': 'canadiansolar.com',
            'lg': 'lgenergy.com',
            'rec': 'recgroup.com'
        }
        
        manufacturer_normalized = manufacturer.lower().strip()
        return domain_mapping.get(manufacturer_normalized)
    
    def _get_vendor_domains(self, manufacturer: str) -> Optional[List[str]]:
        """Get list of domains to include in search."""
        primary_domain = self._get_vendor_domain(manufacturer)
        return [primary_domain] if primary_domain else None
    
    async def _download_and_validate_pdf(self, url: str, component: BOMComponent) -> Optional[str]:
        """
        Download PDF using Firecrawl and validate it contains the component model.
        
        Args:
            url: PDF URL to download
            component: Component to validate against
            
        Returns:
            Path to downloaded PDF if valid, None otherwise
        """
        try:
            # Use Firecrawl to download PDF
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.firecrawl.dev/v1/crawl",
                    headers={
                        "Authorization": f"Bearer {self.firecrawl_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "url": url,
                        "download": True,
                        "type": "pdf"
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Save PDF to temp file
                    temp_pdf_path = self.temp_dir / f"{component.part_number}_{component.row}.pdf"
                    
                    if 'content' in result:
                        # If content is returned directly
                        with open(temp_pdf_path, 'wb') as f:
                            f.write(result['content'])
                    else:
                        # Download from provided URL
                        pdf_response = await client.get(url)
                        with open(temp_pdf_path, 'wb') as f:
                            f.write(pdf_response.content)
                    
                    # Validate PDF contains component model
                    if self._validate_pdf_content(temp_pdf_path, component):
                        # Move to permanent location
                        final_path = self.cache_dir / f"{component.part_number}_spec.pdf"
                        temp_pdf_path.rename(final_path)
                        return str(final_path)
                    else:
                        # Clean up invalid PDF
                        temp_pdf_path.unlink(missing_ok=True)
                        return None
                
        except Exception as e:
            logger.warning(f"Failed to download PDF from {url}: {e}")
            return None
    
    def _validate_pdf_content(self, pdf_path: Path, component: BOMComponent) -> bool:
        """
        Validate that PDF contains the component model string.
        
        Args:
            pdf_path: Path to PDF file
            component: Component to validate against
            
        Returns:
            True if PDF is valid for this component
        """
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                
                # Check first page for model string
                if len(reader.pages) > 0:
                    first_page = reader.pages[0]
                    text = first_page.extract_text().lower()
                    
                    # Check if component identifiers are present
                    model_checks = [
                        component.part_number.lower() in text if component.part_number else False,
                        component.part_name.lower() in text if component.part_name else False,
                        any(word in text for word in component.part_name.lower().split()[:2]) if component.part_name else False
                    ]
                    
                    return any(model_checks)
                    
        except Exception as e:
            logger.warning(f"Failed to validate PDF content: {e}")
            return False
        
        return False
    
    def _find_cached_spec_sheet(self, component: BOMComponent) -> Optional[str]:
        """
        Find a cached spec sheet for the component.
        
        Args:
            component: Component to find cached spec for
            
        Returns:
            Path to cached PDF if found
        """
        # Look for cached files with component identifiers
        cache_patterns = [
            f"{component.part_number}_spec.pdf",
            f"{component.part_number}.pdf",
            f"{component.part_name.replace(' ', '_')}_spec.pdf"
        ]
        
        for pattern in cache_patterns:
            cache_path = self.cache_dir / pattern
            if cache_path.exists():
                return str(cache_path)
        
        # Look for manufacturer-specific cached files
        manufacturer_dir = self.cache_dir / component.manufacturer.lower().replace(' ', '_')
        if manufacturer_dir.exists():
            for pdf_file in manufacturer_dir.glob("*.pdf"):
                if any(term.lower() in pdf_file.name.lower() 
                      for term in [component.part_number, component.part_name] 
                      if term):
                    return str(pdf_file)
        
        return None
    
    async def _assemble_permit_document(self, 
                                      original_permit_path: str,
                                      spec_results: List[SpecSheetResult]) -> str:
        """
        Assemble the final permit document with spec sheets as pages 8-16.
        
        Args:
            original_permit_path: Path to original permit PDF (first 7 pages)
            spec_results: List of spec sheet retrieval results
            
        Returns:
            Path to assembled permit document
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = self.output_dir / f"permit_with_specs_{timestamp}.pdf"
        
        writer = PdfWriter()
        
        try:
            # Add original permit pages (1-7)
            with open(original_permit_path, 'rb') as original_file:
                original_reader = PdfReader(original_file)
                
                # Add first 7 pages or all pages if fewer than 7
                pages_to_add = min(7, len(original_reader.pages))
                for i in range(pages_to_add):
                    writer.add_page(original_reader.pages[i])
            
            # Add spec sheets in BOM order (pages 8+)
            page_count = pages_to_add + 1
            successfully_added = []
            
            # Sort spec results by component row number to maintain BOM order
            sorted_results = sorted(
                [r for r in spec_results if r.pdf_path and r.status in ['found', 'cached']], 
                key=lambda x: x.component.row
            )
            
            for result in sorted_results:
                try:
                    with open(result.pdf_path, 'rb') as spec_file:
                        spec_reader = PdfReader(spec_file)
                        
                        # Add all pages from spec sheet
                        for page in spec_reader.pages:
                            writer.add_page(page)
                            page_count += 1
                        
                        successfully_added.append(result.component.part_name)
                        logger.info(f"Added spec sheet for {result.component.part_name} ({len(spec_reader.pages)} pages)")
                
                except Exception as e:
                    logger.warning(f"Failed to add spec sheet for {result.component.part_name}: {e}")
            
            # Write final PDF
            with open(output_path, 'wb') as output_file:
                writer.write(output_file)
            
            logger.info(f"Assembled permit document with {page_count} total pages")
            logger.info(f"Successfully added spec sheets for: {', '.join(successfully_added)}")
            
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Failed to assemble permit document: {e}")
            raise
    
    def _generate_results_summary(self, 
                                spec_results: List[SpecSheetResult],
                                output_pdf_path: str,
                                start_time: datetime) -> Dict[str, Any]:
        """
        Generate summary of permit generation results.
        
        Args:
            spec_results: List of spec sheet retrieval results
            output_pdf_path: Path to final assembled permit
            start_time: Workflow start time
            
        Returns:
            Results summary dictionary
        """
        end_time = datetime.now()
        processing_time = str(end_time - start_time)
        
        # Categorize results
        found_count = len([r for r in spec_results if r.status == 'found'])
        cached_count = len([r for r in spec_results if r.status == 'cached'])
        missing_count = len([r for r in spec_results if r.status == 'missing'])
        
        missing_components = [
            r.component.part_name for r in spec_results 
            if r.status == 'missing'
        ]
        
        logs = [r.log_message for r in spec_results if r.log_message]
        
        return {
            "status": "ok",
            "output_pdf": output_pdf_path,
            "missing": missing_components,
            "logs": logs,
            "summary": {
                "total_components": len(spec_results),
                "found": found_count,
                "cached": cached_count,
                "missing": missing_count,
                "success_rate": f"{((found_count + cached_count) / len(spec_results) * 100):.1f}%" if spec_results else "0%"
            },
            "processing_time": processing_time,
            "timestamp": end_time.isoformat()
        } 