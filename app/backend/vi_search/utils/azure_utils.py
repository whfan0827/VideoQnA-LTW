import subprocess


def get_azd_env_values() -> dict:
    """
    These values should be defined in the Azure DevOps pipeline.
    - AZURE_OPENAI_API_KEY (Azure OpenAI API key)
    - AZURE_OPENAI_CHATGPT_DEPLOYMENT (Azure OpenAI Chat LLM deployment name)
    - AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT (Azure OpenAI embeddings model deployment name)
    - AZURE_OPENAI_RESOURCE_GROUP (Resource Group name of the Azure OpenAI resource)
    - AZURE_OPENAI_SERVICE (Azure OpenAI resource name)
    - AZURE_SEARCH_KEY (Azure AI Search API key)
    - AZURE_SEARCH_SERVICE (Azure AI Search resource name)
    - AZURE_SEARCH_LOCATION (Azure AI Search instance location, e.g. ukwest)
    - AZURE_SEARCH_SERVICE_RESOURCE_GROUP (Resource Group name of the Azure AI Search resource)
    - AZURE_TENANT_ID (Azure Tenant ID)
    """
    import os
    
    # First, try to read values from environment variables (.env file)
    azd_env_values = {
        "AZURE_OPENAI_API_KEY": os.getenv("AZURE_OPENAI_API_KEY"),
        "AZURE_OPENAI_CHATGPT_DEPLOYMENT": os.getenv("AZURE_OPENAI_CHATGPT_DEPLOYMENT"),
        "AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT": os.getenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT"),
        "AZURE_OPENAI_RESOURCE_GROUP": os.getenv("AZURE_OPENAI_RESOURCE_GROUP"),
        "AZURE_OPENAI_SERVICE": os.getenv("AZURE_OPENAI_SERVICE"),
        "AZURE_SEARCH_KEY": os.getenv("AZURE_SEARCH_KEY"),
        "AZURE_SEARCH_SERVICE": os.getenv("AZURE_SEARCH_SERVICE"),
        "AZURE_SEARCH_LOCATION": os.getenv("AZURE_SEARCH_LOCATION"),
        "AZURE_SEARCH_SERVICE_RESOURCE_GROUP": os.getenv("AZURE_SEARCH_SERVICE_RESOURCE_GROUP"),
        "AZURE_TENANT_ID": os.getenv("AZURE_TENANT_ID"),
    }
    
    # If local environment variables are not set, fall back to azd env get-values
    if not all(v for v in [azd_env_values["AZURE_OPENAI_API_KEY"], azd_env_values["AZURE_OPENAI_SERVICE"]]):
        try:
            output = subprocess.check_output(["azd", "env", "get-values"], encoding='utf-8')
            output = output.split("\n")

            azd_fallback_values = {}
            for line in output:
                if line and "=" in line:
                    key, value = line.split("=", 1)
                    azd_fallback_values[key] = value[1:-1] if len(value) > 2 else value
            
            # Only use azd values for keys that are not set in environment
            for key in azd_env_values:
                if not azd_env_values[key] and key in azd_fallback_values:
                    azd_env_values[key] = azd_fallback_values[key]
                    
        except Exception as e:
            # If azd command fails, keep using environment variables only
            pass

    return azd_env_values
