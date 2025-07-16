import json
import os
from openai import OpenAI
from datetime import datetime

# Configuration
YOUR_API_KEY = os.getenv("PERPLEXITY_API_KEY")
if not YOUR_API_KEY:
    raise ValueError("PERPLEXITY_API_KEY environment variable is required")
PROMPT_FILE = "prompts/perplexity_prompt1"
CONTEXT_FILE_1 = "560_Hester_Creek_Rd/project.json"
CONTEXT_FILE_2 = "560_Hester_Creek_Rd/systems.json"
OUTPUT_FILE = f"perplexity_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

def extract_primary_info(project_json, systems_json):
    """Extract primary information from project and systems JSON files"""
    
    # Extract key project information
    project_info = {
        "address": project_json.get("address", "Unknown"),
        "country": project_json.get("country_name", "Unknown"),
        "state": project_json.get("state", "Unknown"),
        "county": project_json.get("county", "Unknown"),
        "created_date": project_json.get("created_date", "Unknown"),
        "customer": {
            "name": project_json.get("contacts_data", [{}])[0].get("display", "Unknown") if project_json.get("contacts_data") else "Unknown",
            "phone": project_json.get("contacts_data", [{}])[0].get("phone", "Unknown") if project_json.get("contacts_data") else "Unknown"
        }
    }
    
    # Extract key system information
    if systems_json and len(systems_json) > 0:
        system = systems_json[0]  # Get first system
        system_info = {
            "nameplate_capacity_kw": system.get("kw_stc", 0),
            "total_cost": system.get("price_including_tax", 0),
            "annual_generation_kwh": system.get("output_annual_kwh", 0),
            "consumption_offset_percentage": system.get("consumption_offset_percentage", 0),
            "co2_reduction_tons": system.get("co2_tons_lifetime", 0),
            "net_profit": system.get("net_profit", 0),
            "modules": {
                "quantity": system.get("module_quantity", 0),
                "details": []
            },
            "inverters": {
                "details": []
            },
            "mounting_system": {
                "details": []
            }
        }
        
        # Extract module details
        for module in system.get("modules", []):
            system_info["modules"]["details"].append({
                "manufacturer": module.get("manufacturer_name", "Unknown"),
                "model": module.get("code", "Unknown"),
                "quantity": module.get("quantity", 0)
            })
        
        # Extract inverter details
        for inverter in system.get("inverters", []):
            system_info["inverters"]["details"].append({
                "manufacturer": inverter.get("manufacturer_name", "Unknown"),
                "model": inverter.get("code", "Unknown"),
                "quantity": inverter.get("quantity", 0)
            })
        
        # Extract mounting system details
        for other in system.get("others", []):
            system_info["mounting_system"]["details"].append({
                "manufacturer": other.get("manufacturer_name", "Unknown"),
                "model": other.get("code", "Unknown"),
                "quantity": other.get("quantity", 0)
            })
    else:
        system_info = {}
    
    return {
        "project": project_info,
        "system": system_info
    }

def load_file_content(filename):
    """Load content from a file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: {filename} not found")
        return ""

def load_json_context(filename):
    """Load JSON context from a file"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Warning: {filename} not found")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: {filename} contains invalid JSON")
        return {}

def save_response_to_json(response_data, output_filename):
    """Save the response to a JSON file"""
    response_dict = {
        "timestamp": datetime.now().isoformat(),
        "model": response_data.model,
        "usage": {
            "prompt_tokens": response_data.usage.prompt_tokens,
            "completion_tokens": response_data.usage.completion_tokens,
            "total_tokens": response_data.usage.total_tokens
        },
        "choices": []
    }
    
    for choice in response_data.choices:
        choice_dict = {
            "index": choice.index,
            "message": {
                "role": choice.message.role,
                "content": choice.message.content
            },
            "finish_reason": choice.finish_reason
        }
        response_dict["choices"].append(choice_dict)
    
    with open(output_filename, 'w', encoding='utf-8') as f:
        json.dump(response_dict, f, indent=2, ensure_ascii=False)
    
    print(f"Response saved to: {output_filename}")

