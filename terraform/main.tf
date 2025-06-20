# Climatize AI Agent Infrastructure - Azure Terraform Configuration
# Implements Phase 4: Infrastructure as Code for enterprise deployment

terraform {
  required_version = ">= 1.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~>3.1"
    }
  }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {
    key_vault {
      purge_soft_delete_on_destroy    = true
      recover_soft_deleted_key_vaults = true
    }
    cognitive_account {
      purge_soft_delete_on_destroy = true
    }
  }
}

# Local variables
locals {
  project_name = "climatize-ai-agent"
  environment  = var.environment
  location     = var.location
  
  common_tags = {
    Project     = "Climatize AI Agent"
    Environment = var.environment
    Framework   = "Ultrathink"
    ManagedBy   = "Terraform"
    Purpose     = "Agentic AI MVP & Issuer Portal"
  }
}

# Random suffix for unique resource names
resource "random_id" "main" {
  byte_length = 4
}

# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "rg-${local.project_name}-${local.environment}-${random_id.main.hex}"
  location = local.location
  tags     = local.common_tags
}

# Storage Account for Azure Functions and general storage
resource "azurerm_storage_account" "main" {
  name                     = "st${replace(local.project_name, "-", "")}${local.environment}${random_id.main.hex}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = var.environment == "prod" ? "GRS" : "LRS"
  
  blob_properties {
    cors_rule {
      allowed_headers    = ["*"]
      allowed_methods    = ["DELETE", "GET", "HEAD", "MERGE", "POST", "OPTIONS", "PUT"]
      allowed_origins    = ["*"]
      exposed_headers    = ["*"]
      max_age_in_seconds = 200
    }
  }

  tags = local.common_tags
}

# Application Service Plan for Functions
resource "azurerm_service_plan" "main" {
  name                = "asp-${local.project_name}-${local.environment}-${random_id.main.hex}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = var.environment == "prod" ? "P1v3" : "B1"
  
  tags = local.common_tags
}

# Azure Functions App
resource "azurerm_linux_function_app" "main" {
  name                = "func-${local.project_name}-${local.environment}-${random_id.main.hex}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  storage_account_name       = azurerm_storage_account.main.name
  storage_account_access_key = azurerm_storage_account.main.primary_access_key
  service_plan_id            = azurerm_service_plan.main.id

  site_config {
    application_stack {
      python_version = "3.11"
    }
    
    cors {
      allowed_origins = var.environment == "prod" ? [
        "https://${azurerm_static_site.main.default_host_name}"
      ] : ["*"]
    }
  }

  app_settings = {
    "FUNCTIONS_WORKER_RUNTIME"               = "python"
    "WEBSITE_RUN_FROM_PACKAGE"              = "1"
    "SCM_DO_BUILD_DURING_DEPLOYMENT"        = "true"
    "ENABLE_ORYX_BUILD"                     = "true"
    
    # Application Configuration
    "USE_MOCK_HELIOSCOPE"                   = var.use_mock_helioscope
    "LOG_LEVEL"                             = var.log_level
    
    # AI Configuration
    "OPENAI_API_KEY"                        = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=openai-api-key)"
    
    # Database Configuration
    "AZURE_COSMOSDB_CONNECTION_STRING"      = "@Microsoft.KeyVault(VaultName=${azurerm_key_vault.main.name};SecretName=cosmosdb-connection-string)"
    "AZURE_STORAGE_CONNECTION_STRING"       = azurerm_storage_account.main.primary_connection_string
    
    # Redis Configuration
    "REDIS_CONNECTION_STRING"               = azurerm_redis_cache.main.primary_connection_string
    
    # Service Bus Configuration  
    "AZURE_SERVICEBUS_CONNECTION_STRING"    = azurerm_servicebus_namespace.main.default_primary_connection_string
  }

  identity {
    type = "SystemAssigned"
  }

  tags = local.common_tags
}

# Static Web App for Next.js Frontend
resource "azurerm_static_site" "main" {
  name                = "swa-${local.project_name}-${local.environment}-${random_id.main.hex}"
  resource_group_name = azurerm_resource_group.main.name
  location            = "East US2"  # Static Web Apps have limited regions
  sku_tier            = var.environment == "prod" ? "Standard" : "Free"
  sku_size            = var.environment == "prod" ? "Standard" : "Free"

  tags = local.common_tags
}

# Cosmos DB Account
resource "azurerm_cosmosdb_account" "main" {
  name                = "cosmos-${local.project_name}-${local.environment}-${random_id.main.hex}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  offer_type          = "Standard"
  kind                = "GlobalDocumentDB"

  consistency_policy {
    consistency_level       = "BoundedStaleness"
    max_interval_in_seconds = 86400
    max_staleness_prefix    = 1000000
  }

  geo_location {
    location          = azurerm_resource_group.main.location
    failover_priority = 0
  }

  backup {
    type                = "Periodic"
    interval_in_minutes = 240
    retention_in_hours  = 24
  }

  tags = local.common_tags
}

