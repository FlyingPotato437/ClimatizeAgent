#!/usr/bin/env python3
"""
Script to rename files in Aurora project directories:
- Rename .dxf files to "one-line-diagram.dxf"
- Rename CSV files starting with "Aurora Shade Report" to "Aurora-Shade-Report.csv"
- Rename CSV files ending with "Bill of Materials.csv" to "Bill-of-Materials.csv"
- Keep "Hourly-Production-Estimate.csv" unchanged
"""

import os
import glob
from pathlib import Path

def rename_aurora_files():
    """Rename files in all Aurora project directories"""
    
    # Path to aurora projects directory
    aurora_dir = Path("aurora_projects")
    
    if not aurora_dir.exists():
        print(f"Error: Directory {aurora_dir} does not exist")
        return
    
    # Counter for renamed files
    dxf_renamed = 0
    shade_report_renamed = 0
    bom_renamed = 0
    
    print("Starting file renaming process...")
    print("=" * 50)
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(aurora_dir):
        root_path = Path(root)
        
        # Skip the aurora_projects directory itself
        if root_path == aurora_dir:
            continue
            
        print(f"\nProcessing directory: {root_path}")
        
        for file in files:
            file_path = root_path / file
            
            # Handle .dxf files
            if file.lower().endswith('.dxf'):
                if file != "one-line-diagram.dxf":
                    new_name = "one-line-diagram.dxf"
                    new_path = root_path / new_name
                    
                    # Check if target file already exists
                    if new_path.exists():
                        print(f"  Skipping {file} - {new_name} already exists")
                        continue
                    
                    try:
                        file_path.rename(new_path)
                        print(f"  Renamed: {file} → {new_name}")
                        dxf_renamed += 1
                    except Exception as e:
                        print(f"  Error renaming {file}: {e}")
            
            # Handle CSV files
            elif file.lower().endswith('.csv'):
                new_name = None
                
                # Aurora Shade Report files
                if file.startswith("Aurora Shade Report"):
                    new_name = "Aurora-Shade-Report.csv"
                
                # Bill of Materials files (ending with "Bill of Materials.csv")
                elif file.endswith("Bill of Materials.csv"):
                    new_name = "Bill-of-Materials.csv"
                
                # Hourly Production Estimate files - keep as is
                elif file == "Hourly-Production-Estimate.csv":
                    continue
                
                # Apply the rename if we have a new name
                if new_name:
                    new_path = root_path / new_name
                    
                    # Check if target file already exists
                    if new_path.exists():
                        print(f"  Skipping {file} - {new_name} already exists")
                        continue
                    
                    try:
                        file_path.rename(new_path)
                        print(f"  Renamed: {file} → {new_name}")
                        if new_name == "Aurora-Shade-Report.csv":
                            shade_report_renamed += 1
                        elif new_name == "Bill-of-Materials.csv":
                            bom_renamed += 1
                    except Exception as e:
                        print(f"  Error renaming {file}: {e}")
    
    print("\n" + "=" * 50)
    print("Renaming complete!")
    print(f"Total .dxf files renamed: {dxf_renamed}")
    print(f"Total Aurora Shade Report files renamed: {shade_report_renamed}")
    print(f"Total Bill of Materials files renamed: {bom_renamed}")
    print(f"Total files processed: {dxf_renamed + shade_report_renamed + bom_renamed}")

def preview_changes():
    """Preview what files would be renamed without actually renaming them"""
    
    aurora_dir = Path("aurora_projects")
    
    if not aurora_dir.exists():
        print(f"Error: Directory {aurora_dir} does not exist")
        return
    
    print("Preview of files that would be renamed:")
    print("=" * 50)
    
    dxf_to_rename = []
    shade_report_to_rename = []
    bom_to_rename = []
    
    # Walk through all subdirectories
    for root, dirs, files in os.walk(aurora_dir):
        root_path = Path(root)
        
        # Skip the aurora_projects directory itself
        if root_path == aurora_dir:
            continue
            
        for file in files:
            file_path = root_path / file
            
            # Check .dxf files
            if file.lower().endswith('.dxf'):
                if file != "one-line-diagram.dxf":
                    dxf_to_rename.append((str(file_path), "one-line-diagram.dxf"))
            
            # Check CSV files
            elif file.lower().endswith('.csv'):
                if file.startswith("Aurora Shade Report"):
                    shade_report_to_rename.append((str(file_path), "Aurora-Shade-Report.csv"))
                elif file.endswith("Bill of Materials.csv"):
                    bom_to_rename.append((str(file_path), "Bill-of-Materials.csv"))
                # Hourly-Production-Estimate.csv files are left unchanged
    
    print(f"\n.dxf files to rename ({len(dxf_to_rename)}):")
    for old_path, new_name in dxf_to_rename:
        print(f"  {old_path} → {new_name}")
    
    print(f"\nAurora Shade Report files to rename ({len(shade_report_to_rename)}):")
    for old_path, new_name in shade_report_to_rename:
        print(f"  {old_path} → {new_name}")
    
    print(f"\nBill of Materials files to rename ({len(bom_to_rename)}):")
    for old_path, new_name in bom_to_rename:
        print(f"  {old_path} → {new_name}")
    
    print(f"\nTotal files that would be renamed: {len(dxf_to_rename) + len(shade_report_to_rename) + len(bom_to_rename)}")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_changes()
    else:
        # Ask for confirmation before proceeding
        print("This script will rename files in all Aurora project directories.")
        print("Files to be renamed:")
        print("- .dxf files → one-line-diagram.dxf")
        print("- CSV files starting with 'Aurora Shade Report' → Aurora-Shade-Report.csv")
        print("- CSV files ending with 'Bill of Materials.csv' → Bill-of-Materials.csv")
        print("- Hourly-Production-Estimate.csv files will remain unchanged")
        print("\nRun with --preview to see what would be renamed without making changes.")
        
        response = input("\nDo you want to proceed? (y/N): ")
        if response.lower() in ['y', 'yes']:
            rename_aurora_files()
        else:
            print("Operation cancelled.") 