# Terraform Variables for Climatize AI Agent Infrastructure

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "location" {
  description = "Azure region for resource deployment"
  type        = string
  default     = "East US 2"
}

variable "use_mock_helioscope" {
  description = "Whether to use mock Helioscope service for development"
  type        = bool
  default     = true
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
  
  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR"], var.log_level)
    error_message = "Log level must be DEBUG, INFO, WARNING, or ERROR."
  }
}

variable "openai_api_key" {
  description = "OpenAI API key for Ultrathink multi-agent system"
  type        = string
  default     = ""
  sensitive   = true
}

variable "allowed_origins" {
  description = "Allowed CORS origins for the API"
  type        = list(string)
  default     = ["*"]
}

variable "enable_monitoring" {
  description = "Enable comprehensive monitoring and alerting"
  type        = bool
  default     = true
}

variable "backup_retention_days" {
  description = "Number of days to retain backups"
  type        = number
  default     = 30
  
  validation {
    condition     = var.backup_retention_days >= 7 && var.backup_retention_days <= 365
    error_message = "Backup retention must be between 7 and 365 days."
  }
}

variable "enable_high_availability" {
  description = "Enable high availability configuration for production"
  type        = bool
  default     = false
}

variable "custom_domain" {
  description = "Custom domain for the application (optional)"
  type        = string
  default     = ""
}

variable "ssl_certificate_path" {
  description = "Path to SSL certificate for custom domain"
  type        = string
  default     = ""
}

variable "enable_auto_scaling" {
  description = "Enable auto-scaling for Function Apps"
  type        = bool
  default     = false
}

variable "max_instances" {
  description = "Maximum number of instances for auto-scaling"
  type        = number
  default     = 10
  
  validation {
    condition     = var.max_instances >= 1 && var.max_instances <= 200
    error_message = "Max instances must be between 1 and 200."
  }
}

variable "enable_vnet_integration" {
  description = "Enable VNet integration for enhanced security"
  type        = bool
  default     = false
}

variable "ip_whitelist" {
  description = "List of IP addresses allowed to access the resources"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

variable "cosmos_db_throughput" {
  description = "Cosmos DB throughput (RU/s)"
  type        = number
  default     = 400
  
  validation {
    condition     = var.cosmos_db_throughput >= 400
    error_message = "Cosmos DB throughput must be at least 400 RU/s."
  }
}

variable "redis_sku" {
  description = "Redis cache SKU"
  type        = string
  default     = "Basic"
  
  validation {
    condition     = contains(["Basic", "Standard", "Premium"], var.redis_sku)
    error_message = "Redis SKU must be Basic, Standard, or Premium."
  }
}

variable "function_app_sku" {
  description = "Function App service plan SKU"
  type        = string
  default     = "B1"
}

variable "enable_application_insights" {
  description = "Enable Application Insights for monitoring"
  type        = bool
  default     = true
}

variable "notification_email" {
  description = "Email address for critical alerts and notifications"
  type        = string
  default     = ""
}

variable "deployment_slot_enabled" {
  description = "Enable deployment slots for blue-green deployments"
  type        = bool
  default     = false
}

variable "enable_diagnostic_logs" {
  description = "Enable diagnostic logging for all resources"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain diagnostic logs"
  type        = number
  default     = 30
  
  validation {
    condition     = var.log_retention_days >= 1 && var.log_retention_days <= 730
    error_message = "Log retention must be between 1 and 730 days."
  }
} 