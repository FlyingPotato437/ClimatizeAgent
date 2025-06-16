"""
Clean Azure Functions App using modular architecture.
Replaces the monolithic 4k-line function_app.py with proper separation of concerns.
"""
import azure.functions as func
import logging

# Import our clean API routes
from api.routes import (
    quick_look_feasibility_handler,
    get_feasibility_package,
    manual_intake_handler,
    get_all_projects,
    get_project,
    update_project,
    delete_project,
    download_project_package,
    helioscope_webhook_receiver,
    health_check
)

# Import background task handlers
from workers.task_handlers import (
    helioscope_design_engine_handler,
    battery_sizing_engine_handler,
    interconnection_scorer_handler,
    permit_matrix_engine_handler,
    feasibility_and_site_control_handler,
    capital_stack_generator_handler,
    project_packager_and_scorer_handler,
    pro_forma_generator_handler,
    site_control_document_generator_handler,
    eligibility_screener_handler,
    helioscope_parser_handler
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize the Function App
app = func.FunctionApp()

# ========================================
# HTTP API Endpoints
# ========================================

@app.route(route="quick_look_feasibility", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def quick_look_feasibility(req: func.HttpRequest) -> func.HttpResponse:
    """Quick-Look Feasibility analysis endpoint."""
    return quick_look_feasibility_handler(req)

@app.route(route="get_feasibility_package/{project_id}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def get_feasibility_package_route(req: func.HttpRequest) -> func.HttpResponse:
    """Get feasibility package endpoint."""
    return get_feasibility_package(req)

@app.route(route="manual_intake_handler", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def manual_intake(req: func.HttpRequest) -> func.HttpResponse:
    """Manual project intake endpoint."""
    return manual_intake_handler(req)

@app.route(route="projects", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def projects_list(req: func.HttpRequest) -> func.HttpResponse:
    """Get all projects endpoint."""
    return get_all_projects(req)

@app.route(route="projects/{project_id}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET", "PUT", "DELETE"])
def project_detail(req: func.HttpRequest) -> func.HttpResponse:
    """Project CRUD operations endpoint."""
    method = req.method.upper()
    
    if method == "GET":
        return get_project(req)
    elif method == "PUT":
        return update_project(req)
    elif method == "DELETE":
        return delete_project(req)
    else:
        return func.HttpResponse(
            '{"error": "Method not allowed"}',
            status_code=405,
            mimetype="application/json"
        )

@app.route(route="download_project_package/{project_id}", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def download_package(req: func.HttpRequest) -> func.HttpResponse:
    """Download project package endpoint."""
    return download_project_package(req)

@app.route(route="helioscope_webhook", auth_level=func.AuthLevel.ANONYMOUS, methods=["POST"])
def helioscope_webhook(req: func.HttpRequest) -> func.HttpResponse:
    """Helioscope webhook receiver endpoint."""
    return helioscope_webhook_receiver(req)

@app.route(route="health", auth_level=func.AuthLevel.ANONYMOUS, methods=["GET"])
def health(req: func.HttpRequest) -> func.HttpResponse:
    """Health check endpoint."""
    return health_check(req)

# ========================================
# Background Queue Processors
# ========================================

@app.function_name(name="helioscope_design_engine")
@app.queue_trigger(arg_name="msg", queue_name="helioscope-design", connection="AzureWebJobsStorage")
def helioscope_design_engine(msg: func.QueueMessage) -> None:
    """Helioscope design processing queue handler."""
    helioscope_design_engine_handler(msg)

@app.function_name(name="battery_sizing_engine")
@app.queue_trigger(arg_name="msg", queue_name="battery-sizing", connection="AzureWebJobsStorage")
def battery_sizing_engine(msg: func.QueueMessage) -> None:
    """Battery sizing processing queue handler."""
    battery_sizing_engine_handler(msg)

@app.function_name(name="interconnection_scorer")
@app.queue_trigger(arg_name="msg", queue_name="interconnection-scoring", connection="AzureWebJobsStorage")
def interconnection_scorer(msg: func.QueueMessage) -> None:
    """Interconnection scoring queue handler."""
    interconnection_scorer_handler(msg)

@app.function_name(name="permit_matrix_engine")
@app.queue_trigger(arg_name="msg", queue_name="permit-matrix", connection="AzureWebJobsStorage")
def permit_matrix_engine(msg: func.QueueMessage) -> None:
    """Permit matrix generation queue handler."""
    permit_matrix_engine_handler(msg)

@app.function_name(name="feasibility_and_site_control")
@app.queue_trigger(arg_name="msg", queue_name="feasibility-site-control", connection="AzureWebJobsStorage")
def feasibility_and_site_control(msg: func.QueueMessage) -> None:
    """Feasibility and site control queue handler."""
    feasibility_and_site_control_handler(msg)

@app.function_name(name="capital_stack_generator")
@app.queue_trigger(arg_name="msg", queue_name="capital-stack", connection="AzureWebJobsStorage")
def capital_stack_generator(msg: func.QueueMessage) -> None:
    """Capital stack generation queue handler."""
    capital_stack_generator_handler(msg)

@app.function_name(name="project_packager_and_scorer")
@app.queue_trigger(arg_name="msg", queue_name="project-scoring", connection="AzureWebJobsStorage")
def project_packager_and_scorer(msg: func.QueueMessage) -> None:
    """Project packaging and scoring queue handler."""
    project_packager_and_scorer_handler(msg)

@app.function_name(name="pro_forma_generator")
@app.queue_trigger(arg_name="msg", queue_name="pro-forma", connection="AzureWebJobsStorage")
def pro_forma_generator(msg: func.QueueMessage) -> None:
    """Pro forma generation queue handler."""
    pro_forma_generator_handler(msg)

@app.function_name(name="site_control_document_generator")
@app.queue_trigger(arg_name="msg", queue_name="site-control-docs", connection="AzureWebJobsStorage")
def site_control_document_generator(msg: func.QueueMessage) -> None:
    """Site control document generation queue handler."""
    site_control_document_generator_handler(msg)

@app.function_name(name="eligibility_screener")
@app.queue_trigger(arg_name="msg", queue_name="eligibility-screening", connection="AzureWebJobsStorage")
def eligibility_screener(msg: func.QueueMessage) -> None:
    """Eligibility screening queue handler."""
    eligibility_screener_handler(msg)

@app.function_name(name="helioscope_parser")
@app.queue_trigger(arg_name="msg", queue_name="helioscope-parser", connection="AzureWebJobsStorage")
def helioscope_parser(msg: func.QueueMessage) -> None:
    """Helioscope response parser queue handler."""
    helioscope_parser_handler(msg)

# ========================================
# Startup Configuration
# ========================================

if __name__ == "__main__":
    logger.info("🚀 Climatize AI Function App - Modular Architecture v2.0")
    logger.info("✅ Clean separation of concerns")
    logger.info("✅ Service-based architecture") 
    logger.info("✅ Proper error handling")
    logger.info("✅ Comprehensive background processing")
    logger.info("Ready to serve requests!") 