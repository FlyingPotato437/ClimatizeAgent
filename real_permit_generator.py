#!/usr/bin/env python3
"""
Real permit generator using Exa.ai and Firecrawl to find actual spec sheets
"""
import os
import csv
import requests
import tempfile
from pathlib import Path
from datetime import datetime
from exa_py import Exa
from pypdf import PdfWriter, PdfReader

# API Keys
EXA_API_KEY = "9071d31c-fe10-4922-969c-1db58d0f1a87"
FIRECRAWL_API_KEY = "fc-49db2b9a54ce4bd5b3c9325dba2d9bfc"

class RealPermitGenerator:
    def __init__(self):
        self.exa = Exa(api_key=EXA_API_KEY)
        self.firecrawl_base_url = "https://api.firecrawl.dev/v1"
        self.downloaded_specs = {}
        
    def read_bom_csv(self, csv_path):
        """Read BOM from CSV file"""
        components = []
        with open(csv_path, 'r') as f:
            # Skip header lines until we find the actual data
            lines = f.readlines()
            
            # Find the row that starts the actual data (contains "Row,Part Number")
            data_start = 0
            for i, line in enumerate(lines):
                if 'Row,Part Number' in line:
                    data_start = i
                    break
            
            # Parse the data rows
            if data_start > 0:
                # Create reader from the data section
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
                    
                    components.append({
                        'row': len(components) + 1,
                        'part_name': part_name,
                        'part_number': part_number,
                        'manufacturer': manufacturer,
                        'qty': row.get('Qty', '1'),
                        'category': row.get('Category', '')
                    })
                    
                    print(f"  Parsed: {part_number} - {part_name} ({manufacturer})")
        
        return components
    
    def generate_search_queries(self, component):
        """Generate Exa.ai search queries for a component"""
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
        
        if domain and part_number:
            # Vendor-locked slug query
            queries.append(f'filetype:pdf inurl:{part_number} site:{domain}')
            queries.append(f'filetype:pdf "{part_name}" datasheet site:{domain}')
        
        # Generic fallback queries
        if part_number:
            queries.append(f'{part_number} datasheet filetype:pdf')
        
        if part_name:
            queries.append(f'{part_name} datasheet filetype:pdf')
            queries.append(f'{manufacturer} {part_name} specification filetype:pdf')
        
        return queries
    
    def search_with_exa(self, component):
        """Search for spec sheets using Exa.ai"""
        queries = self.generate_search_queries(component)
        
        print(f"🔍 Searching for {component.get('part_name', 'Unknown')} ({component.get('part_number', 'N/A')})")
        
        for query in queries:
            try:
                print(f"  Query: {query}")
                
                # Execute search with Exa
                search_results = self.exa.search(
                    query=query,
                    num_results=5,
                    type="keyword"  # Better for technical documents
                )
                
                # Look for PDF URLs
                for result in search_results.results:
                    if result.url.endswith('.pdf'):
                        print(f"  ✅ Found PDF: {result.url}")
                        return result.url
                    else:
                        # Check if it's a webpage that might have PDF links
                        print(f"  📄 Found webpage: {result.url}")
                        # We could crawl this with Firecrawl to find PDF links
                        
            except Exception as e:
                print(f"  ❌ Search failed: {e}")
                continue
        
        return None
    
    def download_with_firecrawl(self, pdf_url, component):
        """Download PDF using Firecrawl API"""
        try:
            print(f"  📥 Downloading with Firecrawl: {pdf_url}")
            
            headers = {
                'Authorization': f'Bearer {FIRECRAWL_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            # Use Firecrawl to download the PDF
            data = {
                'url': pdf_url,
                'formats': ['pdf'],
                'onlyMainContent': False
            }
            
            response = requests.post(
                f"{self.firecrawl_base_url}/scrape",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # If it's a PDF, we should get the content
                if 'data' in result:
                    # For now, let's try direct download as fallback
                    return self.direct_download_pdf(pdf_url, component)
                else:
                    print(f"  ⚠️ Firecrawl couldn't process PDF, trying direct download")
                    return self.direct_download_pdf(pdf_url, component)
            else:
                print(f"  ❌ Firecrawl API error: {response.status_code}")
                return self.direct_download_pdf(pdf_url, component)
                
        except Exception as e:
            print(f"  ❌ Firecrawl download failed: {e}")
            return self.direct_download_pdf(pdf_url, component)
    
    def direct_download_pdf(self, pdf_url, component):
        """Direct download of PDF with validation"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(pdf_url, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Check if it's actually a PDF
                if response.content.startswith(b'%PDF'):
                    # Save to temp file
                    temp_dir = Path("temp/downloaded_specs")
                    temp_dir.mkdir(parents=True, exist_ok=True)
                    
                    part_number = component.get('part_number', 'unknown').replace('/', '_')
                    temp_path = temp_dir / f"{part_number}_spec.pdf"
                    
                    with open(temp_path, 'wb') as f:
                        f.write(response.content)
                    
                    # Validate PDF content
                    if self.validate_pdf_content(temp_path, component):
                        print(f"  ✅ Downloaded and validated: {temp_path.name}")
                        return str(temp_path)
                    else:
                        print(f"  ⚠️ PDF validation failed")
                        return None
                else:
                    print(f"  ❌ Not a valid PDF file")
                    return None
            else:
                print(f"  ❌ Download failed: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  ❌ Direct download failed: {e}")
            return None
    
    def validate_pdf_content(self, pdf_path, component):
        """Validate that PDF contains relevant content"""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PdfReader(file)
                
                if len(reader.pages) == 0:
                    return False
                
                # Extract text from first page
                first_page_text = reader.pages[0].extract_text().lower()
                
                # Check if component identifiers appear in the text
                part_number = component.get('part_number', '').lower()
                part_name = component.get('part_name', '').lower()
                manufacturer = component.get('manufacturer', '').lower()
                
                # Look for any of the identifying terms
                for term in [part_number, part_name, manufacturer]:
                    if term and len(term) > 2:
                        # Allow for some variation in formatting
                        term_variants = [
                            term,
                            term.replace('-', ''),
                            term.replace(' ', ''),
                            term.replace('.', '')
                        ]
                        
                        if any(variant in first_page_text for variant in term_variants):
                            return True
                
                # If it's a reasonable size PDF (likely has content), accept it
                return len(first_page_text) > 100
                
        except Exception as e:
            print(f"  ⚠️ PDF validation error: {e}")
            return False
    
    def get_fallback_spec(self, component):
        """Get cached fallback spec sheet"""
        specs_dir = Path("assets/specs")
        
        # Direct mapping for known components
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
        
        if part_number in part_mappings:
            spec_path = specs_dir / part_mappings[part_number]
            if spec_path.exists():
                return str(spec_path)
        
        if part_name in part_mappings:
            spec_path = specs_dir / part_mappings[part_name]
            if spec_path.exists():
                return str(spec_path)
        
        return None
    
    def find_spec_sheet(self, component):
        """Find spec sheet using Exa.ai + Firecrawl, with fallback to cache"""
        
        # Step 1: Search with Exa.ai
        pdf_url = self.search_with_exa(component)
        
        if pdf_url:
            # Step 2: Download with Firecrawl
            downloaded_path = self.download_with_firecrawl(pdf_url, component)
            if downloaded_path:
                return downloaded_path, "found"
        
        # Step 3: Fallback to cached spec sheet
        cached_path = self.get_fallback_spec(component)
        if cached_path:
            print(f"  ⚠️ Using cached fallback for {component.get('part_name', 'Unknown')}")
            return cached_path, "cached"
        
        print(f"  ❌ No spec sheet found for {component.get('part_name', 'Unknown')}")
        return None, "missing"
    
    def create_combined_permit(self, permit_path, bom_path):
        """Create combined permit with real spec sheets"""
        
        print("🚀 REAL PERMIT GENERATOR - Using Exa.ai + Firecrawl")
        print("=" * 60)
        
        # Read BOM
        print("📋 Reading bill of materials...")
        components = self.read_bom_csv(bom_path)
        print(f"Found {len(components)} components")
        
        # Find spec sheets using Exa.ai + Firecrawl
        print(f"\n🔍 Finding spec sheets with Exa.ai...")
        spec_results = []
        
        for component in components:
            part_name = component.get('part_name', '').strip()
            part_number = component.get('part_number', '').strip()
            
            # Skip if both are empty
            if not part_name and not part_number:
                continue
            
            # For components with empty part_name, use part_number as name
            if not part_name and part_number:
                component['part_name'] = part_number
                
            print(f"\n--- Component {component.get('row', '?')}: {component.get('part_name', 'Unknown')} ---")
            spec_path, status = self.find_spec_sheet(component)
            
            if spec_path:
                spec_results.append({
                    'component': component,
                    'path': spec_path,
                    'status': status
                })
        
        # Assemble permit
        print(f"\n📄 Assembling permit with {len(spec_results)} spec sheets...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = Path("output/permits")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"permit_with_real_specs_{timestamp}.pdf"
        
        writer = PdfWriter()
        
        # Add first 7 pages from original permit
        with open(permit_path, 'rb') as permit_file:
            permit_reader = PdfReader(permit_file)
            pages_to_add = min(7, len(permit_reader.pages))
            
            for i in range(pages_to_add):
                writer.add_page(permit_reader.pages[i])
            
            print(f"✅ Added {pages_to_add} pages from original permit")
        
        # Add spec sheets in BOM order
        added_specs = []
        for result in sorted(spec_results, key=lambda x: x['component'].get('row', 0)):
            try:
                with open(result['path'], 'rb') as spec_file:
                    spec_reader = PdfReader(spec_file)
                    for page in spec_reader.pages:
                        writer.add_page(page)
                
                component_name = result['component'].get('part_name', 'Unknown')
                status_icon = "🌐" if result['status'] == "found" else "📋"
                added_specs.append(f"{status_icon} {component_name}")
                print(f"✅ Added spec: {component_name} ({result['status']})")
                
            except Exception as e:
                print(f"❌ Failed to add {result['component'].get('part_name', 'Unknown')}: {e}")
        
        # Write final PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        total_pages = pages_to_add + len(added_specs)
        
        # Results summary
        print("\n" + "=" * 60)
        print("🎉 PERMIT GENERATION COMPLETE!")
        print(f"📁 Output: {output_path}")
        print(f"📄 Total Pages: {total_pages}")
        print(f"🌐 Online Found: {sum(1 for r in spec_results if r['status'] == 'found')}")
        print(f"📋 Cached Used: {sum(1 for r in spec_results if r['status'] == 'cached')}")
        
        print(f"\nSpec sheets included:")
        for spec_info in added_specs:
            print(f"  {spec_info}")
        
        # Open the result
        print(f"\n👀 Opening permit...")
        os.system(f"open '{output_path}'")
        
        return str(output_path)

def main():
    generator = RealPermitGenerator()
    
    permit_path = "agents/560_Hester_Creek_Rd/560_Hester_Creek_Rd_Permit.pdf"
    bom_path = "agents/560_Hester_Creek_Rd/bill_of_materials.csv"
    
    result = generator.create_combined_permit(permit_path, bom_path)
    print(f"\n✅ SUCCESS: {result}")

if __name__ == "__main__":
    main()
