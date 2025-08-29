terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

variable "azure_openai_api_key" {
  description = "Azure OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "azure_search_key" {
  description = "Azure Search Key"
  type        = string
  sensitive   = true
}

variable "azure_client_secret" {
  description = "Azure Client Secret"
  type        = string
  sensitive   = true
}

resource "azurerm_log_analytics_workspace" "main" {
  name                = "videoqna-logs"
  location            = "East US"
  resource_group_name = "***REMOVED_RESOURCE_GROUP***"
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "main" {
  name                       = "videoqna-env"
  location                   = "East US"
  resource_group_name        = "***REMOVED_RESOURCE_GROUP***"
  log_analytics_workspace_id = azurerm_log_analytics_workspace.main.id
}

resource "azurerm_container_app" "main" {
  name                         = "videoqna-ltw"
  container_app_environment_id = azurerm_container_app_environment.main.id
  resource_group_name          = "***REMOVED_RESOURCE_GROUP***"
  revision_mode                = "Single"

  template {
    container {
      name   = "videoqna-app"
      image  = "***REMOVED_ACR_URL***/videoqna-ltw:latest"
      cpu    = 2.0
      memory = "4.0Gi"

      env {
        name  = "FLASK_ENV"
        value = "production"
      }

      env {
        name  = "PYTHONPATH"
        value = "/app"
      }

      env {
        name  = "LANGUAGE_MODEL"
        value = "openai"
      }

      env {
        name        = "AZURE_OPENAI_API_KEY"
        secret_name = "azure-openai-api-key"
      }

      env {
        name        = "AZURE_SEARCH_KEY"
        secret_name = "azure-search-key"
      }

      env {
        name        = "AZURE_CLIENT_SECRET"
        secret_name = "azure-client-secret"
      }
    }

    min_replicas = 1
    max_replicas = 3
  }

  secret {
    name  = "azure-openai-api-key"
    value = var.azure_openai_api_key
  }

  secret {
    name  = "azure-search-key"
    value = var.azure_search_key
  }

  secret {
    name  = "azure-client-secret"
    value = var.azure_client_secret
  }

  ingress {
    allow_insecure_connections = false
    external_enabled           = true
    target_port                = 5000

    traffic_weight {
      latest_revision = true
      percentage      = 100
    }
  }
}

output "container_app_fqdn" {
  value = azurerm_container_app.main.latest_revision_fqdn
}