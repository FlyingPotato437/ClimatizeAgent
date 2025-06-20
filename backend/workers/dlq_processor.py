"""
Dead Letter Queue (DLQ) Processor for Azure Functions.
Handles failed messages from poison queues with robust error handling and state management.

Production-ready implementation with:
- Idempotent failure handling
- Blob storage for raw message payloads  
- Workflow state integration
- Comprehensive error handling
- Monitoring and alerting integration
"""
import logging
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import azure.functions as func

from services.workflow_state_service import get_workflow_state_service
from core.database import get_storage_client

logger = logging.getLogger(__name__)

# Initialize services
workflow_state_service = get_workflow_state_service()
storage_client = get_storage_client()


class DLQFailureHandler:
    """Handles different types of DLQ failures with robust error handling."""
    
    def __init__(self):
        self.workflow_state = workflow_state_service
        self.storage = storage_client
    
    async def handle_helioscope_failure(self, msg_body: str, msg_id: str, queue_name: str) -> None:
        """Handle failures from Helioscope processing queue."""
        logger.warning(f"Handling Helioscope failure - Message ID: {msg_id}")
        await self._persist_failure("helioscope", msg_body, msg_id, queue_name)
    
    async def handle_feasibility_failure(self, msg_body: str, msg_id: str, queue_name: str) -> None:
        """Handle failures from feasibility analysis queue."""
        logger.warning(f"Handling feasibility analysis failure - Message ID: {msg_id}")
        await self._persist_failure("feasibility", msg_body, msg_id, queue_name)
    
    async def handle_document_generation_failure(self, msg_body: str, msg_id: str, queue_name: str) -> None:
        """Handle failures from document generation queue."""
        logger.warning(f"Handling document generation failure - Message ID: {msg_id}")
        await self._persist_failure("document_generation", msg_body, msg_id, queue_name)
    
    async def handle_unknown_failure(self, msg_body: str, msg_id: str, queue_name: str) -> None:
        """Handle failures from unknown/unmapped queues."""
        logger.critical(f"Unknown queue failure - Queue: {queue_name}, Message ID: {msg_id}")
        await self._persist_failure(f"unknown-{queue_name}", msg_body, msg_id, queue_name, update_state=False)
    
    async def _persist_failure(self, failure_type: str, msg_body: str, msg_id: str, 
                             queue_name: str, update_state: bool = True) -> None:
        """
        Core failure persistence logic. MUST NOT raise exceptions.
        
        Steps:
        1. Parse message to extract run_id and project_id
        2. Save raw payload to blob storage
        3. Update workflow state if applicable
        4. Log structured failure data
        """
        run_id = None
        project_id = None
        
        try:
            # Step 1: Defensively parse message for metadata
            try:
                data = json.loads(msg_body)
                run_id = data.get("run_id")
                project_id = data.get("project_id")
                logger.info(f"Extracted metadata - Run ID: {run_id}, Project ID: {project_id}")
            except (json.JSONDecodeError, TypeError, AttributeError):
                logger.warning(f"Could not parse message {msg_id} as JSON. Treating as raw data.")
                # Can't extract metadata, but continue with blob storage
                update_state = False
            
            # Step 2: Save raw payload to blob storage for analysis
            blob_name = None
            try:
                timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
                blob_name = f"failed-messages/{failure_type}/{run_id or msg_id}_{timestamp}.json"
                
                failure_metadata = {
                    "message_id": msg_id,
                    "queue_name": queue_name,
                    "failure_type": failure_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "run_id": run_id,
                    "project_id": project_id,
                    "raw_payload": msg_body
                }
                
                await self.storage.upload_document(
                    project_id=project_id or "unknown",
                    filename=blob_name,
                    content=json.dumps(failure_metadata, indent=2).encode('utf-8')
                )
                
                blob_url = self.storage.get_document_url(blob_name)
                logger.info(f"Saved failed message to blob: {blob_url}")
                
            except Exception as e:
                logger.error(f"Failed to save message {msg_id} to blob storage: {e}")
                blob_url = None
            
            # Step 3: Update workflow state if we have run_id and project_id
            if update_state and run_id and project_id:
                try:
                    # Determine which step failed based on failure type
                    failed_step = self._map_failure_type_to_step(failure_type)
                    
                    # Update step status to Failed
                    success = self.workflow_state.update_step_status(
                        project_id=project_id,
                        run_id=run_id,
                        step_name=failed_step,
                        status="Failed",
                        error_details=f"DLQ failure in {queue_name}. Message ID: {msg_id}. Blob: {blob_url or 'N/A'}"
                    )
                    
                    if success:
                        logger.info(f"Updated workflow state for {project_id}/{run_id} - Step: {failed_step}")
                    else:
                        logger.warning(f"Workflow state update was idempotent for {project_id}/{run_id}")
                        
                except Exception as e:
                    logger.error(f"Failed to update workflow state for {run_id}: {e}")
            
            # Step 4: Structured logging for monitoring
            logger.error(
                "DLQ_FAILURE_PROCESSED",
                extra={
                    "message_id": msg_id,
                    "queue_name": queue_name,
                    "failure_type": failure_type,
                    "run_id": run_id,
                    "project_id": project_id,
                    "blob_url": blob_url,
                    "state_updated": update_state and run_id and project_id
                }
            )
            
        except Exception as e:
            # Ultimate safety net - this should never happen
            logger.critical(
                f"CRITICAL: Unhandled exception in DLQ failure handler for message {msg_id}. "
                f"Message will be lost. Error: {e}",
                exc_info=True
            )
    
    def _map_failure_type_to_step(self, failure_type: str) -> str:
        """Map failure type to workflow step name."""
        mapping = {
            "helioscope": "helioscope_fetch",
            "feasibility": "feasibility_analysis", 
            "document_generation": "document_generation"
        }
        return mapping.get(failure_type, "unknown_step")


