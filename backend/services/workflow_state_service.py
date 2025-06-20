"""
Workflow state management service using Azure Table Storage.
Provides idempotent operations with ETag race condition protection.
"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from azure.data.tables import TableServiceClient, UpdateMode
from azure.core.exceptions import ResourceNotFoundError, ResourceExistsError, ResourceModifiedError

from core.config import settings

logger = logging.getLogger(__name__)


class MockWorkflowStateService:
    """Mock workflow state service for development."""
    
    def __init__(self):
        self._workflows = {}
        logger.info("Using mock workflow state service for development")
    
    def create_workflow_run(self, project_id: str, run_id: str, workflow_type: str = "helioscope_processing") -> Dict[str, Any]:
        """Create a new workflow run (mock)."""
        key = f"{project_id}:{run_id}"
        self._workflows[key] = {
            "project_id": project_id,
            "run_id": run_id,
            "workflow_type": workflow_type,
            "status": "Pending",
            "current_step": "init",
            "steps": {}
        }
        logger.info(f"Mock: Created workflow run {run_id} for project {project_id}")
        return self._workflows[key]
    
    def get_workflow_state(self, project_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow state (mock)."""
        key = f"{project_id}:{run_id}"
        return self._workflows.get(key)
    
    def update_step_status(self, project_id: str, run_id: str, step_name: str, 
                          status: str, output: Any = None, error_details: str = None) -> bool:
        """Update step status (mock)."""
        key = f"{project_id}:{run_id}"
        if key in self._workflows:
            if "steps" not in self._workflows[key]:
                self._workflows[key]["steps"] = {}
            self._workflows[key]["steps"][step_name] = {
                "status": status,
                "output": output,
                "error_details": error_details
            }
            self._workflows[key]["current_step"] = step_name
            return True
        return False
    
    def mark_step_processing_with_idempotency(self, project_id: str, run_id: str, step_name: str) -> bool:
        """Mark step as processing (mock)."""
        return self.update_step_status(project_id, run_id, step_name, "Processing")
    
    def get_runs_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get runs by project (mock)."""
        return [wf for key, wf in self._workflows.items() if wf["project_id"] == project_id]


class WorkflowStateService:
    """Service for managing workflow state with ETag-based idempotency."""
    
    def __init__(self):
        self.connection_string = settings.table_storage_connection_string
        self.table_name = "WorkflowState"
        
        if not self.connection_string:
            raise ValueError("TABLE_STORAGE_CONNECTION_STRING is required")
        
        self.table_service = TableServiceClient.from_connection_string(self.connection_string)
        self.table_client = self.table_service.get_table_client(table_name=self.table_name)
        
        # Create table if it doesn't exist
        try:
            self.table_service.create_table(table_name=self.table_name)
        except ResourceExistsError:
            pass  # Table already exists
    
    def create_workflow_run(self, project_id: str, run_id: str, workflow_type: str = "helioscope_processing") -> Dict[str, Any]:
        """
        Create a new workflow run with initial state.
        
        Args:
            project_id: The project ID
            run_id: Unique identifier for this workflow run  
            workflow_type: Type of workflow being executed
            
        Returns:
            Dict containing the created state
        """
        initial_state = {
            "PartitionKey": project_id,
            "RowKey": run_id,
            "RunStatus": "Pending",
            "WorkflowType": workflow_type,
            "CurrentStep": "init",
            "LastUpdate": datetime.now(timezone.utc).isoformat(),
            "ErrorDetails": None,
            "Results": json.dumps({}),
            "Steps": json.dumps({
                "helioscope_fetch": {
                    "status": "Pending",
                    "startTime": None,
                    "endTime": None,
                    "output": None
                },
                "feasibility_analysis": {
                    "status": "Pending", 
                    "startTime": None,
                    "endTime": None,
                    "output": None
                },
                "document_generation": {
                    "status": "Pending",
                    "startTime": None,
                    "endTime": None,
                    "output": None
                }
            })
        }
        
        try:
            entity = self.table_client.create_entity(entity=initial_state)
            logger.info(f"Created workflow run {run_id} for project {project_id}")
            return self._format_entity(entity)
        except ResourceExistsError:
            logger.warning(f"Workflow run {run_id} already exists for project {project_id}")
            return self.get_workflow_state(project_id, run_id)
        except Exception as e:
            logger.error(f"Error creating workflow run {run_id}: {e}")
            raise
    
    def get_workflow_state(self, project_id: str, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Get workflow state by project_id and run_id.
        
        Args:
            project_id: The project ID (PartitionKey)
            run_id: The workflow run ID (RowKey)
            
        Returns:
            Dict containing the workflow state or None if not found
        """
        try:
            entity = self.table_client.get_entity(partition_key=project_id, row_key=run_id)
            return self._format_entity(entity)
        except ResourceNotFoundError:
            return None
        except Exception as e:
            logger.error(f"Error getting workflow state {run_id}: {e}")
            raise
    
    def update_step_status(self, project_id: str, run_id: str, step_name: str, 
                          status: str, output: Any = None, error_details: str = None) -> bool:
        """
        Update a specific step's status with idempotency protection.
        
        Args:
            project_id: The project ID
            run_id: The workflow run ID
            step_name: Name of the step to update
            status: New status (Pending, Processing, Completed, Failed)
            output: Optional output data from the step
            error_details: Error details if status is Failed
            
        Returns:
            bool: True if update was successful, False if step already in target state
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Get current state with ETag
                entity = self.table_client.get_entity(partition_key=project_id, row_key=run_id)
                steps = json.loads(entity.get("Steps", "{}"))
                
                # Check if step is already in the target state (idempotency check)
                current_step_status = steps.get(step_name, {}).get("status")
                if current_step_status == status:
                    logger.info(f"Step {step_name} already in status {status} for run {run_id}")
                    return False
                
                # Terminal state protection: Prevent overwriting Failed or Completed states
                if current_step_status in ["Failed", "Completed"] and status != current_step_status:
                    logger.warning(
                        f"Attempt to change terminal state for {run_id}/{step_name} "
                        f"from '{current_step_status}' to '{status}' was blocked"
                    )
                    return False
                
                # If step is already Processing or Completed, and we're trying to set it to Processing,
                # this is likely a duplicate/retry - skip it
                if status == "Processing" and current_step_status in ["Processing", "Completed"]:
                    logger.info(f"Step {step_name} already {current_step_status} for run {run_id}, skipping")
                    return False
                
                # Update the step
                if step_name not in steps:
                    steps[step_name] = {}
                
                steps[step_name]["status"] = status
                
                if status == "Processing":
                    steps[step_name]["startTime"] = datetime.now(timezone.utc).isoformat()
                elif status in ["Completed", "Failed"]:
                    steps[step_name]["endTime"] = datetime.now(timezone.utc).isoformat()
                    if output is not None:
                        steps[step_name]["output"] = output
                
                # Update entity
                entity["Steps"] = json.dumps(steps)
                entity["CurrentStep"] = step_name
                entity["LastUpdate"] = datetime.now(timezone.utc).isoformat()
                
                if status == "Failed":
                    entity["RunStatus"] = "Failed"
                    entity["ErrorDetails"] = error_details
                elif status == "Completed" and self._all_steps_completed(steps):
                    entity["RunStatus"] = "Completed"
                elif status == "Processing":
                    entity["RunStatus"] = "Processing"
                
                # Update with ETag for optimistic concurrency
                self.table_client.update_entity(
                    entity=entity,
                    mode=UpdateMode.REPLACE,
                    etag=entity.metadata["etag"],
                    match_condition={"if_match": entity.metadata["etag"]}
                )
                
                logger.info(f"Updated step {step_name} to {status} for run {run_id}")
                return True
                
            except ResourceModifiedError:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to update step {step_name} after {max_retries} attempts due to ETag conflicts")
                    raise
                logger.warning(f"ETag conflict updating step {step_name}, retrying (attempt {attempt + 1})")
                continue
            except Exception as e:
                logger.error(f"Error updating step {step_name} for run {run_id}: {e}")
                raise
        
        return False
    
    def mark_step_processing_with_idempotency(self, project_id: str, run_id: str, step_name: str) -> bool:
        """
        Mark a step as processing only if it's currently pending.
        This is the key idempotency check for queue-triggered functions.
        
        Args:
            project_id: The project ID
            run_id: The workflow run ID
            step_name: Name of the step
            
        Returns:
            bool: True if step was marked as processing, False if already processed/processing
        """
        return self.update_step_status(project_id, run_id, step_name, "Processing")
    
    def get_runs_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all workflow runs for a project."""
        try:
            entities = self.table_client.query_entities(
                query_filter=f"PartitionKey eq '{project_id}'"
            )
            return [self._format_entity(entity) for entity in entities]
        except Exception as e:
            logger.error(f"Error getting runs for project {project_id}: {e}")
            raise
    
    def get_failed_runs(self) -> List[Dict[str, Any]]:
        """Get all failed workflow runs for monitoring."""
        try:
            entities = self.table_client.query_entities(
                query_filter="RunStatus eq 'Failed'"
            )
            return [self._format_entity(entity) for entity in entities]
        except Exception as e:
            logger.error(f"Error getting failed runs: {e}")
            raise
    
    def _format_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Format table entity for API consumption."""
        # Parse JSON fields back to objects
        formatted = dict(entity)
        if "Steps" in formatted and isinstance(formatted["Steps"], str):
            formatted["Steps"] = json.loads(formatted["Steps"])
        if "Results" in formatted and isinstance(formatted["Results"], str):
            formatted["Results"] = json.loads(formatted["Results"])
        
        # Remove Azure Table Storage metadata
        formatted.pop("odata.metadata", None)
        formatted.pop("odata.etag", None)
        formatted.pop("Timestamp", None)
        
        return formatted
    
    def _all_steps_completed(self, steps: Dict[str, Any]) -> bool:
        """Check if all steps are completed."""
        for step_name, step_data in steps.items():
            if step_data.get("status") != "Completed":
                return False
        return True


# Singleton instance
_workflow_state_service = None


def get_workflow_state_service():
    """Get workflow state service singleton."""
    global _workflow_state_service
    if _workflow_state_service is None:
        # Use mock service if no connection string is provided
        if not settings.table_storage_connection_string:
            _workflow_state_service = MockWorkflowStateService()
        else:
            _workflow_state_service = WorkflowStateService()
    return _workflow_state_service