import pytest
import json
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone
from azure.core.exceptions import ResourceExistsError, ResourceModifiedError, ResourceNotFoundError

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the specific module directly to avoid issues with services package imports
import importlib.util
spec = importlib.util.spec_from_file_location(
    "workflow_state_service", 
    os.path.join(os.path.dirname(__file__), '..', '..', 'services', 'workflow_state_service.py')
)
workflow_state_service_module = importlib.util.module_from_spec(spec)
sys.modules["workflow_state_service"] = workflow_state_service_module
spec.loader.exec_module(workflow_state_service_module)

WorkflowStateService = workflow_state_service_module.WorkflowStateService

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

@pytest.fixture
def mock_table_service_client():
    """Mocks the Azure TableServiceClient and its nested TableClient."""
    mock_table_client = MagicMock()
    mock_service_client = MagicMock()
    mock_service_client.get_table_client.return_value = mock_table_client
    return mock_service_client, mock_table_client

@pytest.fixture
def workflow_service(mock_table_service_client):
    """Provides a WorkflowStateService instance with mocked dependencies."""
    mock_service_client, _ = mock_table_service_client
    with patch('workflow_state_service.TableServiceClient') as mock_constructor:
        mock_constructor.from_connection_string.return_value = mock_service_client
        # Patch settings to avoid ValueError
        with patch('workflow_state_service.settings.table_storage_connection_string', 'mock_connection_string'):
            service = WorkflowStateService()
            # Replace the client with our mock for inspection
            service.table_client = mock_table_service_client[1]
            yield service

