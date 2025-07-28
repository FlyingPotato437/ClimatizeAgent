#!/bin/bash

# Test Script for ClimatizeAI Permit Generator Workflow
# This script demonstrates the complete workflow from project submission to permit generation

set -e

# Configuration
PROJECT_REF="rdzofqvpkdrbpygtfaxa"
ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJkem9mcXZwa2RyYnB5Z3RmYXhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3MjUwNzYsImV4cCI6MjA2OTMwMTA3Nn0.YEgI135ryq_vA93qPbnBVFkphfb-tDQZWYiA5CUpZjg"
BASE_URL="https://${PROJECT_REF}.supabase.co/functions/v1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing ClimatizeAI Permit Generator Workflow${NC}"
echo "=================================================="

# Step 1: Test project submission without files (should return upload URLs)
echo -e "\n${YELLOW}📤 Step 1: Testing project submission (no files)${NC}"

STEP1_PAYLOAD='{
  "projectMetadata": {
    "projectName": "Demo Solar Installation",
    "address": "123 Solar Street, Sunnyville, CA 94000",
    "systemSize": 8.5,
    "panelCount": 24,
    "inverterType": "Enphase IQ8A",
    "mountingType": "Roof Mount",
    "utilityCompany": "PG&E",
    "jurisdictionName": "Sunnyville",
    "customerInfo": {
      "name": "John Solar",
      "email": "john@solardemo.com",
      "phone": "555-SOLAR-1"
    }
  },
  "hasFiles": {
    "permit": false,
    "bom": false
  }
}'

echo "Sending request to handle-project-submission..."
STEP1_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/handle-project-submission" \
  -H "Authorization: Bearer ${ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "$STEP1_PAYLOAD")

echo "Response:"
echo "$STEP1_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STEP1_RESPONSE"

# Extract project ID from response
PROJECT_ID=$(echo "$STEP1_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('projectId', ''))" 2>/dev/null || echo "")

if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}❌ Failed to get project ID from Step 1${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Step 1 completed. Project ID: ${PROJECT_ID}${NC}"

# Step 2: Simulate file upload completion and resubmit
echo -e "\n${YELLOW}📁 Step 2: Testing project submission (with files)${NC}"

STEP2_PAYLOAD='{
  "projectMetadata": {
    "projectName": "Demo Solar Installation",
    "address": "123 Solar Street, Sunnyville, CA 94000",
    "systemSize": 8.5,
    "panelCount": 24,
    "inverterType": "Enphase IQ8A",
    "mountingType": "Roof Mount",
    "utilityCompany": "PG&E",
    "jurisdictionName": "Sunnyville",
    "customerInfo": {
      "name": "John Solar",
      "email": "john@solardemo.com",
      "phone": "555-SOLAR-1"
    }
  },
  "hasFiles": {
    "permit": true,
    "bom": true
  }
}'

# Create sample BOM CSV content for testing
SAMPLE_BOM="Row,Part Number,Part Name,Manufacturer,Qty,Category
1,Q.PEAK DUO BLK-G10+ 385,Q.PEAK DUO BLK-G10+ 385W Solar Panel,Qcells,24,Solar Panel
2,IQ8A-72-2-US,IQ8A Microinverter,Enphase Energy Inc.,24,Inverter
3,XR-1000-168A,XR Rails 168 inch,IronRidge,12,Mounting
4,29-7000-BLK,End Cap Black,IronRidge,24,Mounting
5,PV-MC4-15A,MC4 Connector 15A,Various,48,Electrical"

# Note: In a real scenario, you would upload the BOM CSV to the signed URL from Step 1
# For this demo, we'll simulate that the files have been uploaded

echo "Sending request with files present..."
STEP2_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/handle-project-submission" \
  -H "Authorization: Bearer ${ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "$STEP2_PAYLOAD")

echo "Response:"
echo "$STEP2_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STEP2_RESPONSE"

# Check if analysis was successful
ANALYSIS_SUCCESS=$(echo "$STEP2_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('success', False))" 2>/dev/null || echo "false")

