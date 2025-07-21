#!/usr/bin/env python3
"""
Simple permit generator without external dependencies
"""
import os
import csv
import shutil
from pathlib import Path
from datetime import datetime

def read_bom_csv(csv_path):
    """Read BOM from CSV file"""
    components = []
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            components.append({
                'row': i,
                'part_name': row.get('Part Name', ''),
                'part_number': row.get('Part Number', ''),
                'manufacturer': row.get('Manufacturer', ''),
                'qty': row.get('Qty', '1')
            })
    return components

def find_spec_sheet(component):
    """Find spec sheet for component"""
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
    
    # Try direct mapping first
    part_number = component.get('part_number', '').strip()
    part_name = component.get('part_name', '').strip()
    
    # Check direct part number mapping
    if part_number in part_mappings:
        spec_path = specs_dir / part_mappings[part_number]
        if spec_path.exists():
            return str(spec_path)
    
    # Check direct part name mapping
    if part_name in part_mappings:
        spec_path = specs_dir / part_mappings[part_name]
        if spec_path.exists():
            return str(spec_path)
    
    # Fallback: try pattern matching
    patterns = [
        f"{part_number.lower().replace('-', '-')}_spec.pdf",
        f"{part_name.lower().replace(' ', '_').replace('.', '')}_spec.pdf"
    ]
    
    for pattern in patterns:
        spec_path = specs_dir / pattern
        if spec_path.exists():
            return str(spec_path)
    
    # Final fallback: partial name matching
    for pdf_file in specs_dir.glob("*.pdf"):
        filename = pdf_file.name.lower()
        if part_number and part_number.lower().replace('-', '') in filename.replace('-', '').replace('_', ''):
            return str(pdf_file)
        if part_name and any(word.lower() in filename for word in part_name.split() if len(word) > 2):
            return str(pdf_file)
    
    return None

def create_simple_combined_pdf():
    """Create a simple combined PDF using system tools"""
    
    print("🚀 Creating combined permit document...")
    
    # Paths
    permit_path = "agents/560_Hester_Creek_Rd/560_Hester_Creek_Rd_Permit.pdf"
    bom_path = "agents/560_Hester_Creek_Rd/bill_of_materials.csv"
    output_dir = Path("output/permits")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Read BOM
    print("📋 Reading bill of materials...")
    components = read_bom_csv(bom_path)
    print(f"Found {len(components)} components")
    
    # Find spec sheets
    print("\n🔍 Finding spec sheets...")
    spec_sheets = []
    for component in components:
        spec_path = find_spec_sheet(component)
        if spec_path:
            spec_sheets.append(spec_path)
            print(f"✅ {component['part_name']} → {Path(spec_path).name}")
        else:
            print(f"❌ {component['part_name']} → not found")
    
    print(f"\n📄 Found {len(spec_sheets)} spec sheets")
    
    # Create timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"permit_with_specs_{timestamp}.pdf"
    
    # Use Python to copy first 7 pages and then add spec sheets
    try:
        import pypdf
        from pypdf import PdfWriter, PdfReader
        
        writer = PdfWriter()
        
        # Add first 7 pages from original permit
        print(f"\n📖 Reading original permit: {permit_path}")
        with open(permit_path, 'rb') as permit_file:
            permit_reader = PdfReader(permit_file)
            pages_to_add = min(7, len(permit_reader.pages))
            
            for i in range(pages_to_add):
                writer.add_page(permit_reader.pages[i])
            
            print(f"✅ Added {pages_to_add} pages from original permit")
        
        # Add spec sheets
        print(f"\n📋 Adding {len(spec_sheets)} spec sheets...")
        for i, spec_path in enumerate(spec_sheets, 1):
            try:
                with open(spec_path, 'rb') as spec_file:
                    spec_reader = PdfReader(spec_file)
                    for page in spec_reader.pages:
                        writer.add_page(page)
                
                print(f"✅ Added spec sheet {i}: {Path(spec_path).name}")
                
            except Exception as e:
                print(f"⚠️ Error adding {Path(spec_path).name}: {e}")
        
        # Write final PDF
        with open(output_path, 'wb') as output_file:
            writer.write(output_file)
        
        total_pages = pages_to_add + len(spec_sheets)
        print(f"\n🎉 SUCCESS! Created permit with {total_pages} pages")
        print(f"📁 Output: {output_path}")
        
        # Open the file
        print("\n👀 Opening PDF...")
        os.system(f"open '{output_path}'")
        
        return str(output_path)
        
    except ImportError:
        print("❌ pypdf not available. Using system pdftk if available...")
        
        # Fallback: use system tools
        try:
            # Create temp directory for preparation
            temp_dir = Path("temp/pdf_assembly")
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy permit (first 7 pages) - we'll use pdftk if available
            permit_copy = temp_dir / "permit_pages_1_7.pdf"
            
            # Use pdftk to extract first 7 pages
            extract_cmd = f"pdftk '{permit_path}' cat 1-7 output '{permit_copy}'"
            if os.system(extract_cmd) != 0:
                # Fallback: copy entire permit
                shutil.copy(permit_path, permit_copy)
                print("⚠️ Could not extract first 7 pages, using full permit")
            
            # Combine all PDFs
            all_pdfs = [str(permit_copy)] + spec_sheets
            combine_cmd = f"pdftk {' '.join(all_pdfs)} cat output '{output_path}'"
            
            if os.system(combine_cmd) == 0:
                print(f"🎉 SUCCESS! Created permit using pdftk")
                print(f"📁 Output: {output_path}")
                os.system(f"open '{output_path}'")
                return str(output_path)
            else:
                print("❌ pdftk not available")
                
        except Exception as e:
            print(f"❌ System tools failed: {e}")
    
    return None

if __name__ == "__main__":
    result = create_simple_combined_pdf()
    if result:
        print(f"\n✅ Final permit ready: {result}")
    else:
        print("\n❌ Failed to create permit. Please install pypdf or pdftk.")
