#!/usr/bin/env python3
"""
Smart Permit Generator - LLM-Filtered Spec Sheet Selection
Uses Exa.ai + OpenAI to find ONLY specific spec sheets, not catalogs
"""
import os
import csv
import requests
import json
from pathlib import Path
from datetime import datetime
from exa_py import Exa
from pypdf import PdfWriter, PdfReader
import openai

# API Keys
EXA_API_KEY = "9071d31c-fe10-4922-969c-1db58d0f1a87"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "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")  # You'll need to set this

class SmartPermitGenerator:
    def __init__(self):
        self.exa = Exa(api_key=EXA_API_KEY)
        
        # Initialize OpenAI client (optional - will use smart fallback if not available)
        try:
            if OPENAI_API_KEY:
                self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
                print("LLM filtering enabled (OpenAI)")
            else:
                self.openai_client = None
                print("Using smart rule-based filtering (no OpenAI key)")
        except Exception as e:
            self.openai_client = None
            print("Using smart rule-based filtering")
        
    def read_bom_csv(self, csv_path):
        """Read BOM from CSV file"""
        components = []
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            
            # Find the data start
            data_start = 0
            for i, line in enumerate(lines):
                if 'Row,Part Number' in line:
                    data_start = i
                    break
            
            if data_start > 0:
                data_lines = lines[data_start:]
                reader = csv.DictReader(data_lines)
                
                for row in reader:
                    part_number = row.get('Part Number', '').strip()
                    part_name = row.get('Part Name', '').strip()
                    manufacturer = row.get('Manufacturer', '').strip()
                    
                    # Skip empty rows or total rows
                    if not part_number and not part_name:
                        continue
                    if 'Total' in str(row.get('Row', '')):
                        continue
                    
                    # Ensure we have a display name
                    display_name = part_name if part_name else part_number
                    
                    components.append({
                        'row': len(components) + 1,
                        'part_name': display_name,
                        'part_number': part_number,
                        'manufacturer': manufacturer,
                        'qty': row.get('Qty', '1'),
                        'category': row.get('Category', '')
                    })
        
        return components

    def generate_specific_queries(self, component):
        """Generate queries that focus on specific spec sheets, not catalogs"""
        part_number = component.get('part_number', '').strip()
        part_name = component.get('part_name', '').strip()
        manufacturer = component.get('manufacturer', '').strip()
        
        queries = []
        
        # Vendor domain mapping
        vendor_domains = {
            'IronRidge': 'ironridge.com',
            'Qcells': 'qcells.com', 
            'Enphase Energy Inc.': 'enphase.com',
            'Enphase': 'enphase.com'
        }
        
        domain = vendor_domains.get(manufacturer, '')
        component_type = self._get_component_type(component)
        
        # Enhanced search based on component type
        if component_type == 'Solar Panel' and 'qcells' in manufacturer.lower():
            # Q.PEAK solar panels need special handling
            if part_number:
                queries.extend([
                    f'filetype:pdf "{part_number}" datasheet site:qcells.com',
                    f'filetype:pdf "Q.PEAK" datasheet site:qcells.com',
                    f'filetype:pdf "{part_number}" specification sheet site:qcells.com'
                ])
        
        elif component_type == 'Microinverter' and 'enphase' in manufacturer.lower():
            # Enphase IQ microinverters
            if part_number:
                queries.extend([
                    f'filetype:pdf "{part_number}" datasheet site:enphase.com',
                    f'filetype:pdf "IQ8" datasheet site:enphase.com',
                    f'filetype:pdf "{part_number}" specification site:enphase.com'
                ])
        
        elif component_type == 'Mounting Rail' and 'ironridge' in manufacturer.lower():
            # XR-100 mounting rails - try series spec sheets
            if part_number:
                queries.extend([
                    f'filetype:pdf "XR-100" datasheet site:ironridge.com',
                    f'filetype:pdf "XR100" specification site:ironridge.com',
                    f'filetype:pdf "XR-100" cutsheet site:ironridge.com'
                ])
        
        elif component_type == 'Grounding Equipment' and 'ironridge' in manufacturer.lower():
            # Grounding equipment - try broader terms
            if part_number:
                queries.extend([
                    f'filetype:pdf "grounding" "lug" datasheet site:ironridge.com',
                    f'filetype:pdf "XR-LUG" specification site:ironridge.com',
                    f'filetype:pdf "grounding" cutsheet site:ironridge.com'
                ])
        
        # Primary: Part number with manufacturer domain
        if part_number and domain:
                queries.extend([
                    f'filetype:pdf "{part_number}" datasheet -catalog -guide site:{domain}',
                    f'filetype:pdf inurl:{part_number} -catalog -parts site:{domain}',
                    f'filetype:pdf "{part_number}" cutsheet site:{domain}',
                    f'filetype:pdf "{part_number}" spec sheet site:{domain}'
                ])
        
        # Enhanced generic searches with better filtering
        if part_number:
            queries.extend([
                f'filetype:pdf "{part_number}" datasheet -catalog -guide -manual',
                f'filetype:pdf "{part_number}" specification sheet -catalog',
                f'filetype:pdf "{part_number}" cutsheet -parts_catalog'
            ])
        
        # Broader searches for hard-to-find components
        if part_name:
            # Try searching by component name/type
            clean_name = part_name.lower()
            if 'rail' in clean_name or 'xr-100' in clean_name:
                queries.extend([
                    f'filetype:pdf "mounting rail" datasheet site:{domain}',
                    f'filetype:pdf "structural rail" specification site:{domain}'
                ])
            elif 'grounding' in clean_name or 'lug' in clean_name:
                queries.extend([
                    f'filetype:pdf "grounding hardware" datasheet site:{domain}',
                    f'filetype:pdf "grounding lug" specification site:{domain}'
                ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        return unique_queries[:6]  # Limit to top 6 most relevant queries
    
    def _get_component_type(self, component):
        """Determine component type from name and part number"""
        part_name = component.get('part_name', '').lower()
        
        if any(word in part_name for word in ['solar', 'panel', 'module', 'q.peak', 'qpeak']):
            return 'Solar Panel'
        elif any(word in part_name for word in ['inverter', 'iq8', 'iq7', 'microinverter']):
            return 'Microinverter' 
        elif any(word in part_name for word in ['rail', 'xr-100', 'xr100']):
            return 'Mounting Rail'
        elif any(word in part_name for word in ['clamp', 'fastening']):
            return 'Module Clamp'
        elif any(word in part_name for word in ['foot', 'flashfoot', 'flash_foot']):
            return 'Roof Attachment'
        elif any(word in part_name for word in ['bolt', 'hardware']):
            return 'Hardware'
        elif any(word in part_name for word in ['splice', 'bonded']):
            return 'Splice/Connector'
        elif any(word in part_name for word in ['lug', 'grounding']):
            return 'Grounding Equipment'
        else:
            return 'Solar Component'

    def filter_pdf_urls_with_llm(self, pdf_urls, component):
        """Use OpenAI to select the most specific spec sheet URL"""
        if not self.openai_client or not pdf_urls:
            return None
            
        try:
            url_list = "\n".join([f"{i+1}. {url}" for i, url in enumerate(pdf_urls)])
            
            prompt = f"""You are an expert solar installation engineer analyzing component specification documents.

COMPONENT TO FIND:
- Part Number: {component.get('part_number', 'Unknown')}
- Part Name: {component.get('part_name', 'Unknown')}
- Manufacturer: {component.get('manufacturer', 'Unknown')}
- Component Type: {self._get_component_type(component)}

CANDIDATE URLs:
{url_list}

ACCEPT REAL MANUFACTURER SPEC SHEETS:
ACCEPT: Official manufacturer datasheets/cutsheets for THIS component
ACCEPT: Cut sheets with "Cut_Sheet" or "cutsheet" in URL (these are GOOD!)
ACCEPT: Datasheets with "datasheet", "Data_sheet", "DS-" in URL
ACCEPT: PDFs from official manufacturer websites (ironridge.com, qcells.com, enphase.com)
ACCEPT: Series datasheets that cover the specific model (e.g., "385-410" range for 400W model)
ACCEPT: Product family specs (e.g., "XR-100" series for XR-100-168A or XR-100-204A)
ACCEPT: Component category specs that include this specific part

ONLY REJECT IF CLEARLY:
- Contains "catalog", "parts_catalog" explicitly in filename
- Contains "installation_guide", "manual", "handbook" in filename  
- Engineering guides or design guides

ANALYSIS PRIORITY:
1. Is this from the official manufacturer website?
2. Does it relate to this component (part number or model series)?
3. Is it a datasheet, cutsheet, or specification document?
4. Does it NOT have explicit "catalog" keywords?

ACCEPT UNLESS CLEARLY A CATALOG OR GUIDE
Cut sheets and datasheets are EXACTLY what we want!

RESPOND WITH ONLY A NUMBER:
- The number (1, 2, 3, etc.) of the BEST datasheet/cutsheet
- Or 0 if ALL files are catalogs/guides

IMPORTANT RESPONSE FORMAT:
- RESPOND WITH ONLY THE NUMBER: "1" or "2" or "3" or "0"
- DO NOT include explanations, reasoning, or extra text
- JUST THE NUMBER

Example responses: "1" or "2" or "0"
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # More deterministic
                max_tokens=100  # Allow detailed reasoning
            )
            
            # Parse response - extract the selected number
            response_text = response.choices[0].message.content.strip()
            print(f"    LLM Response: {response_text}")
            
            try:
                # Look for any number in the response - multiple strategies
                import re
                selected_num = None
                
                # Strategy 1: Number at start of response
                number_match = re.search(r'^(\d+)', response_text)
                if number_match:
                    selected_num = int(number_match.group(1))
                else:
                    # Strategy 2: Number at end of response 
                    number_match = re.search(r'(\d+)\s*$', response_text)
                    if number_match:
                        selected_num = int(number_match.group(1))
                    else:
                        # Strategy 3: Any standalone number in response
                        numbers = re.findall(r'\b(\d+)\b', response_text)
                        if numbers:
                            # Take the last number found (often the final selection)
                            selected_num = int(numbers[-1])
                
                if selected_num is None:
                    print(f"    No number found in LLM response")
                    return None
                
                if selected_num == 0:
                    print(f"    LLM rejected all URLs as unsuitable")
                    return None
                elif 1 <= selected_num <= len(pdf_urls):
                    selected_url = pdf_urls[selected_num - 1]
                    
                    # SAFETY CHECK: Verify LLM didn't select a catalog
                    if any(bad_word in selected_url.lower() for bad_word in ['parts_catalog', 'catalog', 'installation_guide']):
                        print(f"    LLM selected a catalog/guide URL - overriding to None")
                        return None
                    
                    print(f"    LLM selected URL {selected_num}: {selected_url}")
                    return selected_url
                else:
                    print(f"    LLM returned invalid number: {selected_num}")
                    return None
                    
            except Exception as e:
                print(f"    Could not parse LLM response: {e}")
                return None
                
        except Exception as e:
            print(f"    LLM filtering failed: {e}")
        
        # Fallback to simple filtering
        print(f"    Falling back to rule-based filtering")
        return self.simple_url_filter(pdf_urls, component)

    def simple_url_filter(self, pdf_urls, component):
        """Enhanced rule-based URL filtering - very smart about avoiding catalogs"""
        if not pdf_urls:
            return None
        
        part_number = component.get('part_number', '').lower().replace('-', '').replace(' ', '')
        part_name = component.get('part_name', '').lower()
        
        # Score URLs based on specificity
        scored_urls = []
        
        for url in pdf_urls:
            score = 0
            url_lower = url.lower()
            url_clean = url_lower.replace('-', '').replace('_', '').replace(' ', '')
            
            # STRONG positive indicators (specific spec sheets)
            if 'datasheet' in url_lower:
                score += 10
            if 'cutsheet' in url_lower:
                score += 10
            if 'cut_sheet' in url_lower:
                score += 10
            if part_number and len(part_number) > 3 and part_number in url_clean:
                score += 15  # Part number match is very important
            
            # Good indicators
            if 'spec' in url_lower and 'specification' not in url_lower:
                score += 5
            if any(word in url_lower for word in ['ds.pdf', 'datasheet.pdf', 'spec.pdf']):
                score += 8
            
            # STRONG negative indicators (definitely avoid these)
            catalog_words = ['catalog', 'parts_catalog', 'product_catalog', 'guide', 'manual', 
                           'installation', 'engineering', 'design_guide', 'handbook']
            for bad_word in catalog_words:
                if bad_word in url_lower:
                    score -= 20
            
            # Size-based filtering (shorter URLs often more specific)
            if len(url) < 80:  # Very specific URLs
                score += 3
            elif len(url) > 150:  # Very long URLs often catalogs
                score -= 5
            
            # Domain-specific rules
            if 'ironridge.com' in url_lower:
                if 'cutsheet' in url_lower or 'cut_sheet' in url_lower:
                    score += 5
                if 'parts_catalog' in url_lower:
                    score -= 25  # Definitely avoid IronRidge catalog
            
            if 'qcells.com' in url_lower or 'enphase.com' in url_lower:
                if any(word in url_lower for word in ['datasheet', 'ds-', '-ds']):
                    score += 8
            
            print(f"      {url}: score {score}")
            scored_urls.append((score, url))
        
        # Return highest scored URL if it's above threshold
        scored_urls.sort(reverse=True, key=lambda x: x[0])
        
        if scored_urls:
            # Be more aggressive - take the best available option even with low scores
            best_score, best_url = scored_urls[0]
            if best_score > -10:  # Accept anything that's not clearly terrible
                print(f"    Selected best URL (score: {best_score}): {best_url}")
                return best_url
            else:
                print(f"    All URLs are clearly unsuitable (best score: {best_score})")
                return None
        else:
            print(f"    No URLs to evaluate")
            return None

    def search_for_specific_spec(self, component):
        """Search for ONE specific spec sheet using Exa.ai + LLM filtering"""
        component_name = component.get('part_name', 'Unknown')
        print(f"Searching for {component_name} specification...")
        
        queries = self.generate_specific_queries(component)
        pdf_urls = []
        
        # Collect PDFs from multiple queries
        for query in queries[:3]:  # Limit to first 3 queries for speed
            try:
                print(f"    Query: {query}")
                
                search_results = self.exa.search(
                    query=query,
                    num_results=3,  # Only get top 3 results per query
                    type="keyword"
                )
                
                # Collect PDF URLs
                for result in search_results.results:
                    if result.url.endswith('.pdf'):
                        pdf_urls.append(result.url)
                        print(f"    Found: {result.url}")
                
                # If we found some PDFs, process them
                if pdf_urls:
                    break  # Don't keep searching if we found options
                    
            except Exception as e:
                print(f"    Search failed: {e}")
                continue
        
        if not pdf_urls:
            print(f"    No PDFs found for {component_name}")
            return None
        
        # Use LLM to select the best/most specific PDF
        print(f"    Filtering {len(pdf_urls)} PDFs with AI...")
        best_url = self.filter_pdf_urls_with_llm(pdf_urls, component)
        
        if best_url:
            print(f"    Selected: {best_url}")
            return best_url
        else:
            print(f"    No suitable spec sheet found")
            return None

    def download_and_validate_pdf(self, url, component):
        """Download PDF with multiple retry strategies and validate it's a real spec sheet"""
        if not url:
            return None
        
        print(f"    Downloading: {url}")
        
        # Try multiple download strategies
        download_strategies = [
            # Strategy 1: Standard headers
            {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },
            # Strategy 2: More permissive headers
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/pdf,*/*',
                'Accept-Language': 'en-US,en;q=0.9'
            },
            # Strategy 3: Minimal headers
            {
                'User-Agent': 'Python-requests/2.28.1'
            }
        ]
        
        for attempt, headers in enumerate(download_strategies, 1):
            try:
                print(f"      Attempt {attempt}/{len(download_strategies)}...")
                response = requests.get(url, headers=headers, timeout=30, stream=True)
                response.raise_for_status()
                break  # Success!
            except requests.exceptions.RequestException as e:
                if attempt == len(download_strategies):
                    print(f"    Download failed after {attempt} attempts: {e}")
                    return None
                else:
                    print(f"      Attempt {attempt} failed: {e}")
                    continue
        
        try:
            # Save to temp file
            temp_dir = Path("temp/smart_specs")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            part_number = component.get('part_number', 'unknown').replace('/', '_').replace(' ', '_')
            temp_path = temp_dir / f"{part_number}_spec.pdf"
            
            with open(temp_path, 'wb') as f:
                f.write(response.content)
            
            # Strict validation to avoid catalogs
            file_size_mb = len(response.content) / (1024 * 1024)
            
            # Very strict size limits for spec sheets
            if file_size_mb > 10:  # More than 10MB is likely a catalog
                print(f"    PDF too large ({file_size_mb:.1f}MB) - likely a catalog")
                return None
            
            # Quick page count check
            try:
                with open(temp_path, 'rb') as file:
                    reader = PdfReader(file)
                    page_count = len(reader.pages)
                    
                    # Very strict page limits - real spec sheets are usually 1-6 pages
                    if page_count > 8:  # More than 8 pages is likely a catalog
                        print(f"    PDF has {page_count} pages - likely a catalog")
                        return None
                    elif page_count == 0:
                        print(f"    PDF appears empty")
                        return None
                    
                    print(f"    Valid spec sheet: {page_count} pages, {file_size_mb:.1f}MB")
                    return str(temp_path)
                    
            except Exception as e:
                print(f"    PDF validation failed: {e}")
                return None
                
        except Exception as e:
            print(f"    Download error: {e}")
            return None

    def get_fallback_spec(self, component):
        """Get cached spec only as last resort"""
        specs_dir = Path("assets/specs")
        
        part_mappings = {
            'BHW-SQ-03-A1': 'bhw-sq-03-a1_spec.pdf',
            'FF2-02-M2': 'ff2-02-m2_spec.pdf', 
            'XR-LUG-04-A1': 'xr-lug-04-a1_spec.pdf',
            'UFO-END-01-A1': 'ufo-end-01-a1_spec.pdf',
            'UFO-CL-01-A1': 'ufo-cl-01-a1_spec.pdf',
            'XR100-BOSS-01-M1': 'xr100-boss-01-m1_spec.pdf',
            'XR-100-168A': 'xr-100-168a_spec.pdf',
            'XR-100-204A': 'xr-100-204a_spec.pdf',
            'Q.PEAK DUO BLK ML-G10 400': 'q.peak_duo_blk_ml-g10_400_spec.pdf',
            'IQ8A-72-2-US': 'iq8a-72-2-us_spec.pdf'
        }
        
        part_number = component.get('part_number', '').strip()
        part_name = component.get('part_name', '').strip()
        
        for identifier in [part_number, part_name]:
            if identifier in part_mappings:
                spec_path = specs_dir / part_mappings[identifier]
                if spec_path.exists():
                    print(f"    Using cached fallback")
                    return str(spec_path)
        
        return None

    def find_single_spec_sheet(self, component):
        """Find exactly ONE specific spec sheet per component"""
        
        # Step 1: Smart search with Exa.ai + LLM filtering
        pdf_url = self.search_for_specific_spec(component)
        if pdf_url:
            spec_path = self.download_and_validate_pdf(pdf_url, component)
            if spec_path:
                return spec_path, "online"
        
        # ONLY ACCEPT REAL ONLINE SPECS - NO CACHED FALLBACKS
        print(f"    No real manufacturer spec sheet found online")
        return None, "missing"

    def create_smart_permit(self, permit_path, bom_path):
        """Create permit with smart, filtered spec sheets"""
        
        print("🚀 SMART PERMIT GENERATOR - AI-Filtered Spec Sheets Only")
        print("=" * 60)
        
        # Read BOM
        components = self.read_bom_csv(bom_path)
        print(f"Processing {len(components)} components...")
        
        results = []
        added_spec_paths = set()  # Track already added spec sheets for deduplication
        
        # Process each component
        for i, component in enumerate(components, 1):
            component_name = component.get('part_name', 'Unknown')
            print(f"\nComponent {i}/{len(components)}: {component_name}")
            
            spec_path, status = self.find_single_spec_sheet(component)
            
            # ONLY ADD TO RESULTS IF WE FOUND A REAL ONLINE SPEC
            if status == "online" and spec_path:
                # Check for duplicates (both exact path and similar spec sheets)
                spec_filename = Path(spec_path).name.lower()
                duplicate_found = False
                
                # Exact path match
                if spec_path in added_spec_paths:
                    duplicate_found = True
                    print(f"    Spec sheet already added for another component - skipping duplicate")
                
                # Similar spec sheet detection (e.g., XR100_Rail.pdf vs XR100_Rail_US.pdf)
                else:
                    for added_path in added_spec_paths:
                        added_filename = Path(added_path).name.lower()
                        # Check for very similar filenames (same core component type)
                        if (('xr100_rail' in spec_filename and 'xr100_rail' in added_filename) or
                            ('qcells_data_sheet' in spec_filename and 'qcells_data_sheet' in added_filename) or
                            ('iq8' in spec_filename and 'iq8' in added_filename)):
                            duplicate_found = True
                            print(f"    Similar spec sheet already added - skipping similar duplicate")
                            break
                
                if not duplicate_found:
                    results.append({
                        'component': component,
                        'spec_path': spec_path,
                        'status': status
                    })
                    added_spec_paths.add(spec_path)
                    print(f"    Added real manufacturer spec to permit")
            else:
                print(f"    Skipping component - no real spec sheet found online")
        
        # Assemble permit
        print(f"\nAssembling permit with {len(results)} specific spec sheets...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output/permits")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"smart_permit_{timestamp}.pdf"
        
        writer = PdfWriter()
        
        # Add original permit pages (1-7)
        with open(permit_path, 'rb') as permit_file:
            permit_reader = PdfReader(permit_file)
            pages_to_add = min(7, len(permit_reader.pages))
            
            for i in range(pages_to_add):
                writer.add_page(permit_reader.pages[i])
        
        # Add ONLY specific spec sheets
        total_spec_pages = 0
        for result in sorted(results, key=lambda x: x['component'].get('row', 0)):
            try:
                with open(result['spec_path'], 'rb') as spec_file:
                    spec_reader = PdfReader(spec_file)
                    spec_pages = len(spec_reader.pages)
                    
                    # Add all pages from this spec sheet
                    for page in spec_reader.pages:
                        writer.add_page(page)
                    
                    total_spec_pages += spec_pages
                    component_name = result['component'].get('part_name', 'Unknown')
                    status_icon = "[ONLINE]" if result['status'] == 'online' else "[CACHED]"
                    
                    print(f"    {status_icon} {component_name}: {spec_pages} pages")
                
            except Exception as e:
                print(f"    Failed to add {result['component'].get('part_name', 'Unknown')}: {e}")
        
        # Write final PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        total_pages = pages_to_add + total_spec_pages
        online_count = sum(1 for r in results if r['status'] == 'online')
        
        print(f"\nSUCCESS! Smart permit generated:")
        print(f"   Location: {output_path}")
        print(f"   Total pages: {total_pages}")
        print(f"   Spec sheet pages: {total_spec_pages}")
        print(f"   Online specs: {online_count}/{len(components)}")
        print(f"   Coverage: {len(results)}/{len(components)}")
        
        # Open the result
        os.system(f"open '{output_path}'")
        
        return str(output_path)

def main():
    generator = SmartPermitGenerator()
    
    permit_path = "agents/560_Hester_Creek_Rd/560_Hester_Creek_Rd_Permit.pdf"
    bom_path = "agents/560_Hester_Creek_Rd/bill_of_materials.csv"
    
    result = generator.create_smart_permit(permit_path, bom_path)
    print(f"\nSmart permit ready: {result}")

if __name__ == "__main__":
    main()