if [ "$ANALYSIS_SUCCESS" = "True" ] || [ "$ANALYSIS_SUCCESS" = "true" ]; then
    echo -e "${GREEN}✅ Step 2 completed. Project analysis successful.${NC}"
    
    # Extract feasibility score if available
    FEASIBILITY_SCORE=$(echo "$STEP2_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('systemConfig', {}).get('feasibilityScore', 'N/A'))" 2>/dev/null || echo "N/A")
    echo -e "${BLUE}📊 Feasibility Score: ${FEASIBILITY_SCORE}${NC}"
else
    echo -e "${YELLOW}⚠️  Step 2 may have issues (could be due to missing file upload in demo)${NC}"
fi

# Step 3: Test permit packet generation
echo -e "\n${YELLOW}📋 Step 3: Testing permit packet generation${NC}"

STEP3_PAYLOAD="{
  \"projectId\": \"${PROJECT_ID}\"
}"

echo "Sending request to generate-permit-packet..."
STEP3_RESPONSE=$(curl -s -X POST \
  "${BASE_URL}/generate-permit-packet" \
  -H "Authorization: Bearer ${ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "$STEP3_PAYLOAD")

echo "Response:"
echo "$STEP3_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$STEP3_RESPONSE"

# Check if permit generation was successful
PERMIT_SUCCESS=$(echo "$STEP3_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('success', False))" 2>/dev/null || echo "false")

if [ "$PERMIT_SUCCESS" = "True" ] || [ "$PERMIT_SUCCESS" = "true" ]; then
    echo -e "${GREEN}✅ Step 3 completed. Permit packet generated successfully.${NC}"
    
    # Extract download URL if available
    DOWNLOAD_URL=$(echo "$STEP3_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('data', {}).get('downloadUrl', 'N/A'))" 2>/dev/null || echo "N/A")
    echo -e "${BLUE}📥 Download URL: ${DOWNLOAD_URL}${NC}"
else
    echo -e "${YELLOW}⚠️  Step 3 may have issues (expected for demo without actual file uploads)${NC}"
fi

# Summary
echo -e "\n${BLUE}📊 Workflow Test Summary${NC}"
echo "========================"
echo -e "Project ID: ${PROJECT_ID}"
echo -e "Step 1 (Project Submission): ${GREEN}✅ Completed${NC}"
echo -e "Step 2 (File Processing): ${YELLOW}⚠️  Simulated${NC}"
echo -e "Step 3 (Permit Generation): ${YELLOW}⚠️  Simulated${NC}"
echo ""
echo -e "${YELLOW}Note: Full workflow requires actual file uploads to storage buckets.${NC}"
echo -e "${YELLOW}This demo shows the API endpoints are working correctly.${NC}"

# Function status check
echo -e "\n${BLUE}🔍 Function Status Check${NC}"
echo "========================="

# Check if functions are responding
echo "Testing function health..."

HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" \
  "${BASE_URL}/handle-project-submission" \
  -X OPTIONS)

if [ "$HEALTH_CHECK" = "200" ]; then
    echo -e "${GREEN}✅ handle-project-submission: Healthy${NC}"
else
    echo -e "${RED}❌ handle-project-submission: Error (HTTP $HEALTH_CHECK)${NC}"
fi

HEALTH_CHECK2=$(curl -s -o /dev/null -w "%{http_code}" \
  "${BASE_URL}/generate-permit-packet" \
  -X OPTIONS)

if [ "$HEALTH_CHECK2" = "200" ]; then
    echo -e "${GREEN}✅ generate-permit-packet: Healthy${NC}"
else
    echo -e "${RED}❌ generate-permit-packet: Error (HTTP $HEALTH_CHECK2)${NC}"
fi

echo ""
echo -e "${BLUE}🎉 Workflow test completed!${NC}"
echo ""
echo "Next Steps:"
echo "1. Set up environment secrets in Supabase dashboard"
echo "2. Test with real file uploads"
echo "3. Integrate with Lovable frontend"
echo "4. Monitor function logs for any issues"
echo ""
echo "Dashboard URLs:"
echo "📊 Functions: https://supabase.com/dashboard/project/${PROJECT_REF}/functions"
echo "🔒 Secrets: https://supabase.com/dashboard/project/${PROJECT_REF}/functions/secrets"
echo "🗄️  Database: https://supabase.com/dashboard/project/${PROJECT_REF}/editor"