def test_extraction():
    """Test the extraction function to verify it works properly"""
    print("Testing extraction function...")
    print("-" * 50)
    
    # Load context JSON files
    project_json = load_json_context(CONTEXT_FILE_1)
    systems_json = load_json_context(CONTEXT_FILE_2)
    
    if not project_json:
        print("ERROR: Could not load project.json")
        return False
    
    if not systems_json:
        print("ERROR: Could not load systems.json")
        return False
    
    # Extract primary information
    primary_info = extract_primary_info(project_json, systems_json)
    
    # Print extracted information
    print("EXTRACTED PROJECT INFORMATION:")
    print(json.dumps(primary_info, indent=2))
    print("-" * 50)
    
    # Check key fields
    print("KEY FIELD VERIFICATION:")
    project = primary_info.get("project", {})
    system = primary_info.get("system", {})
    
    print(f"✓ Address: {project.get('address', 'MISSING')}")
    print(f"✓ Nameplate Capacity: {system.get('nameplate_capacity_kw', 'MISSING')} kW")
    print(f"✓ Total Cost: ${system.get('total_cost', 'MISSING'):,}")
    print(f"✓ Annual Generation: {system.get('annual_generation_kwh', 'MISSING'):,} kWh")
    print(f"✓ Customer: {project.get('customer', {}).get('name', 'MISSING')}")
    
    # Check modules
    modules = system.get("modules", {})
    if modules.get("details"):
        print(f"✓ Modules: {len(modules['details'])} types found")
        for module in modules["details"]:
            print(f"  - {module['manufacturer']} {module['model']} x{module['quantity']}")
    
    # Check inverters
    inverters = system.get("inverters", {})
    if inverters.get("details"):
        print(f"✓ Inverters: {len(inverters['details'])} types found")
        for inverter in inverters["details"]:
            print(f"  - {inverter['manufacturer']} {inverter['model']} x{inverter['quantity']}")
    
    # Check mounting system
    mounting = system.get("mounting_system", {})
    if mounting.get("details"):
        print(f"✓ Mounting System: {len(mounting['details'])} components found")
        for component in mounting["details"]:
            print(f"  - {component['manufacturer']} {component['model']} x{component['quantity']}")
    
    print("-" * 50)
    print("Extraction test completed successfully!")
    return True

def main():
    # Test extraction first
    if not test_extraction():
        print("Extraction test failed. Please check your JSON files.")
        return
    
    # Ask user if they want to proceed
    response = input("\nDo you want to proceed with the API call? (y/n): ")
    if response.lower() != 'y':
        print("API call cancelled.")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=YOUR_API_KEY, base_url="https://api.perplexity.ai")
    
    # Load prompt from file
    prompt_content = load_file_content(PROMPT_FILE)
    if not prompt_content:
        print(f"Error: Could not load prompt from {PROMPT_FILE}")
        return
    
    # Load context JSON files
    project_json = load_json_context(CONTEXT_FILE_1)
    systems_json = load_json_context(CONTEXT_FILE_2)
    
    # Extract primary information instead of using full JSON
    primary_info = extract_primary_info(project_json, systems_json)
    
    # Prepare context string from extracted primary information
    context_string = f"Project Information: {json.dumps(primary_info, indent=2)}\n\n"
    
    # Prepare messages
    messages = [
        {
            "role": "system",
            "content": (
                "You are a solar project development expert with deep knowledge of renewable energy projects, "
                "permitting, grid interconnection, and financial analysis. Use the provided project information "
                "to inform your responses."
            ),
        },
        {
            "role": "user",
            "content": f"{context_string}Prompt: {prompt_content}"
        },
    ]
    
    print("Sending request to Perplexity API...")
    print(f"Prompt file: {PROMPT_FILE}")
    print(f"Context files: {CONTEXT_FILE_1}, {CONTEXT_FILE_2}")
    print(f"Output file: {OUTPUT_FILE}")
    print(f"Extracted info keys: {list(primary_info.keys())}")
    print("-" * 50)
    
    try:
        # Make API call
        response = client.chat.completions.create(
            model="sonar-reasoning-pro",
            messages=messages,
            max_tokens=4000,
            temperature=0.1,
            stream=False
        )
        
        # Save response to JSON
        save_response_to_json(response, OUTPUT_FILE)
        
        # Print first part of response
        if response.choices:
            content = response.choices[0].message.content
            print("\nFirst 500 characters of response:")
            print("-" * 50)
            print(content[:500] + "..." if len(content) > 500 else content)
        
    except Exception as e:
        print(f"Error making API call: {e}")

if __name__ == "__main__":
    main()