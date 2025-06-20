"""
Clean API routing for the Climatize AI platform.
"""
import azure.functions as func
import logging
import json
from typing import Dict, Any
from services.project_service import ProjectService
from services.helioscope_service import HelioscoperService
from services.mock_helioscope_adapter import MockHelioscopeServiceDecorator
from services.workflow_state_service import get_workflow_state_service
from services.ultrathink_orchestrator import get_ultrathink_orchestrator
from core.database import get_db_client
from core.config import settings
from models.project_simple import UnifiedProjectModel

logger = logging.getLogger(__name__)

# Initialize services
project_service = ProjectService()

# Initialize Helioscope service with mock capability
_helioscope_service = HelioscoperService()
helioscope_service = MockHelioscopeServiceDecorator(
    _helioscope_service, 
    use_mock=settings.use_mock_helioscope
)

workflow_state_service = get_workflow_state_service()

# Initialize Ultrathink orchestrator
ultrathink_orchestrator = get_ultrathink_orchestrator()

def create_error_response(message: str, status_code: int = 500) -> func.HttpResponse:
    """Create standardized error response."""
    return func.HttpResponse(
        json.dumps({"error": message}),
        status_code=status_code,
        mimetype="application/json"
    )

def create_success_response(data: Any, status_code: int = 200) -> func.HttpResponse:
    """Create standardized success response."""
    return func.HttpResponse(
        json.dumps(data, default=str),
        status_code=status_code,
        mimetype="application/json"
    )

def get_user_id_from_headers(req: func.HttpRequest) -> str:
    """
    Extract user ID from request headers.
    For now, this is a simplified version - in production you'd validate JWT tokens.
    """
    # Check for user ID in headers (simplified auth)
    user_id = req.headers.get('X-User-ID')
    if not user_id:
        # Fallback to Authorization header parsing (if using Bearer tokens)
        auth_header = req.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            # In a real system, you'd decode the JWT token here
            # For now, we'll use a simple placeholder
            user_id = "default_user"  # TODO: Implement proper JWT validation
        else:
            user_id = "anonymous"
    
    return user_id

async def check_project_access(user_id: str, project_id: str) -> bool:
    """
    Check if a user has access to a specific project.
    For now, this is simplified - in production you'd check user permissions.
    """
    try:
        project = await project_service.get_project(project_id)
        if not project:
            return False
        
        # For now, allow access if project exists
        # TODO: Implement proper user-project relationship checking
        # You would typically check:
        # - Project ownership
        # - User permissions/roles
        # - Organization membership
        
        return True
    except Exception as e:
        logger.error(f"Error checking project access for user {user_id}, project {project_id}: {e}")
        return False

async def quick_look_feasibility_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint for Quick-Look Feasibility analysis.
    
    Minimal input: address + system size → Complete feasibility package
    """
    logger.info('Processing Quick-Look Feasibility request.')
    
    try:
        req_body = req.get_json()
        if not req_body:
            return create_error_response("Request body is required", 400)

        # Validate required fields
        if not req_body.get('address'):
            return create_error_response("Address is required", 400)

        # Create project using service
        project_id = await project_service.create_quick_look_project(req_body)
        
        return create_success_response({
            "project_id": project_id,
            "status": "Processing started",
            "message": "Feasibility analysis initiated"
        }, 202)
        
    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Unexpected error in quick_look_feasibility_handler: {str(e)}")
        return create_error_response("Internal server error", 500)

async def get_feasibility_package(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint to retrieve completed feasibility package.
    """
    project_id = req.route_params.get('project_id')
    logger.info(f'Retrieving feasibility package for project {project_id}.')
    
    try:
        if not project_id:
            return create_error_response("Project ID is required", 400)
            
        # Get project and format package
        package = await project_service.get_feasibility_package(project_id)
        
        if package is None:
            return create_error_response("Project not found", 404)
        
        # Check if still processing
        if package.get('status') == 'processing':
            return create_success_response({
                "project_id": project_id,
                "status": "In progress",
                "progress_percentage": package.get('progress_percentage', 0),
                "current_stage": package.get('current_stage', 'Initializing')
            }, 202)
        
        return create_success_response(package)
        
    except Exception as e:
        logger.error(f"Error retrieving feasibility package for {project_id}: {str(e)}")
        return create_error_response("Failed to retrieve package", 500)

