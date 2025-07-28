#!/bin/bash

# Supabase Edge Functions Deployment Script
# This script deploys the permit generation system to Supabase

set -e

echo "🚀 Deploying ClimatizeAI Permit Generator to Supabase..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo -e "${RED}❌ Supabase CLI is not installed. Please install it first:${NC}"
    echo "npm install -g supabase"
    exit 1
fi

# Set project reference
PROJECT_REF="rdzofqvpkdrbpygtfaxa"
echo -e "${YELLOW}📡 Using Supabase project: ${PROJECT_REF}${NC}"

# Login to Supabase (if not already logged in)
echo -e "${YELLOW}🔐 Checking Supabase authentication...${NC}"
if ! supabase projects list &> /dev/null; then
    echo -e "${YELLOW}🔑 Please log in to Supabase:${NC}"
    supabase login
fi

# Link to the project
echo -e "${YELLOW}🔗 Linking to Supabase project...${NC}"
supabase link --project-ref $PROJECT_REF

# Deploy database migrations
echo -e "${YELLOW}🗄️  Deploying database migrations...${NC}"
if [ -f "migrations/20250728_initial_schema.sql" ]; then
    supabase db push
    echo -e "${GREEN}✅ Database migrations deployed${NC}"
else
    echo -e "${YELLOW}⚠️  No migrations found, skipping...${NC}"
fi

# Set environment secrets
echo -e "${YELLOW}🔒 Setting up environment secrets...${NC}"
echo "Please ensure these secrets are set in the Supabase dashboard:"
echo "https://supabase.com/dashboard/project/${PROJECT_REF}/functions/secrets"
echo ""
echo "Setting environment secrets..."
supabase secrets set PERPLEXITY_API_KEY="your_perplexity_api_key_here"
supabase secrets set OPENSOLAR_CLIENT_CODE="your_opensolar_client_code"
supabase secrets set OPENSOLAR_USERNAME="your_opensolar_username"
supabase secrets set OPENSOLAR_PASSWORD="your_opensolar_password"
supabase secrets set EXA_API_KEY="your_exa_api_key_here"
supabase secrets set OPENAI_API_KEY="your_openai_api_key_here"
read -p "Press Enter to continue after setting secrets in the dashboard..."

# Deploy Edge Functions
echo -e "${YELLOW}⚡ Deploying Edge Functions...${NC}"

# Deploy handle-project-submission function
if [ -d "functions/handle-project-submission" ]; then
    echo -e "${YELLOW}📤 Deploying handle-project-submission function...${NC}"
    supabase functions deploy handle-project-submission
    echo -e "${GREEN}✅ handle-project-submission deployed${NC}"
else
    echo -e "${RED}❌ handle-project-submission function not found${NC}"
    exit 1
fi

# Deploy generate-permit-packet function
if [ -d "functions/generate-permit-packet" ]; then
    echo -e "${YELLOW}📋 Deploying generate-permit-packet function...${NC}"
    supabase functions deploy generate-permit-packet
    echo -e "${GREEN}✅ generate-permit-packet deployed${NC}"
else
    echo -e "${RED}❌ generate-permit-packet function not found${NC}"
    exit 1
fi

# Create storage buckets (if they don't exist)
echo -e "${YELLOW}🪣 Setting up storage buckets...${NC}"
supabase storage create project-files --public=true 2>/dev/null || echo "bucket 'project-files' already exists"
supabase storage create permit-packages --public=true 2>/dev/null || echo "bucket 'permit-packages' already exists"  
supabase storage create permit-documents --public=false 2>/dev/null || echo "bucket 'permit-documents' already exists"

echo -e "${GREEN}✅ Storage buckets configured${NC}"

# Display function URLs
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo ""
echo "Edge Function URLs:"
echo "📤 Handle Project Submission:"
echo "   https://${PROJECT_REF}.supabase.co/functions/v1/handle-project-submission"
echo ""
echo "📋 Generate Permit Packet:"
echo "   https://${PROJECT_REF}.supabase.co/functions/v1/generate-permit-packet"
echo ""
echo "🎛️  Supabase Dashboard:"
echo "   https://supabase.com/dashboard/project/${PROJECT_REF}"
echo ""
echo "📊 Function Logs:"
echo "   https://supabase.com/dashboard/project/${PROJECT_REF}/functions"
echo ""
echo -e "${YELLOW}⚠️  Remember to set the environment secrets in the dashboard if you haven't already!${NC}"

# Test functions (optional)
read -p "Would you like to test the functions with a sample request? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧪 Testing handle-project-submission function...${NC}"
    
    # Sample test payload
    TEST_PAYLOAD='{
      "projectMetadata": {
        "projectName": "Test Solar Installation",
        "address": "123 Solar St, Sunnyville, CA 94000",
        "systemSize": 8.5,
        "panelCount": 24,
        "inverterType": "Enphase IQ8A",
        "mountingType": "Roof Mount",
        "utilityCompany": "PG&E",
        "jurisdictionName": "Sunnyville",
        "customerInfo": {
          "name": "John Doe",
          "email": "john@example.com",
          "phone": "555-1234"
        }
      },
      "hasFiles": {
        "permit": false,
        "bom": false
      }
    }'
    
    RESPONSE=$(curl -s -X POST \
      "https://${PROJECT_REF}.supabase.co/functions/v1/handle-project-submission" \
      -H "Authorization: Bearer YOUR_ANON_KEY" \
      -H "Content-Type: application/json" \
      -d "$TEST_PAYLOAD")
    
    echo "Response:"
    echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
fi

echo ""
echo -e "${GREEN}🎊 ClimatizeAI Permit Generator is now live on Supabase!${NC}"
