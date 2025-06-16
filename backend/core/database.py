"""
Database client management.
"""
import logging
from typing import Dict, Any, Optional, List
from azure.cosmos import CosmosClient, PartitionKey
from azure.storage.blob import BlobServiceClient

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseClient:
    """Cosmos DB client for project data management."""
    
    def __init__(self):
        self.connection_string = settings.cosmos_db_connection_string
        self.database_name = settings.cosmos_db_name
        self.container_name = settings.cosmos_db_container
        
        if not self.connection_string:
            raise ValueError("COSMOS_DB_CONNECTION_STRING is required")
        
        self.client = CosmosClient.from_connection_string(self.connection_string)
        self.database = self.client.create_database_if_not_exists(id=self.database_name)
        self.container = self.database.create_container_if_not_exists(
            id=self.container_name,
            partition_key=PartitionKey(path="/project_id"),
            offer_throughput=400
        )
    
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project."""
        try:
            response = self.container.create_item(body=project_data)
            logger.info(f"Created project: {project_data['project_id']}")
            return response
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        try:
            response = self.container.read_item(item=project_id, partition_key=project_id)
            return response
        except Exception as e:
            logger.error(f"Error retrieving project {project_id}: {e}")
            return None
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update project with new data."""
        try:
            existing_project = await self.get_project(project_id)
            if not existing_project:
                raise ValueError(f"Project {project_id} not found")
            
            # Deep merge updates
            existing_project = self._deep_merge(existing_project, updates)
            
            response = self.container.replace_item(
                item=project_id,
                body=existing_project
            )
            logger.info(f"Updated project: {project_id}")
            return response
        except Exception as e:
            logger.error(f"Error updating project {project_id}: {e}")
            raise
    
    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects."""
        try:
            query = "SELECT * FROM c ORDER BY c.created_date DESC"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Error retrieving projects: {e}")
            raise
    
    async def query_projects(self, query: str, parameters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Execute custom query on projects."""
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters or [],
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    def _deep_merge(self, base: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries."""
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result


class StorageClient:
    """Azure Blob Storage client for document management."""
    
    def __init__(self):
        self.connection_string = settings.blob_storage_connection_string
        self.container_name = settings.blob_storage_container
        
        if not self.connection_string:
            raise ValueError("BLOB_STORAGE_CONNECTION_STRING is required")
        
        self.client = BlobServiceClient.from_connection_string(self.connection_string)
        
        # Create container if it doesn't exist
        try:
            self.client.create_container(self.container_name)
        except Exception:
            pass  # Container might already exist
    
    async def upload_document(self, project_id: str, filename: str, content: bytes) -> str:
        """Upload document to blob storage."""
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
            logger.error(f"Error uploading document: {e}")
            raise
    
    def get_document_url(self, blob_name: str) -> str:
        """Get document URL."""
        blob_client = self.client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        return blob_client.url
    
    async def download_document(self, blob_name: str) -> bytes:
        """Download document content."""
        try:
            blob_client = self.client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            return blob_client.download_blob().readall()
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            raise


# Singleton instances
_db_client = None
_storage_client = None


def get_db_client() -> DatabaseClient:
    """Get database client singleton."""
    global _db_client
    if _db_client is None:
        _db_client = DatabaseClient()
    return _db_client


def get_storage_client() -> StorageClient:
    """Get storage client singleton."""
    global _storage_client
    if _storage_client is None:
        _storage_client = StorageClient()
    return _storage_client