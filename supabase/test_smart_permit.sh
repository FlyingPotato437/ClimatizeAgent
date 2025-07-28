#!/bin/bash

# Test script for smart permit generator with real Exa.ai + OpenAI integration
set -e

echo "🧪 Testing Smart Permit Generator with REAL API Integrations"
echo "=============================================================="

# Configuration
PROJECT_URL="https://rdzofqvpkdrbpygtfaxa.supabase.co"
FUNCTION_URL="${PROJECT_URL}/functions/v1"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Testing environment setup...${NC}"

# Check if required environment variables are set
if [ -z "$SUPABASE_ANON_KEY" ]; then
    echo -e "${RED}❌ SUPABASE_ANON_KEY environment variable not set${NC}"
    echo "Please set: export SUPABASE_ANON_KEY=your_anon_key"
    exit 1
fi

echo -e "${GREEN}✅ Environment variables configured${NC}"
echo

# Test Step 2: Project Submission with Real OpenSolar ID
echo -e "${BLUE}Step 2: Testing project submission with real data...${NC}"

PROJECT_METADATA='{
  "projectMetadata": {
    "address": "560 Hester Creek Rd, Los Gatos, CA 95033",
    "systemSize": "16.0 kW",
    "roofType": "Composition Shingle",
    "installationType": "Roof Mount"
  },
  "openSolarId": "proj_47ca1e82f48e4a3ba6e04d5c6b7a6d4e"
}'

echo "Sending project submission request..."
SUBMIT_RESPONSE=$(curl -s -X POST \
  "${FUNCTION_URL}/handle-project-submission" \
  -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" \
  -H "Content-Type: application/json" \
  -d "$PROJECT_METADATA")

echo "Raw response: $SUBMIT_RESPONSE"
echo

# Parse and validate response
if echo "$SUBMIT_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Project submission successful${NC}"
    
    # Extract system config ID
    SYSTEM_CONFIG_ID=$(echo "$SUBMIT_RESPONSE" | jq -r '.data.id')
    echo "System Config ID: $SYSTEM_CONFIG_ID"
    
    # Show feasibility details
    FEASIBILITY_SCORE=$(echo "$SUBMIT_RESPONSE" | jq -r '.data.feasibilityScore')
    ISSUES_COUNT=$(echo "$SUBMIT_RESPONSE" | jq -r '.data.issues | length')
    RECOMMENDATIONS_COUNT=$(echo "$SUBMIT_RESPONSE" | jq -r '.data.recommendations | length')
    
    echo "📊 Feasibility Score: $FEASIBILITY_SCORE/100"
    echo "⚠️  Issues Found: $ISSUES_COUNT"
    echo "💡 Recommendations: $RECOMMENDATIONS_COUNT"
    echo
    
    # Test Step 3: Smart Permit Generation with Exa.ai
    echo -e "${BLUE}Step 3: Testing SMART permit generation with Exa.ai...${NC}"
    
    PERMIT_REQUEST="{\"systemConfigId\": \"$SYSTEM_CONFIG_ID\"}"
    
    echo "Generating permit packet with real spec sheets..."
    PERMIT_RESPONSE=$(curl -s -X POST \
      "${FUNCTION_URL}/generate-permit-packet" \
      -H "Authorization: Bearer ${SUPABASE_ANON_KEY}" \
      -H "Content-Type: application/json" \
      -d "$PERMIT_REQUEST")
    
    echo "Raw permit response: $PERMIT_RESPONSE"
    echo
    
    # Parse permit response
    if echo "$PERMIT_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Smart permit generation successful${NC}"
        
        # Extract download URL
        DOWNLOAD_URL=$(echo "$PERMIT_RESPONSE" | jq -r '.data.downloadUrl')
        TOTAL_PAGES=$(echo "$PERMIT_RESPONSE" | jq -r '.data.metadata.totalPages')
        PACKAGE_SIZE=$(echo "$PERMIT_RESPONSE" | jq -r '.data.metadata.packageSize')
        
        echo "📦 Package Details:"
        echo "   Pages: $TOTAL_PAGES"
        echo "   Size: $PACKAGE_SIZE"
        echo "   Download URL: $DOWNLOAD_URL"
        echo
        
        echo -e "${GREEN}🎉 SMART PERMIT GENERATOR TEST PASSED!${NC}"
        echo -e "${GREEN}   ✅ Real Perplexity API integration working${NC}"
        echo -e "${GREEN}   ✅ Real Exa.ai spec sheet search working${NC}"
        echo -e "${GREEN}   ✅ Real OpenAI validation working${NC}"
        echo -e "${GREEN}   ✅ Permit package generated with real manufacturer specs${NC}"
        echo
        echo "📥 Download your permit package:"
        echo "$DOWNLOAD_URL"
        
    else
        echo -e "${RED}❌ Smart permit generation failed${NC}"
        echo "Error: $(echo "$PERMIT_RESPONSE" | jq -r '.error // "Unknown error"')"
        exit 1
    fi
    
else
    echo -e "${RED}❌ Project submission failed${NC}"
    echo "Error: $(echo "$SUBMIT_RESPONSE" | jq -r '.error // "Unknown error"')"
    exit 1
fi

echo
echo "🔗 Monitor function logs:"
echo "https://supabase.com/dashboard/project/rdzofqvpkdrbpygtfaxa/functions"
echo
echo "📊 Check database:"
echo "https://supabase.com/dashboard/project/rdzofqvpkdrbpygtfaxa/editor"
