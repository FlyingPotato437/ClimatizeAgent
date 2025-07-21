#!/usr/bin/env python3
"""
Demo script for testing the Permit Specification Generator
Tests the end-to-end workflow for generating permit documents with spec sheets.
"""
import asyncio
import logging
import os
from pathlib import Path
import sys

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent / "backend"))

from services.permit_spec_generator import PermitSpecGenerator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Keys - replace with your actual keys
EXA_API_KEY = "9071d31c-fe10-4922-969c-1db58d0f1a87"
FIRECRAWL_API_KEY = "fc-49db2b9a54ce4bd5b3c9325dba2d9bfc"

# File paths for the demo
PERMIT_PDF_PATH = "agents/560_Hester_Creek_Rd/560_Hester_Creek_Rd_Permit.pdf"
BOM_CSV_PATH = "agents/560_Hester_Creek_Rd/bill_of_materials.csv"
RESEARCH_NOTES_PATH = "agents/research_output/perplexity/560_Hester_Creek_Rd"


async def test_bom_processing():
    """Test BOM processing and normalization."""
    logger.info("=== Testing BOM Processing ===")
    
    generator = PermitSpecGenerator(EXA_API_KEY, FIRECRAWL_API_KEY)
    components = generator._process_bom(BOM_CSV_PATH)
    
    logger.info(f"Found {len(components)} components:")
    for component in components:
        logger.info(f"  Row {component.row}: {component.part_name} ({component.manufacturer}) - Qty: {component.qty}")
    
    return components


async def test_search_queries():
    """Test search query generation for components."""
    logger.info("=== Testing Search Query Generation ===")
    
    generator = PermitSpecGenerator(EXA_API_KEY, FIRECRAWL_API_KEY)
    components = generator._process_bom(BOM_CSV_PATH)
    
    # Test query generation for a few components
    test_components = components[:3]  # First 3 components
    
    for component in test_components:
        queries = generator._generate_search_queries(component)
        logger.info(f"\nComponent: {component.part_name}")
        logger.info(f"Manufacturer: {component.manufacturer}")
        logger.info("Generated queries:")
        for i, query in enumerate(queries, 1):
            logger.info(f"  {i}. {query}")


async def test_single_component_search():
    """Test searching for a single component spec sheet."""
    logger.info("=== Testing Single Component Search ===")
    
    generator = PermitSpecGenerator(EXA_API_KEY, FIRECRAWL_API_KEY)
    components = generator._process_bom(BOM_CSV_PATH)
    
    # Test with the first component that has a name
    test_component = None
    for component in components:
        if component.part_name and component.part_name.strip():
            test_component = component
            break
    
    if test_component:
        logger.info(f"Testing search for: {test_component.part_name}")
        
        # Create a semaphore for testing
        semaphore = asyncio.Semaphore(1)
        
        try:
            result = await generator._retrieve_component_spec_sheet(
                test_component, {}, semaphore
            )
            
            logger.info(f"Search result: {result.status}")
            logger.info(f"Log message: {result.log_message}")
            if result.pdf_path:
                logger.info(f"PDF saved to: {result.pdf_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return None
    else:
        logger.warning("No suitable component found for testing")
        return None


async def test_pdf_assembly():
    """Test PDF assembly with sample spec sheets."""
    logger.info("=== Testing PDF Assembly ===")
    
    generator = PermitSpecGenerator(EXA_API_KEY, FIRECRAWL_API_KEY)
    
    # Create some dummy spec sheet results for testing
    components = generator._process_bom(BOM_CSV_PATH)
    
    # For demo purposes, create mock results
    spec_results = []
    for i, component in enumerate(components[:3]):  # Use first 3 components
        # Create a mock result (in real usage, these would come from actual searches)
        from services.permit_spec_generator import SpecSheetResult
        
        result = SpecSheetResult(
            component=component,
            status='cached',  # Use cached status for demo
            pdf_path=None,    # No actual PDF for demo
            log_message=f"🔧 {component.part_name} → demo mode (no actual PDF)"
        )
        spec_results.append(result)
    
    try:
        # Test assembly with original permit PDF
        output_pdf = await generator._assemble_permit_document(
            PERMIT_PDF_PATH, spec_results
        )
        
        logger.info(f"Demo PDF assembled successfully: {output_pdf}")
        return output_pdf
        
    except Exception as e:
        logger.error(f"PDF assembly failed: {e}")
        return None


async def test_full_workflow():
    """Test the complete end-to-end workflow."""
    logger.info("=== Testing Full Workflow ===")
    
    generator = PermitSpecGenerator(EXA_API_KEY, FIRECRAWL_API_KEY)
    
    try:
        # Check if research notes exist
        research_path = RESEARCH_NOTES_PATH if Path(RESEARCH_NOTES_PATH).exists() else None
        
        logger.info("Starting full permit generation workflow...")
        results = await generator.generate_permit_with_specs(
            PERMIT_PDF_PATH,
            BOM_CSV_PATH,
            research_path
        )
        
        logger.info("=== Workflow Results ===")
        logger.info(f"Status: {results['status']}")
        logger.info(f"Output PDF: {results['output_pdf']}")
        logger.info(f"Processing time: {results['processing_time']}")
        logger.info(f"Success rate: {results['summary']['success_rate']}")
        
        logger.info("\nComponent search results:")
        for log_message in results['logs']:
            logger.info(f"  {log_message}")
        
        if results['missing']:
            logger.info(f"\nMissing components: {', '.join(results['missing'])}")
        
        return results
        
    except Exception as e:
        logger.error(f"Full workflow failed: {e}")
        return None


async def main():
    """Run all demo tests."""
    logger.info("Starting Permit Generator Demo")
    logger.info("=" * 50)
    
    # Check if required files exist
    if not Path(PERMIT_PDF_PATH).exists():
        logger.error(f"Permit PDF not found: {PERMIT_PDF_PATH}")
        return
    
    if not Path(BOM_CSV_PATH).exists():
        logger.error(f"BOM CSV not found: {BOM_CSV_PATH}")
        return
    
    try:
        # Test 1: BOM Processing
        components = await test_bom_processing()
        
        # Test 2: Search Query Generation
        await test_search_queries()
        
        # Test 3: Single Component Search (optional - requires API calls)
        search_test = os.getenv('TEST_SEARCH', 'false').lower() == 'true'
        if search_test:
            await test_single_component_search()
        else:
            logger.info("Skipping search test (set TEST_SEARCH=true to enable)")
        
        # Test 4: PDF Assembly
        await test_pdf_assembly()
        
        # Test 5: Full Workflow (optional - requires API calls)
        full_test = os.getenv('TEST_FULL', 'false').lower() == 'true'
        if full_test:
            await test_full_workflow()
        else:
            logger.info("Skipping full workflow test (set TEST_FULL=true to enable)")
        
        logger.info("=" * 50)
        logger.info("Demo completed successfully!")
        
        # Print usage instructions
        logger.info("\nTo run with actual API calls:")
        logger.info("  TEST_SEARCH=true python demo_permit_generator.py")
        logger.info("  TEST_FULL=true python demo_permit_generator.py")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 