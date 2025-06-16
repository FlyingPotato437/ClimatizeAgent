# Climatize Platform

A sophisticated tool designed to automate and accelerate early-stage solar project development. The platform handles both manual project entry and automated Aurora Solar integration, providing comprehensive permit analysis, financial modeling, and project scoring.

## 🏗️ Architecture

The platform is built on a **Unified Project Model** that serves as the single source of truth for all project data. This standardized model ensures consistency across all downstream services.

### Core Components

- **Frontend**: React TypeScript application with Material-UI
- **Backend**: Azure Functions (Python) with queue-based processing
- **Database**: Azure Cosmos DB for project storage
- **Storage**: Azure Blob Storage for documents
- **External APIs**: Shovels.ai (permits), Aurora Solar (designs), OpenAI (document generation)

## 🚀 Features

### Dual Data Input Streams
- **Manual Entry**: Comprehensive project form with validation
- **Aurora Integration**: Automated webhook processing for solar designs

### Automated Workflow
1. **Project Intake** → Validates and stores project data
2. **Permit Matrix Generation** → Analyzes jurisdictional requirements using Shovels.ai
3. **Site Control** → Generates Letter of Intent using GPT
4. **Capital Stack Analysis** → Calculates financing structure and returns
5. **Project Scoring** → Assigns fundability score (0-100)

### Dashboard & Analytics
- Project overview with key metrics
- Milestone tracking and progress visualization
- Financial modeling and capital stack analysis
- Document management and generation

## 📋 Prerequisites

- **Azure Account** with active subscription
- **Azure CLI** installed and configured
- **Node.js** (v16 or higher)
- **Python** (3.9 or higher)
- **Azure Functions Core Tools**

### Optional API Keys
- **Shovels.ai API Key** (for permit matrix generation)
- **OpenAI API Key** (for document generation)
- **Aurora Solar API Key** (for design integration)

## 🛠️ Installation

### 1. Clone and Setup

```bash
git clone <repository-url>
cd ClimatizeAIAgent

# Install frontend dependencies
cd frontend
npm install

# Install backend dependencies
cd ../backend
pip install -r requirements.txt
```

### 2. Local Development

#### Backend Setup
```bash
cd backend

# Copy settings file and configure
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your configuration

# Start Azure Functions locally
func start
```

#### Frontend Setup
```bash
cd frontend

# Start development server
npm start
```

The application will be available at `http://localhost:3000` with the backend running on `http://localhost:7071`.

### 3. Azure Deployment

#### Quick Deployment
```bash
# Make deployment script executable (already done)
chmod +x deploy.sh

# Edit deploy.sh to set your SUBSCRIPTION_ID
# Then run deployment
./deploy.sh
```

#### Manual Deployment
```bash
# Create resource group
az group create --name climatize-platform-rg --location eastus

# Deploy infrastructure
az deployment group create \
    --resource-group climatize-platform-rg \
    --template-file azure-deployment.json \
    --parameters appName=climatize-platform

# Deploy function code
cd backend
func azure functionapp publish climatize-platform --python

# Build and deploy frontend
cd ../frontend
npm run build
# Deploy build folder to Azure Static Web Apps or preferred hosting
```

## 🔧 Configuration

### Environment Variables

Set these in your Azure Function App settings:

```bash
# Required for permit analysis
SHOVELS_API_KEY=your-shovels-api-key

# Required for document generation
OPENAI_API_KEY=your-openai-api-key

# Optional for Aurora integration
AURORA_API_KEY=your-aurora-api-key
AURORA_BASE_URL=https://api.aurorasolar.com/v1

# Database settings (auto-configured in Azure)
COSMOS_DB_CONNECTION_STRING=...
COSMOS_DB_NAME=climatize
COSMOS_DB_CONTAINER=projects

# Storage settings (auto-configured in Azure)
BLOB_STORAGE_CONNECTION_STRING=...
BLOB_STORAGE_CONTAINER=project-documents
```

### Frontend Configuration

Update API endpoints in your frontend build to point to your deployed Azure Function:

```typescript
// In your frontend code, update axios base URL
axios.defaults.baseURL = 'https://your-function-app.azurewebsites.net/api';
```

## 📖 Usage

### Creating a Manual Project

1. Navigate to the dashboard
2. Click "Create New Project"
3. Fill out the project form with:
   - Project name and address
   - System specifications
   - Bill of materials
   - Financial information
4. Submit to trigger automated workflow

### Aurora Integration

1. Click "Connect Aurora" on the dashboard
2. Enter your Aurora credentials or API key
3. Projects will automatically sync from Aurora
4. New designs trigger the automated workflow

### Viewing Project Details

1. Click on any project card from the dashboard
2. Navigate through tabs:
   - **Milestones**: Development progress tracking
   - **Permits**: Jurisdictional requirements and matrix
   - **Capital Stack**: Financial modeling and returns
   - **Documents**: Generated files and downloads

## 🔄 Workflow Details

### 1. Manual Intake Handler
- Validates project data using Pydantic models
- Stores in Cosmos DB
- Triggers permit matrix generation

### 2. Aurora Parser
- Processes webhook notifications
- Transforms Aurora data to unified model
- Handles design updates automatically

### 3. Permit Matrix Engine
- Calls Shovels.ai API for jurisdictional data
- Generates permit requirements matrix
- Calculates costs and timelines
- Updates project milestones

### 4. Feasibility & Site Control
- Generates Letter of Intent using GPT
- Stores document in Blob Storage
- Updates site control milestone

### 5. Capital Stack Generator
- Calculates incentives (ITC, state programs)
- Models debt/equity structure
- Computes returns (IRR, cash-on-cash)
- Projects payback periods

### 6. Project Packager & Scorer
- Calculates fundability score (0-100)
- Weighs milestone completion (40%)
- Considers jurisdictional risk (30%)
- Evaluates financial viability (30%)

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 🤝 API Integration

### Shovels.ai
Used for permit matrix generation and jurisdictional analysis.

### OpenAI
Generates legal documents like Letters of Intent.

### Aurora Solar
Processes solar design data via webhooks.

## 🔐 Security

- All API keys stored as environment variables
- Azure Functions with authentication levels
- Cosmos DB with role-based access
- Blob Storage with secure access patterns

## 📊 Monitoring

The platform includes Application Insights for:
- Function execution monitoring
- Error tracking and alerting
- Performance metrics
- Usage analytics

## 🆘 Troubleshooting

### Common Issues

1. **Function not triggering**: Check queue bindings and storage connections
2. **API failures**: Verify external API keys and endpoints
3. **Database errors**: Confirm Cosmos DB connection string
4. **Document generation fails**: Check OpenAI API key and quota

### Logs and Debugging

```bash
# View function logs
az functionapp logs tail --name your-function-app --resource-group your-rg

# Check Application Insights for detailed telemetry
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

[Add your license information here]

## 🙋 Support

For support and questions:
- Create an issue in the repository
- Contact the development team
- Check the troubleshooting section above

---

**Built with ❤️ for the solar development community**