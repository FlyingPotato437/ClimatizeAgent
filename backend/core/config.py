"""
Application configuration management.
"""
import os
from typing import Optional
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # API Keys
    openai_api_key: Optional[str] = None
    shovels_api_key: Optional[str] = None
    helioscope_api_key: Optional[str] = None
    
    # Database
    cosmos_db_connection_string: Optional[str] = None
    cosmos_db_name: str = "climatize"
    cosmos_db_container: str = "projects"
    
    # Storage
    blob_storage_connection_string: Optional[str] = None
    blob_storage_container: str = "project-documents"
    
    # External APIs
    helioscope_base_url: str = "https://api.helioscope.com/v1"
    shovels_base_url: str = "https://api.shovels.ai"
    
    # Application
    environment: str = "development"
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        # Map environment variables
        fields = {
            'openai_api_key': 'OPENAI_API_KEY',
            'shovels_api_key': 'SHOVELS_API_KEY',
            'helioscope_api_key': 'HELIOSCOPE_API_KEY',
            'cosmos_db_connection_string': 'COSMOS_DB_CONNECTION_STRING',
            'blob_storage_connection_string': 'BLOB_STORAGE_CONNECTION_STRING',
        }


def get_settings() -> Settings:
    """Get application settings singleton."""
    return Settings()


# Global settings instance
settings = get_settings()