# Handler registry - maps queue base names to handler methods
HANDLER_REGISTRY = {
    "helioscope-queue": "handle_helioscope_failure",
    "feasibility-queue": "handle_feasibility_failure",
    "document-generation-queue": "handle_document_generation_failure"
}

# Initialize handler instance
dlq_handler = DLQFailureHandler()


async def dispatch_dlq_message(msg: func.QueueMessage) -> None:
    """
    Central dispatcher for DLQ messages. Routes to appropriate handler based on queue name.
    """
    queue_name = msg.queue_name
    base_queue_name = queue_name.removesuffix('-poison')
    msg_body = msg.get_body().decode('utf-8')
    msg_id = msg.id
    
    logger.info(f"Processing DLQ message - Queue: {queue_name}, ID: {msg_id}")
    
    # Get handler method name from registry
    handler_method_name = HANDLER_REGISTRY.get(base_queue_name)
    
    if handler_method_name and hasattr(dlq_handler, handler_method_name):
        handler_method = getattr(dlq_handler, handler_method_name)
        await handler_method(msg_body, msg_id, queue_name)
    else:
        logger.critical(f"No handler found for queue '{queue_name}'. Using unknown handler.")
        await dlq_handler.handle_unknown_failure(msg_body, msg_id, queue_name)


def create_dlq_processor_entrypoint(msg: func.QueueMessage) -> None:
    """
    Ultimate safety net wrapper to prevent poison-poison scenarios.
    This ensures the DLQ processor itself never fails and causes secondary poison messages.
    """
    try:
        logger.info(f"DLQ processor triggered - Queue: {msg.queue_name}, Message ID: {msg.id}")
        
        # Run the async dispatch logic
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(dispatch_dlq_message(msg))
        finally:
            loop.close()
            
    except Exception as e:
        # This is the final defense against unhandled exceptions
        # If we reach here, something is fundamentally broken
        logger.critical(
            f"FATAL: Unhandled exception in DLQ processor entrypoint for message {msg.id}. "
            f"The message will be deleted without processing. Error: {e}",
            exc_info=True
        )
        
        # Send critical alert - this indicates a serious system issue
        # In production, this should trigger immediate alerts
        try:
            logger.critical(
                "DLQ_PROCESSOR_FATAL_ERROR",
                extra={
                    "message_id": msg.id,
                    "queue_name": msg.queue_name,
                    "error": str(e),
                    "alert_level": "CRITICAL"
                }
            )
        except:
            # If even logging fails, there's nothing more we can do
            pass


# Azure Functions trigger definitions
# Each poison queue gets its own trigger function for isolation

def process_helioscope_dlq(msg: func.QueueMessage) -> None:
    """Process messages from helioscope-queue-poison."""
    create_dlq_processor_entrypoint(msg)


def process_feasibility_dlq(msg: func.QueueMessage) -> None:
    """Process messages from feasibility-queue-poison."""
    create_dlq_processor_entrypoint(msg)


def process_document_generation_dlq(msg: func.QueueMessage) -> None:
    """Process messages from document-generation-queue-poison."""
    create_dlq_processor_entrypoint(msg)