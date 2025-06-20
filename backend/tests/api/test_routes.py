import pytest
import json
from unittest.mock import AsyncMock, MagicMock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from api import routes

# Mark all tests in this file as async
pytestmark = pytest.mark.asyncio

class TestApiRoutes:
    """Tests for the API routes in routes.py"""

    async def test_quick_look_feasibility_handler_success(self, mock_azure_func_req, mock_project_service):
        """
        Tests the happy path for the quick look feasibility endpoint.
        - Hypothesis: A valid request should trigger the service and return a 202 Accepted response.
        """
        # Arrange
        req_body = {
            "address": "123 Main St, San Francisco, CA",
            "system_size": 10
        }
        req = mock_azure_func_req(method='POST', body=req_body)
        
        # Act
        response = await routes.quick_look_feasibility_handler(req)

        # Assert
        mock_project_service.create_quick_look_project.assert_called_once_with(req_body)
        assert response.status_code == 202
        response_body = json.loads(response.get_body())
        assert response_body['status'] == 'Processing started'
        assert response_body['project_id'] == 'proj_123'

    @pytest.mark.parametrize("body, expected_error_msg", [
        (None, "Request body is required"),
        ({}, "Address is required"),
        ({"system_size": 10}, "Address is required"),
    ])
    async def test_quick_look_feasibility_handler_bad_request(self, mock_azure_func_req, body, expected_error_msg):
        """
        Tests validation for the quick look feasibility endpoint.
        - Hypothesis: Invalid or missing data in the request body should result in a 400 Bad Request.
        """
        # Arrange
        req = mock_azure_func_req(method='POST', body=body)

        # Act
        response = await routes.quick_look_feasibility_handler(req)

        # Assert
        assert response.status_code == 400
        response_body = json.loads(response.get_body())
        assert response_body['error'] == expected_error_msg

    async def test_helioscope_project_intake_handler_success(self, mock_azure_func_req, mock_helioscope_service):
        """
        Tests the happy path for the Helioscope project intake endpoint.
        - Hypothesis: A valid request should trigger the service and return a 202 Accepted response.
        """
        # Arrange
        req_body = {
            "helioscope_project_id": "hs_proj_123",
            "helioscope_credentials": {"api_token": "fake_token"}
        }
        req = mock_azure_func_req(method='POST', body=req_body)
        
        # Act
        response = await routes.helioscope_project_intake_handler(req)

        # Assert
        mock_helioscope_service.process_complete_helioscope_data.assert_called_once_with(
            project_id=None,
            helioscope_project_id="hs_proj_123",
            helioscope_credentials={"api_token": "fake_token"}
        )
        assert response.status_code == 202
        response_body = json.loads(response.get_body())
        assert response_body['status'] == 'processing'
        assert response_body['project_id'] == 'proj_123'
        assert 'status_url' in response_body

    @pytest.mark.parametrize("body, expected_error_msg", [
        (None, "Request body is required"),
        ({}, "helioscope_project_id is required"),
        ({"helioscope_project_id": "123"}, "helioscope_credentials with api_token are required"),
        ({"helioscope_project_id": "123", "helioscope_credentials": {}}, "helioscope_credentials with api_token are required"),
    ])
    async def test_helioscope_project_intake_handler_bad_request(self, mock_azure_func_req, body, expected_error_msg):
        """
        Tests validation for the Helioscope project intake endpoint.
        - Hypothesis: Invalid or missing data in the request body should result in a 400 Bad Request.
        """
        # Arrange
        req = mock_azure_func_req(method='POST', body=body)

        # Act
        response = await routes.helioscope_project_intake_handler(req)

        # Assert
        assert response.status_code == 400
        response_body = json.loads(response.get_body())
        assert response_body['error'] == expected_error_msg

    async def test_get_workflow_status_success(self, mock_azure_func_req, mock_workflow_state_service):
        """
        Tests the happy path for retrieving workflow status.
        - Hypothesis: A valid request for an existing, accessible run returns the status correctly.
        """
        # Arrange
        route_params = {"project_id": "proj_123", "run_id": "run_abc"}
        headers = {"X-User-ID": "user_123"}
        req = mock_azure_func_req(route_params=route_params, headers=headers)
        
        # Mock the service to return a "Processing" state
        mock_workflow_state_service.get_workflow_state.return_value = {
            "RunStatus": "Processing", "CurrentStep": "some_step", "LastUpdate": "2024-01-01T12:00:00Z",
            "Steps": {}, "ErrorDetails": None, "Results": {}
        }

        # Act
        response = await routes.get_workflow_status(req)

        # Assert
        routes.check_project_access.assert_called_once_with("user_123", "proj_123")
        mock_workflow_state_service.get_workflow_state.assert_called_once_with("proj_123", "run_abc")
        assert response.status_code == 202 # 202 for "Processing"
        response_body = json.loads(response.get_body())
        assert response_body['project_id'] == "proj_123"
        assert response_body['run_id'] == "run_abc"
        assert response_body['status'] == "Processing"

    async def test_get_workflow_status_no_access(self, mock_azure_func_req):
        """
        Tests that a user without access gets a 404 Not Found.
        - Hypothesis: To prevent information leakage, unauthorized access should return 404, not 403.
        """
        # Arrange
        routes.check_project_access.return_value = False # Mock the access check to fail
        route_params = {"project_id": "proj_123", "run_id": "run_abc"}
        headers = {"X-User-ID": "user_456"}
        req = mock_azure_func_req(route_params=route_params, headers=headers)

        # Act
        response = await routes.get_workflow_status(req)

        # Assert
        assert response.status_code == 404
        response_body = json.loads(response.get_body())
        assert response_body['error'] == "Workflow run not found"

    async def test_get_workflow_status_run_not_found(self, mock_azure_func_req, mock_workflow_state_service):
        """
        Tests that a non-existent run returns a 404 Not Found.
        """
        # Arrange
        mock_workflow_state_service.get_workflow_state.return_value = None
        route_params = {"project_id": "proj_123", "run_id": "run_xyz"}
        req = mock_azure_func_req(route_params=route_params)

        # Act
        response = await routes.get_workflow_status(req)

        # Assert
        assert response.status_code == 404
        response_body = json.loads(response.get_body())
        assert response_body['error'] == "Workflow run not found"

    async def test_get_feasibility_package_success_completed(self, mock_azure_func_req, mock_project_service):
        """
        Tests retrieving a completed feasibility package.
        """
        # Arrange
        route_params = {"project_id": "proj_123"}
        req = mock_azure_func_req(route_params=route_params)
        
        mock_project_service.get_feasibility_package.return_value = {
            "project_id": "proj_123",
            "status": "completed",
            "feasibility_score": 85,
            "cost_estimate": 25000
        }

        # Act
        response = await routes.get_feasibility_package(req)

        # Assert
        assert response.status_code == 200
        response_body = json.loads(response.get_body())
        assert response_body['project_id'] == "proj_123"
        assert response_body['status'] == "completed"
        assert response_body['feasibility_score'] == 85

    async def test_get_feasibility_package_still_processing(self, mock_azure_func_req, mock_project_service):
        """
        Tests retrieving a feasibility package that's still processing.
        """
        # Arrange
        route_params = {"project_id": "proj_123"}
        req = mock_azure_func_req(route_params=route_params)
        
        mock_project_service.get_feasibility_package.return_value = {
            "project_id": "proj_123",
            "status": "processing",
            "progress_percentage": 45,
            "current_stage": "Helioscope Analysis"
        }

        # Act
        response = await routes.get_feasibility_package(req)

        # Assert
        assert response.status_code == 202
        response_body = json.loads(response.get_body())
        assert response_body['project_id'] == "proj_123"
        assert response_body['status'] == "In progress"
        assert response_body['progress_percentage'] == 45

    async def test_get_feasibility_package_not_found(self, mock_azure_func_req, mock_project_service):
        """
        Tests retrieving a non-existent feasibility package.
        """
        # Arrange
        route_params = {"project_id": "proj_999"}
        req = mock_azure_func_req(route_params=route_params)
        
        mock_project_service.get_feasibility_package.return_value = None

        # Act
        response = await routes.get_feasibility_package(req)

        # Assert
        assert response.status_code == 404
        response_body = json.loads(response.get_body())
        assert response_body['error'] == "Project not found"

    async def test_health_check_healthy(self, mock_azure_func_req, mock_db_client):
        """Tests the health check endpoint when the database is healthy."""
        # Arrange
        mock_db_client.health_check.return_value = True
        req = mock_azure_func_req()

        # Act
        response = await routes.health_check(req)

        # Assert
        assert response.status_code == 200
        body = json.loads(response.get_body())
        assert body['status'] == 'healthy'
        assert body['database'] == 'connected'

    async def test_health_check_unhealthy(self, mock_azure_func_req, mock_db_client):
        """Tests the health check endpoint when the database is unhealthy."""
        # Arrange
        mock_db_client.health_check.return_value = False
        req = mock_azure_func_req()

        # Act
        response = await routes.health_check(req)

        # Assert
        assert response.status_code == 503
        body = json.loads(response.get_body())
        assert body['status'] == 'unhealthy'
        assert body['database'] == 'disconnected'

    async def test_get_all_projects_success(self, mock_azure_func_req, mock_project_service):
        """
        Tests retrieving all projects for a user.
        """
        # Arrange
        headers = {"X-User-ID": "user_123"}
        req = mock_azure_func_req(headers=headers)
        
        mock_projects = [
            {"project_id": "proj_1", "name": "Solar Project 1"},
            {"project_id": "proj_2", "name": "Solar Project 2"}
        ]
        mock_project_service.get_all_projects_for_user = AsyncMock(return_value=mock_projects)

        # Act
        response = await routes.get_all_projects(req)

        # Assert
        assert response.status_code == 200
        response_body = json.loads(response.get_body())
        assert len(response_body) == 2
        assert response_body[0]['project_id'] == "proj_1"

    async def test_get_user_id_from_headers_with_x_user_id(self):
        """
        Tests extracting user ID from X-User-ID header.
        """
        # Arrange
        req = MagicMock()
        req.headers = {"X-User-ID": "test_user_123"}

        # Act
        user_id = routes.get_user_id_from_headers(req)

        # Assert
        assert user_id == "test_user_123"

    async def test_get_user_id_from_headers_with_bearer_token(self):
        """
        Tests extracting user ID from Authorization header.
        """
        # Arrange
        req = MagicMock()
        req.headers = {"Authorization": "Bearer some_jwt_token"}

        # Act
        user_id = routes.get_user_id_from_headers(req)

        # Assert
        assert user_id == "default_user"  # Simplified implementation

    async def test_get_user_id_from_headers_anonymous(self):
        """
        Tests fallback to anonymous when no auth headers present.
        """
        # Arrange
        req = MagicMock()
        req.headers = {}

        # Act
        user_id = routes.get_user_id_from_headers(req)

        # Assert
        assert user_id == "anonymous"