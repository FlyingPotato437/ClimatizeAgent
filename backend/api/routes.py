"""
Clean API routing for the Climatize AI platform.
"""
import azure.functions as func
import logging
import json
from typing import Dict, Any
from ..services.project_service import ProjectService
from ..services.helioscope_service import HelioscoperService
from ..core.database import get_db_client
from ..models.project import UnifiedProjectModel

logger = logging.getLogger(__name__)

# Initialize services
project_service = ProjectService()
helioscope_service = HelioscoperService()

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
            "version": "2.0.0"
        }
        
        status_code = 200 if db_healthy else 503
        return create_success_response(health_status, status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_error_response("Health check failed", 503) 