# test_permit_agent.py
from permit_ml_generator import helioscope_permit_pipeline, SolarPermitAutomation

def test_permit_agent():
    """Test the permit agent functionality"""
    
    # Initialize the automation class
    automation = SolarPermitAutomation()
    
    # Sample project description for testing
    test_project_description = """
    Residential solar installation on a 2-story single family home.
    System size: 8.5 kW DC, 7.2 kW AC
    Panel type: 320W monocrystalline panels
    Inverter: String inverter, 7.6 kW
    Roof type: Composition shingle, south-facing
    Building: 2,500 sq ft, built in 1995
    Address: 123 Main St, San Jose, CA 95110
    Electrical: 200A main panel, will need meter upgrade
    Fire setbacks: Standard residential setbacks required
    """
    
    # Test 1: Extract solar specifications
    print("=== Testing Solar Specs Extraction ===")
    try:
        solar_specs = automation.extract_solar_specs(test_project_description)
        print("✅ Solar specs extracted successfully")
        print(f"Sample fields: {list(solar_specs.keys())[:5]}...")
    except Exception as e:
        print(f"❌ Solar specs extraction failed: {e}")
    
    # Test 2: Extract electrical specifications  
    print("\n=== Testing Electrical Specs Extraction ===")
    try:
        electrical_specs = automation.extract_electrical_specs(test_project_description)
        print("✅ Electrical specs extracted successfully")
        print(f"Sample fields: {list(electrical_specs.keys())[:5]}...")
    except Exception as e:
        print(f"❌ Electrical specs extraction failed: {e}")
    
    # Test 3: Extract building specifications
    print("\n=== Testing Building Specs Extraction ===")
    try:
        building_specs = automation.extract_building_specs(test_project_description)
        print("✅ Building specs extracted successfully")
        print(f"Sample fields: {list(building_specs.keys())[:5]}...")
    except Exception as e:
        print(f"❌ Building specs extraction failed: {e}")
    
    # Test 4: Test the main pipeline function
    print("\n=== Testing Helioscope Pipeline ===")
    try:
        # Sample project data for the pipeline
        project_data = {
            "project_info": {
                "system_size_kw": 8.5,
                "panel_count": 27,
                "roof_type": "composition_shingle",
                "building_type": "residential",
                "utility": "PG&E",
                "description": test_project_description
            }
            # Optionally, you can add 'solar_system': {...} here if needed
        }
        
        result = helioscope_permit_pipeline(project_data)
        print("✅ Helioscope pipeline completed successfully")
        print(f"Result keys: {list(result.keys())}")
        
        # Print some sample results
        if 'permit_requirements' in result:
            print(f"Permit requirements found: {len(result['permit_requirements'])} items")
        if 'estimated_timeline' in result:
            print(f"Estimated timeline: {result['estimated_timeline']}")
            
    except Exception as e:
        print(f"❌ Helioscope pipeline failed: {e}")
    
    # Test 5: Test ML prediction capabilities
    print("\n=== Testing ML Predictions ===")
    try:
        project_features = {
            "system_size_kw": 8.5,
            "panel_count": 27,
            "roof_area_sqft": 1000,
            "building_age": 29,
            "utility_company": "PG&E"
        }
        
        prediction = automation.predict_solar_project(project_features)
        print("✅ ML prediction completed successfully")
        print(f"Prediction keys: {list(prediction.keys())}")
        
    except Exception as e:
        print(f"❌ ML prediction failed: {e}")

def test_simple_import():
    """Simple test to verify imports work"""
    print("=== Testing Imports ===")
    try:
        from permit_ml_generator import helioscope_permit_pipeline
        print("✅ helioscope_permit_pipeline imported successfully")
        
        from permit_ml_generator import SolarPermitAutomation
        print("✅ SolarPermitAutomation imported successfully")
        
        # Test instantiation
        automation = SolarPermitAutomation()
        print("✅ SolarPermitAutomation instantiated successfully")
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Starting Permit Agent Tests\n")
    
    # Run simple import test first
    test_simple_import()
    print("\n" + "="*50 + "\n")
    
    # Run full functionality test
    test_permit_agent()
    
    print("\n🏁 Tests completed!")