# Cosmos DB Database
resource "azurerm_cosmosdb_sql_database" "main" {
  name                = "climatize-db"
  resource_group_name = azurerm_resource_group.main.name
  account_name        = azurerm_cosmosdb_account.main.name
}

# Cosmos DB Container for Projects
resource "azurerm_cosmosdb_sql_container" "projects" {
  name                  = "projects"
  resource_group_name   = azurerm_resource_group.main.name
  account_name          = azurerm_cosmosdb_account.main.name
  database_name         = azurerm_cosmosdb_sql_database.main.name
  partition_key_path    = "/project_id"
  partition_key_version = 1
  throughput            = var.environment == "prod" ? 1000 : 400

  indexing_policy {
    indexing_mode = "consistent"

    included_path {
      path = "/*"
    }
  }
}

# Redis Cache for agent coordination
resource "azurerm_redis_cache" "main" {
  name                = "redis-${local.project_name}-${local.environment}-${random_id.main.hex}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  capacity            = var.environment == "prod" ? 2 : 0
  family              = var.environment == "prod" ? "C" : "C"
  sku_name            = var.environment == "prod" ? "Standard" : "Basic"
  enable_non_ssl_port = false
  minimum_tls_version = "1.2"

  redis_configuration {
    enable_authentication           = true
    maxmemory_reserved             = var.environment == "prod" ? 50 : 10
    maxmemory_delta                = var.environment == "prod" ? 50 : 10
    maxmemory_policy               = "allkeys-lru"
  }

  tags = local.common_tags
}

# Service Bus Namespace for message queuing
resource "azurerm_servicebus_namespace" "main" {
  name                = "sb-${local.project_name}-${local.environment}-${random_id.main.hex}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = var.environment == "prod" ? "Standard" : "Basic"

  tags = local.common_tags
}

# Service Bus Queue for agent tasks
resource "azurerm_servicebus_queue" "agent_tasks" {
  name         = "agent-tasks"
  namespace_id = azurerm_servicebus_namespace.main.id

  enable_partitioning = var.environment == "prod"
  max_size_in_megabytes = var.environment == "prod" ? 5120 : 1024
}

# Application Insights
resource "azurerm_application_insights" "main" {
  name                = "appi-${local.project_name}-${local.environment}-${random_id.main.hex}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"
  retention_in_days   = var.environment == "prod" ? 90 : 30

  tags = local.common_tags
}

# Key Vault for secrets
resource "azurerm_key_vault" "main" {
  name                        = "kv-${local.project_name}-${local.environment}-${random_id.main.hex}"
  location                    = azurerm_resource_group.main.location
  resource_group_name         = azurerm_resource_group.main.name
  enabled_for_disk_encryption = true
  tenant_id                   = data.azurerm_client_config.current.tenant_id
  soft_delete_retention_days  = 7
  purge_protection_enabled    = false
  sku_name                    = "standard"

  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    key_permissions = [
      "Get", "List", "Create", "Delete", "Update", "Recover", "Backup", "Restore"
    ]

    secret_permissions = [
      "Get", "List", "Set", "Delete", "Recover", "Backup", "Restore"
    ]

    storage_permissions = [
      "Get", "List", "Delete", "Set", "Update", "RegenerateKey", "Recover", "Backup", "Restore"
    ]
  }

  # Function App access policy
  access_policy {
    tenant_id = data.azurerm_client_config.current.tenant_id
    object_id = azurerm_linux_function_app.main.identity[0].principal_id

    secret_permissions = [
      "Get", "List"
    ]
  }

  tags = local.common_tags
}

# Data source for current client configuration
data "azurerm_client_config" "current" {}

# Key Vault Secrets (will be populated manually or via CI/CD)
resource "azurerm_key_vault_secret" "cosmosdb_connection_string" {
  name         = "cosmosdb-connection-string"
  value        = azurerm_cosmosdb_account.main.primary_sql_connection_string
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_key_vault.main]

  tags = local.common_tags
}

# Placeholder for OpenAI API Key (set manually)
resource "azurerm_key_vault_secret" "openai_api_key" {
  name         = "openai-api-key"
  value        = var.openai_api_key != "" ? var.openai_api_key : "PLACEHOLDER_SET_MANUALLY"
  key_vault_id = azurerm_key_vault.main.id
  
  depends_on = [azurerm_key_vault.main]

  tags = local.common_tags
}

# Log Analytics Workspace
resource "azurerm_log_analytics_workspace" "main" {
  name                = "log-${local.project_name}-${local.environment}-${random_id.main.hex}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = var.environment == "prod" ? 30 : 7

  tags = local.common_tags
}

# Container Registry for Docker images
resource "azurerm_container_registry" "main" {
  name                = "acr${replace(local.project_name, "-", "")}${local.environment}${random_id.main.hex}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = var.environment == "prod" ? "Premium" : "Basic"
  admin_enabled       = true

  tags = local.common_tags
} 