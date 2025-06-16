import azure.functions as func
import logging
import json
import sys
import os
import requests
import openai
from datetime import datetime

# Add the parent directory to the path to import shared models
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.models import (
    UnifiedProjectModel, Address, SystemSpecs, Financials, BillOfMaterialItem, 
    RoofType, FeasibilityPackage, ProductionMetrics, BatterySpecs, 
    InterconnectionScore, PermitMatrix, ProForma, SiteControlDocument
)
from shared_utils import CosmosDBClient, BlobStorageClient, invoke_function

app = func.FunctionApp()

@app.route(route="quick_look_feasibility", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def quick_look_feasibility_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint that receives minimal project details to generate a Quick-Look Feasibility Pack.
    
    Workflow:
    1. Parse input: address (or lat/lon, parcel ID), roof_type, annual_kWh_load.
    2. Create a new UnifiedProjectModel with 'Manual' data_source.
    3. Save the initial project to Cosmos DB.
    4. Invoke the first agent in the chain: `helioscope_design_engine`.
    5. Return 202 Accepted with the project_id to poll for results.
    """
    logging.info('Processing Quick-Look Feasibility request.')
    
    try:
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )

        # Basic validation
        if not req_body.get('address'):
            return func.HttpResponse(
                json.dumps({"error": "Address is required"}),
                status_code=400,
                mimetype="application/json"
            )

        # Create a partial project structure from the input
        project_data = {
            "project_name": f"Feasibility Study for {req_body['address'].get('street', 'Unknown Location')}",
            "data_source": "Manual",
            "address": req_body.get('address'),
            "system_specs": {
                "system_size_dc_kw": req_body.get('system_size_dc_kw', 100.0), # Default size
                "module_count": 0, # To be filled by design engine
                "inverter_type": 'string', # Default
                "roof_type": req_body.get('roof_type', 'flat'),
                "annual_kwh_load": req_body.get('annual_kwh_load'),
                "bill_of_materials": []
            },
            "financials": {}
        }

        project = UnifiedProjectModel(**project_data)
        
        # Save initial project to Cosmos DB
        cosmos_client = CosmosDBClient()
        project_dict = project.dict()
        cosmos_client.create_project(project_dict)
        logging.info(f"Successfully created initial project {project.project_id}")
        
        # Invoke the first agent in the workflow
        invoke_function("helioscope_design_engine", project.project_id)
        logging.info(f"Invoked helioscope_design_engine for project {project.project_id}")
        
        # Return response to client
        return func.HttpResponse(
            json.dumps({"project_id": project.project_id, "status": "Processing started"}),
            status_code=202,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Unexpected error in quick_look_feasibility_handler: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="get_feasibility_package/{project_id}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_feasibility_package(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint to retrieve the generated FeasibilityPackage.
    """
    project_id = req.route_params.get('project_id')
    logging.info(f'Retrieving feasibility package for project {project_id}.')
    
    try:
        cosmos_client = CosmosDBClient()
        project = cosmos_client.get_project(project_id)
        
        if not project:
            return func.HttpResponse(
                json.dumps({"error": "Project not found"}),
                status_code=404,
                mimetype="application/json"
            )
            
        # Check if processing is complete (simple check on a late-stage milestone)
        if project.get('milestones', {}).get('financing', 'Not Started') == 'Not Started':
             return func.HttpResponse(
                json.dumps({"project_id": project_id, "status": "In progress"}),
                status_code=202, # Still processing
                mimetype="application/json"
            )

        # Format the full project model into the FeasibilityPackage
        package = format_project_as_feasibility_package(project)

        return func.HttpResponse(
            json.dumps(package.dict(), default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error retrieving feasibility package for {project_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve package"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="manual_intake_handler", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def manual_intake_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint that receives manual project data from the frontend form.
    
    Logic:
    1. Parse the incoming JSON body into a UnifiedProjectModel
    2. Set data_source to 'Manual'
    3. Save the validated model to Cosmos DB
    4. Invoke the permit_matrix_engine function
    5. Return 201 Created with the new project object
    """
    logging.info('Processing manual project intake request.')
    
    try:
        # Parse request body
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Ensure data source is set to Manual
        req_body['data_source'] = 'Manual'
        
        # Validate data using Pydantic model
        try:
            project = UnifiedProjectModel(**req_body)
        except Exception as validation_error:
            logging.error(f"Validation error: {str(validation_error)}")
            return func.HttpResponse(
                json.dumps({"error": f"Invalid project data: {str(validation_error)}"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Save to Cosmos DB
        try:
            cosmos_client = CosmosDBClient()
            project_dict = project.dict()
            saved_project = cosmos_client.create_project(project_dict)
            logging.info(f"Successfully saved project {project.project_id} to database")
        except Exception as db_error:
            logging.error(f"Database error: {str(db_error)}")
            return func.HttpResponse(
                json.dumps({"error": "Failed to save project to database"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Invoke permit matrix engine
        try:
            invoke_function("helioscope_design_engine", project.project_id)
            logging.info(f"Invoked helioscope_design_engine for project {project.project_id}")
        except Exception as invoke_error:
            logging.warning(f"Failed to invoke helioscope_design_engine: {str(invoke_error)}")
            # Don't fail the request if function invocation fails
        
        # Return success response
        return func.HttpResponse(
            json.dumps(project_dict, default=str),
            status_code=201,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Unexpected error in manual_intake_handler: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="get_all_projects", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_all_projects(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint that returns all projects for the dashboard.
    """
    logging.info('Retrieving all projects.')
    
    try:
        cosmos_client = CosmosDBClient()
        projects = cosmos_client.get_all_projects()
        
        return func.HttpResponse(
            json.dumps(projects, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error retrieving projects: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve projects"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="get_project/{project_id}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_project(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint that returns a single project by ID.
    """
    project_id = req.route_params.get('project_id')
    logging.info(f'Retrieving project {project_id}.')
    
    try:
        cosmos_client = CosmosDBClient()
        project = cosmos_client.get_project(project_id)
        
        if not project:
            return func.HttpResponse(
                json.dumps({"error": "Project not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        return func.HttpResponse(
            json.dumps(project, default=str),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error retrieving project {project_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to retrieve project"}),
            status_code=500,
            mimetype="application/json"
        )

@app.route(route="aurora_webhook_receiver", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def aurora_webhook_receiver(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint that receives Aurora webhook notifications.
    Immediately returns 200 OK and queues the design_id for background processing.
    """
    logging.info('Received Aurora webhook notification.')
    
    try:
        req_body = req.get_json()
        if not req_body:
            return func.HttpResponse(
                json.dumps({"error": "Request body is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        design_id = req_body.get('design_id')
        if not design_id:
            return func.HttpResponse(
                json.dumps({"error": "design_id is required"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # In a real implementation, this would add the design_id to a queue
        # For now, we'll invoke the parser directly
        invoke_function("aurora_parser", design_id)
        
        return func.HttpResponse(
            json.dumps({"message": "Webhook received successfully"}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error processing Aurora webhook: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Internal server error"}),
            status_code=500,
            mimetype="application/json"
        )

@app.function_name(name="aurora_parser")
@app.queue_trigger(arg_name="msg", queue_name="aurora-designs", connection="AzureWebJobsStorage")
def aurora_parser(msg: func.QueueMessage) -> None:
    """
    Queue-triggered function that processes Aurora design data.
    
    Logic:
    1. Extract design_id from queue message
    2. Call Aurora API to get design summary and pricing
    3. Transform Aurora data into UnifiedProjectModel schema
    4. Save the model to Cosmos DB
    5. Invoke permit_matrix_engine
    """
    logging.info('Processing Aurora design data.')
    
    try:
        # Get design_id from queue message
        design_id = msg.get_body().decode('utf-8')
        if not design_id:
            logging.error("No design_id found in queue message")
            return
        
        logging.info(f"Processing Aurora design {design_id}")
        
        # Aurora API credentials (should be stored in environment variables)
        aurora_api_key = os.environ.get('AURORA_API_KEY')
        aurora_base_url = os.environ.get('AURORA_BASE_URL', 'https://api.aurorasolar.com/v1')
        
        if not aurora_api_key:
            logging.error("AURORA_API_KEY environment variable not set")
            return
        
        headers = {
            'Authorization': f'Bearer {aurora_api_key}',
            'Content-Type': 'application/json'
        }
        
        # Fetch design summary from Aurora API
        try:
            design_response = requests.get(
                f"{aurora_base_url}/designs/{design_id}/summary",
                headers=headers,
                timeout=30
            )
            design_response.raise_for_status()
            design_data = design_response.json()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch design data from Aurora: {str(e)}")
            return
        
        # Fetch pricing data from Aurora API
        try:
            pricing_response = requests.get(
                f"{aurora_base_url}/designs/{design_id}/pricing",
                headers=headers,
                timeout=30
            )
            pricing_response.raise_for_status()
            pricing_data = pricing_response.json()
        except requests.RequestException as e:
            logging.error(f"Failed to fetch pricing data from Aurora: {str(e)}")
            pricing_data = {}
        
        # Transform Aurora data to UnifiedProjectModel
        try:
            project_data = transform_aurora_data(design_data, pricing_data)
            project = UnifiedProjectModel(**project_data)
        except Exception as transform_error:
            logging.error(f"Failed to transform Aurora data: {str(transform_error)}")
            return
        
        # Save to Cosmos DB
        try:
            cosmos_client = CosmosDBClient()
            project_dict = project.dict()
            saved_project = cosmos_client.create_project(project_dict)
            logging.info(f"Successfully saved Aurora project {project.project_id} to database")
        except Exception as db_error:
            logging.error(f"Database error: {str(db_error)}")
            return
        
        # Invoke permit matrix engine
        try:
            invoke_function("helioscope_design_engine", project.project_id)
            logging.info(f"Invoked helioscope_design_engine for Aurora project {project.project_id}")
        except Exception as invoke_error:
            logging.warning(f"Failed to invoke helioscope_design_engine: {str(invoke_error)}")
        
        logging.info(f"Successfully processed Aurora design {design_id}")
        
    except Exception as e:
        logging.error(f"Unexpected error in aurora_parser: {str(e)}")

def transform_aurora_data(design_data: dict, pricing_data: dict) -> dict:
    """
    Transform Aurora API data into UnifiedProjectModel format.
    """
    # Extract address information
    address_data = design_data.get('site', {}).get('address', {})
    address = Address(
        street=address_data.get('street', ''),
        city=address_data.get('city', ''),
        state=address_data.get('state', ''),
        zip_code=address_data.get('postal_code', '')
    )
    
    # Extract system specifications
    system_data = design_data.get('design', {})
    
    # Extract module information
    modules = system_data.get('modules', [])
    total_modules = sum(module.get('count', 0) for module in modules)
    
    # Create bill of materials from Aurora data
    bill_of_materials = []
    
    # Add modules
    for module in modules:
        if module.get('count', 0) > 0:
            bill_of_materials.append(BillOfMaterialItem(
                component_type='module',
                manufacturer=module.get('manufacturer', ''),
                model=module.get('model', ''),
                quantity=module.get('count', 0)
            ))
    
    # Add inverters
    inverters = system_data.get('inverters', [])
    for inverter in inverters:
        if inverter.get('count', 0) > 0:
            bill_of_materials.append(BillOfMaterialItem(
                component_type='inverter',
                manufacturer=inverter.get('manufacturer', ''),
                model=inverter.get('model', ''),
                quantity=inverter.get('count', 0)
            ))
    
    # Determine inverter type
    inverter_type = 'string'  # default
    if inverters and len(inverters) > 0:
        first_inverter = inverters[0]
        if 'micro' in first_inverter.get('model', '').lower():
            inverter_type = 'microinverter'
    
    system_specs = SystemSpecs(
        system_size_dc_kw=system_data.get('dc_capacity', 0) / 1000,  # Convert W to kW
        module_count=total_modules,
        inverter_type=inverter_type,
        bill_of_materials=bill_of_materials
    )
    
    # Extract financial information
    estimated_capex = pricing_data.get('total_cost', 0)
    price_per_watt = pricing_data.get('price_per_watt', 0)
    
    financials = Financials(
        estimated_capex=estimated_capex,
        price_per_watt=price_per_watt,
        incentives=[],
        capital_stack=None
    )
    
    # Create project name from address and system size
    project_name = f"Solar Project - {address.city}, {address.state} ({system_specs.system_size_dc_kw:.1f} kW)"
    
    return {
        'project_name': project_name,
        'data_source': 'Aurora',
        'address': address.dict(),
        'system_specs': system_specs.dict(),
        'financials': financials.dict()
    }

@app.function_name(name="helioscope_design_engine")
@app.queue_trigger(arg_name="msg", queue_name="helioscope-design", connection="AzureWebJobsStorage")
def helioscope_design_engine(msg: func.QueueMessage) -> None:
    """
    Queue-triggered function to generate PV design and production estimates.
    Mocks a call to HelioScope API for now.
    """
    project_id = msg.get_body().decode('utf-8')
    logging.info(f"Starting HelioScope design for project {project_id}")
    
    try:
        cosmos_client = CosmosDBClient()
        project = cosmos_client.get_project(project_id)
        
        # MOCK: Call HelioScope autodesign API
        system_size_dc_kw = project['system_specs']['system_size_dc_kw']
        system_size_ac_kw = system_size_dc_kw * 0.85 # Simple assumption
        annual_production_kwh = system_size_dc_kw * 1300 # Regional assumption
        
        production_metrics = ProductionMetrics(
            annual_production_kwh=annual_production_kwh,
            specific_yield=annual_production_kwh / system_size_dc_kw,
            performance_ratio=0.85,
            kwh_per_kw=annual_production_kwh / system_size_ac_kw,
            capacity_factor=(annual_production_kwh / (system_size_ac_kw * 8760))
        )
        
        updates = {
            'system_specs.system_size_ac_kw': system_size_ac_kw,
            'production_metrics': production_metrics.dict(),
            'milestones.engineering': 'Conceptual Design'
        }
        cosmos_client.update_project(project_id, updates)
        
        logging.info(f"Generated conceptual design for project {project_id}")
        invoke_function("battery_sizing_engine", project.project_id)

    except Exception as e:
        logging.error(f"Error in helioscope_design_engine for {project_id}: {e}")

@app.function_name(name="battery_sizing_engine")
@app.queue_trigger(arg_name="msg", queue_name="battery-sizing", connection="AzureWebJobsStorage")
def battery_sizing_engine(msg: func.QueueMessage) -> None:
    """
    Sizes a battery using a simple peak-shave heuristic.
    """
    project_id = msg.get_body().decode('utf-8')
    logging.info(f"Starting battery sizing for project {project_id}")
    
    try:
        cosmos_client = CosmosDBClient()
        project = cosmos_client.get_project(project_id)
        
        # Heuristic: Size battery to 25% of system's AC power for 2 hours
        if project.get('system_specs', {}).get('system_size_ac_kw'):
            ac_kw = project['system_specs']['system_size_ac_kw']
            battery_power_kw = ac_kw * 0.25
            battery_energy_kwh = battery_power_kw * 2 # 2-hour duration
            
            battery_specs = BatterySpecs(
                power_kw=battery_power_kw,
                energy_kwh=battery_energy_kwh,
                duration_hours=2
            )
            
            updates = {
                'system_specs.battery_specs': battery_specs.dict()
            }
            cosmos_client.update_project(project_id, updates)
            logging.info(f"Sized battery for project {project_id}")
        
        invoke_function("interconnection_scorer", project.project_id)

    except Exception as e:
        logging.error(f"Error in battery_sizing_engine for {project_id}: {e}")

@app.function_name(name="interconnection_scorer")
@app.queue_trigger(arg_name="msg", queue_name="interconnection-scoring", connection="AzureWebJobsStorage")
def interconnection_scorer(msg: func.QueueMessage) -> None:
    """
    Generates a static interconnection score (stub).
    """
    project_id = msg.get_body().decode('utf-8')
    logging.info(f"Starting interconnection scoring for project {project_id}")
    
    try:
        cosmos_client = CosmosDBClient()
        # MOCK: Static score for now
        interconnection_score = InterconnectionScore(
            score=75,
            utility_name="Pacific Gas & Electric",
            estimated_timeline="6-9 months",
            risk_factors=["Substation capacity may be limited"]
        )
        
        updates = {
            'interconnection_score': interconnection_score.dict(),
            'milestones.interconnection': 'Initial Screen'
        }
        cosmos_client.update_project(project_id, updates)
        
        logging.info(f"Scored interconnection for project {project_id}")
        invoke_function("permit_matrix_engine", project.project_id)

    except Exception as e:
        logging.error(f"Error in interconnection_scorer for {project_id}: {e}")

@app.function_name(name="permit_matrix_engine")
@app.queue_trigger(arg_name="msg", queue_name="permit-matrix", connection="AzureWebJobsStorage")
def permit_matrix_engine(msg: func.QueueMessage) -> None:
    """
    Queue-triggered function that generates permit matrix for a project.
    
    Logic:
    1. Fetch the UnifiedProjectModel from Cosmos DB
    2. Call shovels.ai API with the project's address to get the geo_id
    3. Call shovels.ai for jurisdiction details and current metrics
    4. Generate a JSON object representing the permit matrix
    5. Update the project document in Cosmos DB with the permit matrix and set milestones.permitting to 'Matrix Generated'
    6. Invoke the feasibility_and_site_control function
    """
    logging.info('Generating permit matrix.')
    
    try:
        # Get project_id from queue message
        project_id = msg.get_body().decode('utf-8')
        if not project_id:
            logging.error("No project_id found in queue message")
            return
        
        logging.info(f"Generating permit matrix for project {project_id}")
        
        # Fetch project from Cosmos DB
        try:
            cosmos_client = CosmosDBClient()
            project = cosmos_client.get_project(project_id)
            if not project:
                logging.error(f"Project {project_id} not found in database")
                return
        except Exception as db_error:
            logging.error(f"Failed to fetch project from database: {str(db_error)}")
            return
        
        # Call shovels.ai API to get jurisdiction information
        try:
            permit_matrix = generate_permit_matrix(project['address'])
        except Exception as matrix_error:
            logging.error(f"Failed to generate permit matrix: {str(matrix_error)}")
            # Create a fallback permit matrix
            permit_matrix = create_fallback_permit_matrix(project['address'])
        
        # Update project with permit matrix and milestone
        try:
            updates = {
                'permit_matrix': permit_matrix,
                'milestones': {
                    **project.get('milestones', {}),
                    'permitting': 'Matrix Generated'
                }
            }
            cosmos_client.update_project(project_id, updates)
            logging.info(f"Updated project {project_id} with permit matrix")
        except Exception as update_error:
            logging.error(f"Failed to update project with permit matrix: {str(update_error)}")
            return
        
        # Invoke feasibility and site control function
        try:
            invoke_function("feasibility_and_site_control", project_id)
            logging.info(f"Invoked feasibility_and_site_control for project {project_id}")
        except Exception as invoke_error:
            logging.warning(f"Failed to invoke feasibility_and_site_control: {str(invoke_error)}")
        
        logging.info(f"Successfully generated permit matrix for project {project_id}")
        
    except Exception as e:
        logging.error(f"Unexpected error in permit_matrix_engine: {str(e)}")

def generate_permit_matrix(address: dict) -> dict:
    """
    Generate permit matrix using shovels.ai API and local rules.
    """
    shovels_api_key = os.environ.get('SHOVELS_API_KEY')
    
    # If shovels.ai API is not available, create a mock permit matrix
    if not shovels_api_key:
        logging.warning("SHOVELS_API_KEY not configured, using fallback permit matrix")
        return create_fallback_permit_matrix(address)
    
    try:
        # Call shovels.ai API to get geo_id
        address_string = f"{address['street']}, {address['city']}, {address['state']} {address['zip_code']}"
        
        headers = {
            'Authorization': f'Bearer {shovels_api_key}',
            'Content-Type': 'application/json'
        }
        
        # Get geo_id from address
        geo_response = requests.get(
            f"https://api.shovels.ai/geocode",
            params={'address': address_string},
            headers=headers,
            timeout=30
        )
        geo_response.raise_for_status()
        geo_data = geo_response.json()
        geo_id = geo_data.get('geo_id')
        
        if not geo_id:
            logging.warning("No geo_id found from shovels.ai, using fallback")
            return create_fallback_permit_matrix(address)
        
        # Get jurisdiction details
        jurisdiction_response = requests.get(
            f"https://api.shovels.ai/jurisdictions/{geo_id}",
            headers=headers,
            timeout=30
        )
        jurisdiction_response.raise_for_status()
        jurisdiction_data = jurisdiction_response.json()
        
        # Generate permit matrix from shovels.ai data
        return create_permit_matrix_from_shovels_data(jurisdiction_data, address)
        
    except requests.RequestException as e:
        logging.error(f"Shovels.ai API error: {str(e)}")
        return create_fallback_permit_matrix(address)
    except Exception as e:
        logging.error(f"Error generating permit matrix: {str(e)}")
        return create_fallback_permit_matrix(address)

def create_permit_matrix_from_shovels_data(jurisdiction_data: dict, address: dict) -> dict:
    """
    Create enhanced permit matrix from shovels.ai jurisdiction data with dynamic checklists.
    """
    state = address.get('state', '').upper()
    city = address.get('city', '').lower()
    
    jurisdiction_info = {
        'jurisdiction_name': jurisdiction_data.get('name', f"{address['city']}, {address['state']}"),
        'jurisdiction_type': jurisdiction_data.get('type', 'Municipal'),
        'solar_friendly_rating': jurisdiction_data.get('solar_friendly_rating', 7),
        'average_approval_time': jurisdiction_data.get('average_approval_time', '6-8 weeks'),
        'typical_requirements': jurisdiction_data.get('typical_requirements', [
            'Building permit application',
            'Electrical permit application',
            'Structural engineering report',
            'Site plan review'
        ]),
        'special_considerations': jurisdiction_data.get('special_considerations', []),
        'utility_name': jurisdiction_data.get('utility_name', get_utility_by_location(state, city)),
        'ahj_contact_info': jurisdiction_data.get('contact_info', {})
    }
    
    # Generate permit requirements based on jurisdiction data and state-specific rules
    permit_requirements = generate_dynamic_permit_requirements(jurisdiction_data, address, state)
    
    total_cost = sum(permit['estimated_cost'] for permit in permit_requirements)
    
    # Enhanced risk assessment
    risk_factors = []
    green_flags = []
    
    if jurisdiction_info['solar_friendly_rating'] < 6:
        risk_factors.append("Low solar-friendly rating may indicate longer approval times")
    elif jurisdiction_info['solar_friendly_rating'] >= 8:
        green_flags.append("High solar-friendly rating suggests streamlined approval process")
    
    if jurisdiction_data.get('recent_policy_changes', False):
        risk_factors.append("Recent policy changes may affect approval process")
    
    if jurisdiction_data.get('online_permitting', False):
        green_flags.append("Online permitting system available for faster processing")
    
    # State-specific considerations
    state_considerations = get_state_specific_considerations(state)
    risk_factors.extend(state_considerations.get('risk_factors', []))
    green_flags.extend(state_considerations.get('green_flags', []))
    
    return {
        'jurisdiction_info': jurisdiction_info,
        'permit_requirements': permit_requirements,
        'total_estimated_cost': total_cost,
        'total_estimated_timeline': calculate_total_timeline(permit_requirements),
        'risk_factors': risk_factors,
        'green_flags': green_flags,
        'development_checklist': generate_development_checklist_from_permits(permit_requirements),
        'critical_path': identify_critical_path(permit_requirements)
    }

def generate_dynamic_permit_requirements(jurisdiction_data: dict, address: dict, state: str) -> list:
    """
    Generate dynamic permit requirements based on jurisdiction and state rules.
    """
    requirements = []
    
    # Base building permit
    building_permit = {
        'permit_type': 'Building Permit',
        'authority': jurisdiction_data.get('name', f"{address['city']}, {address['state']}"),
        'estimated_timeline': jurisdiction_data.get('building_permit_timeline', '3-4 weeks'),
        'estimated_cost': jurisdiction_data.get('building_permit_cost', 500),
        'complexity': determine_complexity(jurisdiction_data, 'building'),
        'requirements': get_building_permit_requirements(state),
        'status': 'Not Started',
        'priority': 'High',
        'dependencies': []
    }
    requirements.append(building_permit)
    
    # Electrical permit
    electrical_permit = {
        'permit_type': 'Electrical Permit',
        'authority': jurisdiction_data.get('name', f"{address['city']}, {address['state']}"),
        'estimated_timeline': jurisdiction_data.get('electrical_permit_timeline', '2-3 weeks'),
        'estimated_cost': jurisdiction_data.get('electrical_permit_cost', 300),
        'complexity': determine_complexity(jurisdiction_data, 'electrical'),
        'requirements': get_electrical_permit_requirements(state),
        'status': 'Not Started',
        'priority': 'High',
        'dependencies': ['Building Permit']
    }
    requirements.append(electrical_permit)
    
    # Utility interconnection
    interconnection_permit = {
        'permit_type': 'Utility Interconnection',
        'authority': jurisdiction_data.get('utility_name', get_utility_by_location(state, address.get('city', '').lower())),
        'estimated_timeline': get_interconnection_timeline(state),
        'estimated_cost': jurisdiction_data.get('interconnection_cost', 1000),
        'complexity': 'High',
        'requirements': get_interconnection_requirements(state),
        'status': 'Not Started',
        'priority': 'Critical',
        'dependencies': []
    }
    requirements.append(interconnection_permit)
    
    # State-specific permits
    state_permits = get_state_specific_permits(state, jurisdiction_data)
    requirements.extend(state_permits)
    
    # Add zoning review if required
    if jurisdiction_data.get('requires_zoning_review', True):
        zoning_permit = {
            'permit_type': 'Zoning Review',
            'authority': f"{address['city']} Zoning Department",
            'estimated_timeline': '2-4 weeks',
            'estimated_cost': 250,
            'complexity': 'Low',
            'requirements': [
                'Zoning permit application',
                'Site plan with setbacks',
                'Proof of property ownership',
                'Compliance with local zoning codes'
            ],
            'status': 'Not Started',
            'priority': 'Medium',
            'dependencies': []
        }
        requirements.append(zoning_permit)
    
    return requirements

def get_building_permit_requirements(state: str) -> list:
    """Get state-specific building permit requirements."""
    base_requirements = [
        'Completed building permit application',
        'Site plan showing solar array placement',
        'Structural engineering calculations',
        'Equipment specification sheets',
        'Electrical single-line diagram'
    ]
    
    state_specific = {
        'CA': [
            'CalGreen compliance documentation',
            'Fire setback calculations',
            'Seismic analysis (if required)'
        ],
        'FL': [
            'Wind load calculations',
            'Hurricane tie-down specifications'
        ],
        'TX': [
            'Hail impact resistance certification'
        ],
        'NY': [
            'NYSERDA compliance documentation'
        ]
    }
    
    return base_requirements + state_specific.get(state, [])

def get_electrical_permit_requirements(state: str) -> list:
    """Get state-specific electrical permit requirements."""
    base_requirements = [
        'Electrical permit application',
        'Single-line electrical diagram',
        'Equipment cut sheets',
        'NEC compliance documentation',
        'Grounding and bonding plan'
    ]
    
    state_specific = {
        'CA': [
            'California Electrical Code compliance',
            'Arc fault protection documentation'
        ],
        'TX': [
            'ERCOT interconnection requirements'
        ]
    }
    
    return base_requirements + state_specific.get(state, [])

def get_interconnection_requirements(state: str) -> list:
    """Get state-specific interconnection requirements."""
    base_requirements = [
        'Interconnection application',
        'System design and equipment specs',
        'Professional engineer review',
        'Insurance certificates'
    ]
    
    state_specific = {
        'CA': [
            'Rule 21 compliance documentation',
            'Smart inverter requirements'
        ],
        'TX': [
            'ERCOT nodal protocols compliance'
        ],
        'NY': [
            'CESIR study (if >300kW)'
        ]
    }
    
    return base_requirements + state_specific.get(state, [])

def get_state_specific_permits(state: str, jurisdiction_data: dict) -> list:
    """Get additional state-specific permit requirements."""
    permits = []
    
    if state == 'CA':
        permits.append({
            'permit_type': 'Environmental Review',
            'authority': 'California Environmental Quality Act (CEQA)',
            'estimated_timeline': '4-8 weeks',
            'estimated_cost': 1500,
            'complexity': 'High',
            'requirements': [
                'CEQA compliance documentation',
                'Environmental impact assessment',
                'Mitigated negative declaration (if required)'
            ],
            'status': 'Not Started',
            'priority': 'Medium',
            'dependencies': []
        })
    
    return permits

def get_utility_by_location(state: str, city: str) -> str:
    """Get primary utility by location."""
    utility_map = {
        'CA': {
            'default': 'Pacific Gas & Electric',
            'los angeles': 'Los Angeles Department of Water and Power',
            'san diego': 'San Diego Gas & Electric'
        },
        'TX': {
            'default': 'Oncor Electric Delivery',
            'houston': 'CenterPoint Energy',
            'austin': 'Austin Energy'
        },
        'NY': {
            'default': 'Con Edison',
            'buffalo': 'National Grid'
        }
    }
    
    state_utilities = utility_map.get(state, {'default': 'Local Utility'})
    return state_utilities.get(city, state_utilities['default'])

def get_interconnection_timeline(state: str) -> str:
    """Get state-specific interconnection timelines."""
    timelines = {
        'CA': '6-12 weeks',
        'TX': '8-16 weeks',
        'NY': '4-8 weeks',
        'FL': '6-10 weeks'
    }
    return timelines.get(state, '6-10 weeks')

def get_state_specific_considerations(state: str) -> dict:
    """Get state-specific risk factors and green flags."""
    considerations = {
        'CA': {
            'risk_factors': [
                'Complex CEQA environmental review may be required',
                'Fire safety requirements in high-risk areas'
            ],
            'green_flags': [
                'Strong state incentives and net metering policies',
                'Streamlined permitting in many jurisdictions'
            ]
        },
        'TX': {
            'risk_factors': [
                'ERCOT interconnection can be complex for larger systems',
                'Limited state-level incentives'
            ],
            'green_flags': [
                'Generally business-friendly regulatory environment',
                'Strong property tax exemptions'
            ]
        },
        'NY': {
            'risk_factors': [
                'Complex utility territories and rate structures'
            ],
            'green_flags': [
                'Strong NY-Sun incentive program',
                'Standardized interconnection processes'
            ]
        }
    }
    
    return considerations.get(state, {'risk_factors': [], 'green_flags': []})

def determine_complexity(jurisdiction_data: dict, permit_type: str) -> str:
    """Determine permit complexity based on jurisdiction data."""
    solar_friendly_rating = jurisdiction_data.get('solar_friendly_rating', 7)
    
    if solar_friendly_rating >= 8:
        return 'Low'
    elif solar_friendly_rating >= 6:
        return 'Medium'
    else:
        return 'High'

def calculate_total_timeline(permit_requirements: list) -> str:
    """Calculate total project timeline considering dependencies."""
    # Simple calculation - in production would use critical path analysis
    max_timeline = 0
    
    for permit in permit_requirements:
        timeline_str = permit.get('estimated_timeline', '4 weeks')
        weeks = extract_weeks_from_timeline(timeline_str)
        if weeks > max_timeline:
            max_timeline = weeks
    
    return f"{max_timeline}-{max_timeline + 4} weeks"

def extract_weeks_from_timeline(timeline_str: str) -> int:
    """Extract maximum weeks from timeline string."""
    import re
    
    # Extract numbers from strings like "3-4 weeks", "6 weeks", etc.
    numbers = re.findall(r'\d+', timeline_str)
    if numbers:
        return max(int(num) for num in numbers)
    return 4  # Default

def generate_development_checklist_from_permits(permit_requirements: list) -> list:
    """Generate development checklist from permit requirements."""
    checklist = []
    
    for permit in permit_requirements:
        for requirement in permit.get('requirements', []):
            checklist.append({
                'category': permit['permit_type'],
                'task': requirement,
                'status': 'pending',
                'priority': permit.get('priority', 'medium').lower(),
                'estimated_timeline': permit.get('estimated_timeline', 'TBD'),
                'authority': permit.get('authority', 'TBD')
            })
    
    return checklist

def identify_critical_path(permit_requirements: list) -> list:
    """Identify critical path permits that could delay the project."""
    critical_permits = []
    
    for permit in permit_requirements:
        if (permit.get('priority') == 'Critical' or 
            permit.get('complexity') == 'High' or
            permit.get('permit_type') == 'Utility Interconnection'):
            critical_permits.append({
                'permit_type': permit['permit_type'],
                'timeline': permit['estimated_timeline'],
                'reason': 'Long lead time or high complexity'
            })
    
    return critical_permits

def create_fallback_permit_matrix(address: dict) -> dict:
    """
    Create a fallback permit matrix when external API is not available.
    """
    jurisdiction_name = f"{address['city']}, {address['state']}"
    
    jurisdiction_info = {
        'jurisdiction_name': jurisdiction_name,
        'jurisdiction_type': 'Municipal',
        'solar_friendly_rating': 7,
        'average_approval_time': '6-8 weeks',
        'typical_requirements': [
            'Building permit application',
            'Electrical permit application',
            'Structural engineering report',
            'Site plan review'
        ],
        'special_considerations': [
            'Contact local building department for specific requirements'
        ]
    }
    
    permit_requirements = [
        {
            'permit_type': 'Building Permit',
            'authority': jurisdiction_name,
            'estimated_timeline': '3-4 weeks',
            'estimated_cost': 500,
            'complexity': 'Medium',
            'requirements': [
                'Completed building permit application',
                'Site plan showing solar array placement',
                'Structural engineering calculations',
                'Equipment specification sheets'
            ],
            'status': 'Not Started'
        },
        {
            'permit_type': 'Electrical Permit',
            'authority': jurisdiction_name,
            'estimated_timeline': '2-3 weeks',
            'estimated_cost': 300,
            'complexity': 'Low',
            'requirements': [
                'Electrical permit application',
                'Single-line electrical diagram',
                'Equipment cut sheets',
                'NEC compliance documentation'
            ],
            'status': 'Not Started'
        },
        {
            'permit_type': 'Utility Interconnection',
            'authority': 'Local Utility Company',
            'estimated_timeline': '4-8 weeks',
            'estimated_cost': 1000,
            'complexity': 'High',
            'requirements': [
                'Interconnection application',
                'System design and equipment specs',
                'Professional engineer review',
                'Utility meter upgrades if required'
            ],
            'status': 'Not Started'
        }
    ]
    
    return {
        'jurisdiction_info': jurisdiction_info,
        'permit_requirements': permit_requirements,
        'total_estimated_cost': 1800,
        'total_estimated_timeline': '6-12 weeks',
        'risk_factors': [
            'Permit requirements may vary - verify with local authorities'
        ]
    }

@app.function_name(name="feasibility_and_site_control")
@app.queue_trigger(arg_name="msg", queue_name="feasibility-site-control", connection="AzureWebJobsStorage")
def feasibility_and_site_control(msg: func.QueueMessage) -> None:
    """
    Queue-triggered function that handles feasibility analysis and site control.
    
    Logic:
    1. Fetch the project model
    2. Use GPT to draft a Letter of Intent (LOI)
    3. Save the generated LOI text to Azure Blob Storage
    4. Update the project in Cosmos DB with the LOI path and set milestones.site_control to 'Drafted'
    5. Invoke the capital_stack_generator
    """
    logging.info('Processing feasibility and site control.')
    
    try:
        # Get project_id from queue message
        project_id = msg.get_body().decode('utf-8')
        if not project_id:
            logging.error("No project_id found in queue message")
            return
        
        logging.info(f"Processing feasibility and site control for project {project_id}")
        
        # Fetch project from Cosmos DB
        try:
            cosmos_client = CosmosDBClient()
            project = cosmos_client.get_project(project_id)
            if not project:
                logging.error(f"Project {project_id} not found in database")
                return
        except Exception as db_error:
            logging.error(f"Failed to fetch project from database: {str(db_error)}")
            return
        
        # Generate Letter of Intent using GPT
        try:
            loi_content = generate_letter_of_intent(project)
        except Exception as loi_error:
            logging.error(f"Failed to generate LOI: {str(loi_error)}")
            # Create a fallback LOI
            loi_content = create_fallback_loi(project)
        
        # Save LOI to blob storage
        try:
            blob_client = BlobStorageClient()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"LOI_{timestamp}.txt"
            blob_path = blob_client.upload_document(project_id, filename, loi_content)
            logging.info(f"Uploaded LOI to blob storage: {blob_path}")
        except Exception as blob_error:
            logging.error(f"Failed to upload LOI to blob storage: {str(blob_error)}")
            blob_path = None
        
        # Update project with LOI path and milestone
        try:
            updates = {
                'loi_document_path': blob_path,
                'milestones': {
                    **project.get('milestones', {}),
                    'site_control': 'Drafted'
                }
            }
            cosmos_client.update_project(project_id, updates)
            logging.info(f"Updated project {project_id} with LOI information")
        except Exception as update_error:
            logging.error(f"Failed to update project with LOI information: {str(update_error)}")
            return
        
        # Invoke capital stack generator
        try:
            invoke_function("capital_stack_generator", project_id)
            logging.info(f"Invoked capital_stack_generator for project {project_id}")
        except Exception as invoke_error:
            logging.warning(f"Failed to invoke capital_stack_generator: {str(invoke_error)}")
        
        logging.info(f"Successfully processed feasibility and site control for project {project_id}")
        
    except Exception as e:
        logging.error(f"Unexpected error in feasibility_and_site_control: {str(e)}")

def generate_letter_of_intent(project: dict) -> str:
    """
    Generate an enhanced Letter of Intent using OpenAI GPT with jurisdiction-specific templates.
    """
    openai_api_key = os.environ.get('OPENAI_API_KEY')
    
    if not openai_api_key:
        logging.warning("OPENAI_API_KEY not configured, using fallback LOI")
        return create_enhanced_fallback_loi(project)
    
    try:
        openai.api_key = openai_api_key
        
        address = project['address']
        system_specs = project['system_specs']
        permit_matrix = project.get('permit_matrix', {})
        financials = project.get('financials', {})
        
        # Build context-aware prompt with project specifics
        project_context = build_project_context(project)
        
        prompt = f"""Generate a comprehensive commercial solar site lease Letter of Intent (LOI) for a {system_specs['system_size_dc_kw']} kW DC solar project at {address['street']}, {address['city']}, {address['state']}.

Project Context:
{project_context}

The developer is Climatize, a leading solar development company. Create a professional, jurisdiction-specific LOI that includes:

1. Project Overview
2. Proposed Terms (with placeholders):
   - Landowner name: [LANDOWNER_NAME]
   - Lease rate: [LEASE_RATE_PER_ACRE] per acre per year
   - Term: [LEASE_TERM_YEARS] years
   - Site size: [SITE_ACRES] acres

3. Development Timeline and Milestones
4. Financial Benefits to Landowner
5. Environmental and Community Benefits
6. Risk Mitigation and Insurance
7. Next Steps and Contact Information

Make it jurisdiction-appropriate for {address['state']} and emphasize Climatize's expertise in solar financing and development.

Format as a professional business letter with proper legal language."""

        response = openai.ChatCompletion.create(
            model="gpt-4",  # Use GPT-4 for better document quality
            messages=[
                {"role": "system", "content": "You are an expert legal document assistant specializing in commercial solar development agreements. You understand state-specific regulations, market conditions, and industry best practices."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=2500,
            temperature=0.2  # Lower temperature for more consistent, professional output
        )
        
        loi_content = response.choices[0].message.content.strip()
        logging.info("Successfully generated enhanced LOI using OpenAI GPT-4")
        return loi_content
        
    except Exception as e:
        logging.error(f"OpenAI API error: {str(e)}")
        return create_enhanced_fallback_loi(project)

def build_project_context(project: dict) -> str:
    """
    Build comprehensive project context for AI document generation.
    """
    context_parts = []
    
    # System details
    system_specs = project['system_specs']
    context_parts.append(f"System Size: {system_specs['system_size_dc_kw']} kW DC")
    
    if project.get('production_metrics'):
        annual_production = project['production_metrics'].get('annual_production_kwh', 0)
        context_parts.append(f"Annual Production: {annual_production:,.0f} kWh")
    
    # Financial context
    financials = project.get('financials', {})
    if financials.get('estimated_capex'):
        capex = financials['estimated_capex']
        context_parts.append(f"Estimated Project Cost: ${capex:,.0f}")
    
    # Incentive context
    eligibility = project.get('eligibility_screening', {})
    if eligibility.get('incentive_score'):
        context_parts.append(f"Incentive Score: {eligibility['incentive_score']}/100")
    
    # Permit context
    permit_matrix = project.get('permit_matrix', {})
    if permit_matrix.get('jurisdiction_info'):
        solar_rating = permit_matrix['jurisdiction_info'].get('solar_friendly_rating', 0)
        context_parts.append(f"Solar-Friendly Rating: {solar_rating}/10")
    
    # Risk factors
    warnings = eligibility.get('warnings', [])
    if warnings:
        context_parts.append(f"Key Considerations: {'; '.join(warnings[:2])}")
    
    return "\n".join(f"- {part}" for part in context_parts)

def create_enhanced_fallback_loi(project: dict) -> str:
    """
    Create an enhanced fallback Letter of Intent with more details.
    """
    address = project['address']
    system_specs = project['system_specs']
    
    # Calculate estimated acreage (rough estimate: 5-7 acres per MW)
    estimated_acres = max(system_specs['system_size_dc_kw'] / 1000 * 6, 1)
    
    loi_content = f"""
LETTER OF INTENT
Commercial Solar Site Lease Agreement

Date: {datetime.now().strftime("%B %d, %Y")}

Dear [LANDOWNER_NAME],

Climatize, a leading commercial solar development company, is pleased to present this Letter of Intent (LOI) to lease approximately {estimated_acres:.1f} acres of your property located at {address['street']}, {address['city']}, {address['state']} {address['zip_code']} for the development, construction, and operation of a {system_specs['system_size_dc_kw']} kW DC solar photovoltaic energy facility.

PROJECT OVERVIEW:
This commercial-scale solar installation will generate clean, renewable energy while providing long-term financial benefits to your property. The project is designed to minimize environmental impact while maximizing economic returns for both parties.

PROPOSED LEASE TERMS:

1. ANNUAL LEASE PAYMENT: $[LEASE_RATE_PER_ACRE] per acre per year
   - Annual escalator of 2.0% to protect against inflation
   - Guaranteed minimum annual payment: $[MINIMUM_ANNUAL_PAYMENT]

2. LEASE TERM: [LEASE_TERM_YEARS] years with option to extend
   - Development period: 3-5 years
   - Operational period: 20-25 years
   - Decommissioning and restoration included

3. DEVELOPMENT ACTIVITIES & TIMELINE:
   - Phase 1 (Months 1-6): Site assessments and environmental studies
   - Phase 2 (Months 6-18): Engineering, permitting, and utility coordination
   - Phase 3 (Months 18-36): Construction and commissioning
   - Phase 4 (Years 3-25): Operations and maintenance

4. FINANCIAL BENEFITS TO LANDOWNER:
   - Stable, long-term income with annual escalations
   - Enhanced property tax base for local community
   - No operational responsibilities or maintenance costs
   - Professional liability and property insurance coverage

5. ENVIRONMENTAL & COMMUNITY BENEFITS:
   - Clean energy generation reducing carbon footprint
   - Preservation of agricultural land use compatibility
   - Local job creation during construction and operations
   - Support for local clean energy goals

6. RISK MITIGATION:
   - Comprehensive general liability insurance ($[INSURANCE_AMOUNT])
   - Environmental restoration bond posted prior to construction
   - Professional project management and monitoring
   - Proven track record of successful project development

7. CLIMATIZE ADVANTAGES:
   - Extensive experience in solar project financing
   - Streamlined development process with regulatory expertise
   - Long-term operational support and maintenance
   - Strong financial backing and project completion guarantee

NEXT STEPS:
1. Execution of this Letter of Intent
2. Site due diligence and feasibility studies (60-90 days)
3. Formal lease agreement negotiation and execution
4. Permit applications and utility interconnection process
5. Financial close and construction commencement

This project represents an excellent opportunity to generate substantial long-term income while contributing to clean energy development. We look forward to partnering with you to bring this exciting solar development to fruition.

Please contact our development team to discuss this proposal and answer any questions you may have.

Sincerely,

Climatize Development Team
Email: development@climatize.com
Phone: (555) 123-4567
Website: www.climatize.com

---
IMPORTANT: This Letter of Intent is non-binding and subject to the execution of a definitive lease agreement, completion of satisfactory due diligence, environmental assessments, permitting approvals, and utility interconnection agreements. All terms are subject to negotiation in the formal lease agreement.
    """
    
    return loi_content.strip()

def create_fallback_loi(project: dict) -> str:
    """
    Create a fallback Letter of Intent when OpenAI is not available.
    """
    address = project['address']
    system_specs = project['system_specs']
    
    loi_content = f"""
LETTER OF INTENT
Solar Site Lease Agreement

Date: {datetime.now().strftime("%B %d, %Y")}

Dear [LANDOWNER_NAME],

Climatize, a solar development company, is pleased to present this Letter of Intent (LOI) to lease approximately [ACRES] acres of your property located at {address['street']}, {address['city']}, {address['state']} {address['zip_code']} for the development, construction, and operation of a {system_specs['system_size_dc_kw']} kW DC solar photovoltaic energy facility.

PROPOSED TERMS:

1. LEASE RATE: $[LEASE_RATE_PER_ACRE] per acre per year, with annual escalations of 2%

2. LEASE TERM: [LEASE_TERM_YEARS] years with option to extend

3. DEVELOPMENT ACTIVITIES:
   - Site assessments and environmental studies
   - Surveying and engineering
   - Permitting and regulatory approvals
   - Utility interconnection studies

4. CONSTRUCTION & OPERATION:
   - Professional installation and maintenance
   - Minimal impact on existing land use
   - Restoration bond for site remediation

5. FINANCIAL BENEFITS:
   - Annual lease payments
   - Property tax revenue enhancement
   - Local economic development

6. NEXT STEPS:
   - Execution of formal lease agreement
   - Site due diligence period
   - Permitting and interconnection applications
   - Construction commencement upon approvals

This LOI represents our mutual intent to proceed with negotiations for a formal solar site lease agreement. We look forward to working with you to bring clean energy development to your property while providing long-term financial benefits.

Please contact us to discuss the next steps in this exciting opportunity.

Sincerely,

Climatize Development Team
[CONTACT_INFORMATION]

---
This Letter of Intent is non-binding and subject to execution of a definitive lease agreement and completion of all due diligence activities.
    """
    
    return loi_content.strip()

@app.function_name(name="capital_stack_generator")
@app.queue_trigger(arg_name="msg", queue_name="capital-stack", connection="AzureWebJobsStorage")
def capital_stack_generator(msg: func.QueueMessage) -> None:
    """
    Queue-triggered function that generates capital stack analysis.
    
    Logic:
    1. Fetch the project model
    2. Calculate incentives (start with 30% ITC of estimated_capex)
    3. Define a capital stack (e.g., 40% equity, 60% debt of the post-incentive cost)
    4. Update the financials.capital_stack and financials.incentives fields in the project model
    5. Invoke the final project_packager_and_scorer
    """
    logging.info('Generating capital stack analysis.')
    
    try:
        # Get project_id from queue message
        project_id = msg.get_body().decode('utf-8')
        if not project_id:
            logging.error("No project_id found in queue message")
            return
        
        logging.info(f"Generating capital stack for project {project_id}")
        
        # Fetch project from Cosmos DB
        try:
            cosmos_client = CosmosDBClient()
            project = cosmos_client.get_project(project_id)
            if not project:
                logging.error(f"Project {project_id} not found in database")
                return
        except Exception as db_error:
            logging.error(f"Failed to fetch project from database: {str(db_error)}")
            return
        
        # Generate capital stack analysis
        try:
            capital_stack, climatize_options = generate_capital_stack_analysis(project)
        except Exception as analysis_error:
            logging.error(f"Failed to generate capital stack analysis: {str(analysis_error)}")
            return
        
        # Update project with capital stack and incentives
        try:
            financials = project.get('financials', {})
            financials['capital_stack'] = capital_stack
            financials['incentives'] = climatize_options
            
            updates = {
                'financials': financials
            }
            cosmos_client.update_project(project_id, updates)
            logging.info(f"Updated project {project_id} with capital stack analysis")
        except Exception as update_error:
            logging.error(f"Failed to update project with capital stack: {str(update_error)}")
            return
        
        # Invoke project packager and scorer
        try:
            invoke_function("project_packager_and_scorer", project_id)
            logging.info(f"Invoked project_packager_and_scorer for project {project_id}")
        except Exception as invoke_error:
            logging.warning(f"Failed to invoke project_packager_and_scorer: {str(invoke_error)}")
        
        logging.info(f"Successfully generated capital stack for project {project_id}")
        
    except Exception as e:
        logging.error(f"Unexpected error in capital_stack_generator: {str(e)}")

def generate_capital_stack_analysis(project: dict) -> tuple:
    """
    Generate enhanced capital stack analysis with ITC, REAP, and Climatize loan integration.
    """
    financials = project.get('financials', {})
    system_specs = project.get('system_specs', {})
    address = project.get('address', {})
    
    # Base project cost
    estimated_capex = financials.get('estimated_capex', 0)
    if not estimated_capex and financials.get('price_per_watt') and system_specs.get('system_size_dc_kw'):
        # Calculate CapEx from price per watt if not provided
        estimated_capex = financials['price_per_watt'] * system_specs['system_size_dc_kw'] * 1000
    
    # Enhanced incentive calculation
    incentives = calculate_comprehensive_incentives(project, estimated_capex)
    
    # Calculate post-incentive cost
    total_incentive_value = sum(incentive['value'] for incentive in incentives)
    post_incentive_cost = estimated_capex - total_incentive_value
    
    # Enhanced capital stack with Climatize options
    capital_stack_options = generate_capital_stack_options(post_incentive_cost, project)
    
    # Calculate detailed financial returns
    financial_analysis = calculate_enhanced_financial_returns(
        capital_stack_options['recommended'], 
        project, 
        estimated_capex
    )
    
    # Build comprehensive capital stack
    capital_stack = {
        'total_project_cost': estimated_capex,
        'total_incentive_value': total_incentive_value,
        'post_incentive_cost': post_incentive_cost,
        'incentives_breakdown': incentives,
        'capital_stack_options': capital_stack_options,
        'recommended_structure': capital_stack_options['recommended'],
        'financial_analysis': financial_analysis,
        'climatize_advantages': get_climatize_advantages(project)
    }
    
    climatize_options = {
        'total_available_incentives': total_incentive_value,
        'climatize_loan_options': capital_stack_options['climatize_options'],
        'competitive_advantages': get_climatize_advantages(project),
        'financing_timeline': generate_financing_timeline(),
        'risk_mitigation': assess_financing_risks(project)
    }
    
    return capital_stack, climatize_options

def calculate_comprehensive_incentives(project: dict, estimated_capex: float) -> list:
    """
    Calculate all available incentives including federal, state, and REAP.
    """
    incentives = []
    address = project.get('address', {})
    system_specs = project.get('system_specs', {})
    state = address.get('state', '').upper()
    system_size_kw = system_specs.get('system_size_dc_kw', 0)
    
    # Federal Investment Tax Credit (ITC)
    federal_itc_rate = 0.30  # 30% through 2032
    federal_itc_value = estimated_capex * federal_itc_rate
    incentives.append({
        'type': 'Federal ITC',
        'description': 'Federal Investment Tax Credit (30%)',
        'percentage': federal_itc_rate,
        'value': federal_itc_value,
        'status': 'Available',
        'notes': 'Available through 2032, steps down to 26% in 2033'
    })
    
    # REAP (Rural Energy for America Program) - if applicable
    if is_reap_eligible(address, system_size_kw):
        reap_grant_rate = 0.25  # Up to 25% of project cost
        reap_max_grant = min(estimated_capex * reap_grant_rate, 500000)  # $500k max
        incentives.append({
            'type': 'USDA REAP Grant',
            'description': 'Rural Energy for America Program Grant',
            'percentage': reap_grant_rate,
            'value': reap_max_grant,
            'status': 'Potentially Available',
            'notes': 'Subject to rural location eligibility and USDA approval'
        })
    
    # State-specific incentives
    state_incentives = get_state_incentives(state, estimated_capex, system_size_kw)
    incentives.extend(state_incentives)
    
    # Accelerated depreciation (MACRS)
    macrs_benefit = estimated_capex * 0.15  # Estimated tax benefit from accelerated depreciation
    incentives.append({
        'type': 'MACRS Depreciation',
        'description': 'Modified Accelerated Cost Recovery System',
        'percentage': 0.15,
        'value': macrs_benefit,
        'status': 'Available',
        'notes': '5-year accelerated depreciation schedule'
    })
    
    return incentives

def is_reap_eligible(address: dict, system_size_kw: float) -> bool:
    """
    Determine REAP eligibility based on rural location and system size.
    """
    # Simplified eligibility check - in production, this would use USDA rural maps
    rural_states = ['IA', 'NE', 'KS', 'ND', 'SD', 'MT', 'WY', 'ID', 'UT', 'NV']
    state = address.get('state', '').upper()
    
    # REAP is for rural areas and agricultural businesses
    # System size should be reasonable for agricultural/rural commercial use
    return (state in rural_states and 50 <= system_size_kw <= 2000)

def get_state_incentives(state: str, estimated_capex: float, system_size_kw: float) -> list:
    """
    Get state-specific incentive programs.
    """
    incentives = []
    
    state_programs = {
        'CA': {
            'name': 'Self-Generation Incentive Program (SGIP)',
            'rate': 0.05,
            'max_value': 100000,
            'notes': 'For energy storage systems'
        },
        'NY': {
            'name': 'NY-Sun Incentive',
            'rate': 0.04,
            'max_value': 75000,
            'notes': 'Declining incentive program'
        },
        'NJ': {
            'name': 'Successor Solar Incentive (SuSI)',
            'rate': 0.03,
            'max_value': 50000,
            'notes': 'Performance-based incentive'
        },
        'MA': {
            'name': 'SMART Program',
            'rate': 0.06,
            'max_value': 150000,
            'notes': 'Solar Massachusetts Renewable Target'
        },
        'TX': {
            'name': 'Property Tax Exemption',
            'rate': 0.02,
            'max_value': 25000,
            'notes': 'Ongoing property tax savings'
        }
    }
    
    if state in state_programs:
        program = state_programs[state]
        value = min(estimated_capex * program['rate'], program['max_value'])
        incentives.append({
            'type': 'State Incentive',
            'description': program['name'],
            'percentage': program['rate'],
            'value': value,
            'status': 'Available',
            'notes': program['notes']
        })
    
    return incentives

def generate_capital_stack_options(post_incentive_cost: float, project: dict) -> dict:
    """
    Generate multiple capital stack options including Climatize financing.
    """
    system_size_kw = project.get('system_specs', {}).get('system_size_dc_kw', 0)
    
    # Traditional bank financing
    traditional_option = {
        'name': 'Traditional Bank Financing',
        'equity_percentage': 0.30,
        'debt_percentage': 0.70,
        'equity_amount': post_incentive_cost * 0.30,
        'debt_amount': post_incentive_cost * 0.70,
        'interest_rate': 0.065,  # 6.5%
        'term_years': 15,
        'pros': ['Lower cost of capital', 'Established relationship'],
        'cons': ['Strict underwriting', 'Personal guarantees', 'Longer approval']
    }
    
    # SBA financing option
    sba_option = {
        'name': 'SBA 504 Green Financing',
        'equity_percentage': 0.10,
        'debt_percentage': 0.90,
        'equity_amount': post_incentive_cost * 0.10,
        'debt_amount': post_incentive_cost * 0.90,
        'interest_rate': 0.055,  # 5.5%
        'term_years': 20,
        'pros': ['Low down payment', 'Fixed rates', 'Long terms'],
        'cons': ['Complex approval', 'Owner occupancy requirements']
    }
    
    # Climatize financing options
    climatize_option = {
        'name': 'Climatize Solar Financing',
        'equity_percentage': 0.20,
        'debt_percentage': 0.80,
        'equity_amount': post_incentive_cost * 0.20,
        'debt_amount': post_incentive_cost * 0.80,
        'interest_rate': 0.058,  # 5.8%
        'term_years': 20,
        'climatize_features': [
            'Streamlined approval process (2-3 weeks)',
            'Solar-specific underwriting expertise',
            'No personal guarantees for qualified borrowers',
            'Flexible payment schedules during construction',
            'Integrated project management and financing'
        ],
        'pros': ['Fast approval', 'Solar expertise', 'Integrated service'],
        'cons': ['Slightly higher rates than banks']
    }
    
    # Calculate debt service for each option
    for option in [traditional_option, sba_option, climatize_option]:
        option['annual_debt_service'] = calculate_annual_debt_service(
            option['debt_amount'], 
            option['interest_rate'], 
            option['term_years']
        )
    
    return {
        'traditional': traditional_option,
        'sba': sba_option,
        'climatize': climatize_option,
        'recommended': climatize_option,  # Recommend Climatize for speed and expertise
        'climatize_options': generate_climatize_loan_products(post_incentive_cost, system_size_kw)
    }

def calculate_annual_debt_service(principal: float, rate: float, years: int) -> float:
    """Calculate annual debt service (principal + interest)."""
    monthly_rate = rate / 12
    num_payments = years * 12
    if monthly_rate == 0:
        return principal / (years * 12) * 12
    
    monthly_payment = principal * (monthly_rate * (1 + monthly_rate)**num_payments) / ((1 + monthly_rate)**num_payments - 1)
    return monthly_payment * 12

def generate_climatize_loan_products(post_incentive_cost: float, system_size_kw: float) -> list:
    """
    Generate specific Climatize loan product options.
    """
    products = []
    
    # Standard Commercial Solar Loan
    products.append({
        'product_name': 'Commercial Solar Loan',
        'loan_amount': post_incentive_cost * 0.80,
        'down_payment_percent': 20,
        'interest_rate': 0.058,
        'term_years': 20,
        'features': ['No personal guarantees for qualified borrowers', 'Fixed rate', 'Solar-optimized terms'],
        'target_customer': 'Established businesses with strong cash flow'
    })
    
    # Bridge financing for development
    products.append({
        'product_name': 'Solar Development Bridge Loan',
        'loan_amount': post_incentive_cost * 0.90,
        'down_payment_percent': 10,
        'interest_rate': 0.068,
        'term_years': 3,
        'features': ['Interest-only during development', 'Converts to term loan at COD'],
        'target_customer': 'Projects under development needing bridge financing'
    })
    
    # Equipment financing
    if system_size_kw <= 500:  # Smaller systems
        products.append({
            'product_name': 'Solar Equipment Financing',
            'loan_amount': post_incentive_cost * 0.85,
            'down_payment_percent': 15,
            'interest_rate': 0.062,
            'term_years': 15,
            'features': ['Equipment as collateral', 'Fast approval', 'Competitive rates'],
            'target_customer': 'Small to medium commercial installations'
        })
    
    return products

def calculate_enhanced_financial_returns(capital_stack: dict, project: dict, total_capex: float) -> dict:
    """
    Calculate detailed financial returns and metrics.
    """
    system_specs = project.get('system_specs', {})
    production_metrics = project.get('production_metrics', {})
    address = project.get('address', {})
    
    system_size_kw = system_specs.get('system_size_dc_kw', 0)
    annual_production = production_metrics.get('annual_production_kwh', system_size_kw * 1400)  # Default production
    
    # Revenue calculations
    electricity_rate = get_electricity_rate_by_state(address.get('state', ''))
    annual_energy_revenue = annual_production * electricity_rate
    
    # Operating expenses
    annual_om_cost = system_size_kw * 15  # $15/kW/year O&M
    annual_insurance = total_capex * 0.005  # 0.5% of capex
    annual_property_tax = total_capex * 0.015  # 1.5% property tax (varies by location)
    total_annual_expenses = annual_om_cost + annual_insurance + annual_property_tax
    
    # Net income before debt service
    annual_net_before_debt = annual_energy_revenue - total_annual_expenses
    annual_debt_service = capital_stack['annual_debt_service']
    annual_net_after_debt = annual_net_before_debt - annual_debt_service
    
    # Financial metrics
    equity_amount = capital_stack['equity_amount']
    cash_on_cash_return = annual_net_after_debt / equity_amount if equity_amount > 0 else 0
    
    # Simple payback
    simple_payback = equity_amount / annual_net_after_debt if annual_net_after_debt > 0 else 99
    
    # IRR estimation (simplified)
    estimated_irr = calculate_estimated_irr(
        equity_amount, 
        annual_net_after_debt, 
        total_capex * 0.1  # Estimated residual value
    )
    
    return {
        'annual_energy_production_kwh': annual_production,
        'electricity_rate_per_kwh': electricity_rate,
        'annual_energy_revenue': annual_energy_revenue,
        'annual_operating_expenses': total_annual_expenses,
        'annual_net_before_debt': annual_net_before_debt,
        'annual_debt_service': annual_debt_service,
        'annual_net_cash_flow': annual_net_after_debt,
        'cash_on_cash_return': cash_on_cash_return,
        'simple_payback_years': simple_payback,
        'estimated_irr': estimated_irr,
        'debt_service_coverage_ratio': annual_net_before_debt / annual_debt_service if annual_debt_service > 0 else 0
    }

def get_electricity_rate_by_state(state: str) -> float:
    """Get average commercial electricity rates by state ($/kWh)."""
    state_rates = {
        'CA': 0.22, 'NY': 0.18, 'NJ': 0.16, 'MA': 0.20, 'CT': 0.19,
        'TX': 0.11, 'FL': 0.12, 'NC': 0.10, 'AZ': 0.13, 'NV': 0.14,
        'CO': 0.12, 'IL': 0.10, 'OH': 0.11, 'PA': 0.12, 'MI': 0.13
    }
    return state_rates.get(state.upper(), 0.13)  # National average ~$0.13/kWh

def calculate_estimated_irr(initial_investment: float, annual_cash_flow: float, terminal_value: float) -> float:
    """Simplified IRR calculation."""
    # Simplified IRR using approximation for 20-year project
    total_cash_flows = annual_cash_flow * 20 + terminal_value
    if initial_investment <= 0:
        return 0
    return ((total_cash_flows / initial_investment) ** (1/20)) - 1

def get_climatize_advantages(project: dict) -> list:
    """Get Climatize-specific advantages for this project."""
    return [
        'Solar-specialized underwriting and risk assessment',
        'Streamlined approval process (2-3 weeks vs 2-3 months)',
        'Integrated project development and financing services',
        'Flexible construction-to-permanent financing',
        'No personal guarantees for qualified commercial borrowers',
        'Experienced team with 500+ successful solar financings',
        'Competitive rates with solar industry expertise',
        'Ongoing support throughout project lifecycle'
    ]

def generate_financing_timeline() -> dict:
    """Generate typical financing timeline for Climatize loans."""
    return {
        'application_to_approval': '14-21 days',
        'documentation_phase': '7-14 days',
        'closing_to_funding': '3-7 days',
        'total_process': '4-6 weeks',
        'milestones': [
            {'week': 1, 'activity': 'Application submission and initial review'},
            {'week': 2, 'activity': 'Underwriting and project analysis'},
            {'week': 3, 'activity': 'Conditional approval and documentation'},
            {'week': 4, 'activity': 'Final approval and closing preparation'},
            {'week': 5, 'activity': 'Closing and initial funding'},
            {'week': 6, 'activity': 'Construction monitoring and draw requests'}
        ]
    }

def assess_financing_risks(project: dict) -> dict:
    """Assess and provide risk mitigation strategies."""
    risks = []
    mitigations = []
    
    # Technology risk
    risks.append('Equipment performance and warranty risk')
    mitigations.append('Tier 1 equipment requirements and comprehensive warranties')
    
    # Construction risk
    risks.append('Construction delays and cost overruns')
    mitigations.append('Fixed-price EPC contracts with performance guarantees')
    
    # Permitting risk
    permit_matrix = project.get('permit_matrix', {})
    if permit_matrix.get('jurisdiction_info', {}).get('solar_friendly_rating', 5) < 6:
        risks.append('Permitting complexity in jurisdiction')
        mitigations.append('Experienced local permitting team and regulatory expertise')
    
    # Interconnection risk
    interconnection = project.get('interconnection_score', {})
    if interconnection.get('score', 50) < 70:
        risks.append('Utility interconnection challenges')
        mitigations.append('Early utility engagement and interconnection insurance')
    
    return {
        'identified_risks': risks,
        'mitigation_strategies': mitigations,
        'overall_risk_rating': 'Medium',  # Could be calculated based on various factors
        'climatize_risk_management': [
            'Comprehensive project insurance requirements',
            'Experienced construction monitoring team',
            'Reserve accounts for contingencies',
            'Strong contractor pre-qualification process'
        ]
    }

@app.function_name(name="project_packager_and_scorer")
@app.queue_trigger(arg_name="msg", queue_name="project-scoring", connection="AzureWebJobsStorage")
def project_packager_and_scorer(msg: func.QueueMessage) -> None:
    """
    Queue-triggered function that calculates final project score and packages the project.
    
    Logic:
    1. Fetch the completed project model
    2. Calculate the fundability_score (0-100) as a weighted average:
       - Milestone Completion: 40%
       - Jurisdictional Risk (from shovels.ai metrics): 30%
       - Financial Viability (based on CapEx vs. incentives): 30%
    3. Update the project model with the final score
    4. This function marks the end of the automated workflow
    """
    logging.info('Calculating project score and packaging.')
    
    try:
        # Get project_id from queue message
        project_id = msg.get_body().decode('utf-8')
        if not project_id:
            logging.error("No project_id found in queue message")
            return
        
        logging.info(f"Scoring and packaging project {project_id}")
        
        # Fetch project from Cosmos DB
        try:
            cosmos_client = CosmosDBClient()
            project = cosmos_client.get_project(project_id)
            if not project:
                logging.error(f"Project {project_id} not found in database")
                return
        except Exception as db_error:
            logging.error(f"Failed to fetch project from database: {str(db_error)}")
            return
        
        # Calculate fundability score
        try:
            fundability_score, fundability_factors = calculate_fundability_score(project)
        except Exception as score_error:
            logging.error(f"Failed to calculate fundability score: {str(score_error)}")
            fundability_score = 50  # Default score
        
        # Update project with final score
        try:
            updates = {
                'fundability_score': fundability_score,
                'fundability_factors': fundability_factors,
                'scoring_completed_at': datetime.now().isoformat()
            }
            cosmos_client.update_project(project_id, updates)
            logging.info(f"Updated project {project_id} with fundability score: {fundability_score}")
        except Exception as update_error:
            logging.error(f"Failed to update project with final score: {str(update_error)}")
            return
        
        logging.info(f"Successfully completed project workflow for {project_id} with score {fundability_score}")
        
    except Exception as e:
        logging.error(f"Unexpected error in project_packager_and_scorer: {str(e)}")

def calculate_fundability_score(project: dict) -> tuple:
    """
    Calculates a comprehensive fundability score based on project readiness, 
    policy environment, and financial risk factors.
    Returns a tuple of (score, factors_dict).
    """
    base_score = 40  # Start with baseline
    factors = {}
    
    # 1. Milestone Completion Assessment (40% weight)
    milestone_score, milestone_factors = assess_milestone_completion(project)
    factors.update(milestone_factors)
    
    # 2. Jurisdictional Risk Assessment (30% weight)
    jurisdictional_score, jurisdictional_factors = assess_jurisdictional_risk(project)
    factors.update(jurisdictional_factors)
    
    # 3. Financial Viability Assessment (30% weight)
    financial_score, financial_factors = assess_financial_viability(project)
    factors.update(financial_factors)
    
    # Calculate weighted score
    total_score = (
        base_score + 
        milestone_score * 0.40 + 
        jurisdictional_score * 0.30 + 
        financial_score * 0.30
    )
    
    # Apply eligibility screening impact
    eligibility = project.get('eligibility_screening', {})
    if eligibility.get('eligible') == False:
        total_score = min(total_score, 25)  # Cap at 25 if ineligible
        factors['eligibility_impact'] = 'Project failed eligibility screening'
    elif eligibility.get('warnings'):
        total_score *= 0.95  # Slight reduction for warnings
        factors['eligibility_impact'] = f"{len(eligibility['warnings'])} screening concerns identified"
    
    # Ensure score is within bounds
    final_score = max(0, min(100, int(total_score)))
    
    return final_score, factors

def assess_milestone_completion(project: dict) -> tuple:
    """
    Assess milestone completion and readiness (40% of total score).
    """
    milestones = project.get('milestones', {})
    score = 0
    factors = {}
    
    # Define milestone weights and completion values
    milestone_weights = {
        'site_control': 25,    # Critical for financing
        'permitting': 20,      # Important for timeline certainty
        'interconnection': 20, # Critical path item
        'engineering': 15,     # Technical readiness
        'offtake': 10,        # Revenue certainty
        'financing': 10        # Final step
    }
    
    completion_values = {
        'Not Started': 0,
        'Drafted': 0.3,
        'LOI Drafted': 0.3,
        'Application Drafted': 0.3,
        'Matrix Generated': 0.5,
        'Applications Drafted': 0.6,
        'Submitted': 0.8,
        'Negotiating': 0.8,
        'Approved': 1.0,
        'Signed': 1.0,
        'Completed': 1.0,
        'Initial Screen': 0.4,
        'Conceptual Design': 0.5,
        'Detailed': 0.8,
        'Stamped': 1.0,
        'Initial Analysis': 0.5,
        'Package Prepared': 0.7,
        'In Diligence': 0.9,
        'Committed': 1.0
    }
    
    total_possible = sum(milestone_weights.values())
    achieved_score = 0
    
    for milestone, weight in milestone_weights.items():
        status = milestones.get(milestone, 'Not Started')
        completion = completion_values.get(status, 0)
        milestone_score = weight * completion
        achieved_score += milestone_score
        
        factors[f'{milestone}_completion'] = f'{status} ({completion*100:.0f}%)'
    
    # Calculate percentage score out of 60 points possible
    percentage_complete = achieved_score / total_possible
    milestone_score = percentage_complete * 60  # Max 60 points
    
    factors['overall_milestone_completion'] = f'{percentage_complete*100:.0f}%'
    
    return milestone_score, factors

def assess_jurisdictional_risk(project: dict) -> tuple:
    """
    Assess jurisdictional and regulatory risk (30% of total score).
    """
    score = 0
    factors = {}
    
    permit_matrix = project.get('permit_matrix', {})
    interconnection = project.get('interconnection_score', {})
    address = project.get('address', {})
    
    # Solar-friendly rating assessment (up to 15 points)
    solar_rating = permit_matrix.get('jurisdiction_info', {}).get('solar_friendly_rating', 5)
    if solar_rating >= 8:
        score += 15
        factors['jurisdiction_rating'] = 'High solar-friendly (8-10)'
    elif solar_rating >= 6:
        score += 10
        factors['jurisdiction_rating'] = 'Moderate solar-friendly (6-7)'
    else:
        score += 5
        factors['jurisdiction_rating'] = 'Low solar-friendly (<6)'
    
    # Interconnection risk assessment (up to 10 points)
    interconnection_score = interconnection.get('score', 50)
    if interconnection_score >= 80:
        score += 10
        factors['interconnection_risk'] = 'Low risk (80+ score)'
    elif interconnection_score >= 60:
        score += 7
        factors['interconnection_risk'] = 'Medium risk (60-79 score)'
    else:
        score += 3
        factors['interconnection_risk'] = 'High risk (<60 score)'
    
    # State policy environment (up to 5 points)
    state = address.get('state', '').upper()
    favorable_states = ['CA', 'NY', 'NJ', 'MA', 'CT', 'MD', 'CO']
    moderate_states = ['TX', 'FL', 'NC', 'AZ', 'NV', 'IL', 'OH']
    
    if state in favorable_states:
        score += 5
        factors['state_policy'] = 'Favorable policy environment'
    elif state in moderate_states:
        score += 3
        factors['state_policy'] = 'Moderate policy environment'
    else:
        score += 1
        factors['state_policy'] = 'Limited policy support'
    
    return score, factors

def assess_financial_viability(project: dict) -> tuple:
    """
    Assess financial viability and returns (30% of total score).
    """
    score = 0
    factors = {}
    
    financials = project.get('financials', {})
    system_specs = project.get('system_specs', {})
    
    # Incentive availability (up to 10 points)
    eligibility = project.get('eligibility_screening', {})
    incentive_score = eligibility.get('incentive_score', 50)
    
    if incentive_score >= 80:
        score += 10
        factors['incentive_availability'] = 'Excellent (80+ score)'
    elif incentive_score >= 60:
        score += 7
        factors['incentive_availability'] = 'Good (60-79 score)'
    elif incentive_score >= 40:
        score += 4
        factors['incentive_availability'] = 'Fair (40-59 score)'
    else:
        score += 1
        factors['incentive_availability'] = 'Limited (<40 score)'
    
    # Project economics (up to 15 points)
    capital_stack = financials.get('capital_stack', {})
    financial_analysis = capital_stack.get('financial_analysis', {})
    
    # IRR assessment
    irr = financial_analysis.get('estimated_irr', 0)
    if irr >= 0.15:  # 15%+
        score += 8
        factors['project_irr'] = f'Excellent ({irr*100:.1f}%)'
    elif irr >= 0.12:  # 12-15%
        score += 6
        factors['project_irr'] = f'Good ({irr*100:.1f}%)'
    elif irr >= 0.08:  # 8-12%
        score += 4
        factors['project_irr'] = f'Fair ({irr*100:.1f}%)'
    else:
        score += 1
        factors['project_irr'] = f'Poor ({irr*100:.1f}%)'
    
    # Debt service coverage ratio
    dscr = financial_analysis.get('debt_service_coverage_ratio', 0)
    if dscr >= 1.5:
        score += 4
        factors['debt_coverage'] = f'Strong ({dscr:.2f}x)'
    elif dscr >= 1.25:
        score += 3
        factors['debt_coverage'] = f'Adequate ({dscr:.2f}x)'
    elif dscr >= 1.1:
        score += 2
        factors['debt_coverage'] = f'Marginal ({dscr:.2f}x)'
    else:
        score += 0
        factors['debt_coverage'] = f'Weak ({dscr:.2f}x)'
    
    # Payback period assessment
    payback = financial_analysis.get('simple_payback_years', 20)
    if payback <= 6:
        score += 3
        factors['payback_period'] = f'Excellent ({payback:.1f} years)'
    elif payback <= 8:
        score += 2
        factors['payback_period'] = f'Good ({payback:.1f} years)'
    elif payback <= 12:
        score += 1
        factors['payback_period'] = f'Fair ({payback:.1f} years)'
    else:
        score += 0
        factors['payback_period'] = f'Poor ({payback:.1f} years)'
    
    return score, factors

def generate_enhanced_milestone_tracker(project: dict) -> dict:
    """
    Generate enhanced milestone tracker with dynamic checklists and alerts.
    """
    milestones = project.get('milestones', {})
    permit_matrix = project.get('permit_matrix', {})
    
    # Define enhanced milestone structure
    enhanced_milestones = {
        'site_control': {
            'name': 'Site Control',
            'current_status': milestones.get('site_control', 'Not Started'),
            'completion_percentage': calculate_milestone_completion_percentage('site_control', milestones),
            'checklist': generate_site_control_checklist(project),
            'alerts': generate_site_control_alerts(project),
            'next_steps': generate_site_control_next_steps(project),
            'timeline': '2-8 weeks',
            'critical_path': True
        },
        'permitting': {
            'name': 'Permitting',
            'current_status': milestones.get('permitting', 'Not Started'),
            'completion_percentage': calculate_milestone_completion_percentage('permitting', milestones),
            'checklist': generate_permitting_checklist(project),
            'alerts': generate_permitting_alerts(project),
            'next_steps': generate_permitting_next_steps(project),
            'timeline': permit_matrix.get('total_estimated_timeline', '6-12 weeks'),
            'critical_path': True
        },
        'interconnection': {
            'name': 'Utility Interconnection',
            'current_status': milestones.get('interconnection', 'Not Started'),
            'completion_percentage': calculate_milestone_completion_percentage('interconnection', milestones),
            'checklist': generate_interconnection_checklist(project),
            'alerts': generate_interconnection_alerts(project),
            'next_steps': generate_interconnection_next_steps(project),
            'timeline': '4-16 weeks',
            'critical_path': True
        },
        'engineering': {
            'name': 'Engineering & Design',
            'current_status': milestones.get('engineering', 'Not Started'),
            'completion_percentage': calculate_milestone_completion_percentage('engineering', milestones),
            'checklist': generate_engineering_checklist(project),
            'alerts': generate_engineering_alerts(project),
            'next_steps': generate_engineering_next_steps(project),
            'timeline': '3-8 weeks',
            'critical_path': False
        },
        'financing': {
            'name': 'Financing',
            'current_status': milestones.get('financing', 'Not Started'),
            'completion_percentage': calculate_milestone_completion_percentage('financing', milestones),
            'checklist': generate_financing_checklist(project),
            'alerts': generate_financing_alerts(project),
            'next_steps': generate_financing_next_steps(project),
            'timeline': '4-8 weeks',
            'critical_path': True
        }
    }
    
    # Calculate overall project completion
    total_completion = sum(m['completion_percentage'] for m in enhanced_milestones.values()) / len(enhanced_milestones)
    
    # Identify critical alerts
    critical_alerts = []
    for milestone in enhanced_milestones.values():
        critical_alerts.extend([alert for alert in milestone['alerts'] if alert.get('priority') == 'high'])
    
    return {
        'enhanced_milestones': enhanced_milestones,
        'overall_completion_percentage': total_completion,
        'critical_alerts': critical_alerts,
        'estimated_completion_date': calculate_estimated_completion_date(enhanced_milestones),
        'bottlenecks': identify_project_bottlenecks(enhanced_milestones)
    }

def calculate_milestone_completion_percentage(milestone_type: str, milestones: dict) -> int:
    """Calculate completion percentage for a specific milestone."""
    status = milestones.get(milestone_type, 'Not Started')
    
    completion_map = {
        'Not Started': 0,
        'Drafted': 25, 'LOI Drafted': 25, 'Application Drafted': 25,
        'Matrix Generated': 50, 'Initial Screen': 40, 'Conceptual Design': 50,
        'Applications Drafted': 60, 'Submitted': 75, 'Initial Analysis': 50,
        'Negotiating': 80, 'Detailed': 80, 'Package Prepared': 70,
        'Approved': 90, 'Signed': 100, 'Completed': 100, 
        'Stamped': 100, 'In Diligence': 90, 'Committed': 100
    }
    
    return completion_map.get(status, 0)

def generate_site_control_checklist(project: dict) -> list:
    """Generate site control checklist items."""
    return [
        {'task': 'Property owner identification and contact', 'status': 'pending', 'priority': 'high'},
        {'task': 'Site visit and preliminary assessment', 'status': 'pending', 'priority': 'high'},
        {'task': 'Draft Letter of Intent (LOI)', 'status': 'completed' if project.get('project_documents', {}).get('site_control') else 'pending', 'priority': 'high'},
        {'task': 'LOI negotiation and execution', 'status': 'pending', 'priority': 'high'},
        {'task': 'Title and ownership verification', 'status': 'pending', 'priority': 'medium'},
        {'task': 'Environmental Phase I assessment', 'status': 'pending', 'priority': 'medium'},
        {'task': 'Survey and boundary verification', 'status': 'pending', 'priority': 'medium'}
    ]

def generate_site_control_alerts(project: dict) -> list:
    """Generate site control alerts."""
    alerts = []
    
    milestones = project.get('milestones', {})
    if milestones.get('site_control') == 'Not Started':
        alerts.append({
            'message': 'Site control not initiated - critical for project financing',
            'priority': 'high',
            'action': 'Begin property owner outreach immediately'
        })
    
    return alerts

def generate_site_control_next_steps(project: dict) -> list:
    """Generate site control next steps."""
    milestones = project.get('milestones', {})
    status = milestones.get('site_control', 'Not Started')
    
    if status == 'Not Started':
        return [
            'Contact Climatize development team for site control assistance',
            'Review AI-generated LOI template',
            'Identify and contact property owner',
            'Schedule site visit'
        ]
    elif status == 'LOI Drafted':
        return [
            'Review LOI with legal counsel',
            'Present LOI to property owner',
            'Begin lease rate negotiations',
            'Set timeline for lease execution'
        ]
    else:
        return ['Continue lease negotiations', 'Prepare for due diligence phase']

# Similar functions would be implemented for other milestones...
def generate_permitting_checklist(project: dict) -> list:
    """Generate permitting checklist from permit matrix."""
    permit_matrix = project.get('permit_matrix', {})
    checklist = []
    
    for permit in permit_matrix.get('permit_requirements', []):
        for requirement in permit.get('requirements', []):
            checklist.append({
                'task': f"{permit['permit_type']}: {requirement}",
                'status': 'pending',
                'priority': permit.get('priority', 'medium').lower(),
                'authority': permit.get('authority', 'TBD')
            })
    
    return checklist

def generate_permitting_alerts(project: dict) -> list:
    """Generate permitting alerts."""
    alerts = []
    permit_matrix = project.get('permit_matrix', {})
    
    # Check for high-risk permits
    for permit in permit_matrix.get('permit_requirements', []):
        if permit.get('complexity') == 'High':
            alerts.append({
                'message': f"{permit['permit_type']} identified as high complexity",
                'priority': 'medium',
                'action': f"Engage early with {permit.get('authority', 'permitting authority')}"
            })
    
    return alerts

def generate_permitting_next_steps(project: dict) -> list:
    """Generate permitting next steps."""
    return [
        'Review jurisdiction-specific permit requirements',
        'Engage with local permitting consultants',
        'Prepare permit application packages',
        'Submit applications in optimal sequence'
    ]

def generate_interconnection_checklist(project: dict) -> list:
    """Generate interconnection checklist."""
    return [
        {'task': 'Utility interconnection application', 'status': 'pending', 'priority': 'high'},
        {'task': 'System impact study (if required)', 'status': 'pending', 'priority': 'high'},
        {'task': 'Interconnection agreement execution', 'status': 'pending', 'priority': 'high'},
        {'task': 'Meter and equipment coordination', 'status': 'pending', 'priority': 'medium'}
    ]

def generate_interconnection_alerts(project: dict) -> list:
    """Generate interconnection alerts."""
    alerts = []
    
    interconnection = project.get('interconnection_score', {})
    if interconnection.get('score', 50) < 60:
        alerts.append({
            'message': 'Interconnection challenges identified',
            'priority': 'high',
            'action': 'Consider interconnection insurance or alternative solutions'
        })
    
    return alerts

def generate_interconnection_next_steps(project: dict) -> list:
    """Generate interconnection next steps."""
    return [
        'Submit preliminary interconnection application',
        'Coordinate with utility for system impact study',
        'Review interconnection requirements and costs',
        'Plan for utility upgrades if needed'
    ]

def generate_engineering_checklist(project: dict) -> list:
    """Generate engineering checklist."""
    return [
        {'task': 'Detailed system design', 'status': 'pending', 'priority': 'high'},
        {'task': 'Structural engineering analysis', 'status': 'pending', 'priority': 'high'},
        {'task': 'Electrical design and calculations', 'status': 'pending', 'priority': 'high'},
        {'task': 'PE stamp and approval', 'status': 'pending', 'priority': 'medium'}
    ]

def generate_engineering_alerts(project: dict) -> list:
    """Generate engineering alerts."""
    return []

def generate_engineering_next_steps(project: dict) -> list:
    """Generate engineering next steps."""
    return [
        'Finalize system sizing and layout',
        'Complete structural analysis',
        'Obtain professional engineer review',
        'Prepare construction documents'
    ]

def generate_financing_checklist(project: dict) -> list:
    """Generate financing checklist."""
    return [
        {'task': 'Prepare financing package', 'status': 'pending', 'priority': 'high'},
        {'task': 'Submit loan application to Climatize', 'status': 'pending', 'priority': 'high'},
        {'task': 'Complete financial due diligence', 'status': 'pending', 'priority': 'medium'},
        {'task': 'Execute financing agreements', 'status': 'pending', 'priority': 'high'}
    ]

def generate_financing_alerts(project: dict) -> list:
    """Generate financing alerts."""
    return []

def generate_financing_next_steps(project: dict) -> list:
    """Generate financing next steps."""
    return [
        'Review Climatize financing options',
        'Prepare financial documentation',
        'Submit financing application',
        'Complete lender due diligence'
    ]

def calculate_estimated_completion_date(enhanced_milestones: dict) -> str:
    """Calculate estimated project completion date."""
    # Simplified calculation - would be more sophisticated in production
    weeks_remaining = 0
    for milestone in enhanced_milestones.values():
        if milestone['completion_percentage'] < 100:
            timeline = milestone['timeline']
            weeks = extract_weeks_from_timeline(timeline)
            weeks_remaining = max(weeks_remaining, weeks)
    
    return f"{weeks_remaining} weeks"

def identify_project_bottlenecks(enhanced_milestones: dict) -> list:
    """Identify potential project bottlenecks."""
    bottlenecks = []
    
    for milestone_key, milestone in enhanced_milestones.items():
        if milestone['critical_path'] and milestone['completion_percentage'] < 25:
            bottlenecks.append({
                'milestone': milestone['name'],
                'issue': 'Critical path milestone not started',
                'impact': 'High risk of project delay'
            })
    
    return bottlenecks

def generate_next_steps(project: dict) -> list:
    """
    Generates a list of next steps for the developer.
    """
    steps = [
        "Review the draft Letter of Intent (LOI) and prepare for site owner negotiation.",
        "Begin formal interconnection application process with the utility.",
        "Engage with Climatize to finalize financing options and secure funding commitment."
    ]
    return steps

def format_project_as_feasibility_package(project: dict) -> FeasibilityPackage:
    """
    Transforms the full UnifiedProjectModel into the summarized FeasibilityPackage.
    """
    addr = project['address']
    full_address = f"{addr['street']}, {addr['city']}, {addr['state']} {addr['zip_code']}"

    permit_matrix = project.get('permit_matrix', {})
    permit_checklist = [
        {
            "name": req['permit_type'],
            "status": req['status'],
            "flag": req['flag_color']
        } for req in permit_matrix.get('requirements', [])
    ]
    
    package = FeasibilityPackage(
        project_id=project['project_id'],
        generation_date=datetime.now(),
        site_address=full_address,
        coordinates={'lat': addr.get('lat'), 'lon': addr.get('lon')},
        roof_type=project['system_specs']['roof_type'],
        annual_kwh_load=project['system_specs'].get('annual_kwh_load'),
        pv_layout_image_url=project.get('project_documents', {}).get('pv_layout_pdf_url'),
        system_size_dc_kw=project['system_specs']['system_size_dc_kw'],
        system_size_ac_kw=project['system_specs']['system_size_ac_kw'],
        annual_production_kwh=project['production_metrics']['annual_production_kwh'],
        specific_yield=project['production_metrics']['specific_yield'],
        performance_ratio=project['production_metrics']['performance_ratio'],
        battery_recommendation=project['system_specs'].get('battery_specs'),
        interconnection_score=project['interconnection_score']['score'],
        interconnection_notes=", ".join(project['interconnection_score']['risk_factors']),
        permit_checklist=permit_checklist,
        red_flags=permit_matrix.get('red_flags', []),
        green_flags=permit_matrix.get('green_flags', []),
        pro_forma_summary=project['financials']['pro_forma'],
        next_steps=project['next_steps'],
        climatize_funding_cta="Based on this preliminary analysis, your project appears to be a strong candidate for Climatize financing. Please contact us to discuss next steps."
    )
    return package

@app.function_name(name="pro_forma_generator")
@app.queue_trigger(arg_name="msg", queue_name="pro-forma", connection="AzureWebJobsStorage")
def pro_forma_generator(msg: func.QueueMessage) -> None:
    """
    Generates a 5-line pro-forma for the project.
    """
    project_id = msg.get_body().decode('utf-8')
    logging.info(f"Generating pro-forma for project {project_id}")
    
    try:
        cosmos_client = CosmosDBClient()
        project = cosmos_client.get_project(project_id)
        
        # MOCK: financial calculations
        system_size_kw = project['system_specs']['system_size_dc_kw']
        capex_total = system_size_kw * 2.5 * 1000 # $2.50/W
        itc_amount = capex_total * 0.30 # 30% ITC
        
        pro_forma = ProForma(
            capex_total=capex_total,
            capex_per_watt=2.50,
            itc_percentage=30.0,
            itc_amount=itc_amount,
            simple_payback_years=8.5,
            irr_band_low=0.08,
            irr_band_high=0.12,
            lcoe_cents_per_kwh=9.5,
            net_present_value=capex_total * 0.2 # Dummy value
        )
        
        updates = {
            'financials.pro_forma': pro_forma.dict(),
            'milestones.financing': 'Initial Analysis'
        }
        cosmos_client.update_project(project_id, updates)
        
        logging.info(f"Generated pro-forma for project {project_id}")
        invoke_function("site_control_document_generator", project_id)

    except Exception as e:
        logging.error(f"Error in pro_forma_generator for {project_id}: {e}")

@app.function_name(name="site_control_document_generator")
@app.queue_trigger(arg_name="msg", queue_name="site-control-docs", connection="AzureWebJobsStorage")
def site_control_document_generator(msg: func.QueueMessage) -> None:
    """
    This function was formerly feasibility_and_site_control.
    It now focuses on drafting the LOI/Lease document.
    """
    project_id = msg.get_body().decode('utf-8')
    logging.info(f"Generating site control document for project {project_id}")
    
    try:
        cosmos_client = CosmosDBClient()
        project = cosmos_client.get_project(project_id)
        
        if not project:
            logging.error(f"Project {project_id} not found in database")
            return
        
        # Generate Letter of Intent (LOI)
        try:
            loi_content = generate_letter_of_intent(project)
            site_doc = SiteControlDocument(
                document_type="LOI",
                status="Drafted",
                generated_date=datetime.now(),
                document_content=loi_content
            )

            updates = {
                'project_documents.site_control': site_doc.dict(),
                'milestones.site_control': 'LOI Drafted'
            }
            cosmos_client.update_project(project_id, updates)
            logging.info(f"Generated LOI for project {project_id}")
        except Exception as loi_error:
            logging.error(f"Failed to generate LOI: {str(loi_error)}")
            # Fallback status
            updates = {'milestones.site_control': 'Error Drafting'}
            cosmos_client.update_project(project_id, updates)
            return

        # Invoke capital stack generator
        try:
            invoke_function("capital_stack_generator", project_id)
            logging.info(f"Invoked capital_stack_generator for project {project_id}")
        except Exception as invoke_error:
            logging.warning(f"Failed to invoke capital_stack_generator: {str(invoke_error)}")
        
        logging.info(f"Successfully processed site control for project {project_id}")
        
    except Exception as e:
        logging.error(f"Unexpected error in site_control_document_generator: {str(e)}")

# === NEW AGENTIC AI MVP FUNCTIONS ===

def auto_expand_minimal_input(zip_code: str, system_size_kw: float, additional_data: dict) -> dict:
    """
    Auto-expand minimal input (ZIP + system size) into full project data.
    """
    # Geocode ZIP code to get address and coordinates
    try:
        import requests
        geocode_url = f"https://api.zippopotam.us/us/{zip_code}"
        response = requests.get(geocode_url, timeout=10)
        if response.status_code == 200:
            zip_data = response.json()
            place = zip_data['places'][0]
            
            address = Address(
                street=additional_data.get('street', f"Property in {place['place name']}"),
                city=place['place name'],
                state=place['state abbreviation'],
                zip_code=zip_code,
                lat=float(place['latitude']),
                lon=float(place['longitude'])
            )
        else:
            # Fallback for unknown ZIP
            address = Address(
                street=f"Property in {zip_code}",
                city="Unknown",
                state="Unknown", 
                zip_code=zip_code
            )
    except Exception as e:
        logging.warning(f"Geocoding failed for {zip_code}: {str(e)}")
        address = Address(
            street=f"Property in {zip_code}",
            city="Unknown",
            state="Unknown",
            zip_code=zip_code
        )
    
    # Auto-calculate system specs based on size
    estimated_module_count = int(system_size_kw * 2.5)  # ~400W modules
    roof_type = additional_data.get('roof_type', 'flat')
    
    system_specs = SystemSpecs(
        system_size_dc_kw=system_size_kw,
        module_count=estimated_module_count,
        inverter_type=additional_data.get('inverter_type', 'string'),
        roof_type=roof_type,
        bill_of_materials=[]
    )
    
    # Estimate financials
    price_per_watt = 2.50  # Default $/W
    estimated_capex = system_size_kw * 1000 * price_per_watt
    
    financials = Financials(
        estimated_capex=estimated_capex,
        price_per_watt=price_per_watt,
        incentives=[],
        capital_stack=None
    )
    
    project_name = f"Solar Project - {address.city}, {address.state} ({system_size_kw:.1f} kW)"
    
    return {
        'project_name': project_name,
        'data_source': 'Helioscope',
        'address': address.dict(),
        'system_specs': system_specs.dict(),
        'financials': financials.dict()
    }

def get_processing_status(project: dict) -> str:
    """
    Determine the overall processing status of a project.
    """
    milestones = project.get('milestones', {})
    
    # Check if all major milestones are complete
    if (milestones.get('financing') != 'Not Started' and 
        project.get('fundability_score', 0) > 0):
        return "completed"
    elif milestones.get('permitting') != 'Not Started':
        return "processing"
    else:
        return "starting"

def calculate_progress_percentage(project: dict) -> int:
    """
    Calculate the progress percentage based on completed milestones.
    """
    milestones = project.get('milestones', {})
    completed = 0
    total = 6
    
    milestone_stages = [
        'site_control', 'permitting', 'interconnection', 
        'engineering', 'offtake', 'financing'
    ]
    
    for stage in milestone_stages:
        if milestones.get(stage, 'Not Started') != 'Not Started':
            completed += 1
    
    return int((completed / total) * 100)

def get_current_processing_stage(project: dict) -> str:
    """
    Get the current processing stage description.
    """
    milestones = project.get('milestones', {})
    
    if milestones.get('financing') != 'Not Started':
        return "Finalizing financial analysis"
    elif milestones.get('site_control') != 'Not Started':
        return "Generating site control documents"
    elif milestones.get('permitting') != 'Not Started':
        return "Analyzing permit requirements"
    elif milestones.get('engineering') != 'Not Started':
        return "Creating system design"
    else:
        return "Initializing project analysis"

def format_project_as_ai_package(project: dict) -> dict:
    """
    Format the project into a comprehensive AI package for download.
    """
    from datetime import datetime
    
    addr = project['address']
    full_address = f"{addr['street']}, {addr['city']}, {addr['state']} {addr['zip_code']}"
    
    # Build comprehensive package
    package = {
        "project_id": project['project_id'],
        "generation_date": datetime.now(),
        "project_overview": {
            "project_name": project['project_name'],
            "site_address": full_address,
            "system_size_kw": project['system_specs']['system_size_dc_kw'],
            "estimated_annual_production": project.get('production_metrics', {}).get('annual_production_kwh', 0),
            "fundability_score": project.get('fundability_score', 0)
        },
        "site_analysis": {
            "coordinates": {
                "lat": addr.get('lat'),
                "lon": addr.get('lon')
            },
            "roof_type": project['system_specs'].get('roof_type', 'flat'),
            "system_specs": project['system_specs'],
            "production_metrics": project.get('production_metrics', {})
        },
        "permit_analysis": project.get('permit_matrix', {}),
        "interconnection_analysis": project.get('interconnection_score', {}),
        "financial_analysis": {
            "capital_stack": project.get('financials', {}).get('capital_stack', {}),
            "incentives": project.get('financials', {}).get('incentives', []),
            "pro_forma": project.get('financials', {}).get('pro_forma', {})
        },
        "site_control_documents": project.get('project_documents', {}).get('site_control', {}),
        "development_checklist": generate_development_checklist(project),
        "next_steps": generate_next_steps(project),
        "climatize_funding_options": project.get('climatize_funding_options', [])
    }
    
    return package

def generate_development_checklist(project: dict) -> list:
    """
    Generate a dynamic development checklist based on project status.
    """
    checklist = []
    milestones = project.get('milestones', {})
    permit_matrix = project.get('permit_matrix', {})
    
    # Site Control Tasks
    if milestones.get('site_control') == 'Not Started':
        checklist.append({
            "category": "Site Control",
            "task": "Negotiate and execute site control agreement",
            "status": "pending",
            "priority": "high",
            "estimated_timeline": "2-4 weeks"
        })
    
    # Permit Tasks
    if permit_matrix:
        for req in permit_matrix.get('permit_requirements', []):
            checklist.append({
                "category": "Permitting",
                "task": f"Submit {req['permit_type']} application",
                "status": req.get('status', 'pending'),
                "priority": "medium",
                "estimated_timeline": req.get('estimated_timeline', 'TBD')
            })
    
    # Interconnection Tasks
    if milestones.get('interconnection') == 'Not Started':
        checklist.append({
            "category": "Interconnection",
            "task": "Submit utility interconnection application",
            "status": "pending",
            "priority": "high",
            "estimated_timeline": "4-8 weeks"
        })
    
    # Engineering Tasks
    if milestones.get('engineering') in ['Not Started', 'Conceptual']:
        checklist.append({
            "category": "Engineering",
            "task": "Complete detailed engineering design",
            "status": "pending",
            "priority": "medium",
            "estimated_timeline": "3-6 weeks"
        })
    
    # Financing Tasks
    if milestones.get('financing') == 'Not Started':
        checklist.append({
            "category": "Financing",
            "task": "Secure project financing commitment",
            "status": "pending",
            "priority": "high",
            "estimated_timeline": "4-8 weeks"
        })
    
    return checklist

def generate_downloadable_package(project: dict) -> str:
    """
    Generate a downloadable ZIP package with all project documents.
    """
    import zipfile
    import io
    import json
    from datetime import datetime
    
    try:
        # Create in-memory ZIP file
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Project Overview JSON
            overview = format_project_as_ai_package(project)
            zip_file.writestr("01_Project_Overview.json", 
                            json.dumps(overview, default=str, indent=2))
            
            # Site Control Documents
            site_control = project.get('project_documents', {}).get('site_control', {})
            if site_control.get('document_content'):
                zip_file.writestr("02_Site_Control_LOI.txt", 
                                site_control['document_content'])
            
            # Permit Matrix
            permit_matrix = project.get('permit_matrix', {})
            if permit_matrix:
                zip_file.writestr("03_Permit_Matrix.json", 
                                json.dumps(permit_matrix, default=str, indent=2))
            
            # Financial Analysis
            financials = project.get('financials', {})
            if financials:
                zip_file.writestr("04_Financial_Analysis.json", 
                                json.dumps(financials, default=str, indent=2))
            
            # Development Checklist
            checklist = generate_development_checklist(project)
            zip_file.writestr("05_Development_Checklist.json", 
                            json.dumps(checklist, default=str, indent=2))
        
        # Upload to blob storage
        blob_client = BlobStorageClient()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"project_package_{timestamp}.zip"
        
        zip_buffer.seek(0)
        blob_path = blob_client.upload_document(
            project['project_id'], 
            filename, 
            zip_buffer.getvalue()
        )
        
        return blob_client.get_document_url(blob_path)
        
    except Exception as e:
        logging.error(f"Error generating downloadable package: {str(e)}")
        raise

@app.route(route="download_project_package/{project_id}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def download_project_package(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint to download the complete project package as a ZIP file.
    """
    project_id = req.route_params.get('project_id')
    logging.info(f'Generating download package for project {project_id}.')
    
    try:
        cosmos_client = CosmosDBClient()
        project = cosmos_client.get_project(project_id)
        
        if not project:
            return func.HttpResponse(
                json.dumps({"error": "Project not found"}),
                status_code=404,
                mimetype="application/json"
            )
        
        # Generate and return ZIP package
        zip_url = generate_downloadable_package(project)
        
        return func.HttpResponse(
            json.dumps({"download_url": zip_url}),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        logging.error(f"Error generating download package for {project_id}: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": "Failed to generate download package"}),
            status_code=500,
            mimetype="application/json"
        )

# === NEW AI WORKFLOW FUNCTIONS ===

@app.function_name(name="eligibility_screener")
@app.queue_trigger(arg_name="msg", queue_name="eligibility-screening", connection="AzureWebJobsStorage")
def eligibility_screener(msg: func.QueueMessage) -> None:
    """
    Queue-triggered function that screens projects for eligibility based on 
    incentives, permits, and interconnection feasibility.
    """
    project_id = msg.get_body().decode('utf-8')
    logging.info(f"Starting eligibility screening for project {project_id}")
    
    try:
        cosmos_client = CosmosDBClient()
        project = cosmos_client.get_project(project_id)
        
        if not project:
            logging.error(f"Project {project_id} not found")
            return
        
        # Perform eligibility screening
        eligibility_results = perform_eligibility_screening(project)
        
        # Update project with screening results
        updates = {
            'eligibility_screening': eligibility_results,
            'milestones.screening': 'Completed'
        }
        cosmos_client.update_project(project_id, updates)
        
        # Only proceed if project passes screening
        if eligibility_results['eligible']:
            logging.info(f"Project {project_id} passed eligibility screening")
            invoke_function("helioscope_design_engine", project_id)
        else:
            logging.info(f"Project {project_id} failed eligibility screening")
            # Update with rejection reason and skip further processing
            updates = {
                'fundability_score': 0,
                'processing_status': 'ineligible',
                'rejection_reasons': eligibility_results['rejection_reasons']
            }
            cosmos_client.update_project(project_id, updates)
        
    except Exception as e:
        logging.error(f"Error in eligibility_screener for {project_id}: {e}")

def perform_eligibility_screening(project: dict) -> dict:
    """
    Perform comprehensive eligibility screening for a project.
    """
    rejection_reasons = []
    warnings = []
    
    address = project['address']
    system_specs = project['system_specs']
    
    # Geographic eligibility
    state = address.get('state', '').upper()
    if state in ['AK', 'HI']:  # Example: exclude Alaska and Hawaii for now
        rejection_reasons.append("Geographic restriction: State not currently supported")
    
    # System size eligibility
    system_size = system_specs.get('system_size_dc_kw', 0)
    if system_size < 50:  # Minimum 50kW for commercial projects
        rejection_reasons.append("System size below minimum threshold (50kW)")
    elif system_size > 5000:  # Maximum 5MW
        rejection_reasons.append("System size above maximum threshold (5MW)")
    
    # Incentive availability check
    incentive_score = check_incentive_availability(address, system_size)
    if incentive_score < 30:  # Minimum incentive threshold
        warnings.append("Limited incentive availability may impact project economics")
    
    # Basic interconnection feasibility
    interconnection_risk = assess_basic_interconnection_risk(address)
    if interconnection_risk == 'high':
        warnings.append("Potential interconnection challenges identified")
    
    # Permitting complexity assessment
    permitting_risk = assess_permitting_complexity(address)
    if permitting_risk == 'high':
        warnings.append("Complex permitting requirements anticipated")
    
    eligible = len(rejection_reasons) == 0
    
    return {
        'eligible': eligible,
        'rejection_reasons': rejection_reasons,
        'warnings': warnings,
        'incentive_score': incentive_score,
        'interconnection_risk': interconnection_risk,
        'permitting_risk': permitting_risk,
        'screening_date': datetime.now().isoformat()
    }

def check_incentive_availability(address: dict, system_size: float) -> int:
    """
    Check federal and state incentive availability. Returns score 0-100.
    """
    score = 30  # Base federal ITC
    state = address.get('state', '').upper()
    
    # State-specific incentives
    high_incentive_states = ['CA', 'NY', 'NJ', 'MA', 'CT', 'MD']
    medium_incentive_states = ['TX', 'FL', 'NC', 'AZ', 'NV', 'CO']
    
    if state in high_incentive_states:
        score += 40
    elif state in medium_incentive_states:
        score += 20
    else:
        score += 10
    
    # Size-based incentives
    if 100 <= system_size <= 1000:  # Sweet spot for incentives
        score += 20
    elif system_size > 1000:
        score += 10
    
    return min(score, 100)

def assess_basic_interconnection_risk(address: dict) -> str:
    """
    Assess basic interconnection risk based on location and utility.
    """
    state = address.get('state', '').upper()
    
    # High-risk states (based on known utility challenges)
    high_risk_states = ['TX', 'CA']  # ERCOT and CAISO complexities
    medium_risk_states = ['NY', 'NJ', 'MA']  # Dense markets
    
    if state in high_risk_states:
        return 'high'
    elif state in medium_risk_states:
        return 'medium'
    else:
        return 'low'

def assess_permitting_complexity(address: dict) -> str:
    """
    Assess permitting complexity based on location.
    """
    state = address.get('state', '').upper()
    city = address.get('city', '').lower()
    
    # High complexity jurisdictions
    high_complexity_states = ['CA', 'NY', 'NJ']
    high_complexity_cities = ['san francisco', 'new york', 'boston', 'seattle']
    
    if state in high_complexity_states or any(hc_city in city for hc_city in high_complexity_cities):
        return 'high'
    else:
        return 'medium'

@app.function_name(name="helioscope_parser")
@app.queue_trigger(arg_name="msg", queue_name="helioscope-parser", connection="AzureWebJobsStorage")
def helioscope_parser(msg: func.QueueMessage) -> None:
    """
    Queue-triggered function that processes Helioscope design data.
    """
    webhook_data = json.loads(msg.get_body().decode('utf-8'))
    logging.info(f"Processing Helioscope webhook: {webhook_data}")
    
    try:
        project_id = webhook_data.get('project_id')
        design_id = webhook_data.get('design_id')
        
        if not project_id and not design_id:
            logging.error("No project_id or design_id found in webhook")
            return
        
        # Call Helioscope API to get design data
        helioscope_data = fetch_helioscope_design_data(design_id or project_id)
        
        if project_id:
            # Update existing project
            cosmos_client = CosmosDBClient()
            project = cosmos_client.get_project(project_id)
            
            if project:
                # Transform and update project with Helioscope data
                updates = transform_helioscope_data(helioscope_data)
                cosmos_client.update_project(project_id, updates)
                
                # Continue pipeline
                invoke_function("interconnection_scorer", project_id)
        else:
            # Create new project from Helioscope data
            project_data = create_project_from_helioscope(helioscope_data)
            project = UnifiedProjectModel(**project_data)
            
            cosmos_client = CosmosDBClient()
            cosmos_client.create_project(project.dict())
            
            # Start pipeline
            invoke_function("eligibility_screener", project.project_id)
        
    except Exception as e:
        logging.error(f"Error in helioscope_parser: {e}")

def fetch_helioscope_design_data(design_id: str) -> dict:
    """
    Fetch design data from Helioscope API.
    """
    # Mock Helioscope API integration
    # In production, this would call the actual Helioscope API
    logging.info(f"Fetching Helioscope data for design {design_id}")
    
    # Mock data structure
    return {
        "design_id": design_id,
        "system_size_dc_kw": 250.0,
        "system_size_ac_kw": 212.5,
        "annual_production_kwh": 325000,
        "module_count": 625,
        "inverter_count": 5,
        "layout_image_url": f"https://helioscope.com/designs/{design_id}/layout.png",
        "performance_metrics": {
            "specific_yield": 1300,
            "performance_ratio": 0.85,
            "capacity_factor": 0.20
        }
    }

def transform_helioscope_data(helioscope_data: dict) -> dict:
    """
    Transform Helioscope API data into our project format.
    """
    return {
        'system_specs.system_size_ac_kw': helioscope_data.get('system_size_ac_kw'),
        'production_metrics': {
            'annual_production_kwh': helioscope_data.get('annual_production_kwh'),
            'specific_yield': helioscope_data['performance_metrics'].get('specific_yield'),
            'performance_ratio': helioscope_data['performance_metrics'].get('performance_ratio'),
            'capacity_factor': helioscope_data['performance_metrics'].get('capacity_factor'),
            'kwh_per_kw': helioscope_data.get('annual_production_kwh', 0) / helioscope_data.get('system_size_ac_kw', 1)
        },
        'project_documents.pv_layout_pdf_url': helioscope_data.get('layout_image_url'),
        'milestones.engineering': 'Conceptual Design'
    }

def create_project_from_helioscope(helioscope_data: dict) -> dict:
    """
    Create a new project from Helioscope webhook data.
    """
    # This would extract address and other info from Helioscope data
    # For now, using mock data
    address = Address(
        street="TBD from Helioscope",
        city="Unknown",
        state="Unknown",
        zip_code="00000"
    )
    
    system_specs = SystemSpecs(
        system_size_dc_kw=helioscope_data.get('system_size_dc_kw', 0),
        system_size_ac_kw=helioscope_data.get('system_size_ac_kw', 0),
        module_count=helioscope_data.get('module_count', 0),
        inverter_type='string',
        roof_type='flat',
        bill_of_materials=[]
    )
    
    financials = Financials(
        estimated_capex=helioscope_data.get('system_size_dc_kw', 0) * 1000 * 2.50,
        price_per_watt=2.50
    )
    
    return {
        'project_name': f"Helioscope Project {helioscope_data.get('design_id')}",
        'data_source': 'Helioscope',
        'address': address.dict(),
        'system_specs': system_specs.dict(),
        'financials': financials.dict()
    }