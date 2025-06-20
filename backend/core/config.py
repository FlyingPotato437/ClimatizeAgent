"""
Application configuration management.
"""
import os
from typing import Optional


class Settings:
    """Application settings with environment variable support."""
    
    def __init__(self):
        # API Keys
        self.openai_api_key: Optional[str] = os.getenv('OPENAI_API_KEY')
        self.azure_openai_endpoint: Optional[str] = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.azure_openai_api_version: str = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        self.azure_openai_deployment: str = os.getenv('AZURE_OPENAI_DEPLOYMENT', 'gpt-4o')
        self.shovels_api_key: Optional[str] = os.getenv('SHOVELS_API_KEY')
        self.helioscope_api_key: Optional[str] = os.getenv('HELIOSCOPE_API_KEY')
        
        # Database
        self.cosmos_db_connection_string: Optional[str] = os.getenv('COSMOS_DB_CONNECTION_STRING')
        self.cosmos_db_name: str = os.getenv('COSMOS_DB_NAME', 'climatize')
        self.cosmos_db_container: str = os.getenv('COSMOS_DB_CONTAINER', 'projects')
        
        # Storage
        self.blob_storage_connection_string: Optional[str] = os.getenv('BLOB_STORAGE_CONNECTION_STRING')
        self.blob_storage_container: str = os.getenv('BLOB_STORAGE_CONTAINER', 'project-documents')
        self.table_storage_connection_string: Optional[str] = os.getenv('TABLE_STORAGE_CONNECTION_STRING')
        
        # External APIs
        self.helioscope_base_url: str = os.getenv('HELIOSCOPE_BASE_URL', 'https://api.helioscope.com/v1')
        self.shovels_base_url: str = os.getenv('SHOVELS_BASE_URL', 'https://api.shovels.ai')
        
        # Application
        self.environment: str = os.getenv('ENVIRONMENT', 'development')
        self.log_level: str = os.getenv('LOG_LEVEL', 'INFO')
        self.use_mock_helioscope: bool = os.getenv('USE_MOCK_HELIOSCOPE', 'true').lower() == 'true'


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


# Global settings instance
settings = get_settings()