async def manual_intake_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint for manual project data intake.
    """
    logger.info('Processing manual project intake request.')
    
    try:
        req_body = req.get_json()
        if not req_body:
            return create_error_response("Request body is required", 400)
        
        # Create project using service
        project = await project_service.create_manual_project(req_body)
        
        return create_success_response({
            "project_id": project['project_id'],
            "status": "Created",
            "message": "Project created successfully"
        }, 201)
        
    except ValueError as e:
        return create_error_response(f"Invalid project data: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Error in manual intake: {str(e)}")
        return create_error_response("Failed to create project", 500)

async def get_all_projects(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint to retrieve all projects with pagination.
    """
    logger.info('Retrieving all projects.')
    
    try:
        # Get query parameters
        page = int(req.params.get('page', 1))
        limit = int(req.params.get('limit', 20))
        status_filter = req.params.get('status')
        
        # Get projects using service
        projects = await project_service.get_all_projects(page, limit, status_filter)
        
        return create_success_response(projects)
        
    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Error retrieving projects: {str(e)}")
        return create_error_response("Failed to retrieve projects", 500)

async def get_project(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint to retrieve a specific project.
    """
    project_id = req.route_params.get('project_id')
    logger.info(f'Retrieving project {project_id}.')
    
    try:
        if not project_id:
            return create_error_response("Project ID is required", 400)
            
        project = await project_service.get_project(project_id)
        
        if not project:
            return create_error_response("Project not found", 404)
            
        return create_success_response(project)
        
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {str(e)}")
        return create_error_response("Failed to retrieve project", 500)

async def update_project(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP PUT endpoint to update a project.
    """
    project_id = req.route_params.get('project_id')
    logger.info(f'Updating project {project_id}.')
    
    try:
        if not project_id:
            return create_error_response("Project ID is required", 400)
            
        req_body = req.get_json()
        if not req_body:
            return create_error_response("Request body is required", 400)
        
        updated_project = await project_service.update_project(project_id, req_body)
        
        if not updated_project:
            return create_error_response("Project not found", 404)
            
        return create_success_response(updated_project)
        
    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Error updating project {project_id}: {str(e)}")
        return create_error_response("Failed to update project", 500)

async def delete_project(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP DELETE endpoint to delete a project.
    """
    project_id = req.route_params.get('project_id')
    logger.info(f'Deleting project {project_id}.')
    
    try:
        if not project_id:
            return create_error_response("Project ID is required", 400)
            
        success = await project_service.delete_project(project_id)
        
        if not success:
            return create_error_response("Project not found", 404)
            
        return create_success_response({"message": "Project deleted successfully"})
        
    except Exception as e:
        logger.error(f"Error deleting project {project_id}: {str(e)}")
        return create_error_response("Failed to delete project", 500)

async def download_project_package(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint to download complete project package as ZIP.
    """
    project_id = req.route_params.get('project_id')
    logger.info(f'Generating download package for project {project_id}.')
    
    try:
        if not project_id:
            return create_error_response("Project ID is required", 400)
            
        # Generate downloadable package
        package_url = await project_service.generate_download_package(project_id)
        
        if not package_url:
            return create_error_response("Project not found or package generation failed", 404)
            
        return create_success_response({
            "download_url": package_url,
            "expires_in": "24 hours"
        })
        
    except Exception as e:
        logger.error(f"Error generating download package for {project_id}: {str(e)}")
        return create_error_response("Failed to generate download package", 500)

async def helioscope_project_intake_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint for Helioscope project intake using client credentials.
    
    Expected payload:
    {
        "helioscope_project_id": "string",
        "helioscope_credentials": {
            "api_token": "string",
            "username": "string" (optional)
        },
        "project_name": "string" (optional)
    }
    """
    logger.info('Processing Helioscope project intake request.')
    
    try:
        req_body = req.get_json()
        if not req_body:
            return create_error_response("Request body is required", 400)

        # Validate required fields
        helioscope_project_id = req_body.get('helioscope_project_id')
        helioscope_credentials = req_body.get('helioscope_credentials')
        
        if not helioscope_project_id:
            return create_error_response("helioscope_project_id is required", 400)
        
        if not helioscope_credentials or not helioscope_credentials.get('api_token'):
            return create_error_response("helioscope_credentials with api_token are required", 400)

        # Process the Helioscope project data
        result = await helioscope_service.process_complete_helioscope_data(
            project_id=None,  # Will be generated in the service
            helioscope_project_id=helioscope_project_id,
            helioscope_credentials=helioscope_credentials
        )
        
        return create_success_response({
            "message": "Helioscope project processing initiated",
            "project_id": result.get('project_id'),
            "run_id": result.get('run_id'),
            "status": "processing",
            "status_url": f"/api/workflow/status/{result.get('project_id')}/{result.get('run_id')}"
        }, 202)
        
    except Exception as e:
        logger.error(f"Error in Helioscope project intake: {str(e)}")
        return create_error_response(f"Internal server error: {str(e)}")

async def helioscope_webhook_receiver(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint for Helioscope webhook callbacks.
    """
    logger.info('Processing Helioscope webhook.')
    
    try:
        req_body = req.get_json()
        if not req_body:
            return create_error_response("Request body is required", 400)
        
        project_id = req_body.get('project_id')
        if not project_id:
            return create_error_response("Project ID is required in webhook payload", 400)
        
        # Process webhook using service
        result = await helioscope_service.parse_helioscope_response(project_id, req_body)
        
        return create_success_response({
            "status": "processed",
            "project_id": project_id
        })
        
    except Exception as e:
        logger.error(f"Error processing Helioscope webhook: {str(e)}")
        return create_error_response("Failed to process webhook", 500)

async def generate_permitting_package_handler(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint for generating complete permitting package.
    
    Expected payload:
    {
        "project_id": "string"
    }
    """
    logger.info('Processing permitting package generation request.')
    
    try:
        req_body = req.get_json()
        if not req_body:
            return create_error_response("Request body is required", 400)

        project_id = req_body.get('project_id')
        if not project_id:
            return create_error_response("project_id is required", 400)

        # Generate complete permitting package
        result = await project_service.generate_complete_permitting_package(project_id)
        
        return create_success_response({
            "message": "Permitting package generated successfully",
            "result": result
        })
        
    except Exception as e:
        logger.error(f"Error generating permitting package: {str(e)}")
        return create_error_response(f"Internal server error: {str(e)}")

async def get_workflow_status(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint to get workflow run status with authorization.
    
    Path: /api/workflow/status/{project_id}/{run_id}
    Headers: X-User-ID or Authorization Bearer token
    """
    project_id = req.route_params.get('project_id')
    run_id = req.route_params.get('run_id')
    
    logger.info(f'Getting workflow status for project {project_id}, run {run_id}.')
    
    try:
        if not project_id or not run_id:
            return create_error_response("Both project_id and run_id are required", 400)
        
        # Get user ID from headers
        user_id = get_user_id_from_headers(req)
        
        # Check if user has access to this project
        has_access = await check_project_access(user_id, project_id)
        if not has_access:
            # Return 404 instead of 403 to avoid leaking information about run existence
            return create_error_response("Workflow run not found", 404)
        
        # Get workflow state
        workflow_state = workflow_state_service.get_workflow_state(project_id, run_id)
        
        if not workflow_state:
            return create_error_response("Workflow run not found", 404)
        
        # Format response for frontend consumption
        response_data = {
            "project_id": project_id,
            "run_id": run_id,
            "status": workflow_state.get("RunStatus"),
            "current_step": workflow_state.get("CurrentStep"),
            "last_update": workflow_state.get("LastUpdate"),
            "steps": workflow_state.get("Steps", {}),
            "error_details": workflow_state.get("ErrorDetails"),
            "results": workflow_state.get("Results", {})
        }
        
        # Determine HTTP status code based on workflow status
        status_code = 200
        if workflow_state.get("RunStatus") == "Processing":
            status_code = 202  # Accepted, still processing
        elif workflow_state.get("RunStatus") == "Failed":
            status_code = 200  # Return 200 but indicate failure in the response
        
        return create_success_response(response_data, status_code)
        
    except Exception as e:
        logger.error(f"Error getting workflow status for {project_id}/{run_id}: {str(e)}")
        return create_error_response("Failed to get workflow status", 500)

async def ultrathink_collaborative_analysis(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP POST endpoint for Ultrathink multi-agent collaborative analysis.
    Implements the core "agentic AI that bounces ideas off each other" functionality.
    """
    logger.info('🧠 Processing Ultrathink collaborative analysis request.')
    
    try:
        req_body = req.get_json()
        if not req_body:
            return create_error_response("Request body is required", 400)

        # Validate required fields
        project_id = req_body.get('project_id')
        if not project_id:
            return create_error_response("Project ID is required", 400)

        # Get project data
        project = await project_service.get_project(project_id)
        if not project:
            return create_error_response("Project not found", 404)

        # Run Ultrathink collaborative analysis
        collaborative_result = await ultrathink_orchestrator.analyze_project_collaboratively(project)
        
        return create_success_response({
            "status": "Analysis complete",
            "analysis_results": collaborative_result,
            "ultrathink_framework": "Multi-agent collaborative reasoning with conflict resolution",
            "message": "Collaborative analysis completed successfully"
        })
        
    except ValueError as e:
        return create_error_response(str(e), 400)
    except Exception as e:
        logger.error(f"Unexpected error in ultrathink_collaborative_analysis: {str(e)}")
        return create_error_response("Internal server error", 500)

async def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    HTTP GET endpoint for health checking.
    """
    try:
        # Basic health checks
        db_client = get_db_client()
        db_healthy = await db_client.health_check()
        
        health_status = {
            "status": "healthy" if db_healthy else "unhealthy",
            "database": "connected" if db_healthy else "disconnected",
            "timestamp": str(func.utcnow()),
            "version": "2.0.0",
            "ultrathink_enabled": True,
            "features": {
                "multi_agent_collaboration": True,
                "conflict_resolution": True,
                "langgraph_orchestration": True
            }
        }
        
        status_code = 200 if db_healthy else 503
        return create_success_response(health_status, status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_error_response("Health check failed", 503) 