class TestWorkflowStateService:
    """Tests for the WorkflowStateService."""

    def test_create_workflow_run_success(self, workflow_service, mock_table_service_client):
        """
        Tests successful creation of a new workflow run.
        """
        # Arrange
        _, mock_table_client = mock_table_service_client
        project_id = "proj_123"
        run_id = "run_abc"
        
        mock_table_client.create_entity.return_value = {
            "PartitionKey": project_id,
            "RowKey": run_id,
            "RunStatus": "Pending"
        }
        
        # Act
        result = workflow_service.create_workflow_run(project_id, run_id)

        # Assert
        mock_table_client.create_entity.assert_called_once()
        call_args = mock_table_client.create_entity.call_args[1]['entity']
        assert call_args['PartitionKey'] == project_id
        assert call_args['RowKey'] == run_id
        assert call_args['RunStatus'] == "Pending"
        assert json.loads(call_args['Steps'])['helioscope_fetch']['status'] == "Pending"

    def test_create_workflow_run_already_exists(self, workflow_service, mock_table_service_client):
        """
        Tests that if a workflow run already exists, it is fetched instead of recreated.
        """
        # Arrange
        _, mock_table_client = mock_table_service_client
        mock_table_client.create_entity.side_effect = ResourceExistsError("Entity already exists")
        mock_table_client.get_entity.return_value = {
            "PartitionKey": "proj_123", 
            "RowKey": "run_abc", 
            "RunStatus": "Existing",
            "Steps": "{}",
            "Results": "{}"
        }
        
        # Act
        result = workflow_service.create_workflow_run("proj_123", "run_abc")

        # Assert
        assert result['RunStatus'] == "Existing"

    def test_get_workflow_state_not_found(self, workflow_service, mock_table_service_client):
        """
        Tests that get_workflow_state returns None when the entity is not found.
        """
        # Arrange
        _, mock_table_client = mock_table_service_client
        mock_table_client.get_entity.side_effect = ResourceNotFoundError("Not found")

        # Act
        result = workflow_service.get_workflow_state("proj_123", "run_abc")

        # Assert
        assert result is None

    @pytest.mark.parametrize("status_to_set, current_status, expected_call", [
        ("Processing", "Pending", True),
        ("Processing", "Processing", False), # Idempotency check
        ("Processing", "Completed", False), # Terminal state check
        ("Completed", "Processing", True),
        ("Failed", "Completed", False), # Terminal state check
    ])
    def test_update_step_status_idempotency_and_terminal_states(
        self, workflow_service, mock_table_service_client, status_to_set, current_status, expected_call
    ):
        """
        Tests the idempotency and terminal state protection in update_step_status.
        - Hypothesis: The service should not update a step if it's already in the target state
          or if it's in a terminal state (Completed, Failed).
        """
        # Arrange
        _, mock_table_client = mock_table_service_client
        project_id = "proj_123"
        run_id = "run_abc"
        step_name = "test_step"
        
        mock_entity = {
            "PartitionKey": project_id,
            "RowKey": run_id,
            "Steps": json.dumps({step_name: {"status": current_status}}),
            "metadata": {"etag": "W/\"datetime'2024-01-01T00%3A00%3A00Z'\""}
        }
        mock_table_client.get_entity.return_value = mock_entity

        # Act
        result = workflow_service.update_step_status(project_id, run_id, step_name, status_to_set)

        # Assert
        if expected_call:
            mock_table_client.update_entity.assert_called_once()
            assert result is True
        else:
            mock_table_client.update_entity.assert_not_called()
            assert result is False

    def test_update_step_status_handles_etag_conflict_with_retry(self, workflow_service, mock_table_service_client):
        """
        Tests that update_step_status retries on a ResourceModifiedError (ETag conflict)
        and eventually succeeds.
        - Hypothesis: Concurrency conflicts are handled gracefully by refetching and retrying the update.
        """
        # Arrange
        _, mock_table_client = mock_table_service_client
        project_id = "proj_123"
        run_id = "run_abc"
        step_name = "test_step"

        # First call to get_entity
        initial_entity = {
            "PartitionKey": project_id, "RowKey": run_id,
            "Steps": json.dumps({step_name: {"status": "Pending"}}),
            "metadata": {"etag": "etag_1"}
        }
        # Second call to get_entity after the conflict
        updated_entity = {
            "PartitionKey": project_id, "RowKey": run_id,
            "Steps": json.dumps({step_name: {"status": "Pending"}, "other_step": {"status": "Completed"}}),
            "metadata": {"etag": "etag_2"}
        }
        mock_table_client.get_entity.side_effect = [initial_entity, updated_entity]

        # First call to update_entity fails, second succeeds
        mock_table_client.update_entity.side_effect = [
            ResourceModifiedError("ETag conflict"),
            MagicMock() # Success
        ]

        # Act
        result = workflow_service.update_step_status(project_id, run_id, step_name, "Processing")

        # Assert
        assert result is True
        assert mock_table_client.get_entity.call_count == 2
        assert mock_table_client.update_entity.call_count == 2
        
        # Check that the final update was attempted with the new ETag
        final_call_args = mock_table_client.update_entity.call_args_list[1]
        assert final_call_args[1]['etag'] == "etag_2"
        
        # Check that the final update includes the data from the conflicting write
        final_entity_payload = final_call_args[1]['entity']
        final_steps = json.loads(final_entity_payload['Steps'])
        assert final_steps['test_step']['status'] == 'Processing'
        assert final_steps['other_step']['status'] == 'Completed'

    def test_mark_step_processing_with_idempotency(self, workflow_service, mock_table_service_client):
        """
        Tests the mark_step_processing_with_idempotency convenience method.
        """
        # Arrange
        _, mock_table_client = mock_table_service_client
        project_id = "proj_123"
        run_id = "run_abc"
        step_name = "test_step"
        
        mock_entity = {
            "PartitionKey": project_id,
            "RowKey": run_id,
            "Steps": json.dumps({step_name: {"status": "Pending"}}),
            "metadata": {"etag": "etag_1"}
        }
        mock_table_client.get_entity.return_value = mock_entity

        # Act
        result = workflow_service.mark_step_processing_with_idempotency(project_id, run_id, step_name)

        # Assert
        assert result is True
        mock_table_client.update_entity.assert_called_once()

    def test_get_runs_by_project(self, workflow_service, mock_table_service_client):
        """
        Tests retrieving all workflow runs for a specific project.
        """
        # Arrange
        _, mock_table_client = mock_table_service_client
        project_id = "proj_123"
        
        mock_entities = [
            {"PartitionKey": project_id, "RowKey": "run_1", "RunStatus": "Completed", "Steps": "{}", "Results": "{}"},
            {"PartitionKey": project_id, "RowKey": "run_2", "RunStatus": "Processing", "Steps": "{}", "Results": "{}"}
        ]
        mock_table_client.query_entities.return_value = mock_entities

        # Act
        result = workflow_service.get_runs_by_project(project_id)

        # Assert
        assert len(result) == 2
        assert result[0]['RowKey'] == "run_1"
        assert result[1]['RowKey'] == "run_2"
        mock_table_client.query_entities.assert_called_once_with(
            query_filter=f"PartitionKey eq '{project_id}'"
        )

    def test_format_entity_removes_metadata(self, workflow_service):
        """
        Tests that _format_entity properly removes Azure Table Storage metadata.
        """
        # Arrange
        entity = {
            "PartitionKey": "proj_123",
            "RowKey": "run_abc",
            "Steps": '{"step1": {"status": "Completed"}}',
            "Results": '{"output": "test"}',
            "odata.metadata": "metadata_url",
            "odata.etag": "etag_value",
            "Timestamp": "2024-01-01T00:00:00Z"
        }

        # Act
        result = workflow_service._format_entity(entity)

        # Assert
        assert "odata.metadata" not in result
        assert "odata.etag" not in result
        assert "Timestamp" not in result
        assert isinstance(result["Steps"], dict)
        assert isinstance(result["Results"], dict)
        assert result["Steps"]["step1"]["status"] == "Completed"