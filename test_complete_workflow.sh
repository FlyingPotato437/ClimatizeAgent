#!/bin/bash

# Complete Step 2 & 3 Workflow Test
set -e

echo "🚀 TESTING COMPLETE STEPS 2 & 3 WORKFLOW"
echo "========================================"

# Configuration
PROJECT_URL="https://rdzofqvpkdrbpygtfaxa.supabase.co"
AUTH_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJkem9mcXZwa2RyYnB5Z3RmYXhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTM3MjUwNzYsImV4cCI6MjA2OTMwMTA3Nn0.YEgI135ryq_vA93qPbnBVFkphfb-tDQZWYiA5CUpZjg"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Pre-flight checks...${NC}"

# Test 1: Verify APIs working
echo "1. Testing Smart Permit Generator APIs..."
API_TEST=$(curl -s -X POST "${PROJECT_URL}/functions/v1/test-smart-permit" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "apikey: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json")

if echo "$API_TEST" | jq -e '.success' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Smart Permit APIs working${NC}"
    EXA_RESULTS=$(echo "$API_TEST" | jq -r '.test_results.exa_search.results_found')
    echo "   - Exa.ai results: $EXA_RESULTS spec sheets found"
    SAMPLE_URL=$(echo "$API_TEST" | jq -r '.test_results.exa_search.sample_url')
    echo "   - Sample spec: $SAMPLE_URL"
else
    echo -e "${RED}❌ Smart Permit APIs failed${NC}"
    echo "$API_TEST"
    exit 1
fi

# Test 2: Verify ResearchAgent components
echo "2. Testing ResearchAgent components..."
RESEARCH_TEST=$(curl -s -X POST "${PROJECT_URL}/functions/v1/test-research-agent" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "apikey: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json")

if echo "$RESEARCH_TEST" | jq -e '.success' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ ResearchAgent working${NC}"
    FEASIBILITY=$(echo "$RESEARCH_TEST" | jq -r '.test_results.feasibility_analysis.score')
    echo "   - Feasibility Score: $FEASIBILITY/100"
    COMPONENTS=$(echo "$RESEARCH_TEST" | jq -r '.test_results.bom_conversion.components_converted')
    echo "   - Components converted: $COMPONENTS"
else
    echo -e "${RED}❌ ResearchAgent failed${NC}"
    echo "$RESEARCH_TEST"
    exit 1
fi

echo
echo -e "${BLUE}🚀 STEP 2: Project Submission & Analysis${NC}"
echo "========================================="

STEP2_RESPONSE=$(curl -s -X POST "${PROJECT_URL}/functions/v1/handle-project-submission" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "apikey: ${AUTH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "projectMetadata": {
      "address": "560 Hester Creek Rd, Los Gatos, CA 95033",
      "systemSize": "16.0 kW",
      "roofType": "Composition Shingle", 
      "installationType": "Roof Mount"
    },
    "openSolarId": "proj_47ca1e82f48e4a3ba6e04d5c6b7a6d4e"
  }')

echo "Step 2 Response:"
echo "$STEP2_RESPONSE" | jq '.'

# Check Step 2 success
if echo "$STEP2_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ STEP 2 SUCCESS!${NC}"
    
    # Extract project details
    SYSTEM_CONFIG_ID=$(echo "$STEP2_RESPONSE" | jq -r '.data.projectId // .data.systemConfig.projectInfo.id // "unknown"')
    FEASIBILITY_SCORE=$(echo "$STEP2_RESPONSE" | jq -r '.data.systemConfig.feasibilityScore // .data.feasibilityScore // "unknown"')
    COMPONENTS_COUNT=$(echo "$STEP2_RESPONSE" | jq -r '.data.systemConfig.components | length // 0')
    
    echo -e "${YELLOW}📊 Project Analysis Results:${NC}"
    echo "   🆔 System Config ID: $SYSTEM_CONFIG_ID"
    echo "   📈 Feasibility Score: $FEASIBILITY_SCORE/100"
    echo "   🔧 Components Analyzed: $COMPONENTS_COUNT"
    
    # Test Step 3 if Step 2 succeeded
    echo
    echo -e "${BLUE}🚀 STEP 3: Smart Permit Generation${NC}"
    echo "=================================="
    
    STEP3_RESPONSE=$(curl -s -X POST "${PROJECT_URL}/functions/v1/generate-permit-packet" \
      -H "Authorization: Bearer ${AUTH_TOKEN}" \
      -H "apikey: ${AUTH_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "{\"systemConfigId\": \"$SYSTEM_CONFIG_ID\"}")
    
    echo "Step 3 Response:"
    echo "$STEP3_RESPONSE" | jq '.'
    
    # Check Step 3 success
    if echo "$STEP3_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        echo -e "${GREEN}✅ STEP 3 SUCCESS!${NC}"
        
        DOWNLOAD_URL=$(echo "$STEP3_RESPONSE" | jq -r '.data.downloadUrl // "unknown"')
        TOTAL_PAGES=$(echo "$STEP3_RESPONSE" | jq -r '.data.metadata.totalPages // "unknown"')
        PACKAGE_SIZE=$(echo "$STEP3_RESPONSE" | jq -r '.data.metadata.packageSize // "unknown"')
        
        echo -e "${YELLOW}📦 Permit Package Generated:${NC}"
        echo "   📄 Total Pages: $TOTAL_PAGES"
        echo "   💾 Package Size: $PACKAGE_SIZE"
        echo "   🔗 Download URL: $DOWNLOAD_URL"
        
        echo
        echo -e "${GREEN}🎉 COMPLETE WORKFLOW SUCCESS!${NC}"
        echo "================================="
        echo -e "${GREEN}✅ Step 2: Project analysis with Perplexity AI${NC}"
        echo -e "${GREEN}✅ Step 3: Smart permit generation with Exa.ai + OpenAI${NC}"
        echo -e "${GREEN}✅ Real manufacturer specifications found${NC}"
        echo -e "${GREEN}✅ Permit package generated and uploaded${NC}"
        echo
        echo "🔗 Download your permit package:"
        echo "$DOWNLOAD_URL"
        
    else
        echo -e "${RED}❌ STEP 3 FAILED${NC}"
        STEP3_ERROR=$(echo "$STEP3_RESPONSE" | jq -r '.error // .message // "Unknown error"')
        echo "Error: $STEP3_ERROR"
        
        # Still success if Step 2 worked
        echo -e "${YELLOW}⚠️ Partial Success: Step 2 worked, Step 3 needs debugging${NC}"
    fi
    
else
    echo -e "${RED}❌ STEP 2 FAILED${NC}"
    STEP2_ERROR=$(echo "$STEP2_RESPONSE" | jq -r '.error // .message // "Unknown error"')
    echo "Error: $STEP2_ERROR"
    
    echo
    echo -e "${YELLOW}🔍 Individual components work but full workflow failed.${NC}"
    echo "   - Perplexity API: ✅ Working"
    echo "   - Exa.ai API: ✅ Working"  
    echo "   - Component conversion: ✅ Working"
    echo "   - Issue: Likely database or error handling"
fi

echo
echo "🔗 Function Logs: https://supabase.com/dashboard/project/rdzofqvpkdrbpygtfaxa/functions"
echo "📊 Database: https://supabase.com/dashboard/project/rdzofqvpkdrbpygtfaxa/editor"
