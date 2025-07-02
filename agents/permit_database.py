import json
from typing import Dict, List, Optional
from pathlib import Path
import requests
from urllib.parse import urljoin, urlparse
import os

class PermitDatabase:
    """Database of real permit information with actual agency URLs"""
    
    def __init__(self, database_path: str = "./data/permit_database.json"):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(exist_ok=True)
        self.permit_data = self._load_database()
    
    def _load_database(self) -> Dict:
        """Load permit database from JSON file"""
        if self.database_path.exists():
            with open(self.database_path, 'r') as f:
                return json.load(f)
        else:
            # Initialize with empty structure
            return {"agencies": {}, "permits": {}}
    
    def _save_database(self):
        """Save permit database to JSON file"""
        with open(self.database_path, 'w') as f:
            json.dump(self.permit_data, f, indent=2)
    
    def add_agency(self, agency_id: str, name: str, website: str):
        """Add a new agency to the database"""
        self.permit_data["agencies"][agency_id] = {
            "name": name,
            "website": website
        }
        self._save_database()
    
    def add_permit(self, permit_id: str, name: str, agency_id: str, 
                   form_url: str, requirements: List[str]):
        """Add a new permit to the database"""
        self.permit_data["permits"][permit_id] = {
            "name": name,
            "agency_id": agency_id,
            "form_url": form_url,
            "requirements": requirements
        }
        self._save_database()
    
    def get_permit_by_type(self, permit_type: str) -> Optional[Dict]:
        """Get permit information by type (e.g., 'building', 'electrical', 'environmental')"""
        for permit_id, permit in self.permit_data["permits"].items():
            if permit_type.lower() in permit["name"].lower():
                return permit
        return None
    
    def get_agency_permits(self, agency_id: str) -> List[Dict]:
        """Get all permits for a specific agency"""
        return [
            permit for permit_id, permit in self.permit_data["permits"].items()
            if permit["agency_id"] == agency_id
        ]
    
    def validate_url(self, url: str) -> bool:
        """Validate if a URL is accessible"""
        try:
            response = requests.head(url, timeout=10, allow_redirects=True)
            return response.status_code == 200
        except:
            return False
    
    def update_permit_status(self, permit_id: str, status: str):
        """Update the status of a permit (e.g., 'active', 'inactive', 'updated')"""
        if permit_id in self.permit_data["permits"]:
            self.permit_data["permits"][permit_id]["status"] = status
            self.permit_data["permits"][permit_id]["last_updated"] = None  # Add timestamp
            self._save_database()

class PermitDownloader:
    """Download permit forms from agency websites"""
    
    def __init__(self, download_dir: str = "./downloads/permits"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download_permit_form(self, form_url: str, permit_name: str) -> Optional[str]:
        """Download a permit form from the given URL"""
        try:
            # Create filename from permit name
            safe_name = "".join(c for c in permit_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}_form.pdf"
            filepath = self.download_dir / filename
            
            # Download the form
            response = requests.get(form_url, timeout=30)
            response.raise_for_status()
            
            # Save the file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return str(filepath)
            
        except Exception as e:
            print(f"Error downloading permit form: {str(e)}")
            return None
    
    def download_agency_forms(self, agency_id: str, permit_db: PermitDatabase) -> Dict[str, str]:
        """Download all forms for a specific agency"""
        results = {}
        agency_permits = permit_db.get_agency_permits(agency_id)
        
        for permit in agency_permits:
            if permit.get("form_url"):
                filepath = self.download_permit_form(permit["form_url"], permit["name"])
                if filepath:
                    results[permit["name"]] = filepath
        
        return results

class PermitFormFiller:
    """Fill out permit forms with project data"""
    
    def __init__(self, field_mappings_path: str = "./data/field_mappings.json"):
        self.field_mappings_path = Path(field_mappings_path)
        self.field_mappings_path.parent.mkdir(exist_ok=True)
        self.mappings = self._load_field_mappings()
    
    def _load_field_mappings(self) -> Dict:
        """Load field mappings from JSON file"""
        if self.field_mappings_path.exists():
            with open(self.field_mappings_path, 'r') as f:
                return json.load(f)
        else:
            return {}
    
    def _save_field_mappings(self):
        """Save field mappings to JSON file"""
        with open(self.field_mappings_path, 'w') as f:
            json.dump(self.mappings, f, indent=2)
    
    def add_field_mapping(self, permit_type: str, form_field: str, project_field: str, 
                         transformation: Optional[str] = None):
        """Add a mapping between form fields and project data fields"""
        if permit_type not in self.mappings:
            self.mappings[permit_type] = {}
        
        self.mappings[permit_type][form_field] = {
            "project_field": project_field,
            "transformation": transformation
        }
        self._save_field_mappings()
    
    def fill_permit_form(self, permit_type: str, project_data: Dict, 
                        form_template_path: str) -> Dict[str, str]:
        """Fill out a permit form with project data"""
        if permit_type not in self.mappings:
            return {"error": f"No field mappings found for permit type: {permit_type}"}
        
        filled_form = {}
        
        for form_field, mapping in self.mappings[permit_type].items():
            project_field = mapping["project_field"]
            transformation = mapping.get("transformation")
            
            # Get value from project data
            value = self._get_nested_value(project_data, project_field)
            
            # Apply transformation if specified
            if transformation and value:
                value = self._apply_transformation(value, transformation)
            
            filled_form[form_field] = value
        
        return filled_form
    
    def _get_nested_value(self, data: Dict, field_path: str):
        """Get value from nested dictionary using dot notation"""
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _apply_transformation(self, value, transformation: str):
        """Apply transformation to a value"""
        if transformation == "uppercase":
            return str(value).upper()
        elif transformation == "lowercase":
            return str(value).lower()
        elif transformation == "title":
            return str(value).title()
        elif transformation.startswith("format_date"):
            # Add date formatting logic
            return value
        else:
            return value

# Example usage and initialization
def initialize_sample_database():
    """Initialize the database with sample real permit data"""
    db = PermitDatabase()
    
    # Real California agencies
    db.add_agency(
        "california_energy_commission",
        "California Energy Commission",
        "https://www.energy.ca.gov"
    )
    
    db.add_agency(
        "california_department_of_water_resources", 
        "California Department of Water Resources",
        "https://water.ca.gov"
    )
    
    # Sample permits with real URLs
    db.add_permit(
        "cec_solar_thermal",
        "Solar Thermal Power Plant Certification",
        "california_energy_commission",
        "https://www.energy.ca.gov/sitingcases/solar_thermal/forms",
        ["Environmental Impact Report", "Technical Specifications"]
    )
    
    return db

if __name__ == "__main__":
    # Initialize sample database
    db = initialize_sample_database()
    print("✓ Sample permit database initialized")
    
    # Test downloader
    downloader = PermitDownloader()
    print("✓ Permit downloader initialized")
    
    # Test form filler
    filler = PermitFormFiller()
    print("✓ Permit form filler initialized") 