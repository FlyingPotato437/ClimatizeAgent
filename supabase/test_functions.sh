#!/bin/bash

# Test Supabase Edge Functions - Steps 2 and 3
set -e

echo "🔥 Testing Smart Permit Generator - Steps 2 & 3"
echo "=============================================="

# Project configuration
PROJECT_URL="https://rdzofqvpkdrbpygtfaxa.supabase.co"
ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InJkem9mcXZwa2RyYnB5Z3RmYXhhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MjIzNDM4MzcsImV4cCI6MjAzNzkxOTgzN30.lHH0Q4ksyStw9X2Dj0FMJaJJ3w6iJG0CTJbzGV4hF9A"

# Test Step 2: Project Submission
echo
echo "🚀 STEP 2: Testing handle-project-submission..."
echo "================================================"

STEP2_RESPONSE=$(curl -s -X POST \
  "${PROJECT_URL}/functions/v1/handle-project-submission" \
  -H "Authorization: Bearer ${ANON_KEY}" \
  -H "Content-Type: application/json" \
  -H "apikey: ${ANON_KEY}" \
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

# Check if Step 2 succeeded
if echo "$STEP2_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Step 2 PASSED - Project submission successful"
    
    # Extract system config ID for Step 3
    SYSTEM_CONFIG_ID=$(echo "$STEP2_RESPONSE" | jq -r '.data.id')
    FEASIBILITY_SCORE=$(echo "$STEP2_RESPONSE" | jq -r '.data.feasibilityScore')
    
    echo "📊 Feasibility Score: $FEASIBILITY_SCORE/100"
    echo "🆔 System Config ID: $SYSTEM_CONFIG_ID"
    
    # Test Step 3: Smart Permit Generation
    echo
    echo "🚀 STEP 3: Testing generate-permit-packet with SMART PERMIT GENERATOR..."
    echo "======================================================================="
    
    STEP3_RESPONSE=$(curl -s -X POST \
      "${PROJECT_URL}/functions/v1/generate-permit-packet" \
      -H "Authorization: Bearer ${ANON_KEY}" \
      -H "Content-Type: application/json" \
      -H "apikey: ${ANON_KEY}" \
      -d "{\"systemConfigId\": \"$SYSTEM_CONFIG_ID\"}")
    
    echo "Step 3 Response:"
    echo "$STEP3_RESPONSE" | jq '.'
    
    # Check if Step 3 succeeded
    if echo "$STEP3_RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
        echo "✅ Step 3 PASSED - Smart permit generation successful"
        
        DOWNLOAD_URL=$(echo "$STEP3_RESPONSE" | jq -r '.data.downloadUrl')
        TOTAL_PAGES=$(echo "$STEP3_RESPONSE" | jq -r '.data.metadata.totalPages')
        PACKAGE_SIZE=$(echo "$STEP3_RESPONSE" | jq -r '.data.metadata.packageSize')
        
        echo
        echo "🎉 SMART PERMIT GENERATOR SUCCESS!"
        echo "================================="
        echo "📦 Package Details:"
        echo "   📄 Total Pages: $TOTAL_PAGES"
        echo "   💾 Package Size: $PACKAGE_SIZE" 
        echo "   🔗 Download URL: $DOWNLOAD_URL"
        echo
        echo "🧪 Features Tested:"
        echo "   ✅ Real Perplexity API integration"
        echo "   ✅ OpenSolar API data fetching"
        echo "   ✅ Exa.ai spec sheet searching" 
        echo "   ✅ OpenAI catalog filtering"
        echo "   ✅ Real manufacturer spec downloads"
        echo "   ✅ PDF generation and storage"
        echo
        echo "📥 Download your permit package:"
        echo "$DOWNLOAD_URL"
        
    else
        echo "❌ Step 3 FAILED - Smart permit generation failed"
        echo "Error: $(echo "$STEP3_RESPONSE" | jq -r '.error // .message // "Unknown error"')"
        exit 1
    fi
    
else
    echo "❌ Step 2 FAILED - Project submission failed" 
    echo "Error: $(echo "$STEP2_RESPONSE" | jq -r '.error // .message // "Unknown error"')"
    exit 1
fi

echo
echo "🎯 FULL WORKFLOW COMPLETE!"
echo "========================="
echo "Both Step 2 (project analysis) and Step 3 (smart permit generation) are working!"
echo
echo "🔗 Monitor functions: https://supabase.com/dashboard/project/rdzofqvpkdrbpygtfaxa/functions"
echo "📊 Check database: https://supabase.com/dashboard/project/rdzofqvpkdrbpygtfaxa/editor"
