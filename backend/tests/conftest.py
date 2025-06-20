import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock, PropertyMock

# It's good practice to place shared fixtures in a conftest.py file.
# These fixtures can be used by any test in the same directory or subdirectories.

@pytest.fixture
def mock_db_client(mocker):
    """Mocks the database client."""
    mock = MagicMock()
    mock.get_project = AsyncMock(return_value={"project_id": "test_project"})
    mock.update_project = AsyncMock(return_value=True)
    mock.create_project = AsyncMock(return_value={"project_id": "new_project"})
    mock.health_check = AsyncMock(return_value=True)
    return mock

@pytest.fixture
def mock_storage_client(mocker):
    """Mocks the storage client."""
    mock = MagicMock()
    mock.upload_document = AsyncMock(return_value="https://blob.storage/path/to/doc.pdf")
    mock.get_document_url = MagicMock(return_value="https://blob.storage/path/to/doc.pdf?sas_token=123")
    return mock

@pytest.fixture
def mock_project_service(mocker):
    """Mocks the ProjectService."""
    mock = MagicMock()
    mock.get_project = AsyncMock(return_value={"project_id": "proj_123", "project_name": "Test Project"})
    mock.check_project_access = AsyncMock(return_value=True)
    mock.create_quick_look_project = AsyncMock(return_value="proj_123")
    mock.get_feasibility_package = AsyncMock(return_value={"project_id": "proj_123", "status": "completed"})
    return mock

@pytest.fixture
def mock_helioscope_service(mocker):
    """Mocks the HelioscoperService."""
    mock = MagicMock()
    mock.process_complete_helioscope_data = AsyncMock(return_value={
        "project_id": "proj_123",
        "run_id": "run_abc",
        "status": "processing"
    })
    return mock

@pytest.fixture
def mock_workflow_state_service(mocker):
    """Mocks the WorkflowStateService."""
    mock = MagicMock()
    mock.get_workflow_state = MagicMock(return_value={
        "RunStatus": "Processing",
        "CurrentStep": "helioscope_fetch",
        "Steps": {"helioscope_fetch": {"status": "Processing"}}
    })
    mock.create_workflow_run = MagicMock()
    mock.update_step_status = MagicMock(return_value=True)
    mock.mark_step_processing_with_idempotency = MagicMock(return_value=True)
    return mock

@pytest.fixture(autouse=True)
def mock_services_in_routes(mocker, mock_project_service, mock_helioscope_service, mock_workflow_state_service, mock_db_client):
    """
    Automatically mocks service instantiations in the routes module for all tests.
    This prevents real service objects from being created during API tests.
    """
    mocker.patch('api.routes.project_service', new=mock_project_service)
    mocker.patch('api.routes.helioscope_service', new=mock_helioscope_service)
    mocker.patch('api.routes.workflow_state_service', new=mock_workflow_state_service)
    mocker.patch('api.routes.get_db_client', return_value=mock_db_client)
    # Also mock the check_project_access helper as it depends on a real service
    mocker.patch('api.routes.check_project_access', new=AsyncMock(return_value=True))

@pytest.fixture
def mock_azure_func_req():
    """Factory fixture to create mock Azure Function HttpRequest objects."""
    def _create_req(
        method='GET',
        params=None,
        headers=None,
        route_params=None,
        body=None
    ):
        req = MagicMock()
        req.method = method
        req.params = params or {}
        req.headers = headers or {}
        req.route_params = route_params or {}

        if body is not None:
            req.get_json = MagicMock(return_value=body)
            req.get_body = MagicMock(return_value=json.dumps(body).encode('utf-8'))
        else:
            req.get_json = MagicMock(side_effect=ValueError("No JSON body"))
            req.get_body = MagicMock(return_value=b'')
        
        return req
    return _create_req