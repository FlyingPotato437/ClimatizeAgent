#!/usr/bin/env python3
"""Debug script to check PDF files"""

import pypdf
from pypdf import PdfReader
import sys

def debug_pdf(pdf_path):
    """Debug a PDF file to check its structure"""
    try:
        with open(pdf_path, 'rb') as file:
            reader = PdfReader(file)
            print(f"PDF: {pdf_path}")
            print(f"Number of pages: {len(reader.pages)}")
            
            # Check first few pages
            for i, page in enumerate(reader.pages[:3]):
                try:
                    text = page.extract_text()
                    print(f"Page {i+1}: {len(text)} characters")
                    if text.strip():
                        print(f"  Sample text: {text[:100]}...")
                    else:
                        print("  No extractable text found")
                        
                    # Check if page has content streams
                    if '/Contents' in page:
                        print(f"  Has content streams: Yes")
                    else:
                        print(f"  Has content streams: No")
                        
                except Exception as e:
                    print(f"  Error reading page {i+1}: {e}")
                    
        return True
        
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return False

if __name__ == "__main__":
    # Check original permit
    print("=== ORIGINAL PERMIT ===")
    original_path = "agents/560_Hester_Creek_Rd/560_Hester_Creek_Rd_Permit.pdf"
    debug_pdf(original_path)
    
    print("\n=== GENERATED OUTPUT ===")
    # Check most recent output
    output_path = "output/permits/permit_with_specs_20250720_114407.pdf"
    debug_pdf(output_path)
    
    print("\n=== CACHED SPEC SHEETS ===")
    # Check some cached spec sheets
    import os
    cache_dir = "assets/cache/spec_sheets"
    if os.path.exists(cache_dir):
        for filename in os.listdir(cache_dir)[:3]:  # First 3 files
            if filename.endswith('.pdf'):
                print(f"\n--- {filename} ---")
                debug_pdf(os.path.join(cache_dir, filename))
