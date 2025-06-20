"""
Database client management.
"""
import logging
from typing import Dict, Any, Optional, List
from azure.cosmos import CosmosClient, PartitionKey
from azure.storage.blob import BlobServiceClient

from core.config import settings

logger = logging.getLogger(__name__)


class MockDatabaseClient:
    """Mock database client for development."""
    
    def __init__(self):
        self._projects = {}
        logger.info("Using mock database client for development")
    
    async def create_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new project (mock)."""
        project_id = project_data.get('project_id')
        self._projects[project_id] = project_data
        logger.info(f"Mock: Created project {project_id}")
        return project_data
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID (mock)."""
        return self._projects.get(project_id)
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update project (mock)."""
        if project_id in self._projects:
            self._projects[project_id].update(updates)
            return self._projects[project_id]
        raise ValueError(f"Project {project_id} not found")
    
    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects (mock)."""
        return list(self._projects.values())
    
    async def query_projects(self, query: str, parameters: Optional[List[Dict[str, Any]]] = None) -> List[Dict[str, Any]]:
        """Execute custom query (mock)."""
        return list(self._projects.values())


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


class MockStorageClient:
    """Mock storage client for development."""
    
    def __init__(self):
        self._documents = {}
        logger.info("Using mock storage client for development")
    
    async def upload_document(self, project_id: str, filename: str, content: bytes) -> str:
        """Upload document (mock)."""
        blob_name = f"{project_id}/{filename}"
        self._documents[blob_name] = content
        logger.info(f"Mock: Uploaded document {blob_name}")
        return blob_name
    
    def get_document_url(self, blob_name: str) -> str:
        """Get document URL (mock)."""
        return f"https://mock-storage.com/{blob_name}"
    
    async def download_document(self, blob_name: str) -> bytes:
        """Download document (mock)."""
        return self._documents.get(blob_name, b"Mock document content")


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


def get_db_client():
    """Get database client singleton."""
    global _db_client
    if _db_client is None:
        # Use mock client if no connection string is provided
        if not settings.cosmos_db_connection_string:
            _db_client = MockDatabaseClient()
        else:
            _db_client = DatabaseClient()
    return _db_client


def get_storage_client():
    """Get storage client singleton."""
    global _storage_client
    if _storage_client is None:
        # Use mock client if no connection string is provided
        if not settings.blob_storage_connection_string:
            _storage_client = MockStorageClient()
        else:
            _storage_client = StorageClient()
    return _storage_client