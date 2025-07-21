#!/usr/bin/env python3
"""
ClimatizeAI Permit Generation Demo
Complete end-to-end workflow for generating permit documents with spec sheets.

This demo implements the workflow you requested:
1. Processes BOM from CSV
2. Searches for spec sheets using Exa.ai
3. Downloads and validates PDFs using Firecrawl
4. Assembles final permit with first 7 pages + spec sheets
"""
import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.append(str(Path(__file__).parent / "backend"))

from services.permit_spec_generator import PermitSpecGenerator

# Configure clean logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Your API credentials
EXA_API_KEY = "9071d31c-fe10-4922-969c-1db58d0f1a87"
FIRECRAWL_API_KEY = "fc-49db2b9a54ce4bd5b3c9325dba2d9bfc"

# Demo file paths
PERMIT_PDF_PATH = "agents/560_Hester_Creek_Rd/560_Hester_Creek_Rd_Permit.pdf"
BOM_CSV_PATH = "agents/560_Hester_Creek_Rd/bill_of_materials.csv"
RESEARCH_NOTES_PATH = "agents/research_output/perplexity/560_Hester_Creek_Rd"


async def main():
    """Run the complete permit generation demo."""
    
    print("=" * 60)
    print("🏗️  CLIMATIZE AI - PERMIT GENERATION DEMO")
    print("=" * 60)
    print()
    
    # Verify input files exist
    if not Path(PERMIT_PDF_PATH).exists():
        print(f"❌ ERROR: Permit PDF not found: {PERMIT_PDF_PATH}")
        return
    
    if not Path(BOM_CSV_PATH).exists():
        print(f"❌ ERROR: BOM CSV not found: {BOM_CSV_PATH}")
        return
    
    print(f"📄 Input Files:")
    print(f"   • Permit PDF: {PERMIT_PDF_PATH}")
    print(f"   • BOM CSV: {BOM_CSV_PATH}")
    print(f"   • Research Notes: {RESEARCH_NOTES_PATH}")
    print()
    
    try:
        # Initialize the permit generator
        print("🔧 Initializing Permit Generator...")
        generator = PermitSpecGenerator(EXA_API_KEY, FIRECRAWL_API_KEY)
        print("✅ Generator initialized with API keys")
        print()
        
        # Run the complete workflow
        print("🚀 Starting End-to-End Workflow...")
        print("   This will:")
        print("   1. Process Bill of Materials")
        print("   2. Search for component spec sheets using Exa.ai")
        print("   3. Download PDFs using Firecrawl (or use cache)")
        print("   4. Validate spec sheet content")
        print("   5. Assemble final permit document")
        print()
        
        # Check if research notes exist
        research_path = RESEARCH_NOTES_PATH if Path(RESEARCH_NOTES_PATH).exists() else None
        
        # Run the complete workflow
        results = await generator.generate_permit_with_specs(
            PERMIT_PDF_PATH,
            BOM_CSV_PATH,
            research_path
        )
        
        # Display results
        print("=" * 60)
        print("📊 RESULTS SUMMARY")
        print("=" * 60)
        
        print(f"Status: {'✅ SUCCESS' if results['status'] == 'ok' else '❌ FAILED'}")
        print(f"Output PDF: {results['output_pdf']}")
        print(f"Processing Time: {results['processing_time']}")
        print()
        
        print("📈 Component Analysis:")
        summary = results['summary']
        print(f"   • Total Components: {summary['total_components']}")
        print(f"   • Found via Search: {summary['found']}")
        print(f"   • Found in Cache: {summary['cached']}")
        print(f"   • Missing: {summary['missing']}")
        print(f"   • Success Rate: {summary['success_rate']}")
        print()
        
        print("🔍 Component Search Log:")
        for log_message in results['logs']:
            print(f"   {log_message}")
        
        if results['missing']:
            print(f"\n⚠️  Missing Components: {', '.join(results['missing'])}")
        
        print()
        print("=" * 60)
        print("🎉 DELIVERABLE READY!")
        print("=" * 60)
        print(f"📋 Final permit document: {results['output_pdf']}")
        print("📄 Document structure:")
        print("   • Pages 1-7: Original permit design pages")
        print("   • Pages 8+: Component specification sheets")
        print("   • Ready for AHJ submission (after manual review)")
        print()
        
        # Show file info
        output_path = Path(results['output_pdf'])
        if output_path.exists():
            file_size = output_path.stat().st_size / 1024  # KB
            print(f"📁 File size: {file_size:.1f} KB")
        
        print("\n🎯 Workflow Complete!")
        print("The permit is ready for:")
        print("   • Engineering review")
        print("   • Legal signatures") 
        print("   • Installer wet-stamps")
        print("   • AHJ submission")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        logger.exception("Workflow failed")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main()) 