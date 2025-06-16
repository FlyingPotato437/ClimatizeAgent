#!/bin/bash

# Climatize Platform Deployment Script
# This script deploys the Climatize platform to Azure

set -e

# Configuration
RESOURCE_GROUP="climatize-platform-rg"
LOCATION="eastus"
APP_NAME="climatize-platform"
SUBSCRIPTION_ID=""  # Set your subscription ID

echo "🚀 Starting Climatize Platform Deployment"
echo "=========================================="

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    echo "❌ Azure CLI is not installed. Please install it first."
    echo "   Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Login to Azure (if not already logged in)
echo "🔐 Checking Azure authentication..."
if ! az account show &> /dev/null; then
    echo "Please login to Azure:"
    az login
fi

# Set subscription if provided
if [ ! -z "$SUBSCRIPTION_ID" ]; then
    echo "📋 Setting subscription: $SUBSCRIPTION_ID"
    az account set --subscription "$SUBSCRIPTION_ID"
fi

# Create resource group
echo "📁 Creating resource group: $RESOURCE_GROUP"
az group create --name "$RESOURCE_GROUP" --location "$LOCATION"

# Deploy Azure resources using ARM template
echo "☁️  Deploying Azure resources..."
az deployment group create \
    --resource-group "$RESOURCE_GROUP" \
    --template-file azure-deployment.json \
    --parameters appName="$APP_NAME" location="$LOCATION"

# Get deployment outputs
echo "📝 Getting deployment information..."
FUNCTION_APP_NAME=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "azure-deployment" \
    --query properties.outputs.functionAppName.value \
    --output tsv)

COSMOS_ACCOUNT_NAME=$(az deployment group show \
    --resource-group "$RESOURCE_GROUP" \
    --name "azure-deployment" \
    --query properties.outputs.cosmosAccountName.value \
    --output tsv)

echo "✅ Azure resources deployed successfully!"
echo "   Function App: $FUNCTION_APP_NAME"
echo "   Cosmos DB: $COSMOS_ACCOUNT_NAME"

# Deploy the backend function code
echo "🔧 Deploying backend functions..."
cd backend

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Deploy to Azure Functions
echo "🚀 Deploying function code..."
func azure functionapp publish "$FUNCTION_APP_NAME" --python

cd ..

# Build and deploy frontend (optional - can be deployed to Azure Static Web Apps)
echo "🌐 Building frontend..."
cd frontend

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Build the React app
echo "🏗️  Building React application..."
npm run build

cd ..

echo ""
echo "🎉 Deployment completed successfully!"
echo "=========================================="
echo "Backend Function App: https://$FUNCTION_APP_NAME.azurewebsites.net"
echo ""
echo "📋 Next steps:"
echo "1. Configure environment variables in Azure Function App:"
echo "   - SHOVELS_API_KEY: Your shovels.ai API key"
echo "   - OPENAI_API_KEY: Your OpenAI API key"
echo "   - AURORA_API_KEY: Your Aurora Solar API key (optional)"
echo ""
echo "2. Deploy the frontend to Azure Static Web Apps or your preferred hosting service"
echo ""
echo "3. Update frontend API endpoints to point to: https://$FUNCTION_APP_NAME.azurewebsites.net/api"
echo ""
echo "🔧 To configure environment variables:"
echo "az functionapp config appsettings set --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP --settings \\"
echo "    SHOVELS_API_KEY='your-shovels-api-key' \\"
echo "    OPENAI_API_KEY='your-openai-api-key' \\"
echo "    AURORA_API_KEY='your-aurora-api-key'"