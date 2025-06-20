"""
Azure Functions App for Dead Letter Queue Processing.
Contains function definitions for all poison queue handlers.
"""
import azure.functions as func
import logging
from workers.dlq_processor import (
    process_helioscope_dlq,
    process_feasibility_dlq, 
    process_document_generation_dlq
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = func.FunctionApp()


@app.function_name(name="ProcessHelioscopeDlq")
@app.queue_trigger(
    arg_name="msg",
    queue_name="helioscope-queue-poison",
    connection="AzureWebJobsStorage"
)
def helioscope_dlq_handler(msg: func.QueueMessage) -> None:
    """
    Azure Function trigger for Helioscope poison queue.
    Processes failed messages from helioscope-queue.
    """
    process_helioscope_dlq(msg)


@app.function_name(name="ProcessFeasibilityDlq")
@app.queue_trigger(
    arg_name="msg", 
    queue_name="feasibility-queue-poison",
    connection="AzureWebJobsStorage"
)
def feasibility_dlq_handler(msg: func.QueueMessage) -> None:
    """
    Azure Function trigger for Feasibility analysis poison queue.
    Processes failed messages from feasibility-queue.
    """
    process_feasibility_dlq(msg)


@app.function_name(name="ProcessDocumentGenerationDlq")
@app.queue_trigger(
    arg_name="msg",
    queue_name="document-generation-queue-poison", 
    connection="AzureWebJobsStorage"
)
def document_generation_dlq_handler(msg: func.QueueMessage) -> None:
    """
    Azure Function trigger for Document generation poison queue.
    Processes failed messages from document-generation-queue.
    """
    process_document_generation_dlq(msg)


@app.function_name(name="DlqHealthCheck")
@app.route(route="dlq/health", methods=["GET"])
def dlq_health_check(req: func.HttpRequest) -> func.HttpResponse:
    """
    Health check endpoint for DLQ processor configuration.
    Validates that all expected queues have handlers configured.
    """
    try:
        # Define expected queues that should have DLQ handlers
        expected_queues = [
            "helioscope-queue",
            "feasibility-queue", 
            "document-generation-queue"
        ]
        
        # Check handler registry from dlq_processor
        from workers.dlq_processor import HANDLER_REGISTRY
        configured_queues = list(HANDLER_REGISTRY.keys())
        
        missing_handlers = [q for q in expected_queues if q not in configured_queues]
        
        if not missing_handlers:
            return func.HttpResponse(
                "OK: All expected queues have DLQ handlers configured.",
                status_code=200
            )
        else:
            error_msg = f"Configuration Error: Missing DLQ handlers for queues: {', '.join(missing_handlers)}"
            logger.error(error_msg)
            return func.HttpResponse(error_msg, status_code=500)
            
    except Exception as e:
        error_msg = f"Health check failed: {str(e)}"
        logger.error(error_msg)
        return func.HttpResponse(error_msg, status_code=500)