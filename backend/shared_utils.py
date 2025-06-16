import os
import logging
from azure.cosmos import CosmosClient, PartitionKey
from azure.storage.blob import BlobServiceClient
import json
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CosmosDBClient:
    def __init__(self):
        self.connection_string = os.environ.get('COSMOS_DB_CONNECTION_STRING')
        self.database_name = os.environ.get('COSMOS_DB_NAME', 'climatize')
        self.container_name = os.environ.get('COSMOS_DB_CONTAINER', 'projects')
        
        if not self.connection_string:
            raise ValueError("COSMOS_DB_CONNECTION_STRING environment variable is required")
        
        self.client = CosmosClient.from_connection_string(self.connection_string)
        self.database = self.client.create_database_if_not_exists(id=self.database_name)
        self.container = self.database.create_container_if_not_exists(
            id=self.container_name,
            partition_key=PartitionKey(path="/project_id"),
            offer_throughput=400
        )
    
    def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project in Cosmos DB"""
        try:
            response = self.container.create_item(body=project_data)
            logger.info(f"Created project with ID: {project_data['project_id']}")
            return response
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a project by ID"""
        try:
            response = self.container.read_item(item=project_id, partition_key=project_id)
            return response
        except Exception as e:
            logger.error(f"Error retrieving project {project_id}: {str(e)}")
            return None
    
    def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update a project with new data"""
        try:
            # Get existing project
            existing_project = self.get_project(project_id)
            if not existing_project:
                raise ValueError(f"Project {project_id} not found")
            
            # Merge updates
            existing_project.update(updates)
            
            # Update in database
            response = self.container.replace_item(
                item=project_id, 
                body=existing_project
            )
            logger.info(f"Updated project {project_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {str(e)}")
            raise
    
    def get_all_projects(self) -> list:
        """Retrieve all projects"""
        try:
            query = "SELECT * FROM c"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Error retrieving all projects: {str(e)}")
            raise

class BlobStorageClient:
    def __init__(self):
        self.connection_string = os.environ.get('BLOB_STORAGE_CONNECTION_STRING')
        self.container_name = os.environ.get('BLOB_STORAGE_CONTAINER', 'project-documents')
        
        if not self.connection_string:
            raise ValueError("BLOB_STORAGE_CONNECTION_STRING environment variable is required")
        
        self.client = BlobServiceClient.from_connection_string(self.connection_string)
        
        # Create container if it doesn't exist
        try:
            self.client.create_container(self.container_name)
        except Exception:
            pass  # Container might already exist
    
    def upload_document(self, project_id: str, filename: str, content: str) -> str:
        """Upload a document to blob storage"""
        try:
            blob_name = f"{project_id}/{filename}"
            blob_client = self.client.get_blob_client(
                container=self.container_name, 
                blob=blob_name
            )
            
            blob_client.upload_blob(content, overwrite=True)
            logger.info(f"Uploaded document: {blob_name}")
            return blob_name
        except Exception as e:
            logger.error(f"Error uploading document: {str(e)}")
            raise
    
    def get_document_url(self, blob_name: str) -> str:
        """Get the URL for a document"""
        blob_client = self.client.get_blob_client(
            container=self.container_name, 
            blob=blob_name
        )
        return blob_client.url

def invoke_function(function_name: str, project_id: str):
    """Helper function to invoke other Azure Functions"""
    # In a real Azure Functions environment, this would use the Azure Functions runtime
    # For now, we'll use a simple logging approach
    logger.info(f"Invoking function {function_name} with project_id: {project_id}")
    # TODO: Implement actual function invocation for production