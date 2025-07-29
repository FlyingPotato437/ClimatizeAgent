# ClimatizeAI Edge Functions Documentation

> **Status**: Updated with new OpenSolar token `s_PZAFD3MP5BYXAZ7NP4UDCKCXEE6EQ4NT` - All functions validated and ready for deployment

## Overview

This document describes the two main Supabase Edge Functions that power the ClimatizeAI permit generation workflow:

1. **`research-button`** - Generates 16 comprehensive research files using Perplexity AI
2. **`planset-button`** - Creates complete permit planset with Tony's uploads + generated specs

Both functions are deployed to production Supabase project `rdzofqvpkdrbpygtfaxa` and ready for frontend integration.

---

## 🔬 Research Button Function

### Purpose
Retrieves OpenSolar project data and generates 16 detailed research analysis files using actual Perplexity prompts.

### Endpoint
```
POST https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/research-button
```

### Headers
```json
{
  "Authorization": "Bearer YOUR_SUPABASE_ANON_KEY",
  "Content-Type": "application/json"
}
```

### Input Parameters
```json
{
  "openSolarId": "7481941",        // OpenSolar project ID
  "openSolarOrgId": "183989"       // OpenSolar organization ID
}
```

### Processing Workflow
1. **Fetch OpenSolar Data**: Retrieves project.json, systems.json, BOM, and single line diagram
2. **Load 16 Prompts**: Uses actual prompts from `agents/prompts/perplexity/perplexity_prompt1` through `perplexity_prompt16`
3. **Populate Templates**: Replaces variables like `{address}`, `{nameplate_capacity}` with real project data
4. **Sequential Processing**: Processes prompts 1-16 sequentially with 1-second delays (not parallel)
5. **Generate Research**: Calls Perplexity API for each prompt using sonar-pro model
6. **Store Files**: Saves 16 markdown files to Supabase Storage `research-files` bucket
7. **Database Entry**: Creates record in `research_analyses` table with metadata

### Output Response
```json
{
  "success": true,
  "data": {
    "researchId": "research_1738123456789_abc123",
    "projectInfo": {
      "id": "7481941",
      "address": "560 Hester Creek Rd, Los Gatos, CA 95033",
      "title": "560 Hester Creek Solar",
      "nameplate_capacity_kw": 16.0,
      "annual_generation_kwh": 24000,
      "co2_reduction_tons": 120,
      "total_cost": 45000
    },
    "systemsData": [...],
    "bomData": [...],
    "singleLineDiagram": "https://...",
    "researchFiles": [
      {
        "section": "perplexity_response_1",
        "fileName": "perplexity_response_1.md",
        "url": "https://rdzofqvpkdrbpygtfaxa.supabase.co/storage/v1/object/public/research-files/...",
        "size": 4567
      },
      // ... 15 more files
    ],
    "metadata": {
      "totalFiles": 16,
      "totalSizeBytes": 73450,
      "processingTimeSeconds": 180,
      "createdAt": "2025-07-28T20:30:00Z"
    }
  },
  "message": "Research analysis completed successfully"
}
```

### Generated Files
- `perplexity_response_1.md` - Project Overview (Investment-grade development memo)
- `perplexity_response_2.md` - Solar Resource & Energy Production Analysis
- `perplexity_response_3.md` - Site Assessment & Real Estate Due Diligence
- `perplexity_response_4.md` - Grid Interconnection Analysis
- `perplexity_response_5.md` - Permitting & Regulatory Requirements
- `perplexity_response_6.md` - Financial Analysis & Economics
- `perplexity_response_7.md` - Environmental Impact Assessment
- `perplexity_response_8.md` - Technical Specifications & Equipment
- `perplexity_response_9.md` - Construction Timeline & Logistics
- `perplexity_response_10.md` - Risk Assessment & Mitigation
- `perplexity_response_11.md` - Operations & Maintenance Plan
- `perplexity_response_12.md` - Performance Monitoring & Optimization
- `perplexity_response_13.md` - Community Engagement & Impact
- `perplexity_response_14.md` - Insurance & Risk Management
- `perplexity_response_15.md` - Decommissioning & End-of-Life Planning
- `perplexity_response_16.md` - Investment Summary & Recommendations

---

## 📋 Planset Button Function

### Purpose
Combines Tony's uploaded first few pages with generated permit documents to create a complete planset ZIP package.

### Endpoint
```
POST https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/planset-button
```

### Headers
```json
{
  "Authorization": "Bearer YOUR_SUPABASE_ANON_KEY",
  "Content-Type": "application/json"
}
```

### Input Parameters
```json
{
  "researchId": "research_1738123456789_abc123",  // From research-button response
  "tonyUploadFiles": [                            // Tony's uploaded PDF pages
    {
      "fileName": "tony_page_1.pdf",
      "content": "base64_encoded_pdf_content",
      "pageCount": 3
    }
  ]
}
```

### Processing Workflow
1. **Validate Input**: Ensures research ID exists and uploaded files are provided
2. **Retrieve Research**: Fetches research data and BOM from database
3. **Extract BOM Components**: Processes OpenSolar systems data for solar components
4. **Smart Permit Generator**: 
   - Uses Exa.ai to search for real manufacturer specification sheets
   - OpenAI validates specs to filter out catalogs
   - Downloads and processes manufacturer datasheets
5. **Combine Documents**: Merges Tony's uploaded pages with generated permit documents
6. **Create Planset ZIP**: Packages everything into a complete planset
7. **Upload & Store**: Saves ZIP to `permit-packages` bucket and creates database record

### Output Response
```json
{
  "success": true,
  "data": {
    "plansetId": "planset_1738123456790_def456",
    "downloadUrl": "https://rdzofqvpkdrbpygtfaxa.supabase.co/storage/v1/object/public/permit-packages/planset_1738123456790_def456.zip",
    "metadata": {
      "totalPages": 25,
      "totalSizeBytes": 15200000,
      "tonyUploadPages": 3,
      "generatedSpecPages": 22,
      "componentsProcessed": 10,
      "specsFound": 7,
      "createdAt": "2025-07-28T20:35:00Z",
      "expiresAt": "2025-08-04T20:35:00Z"
    },
    "components": [
      {
        "name": "Q.PEAK DUO BLK ML-G10 400W",
        "manufacturer": "Qcells",
        "category": "Solar Panel",
        "specSheetFound": true,
        "specUrl": "https://..."
      }
    ]
  },
  "message": "Planset generated successfully"
}
```

---

## 🗄️ Database Schema

### `research_analyses` Table
```sql
CREATE TABLE research_analyses (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  research_id TEXT UNIQUE NOT NULL,
  opensolar_project_id TEXT,
  opensolar_org_id TEXT,
  project_info JSONB,
  systems_data JSONB,
  bom_data JSONB,
  single_line_diagram_url TEXT,
  research_files_metadata JSONB,
  total_files INTEGER DEFAULT 16,
  total_size_bytes BIGINT,
  processing_time_seconds INTEGER,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### `permit_packages` Table
```sql
CREATE TABLE permit_packages (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  planset_id TEXT UNIQUE NOT NULL,
  research_id TEXT REFERENCES research_analyses(research_id),
  download_url TEXT NOT NULL,
  total_pages INTEGER,
  total_size_bytes BIGINT,
  tony_upload_pages INTEGER,
  generated_spec_pages INTEGER,
  components_processed INTEGER,
  specs_found INTEGER,
  expires_at TIMESTAMP WITH TIME ZONE,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## 📁 Storage Buckets

### `research-files` Bucket
- **Purpose**: Stores 16 research markdown files
- **Public Access**: Yes (with RLS policies)
- **File Naming**: `research_ID/perplexity_response_N.md`
- **Retention**: Permanent

### `permit-packages` Bucket  
- **Purpose**: Stores complete planset ZIP files
- **Public Access**: Yes (with signed URLs)
- **File Naming**: `planset_ID.zip`
- **Retention**: 7 days (configurable)

---

## 🔑 Environment Variables

Required environment secrets in Supabase Dashboard:

```bash
# Perplexity API
PERPLEXITY_API_KEY=your_perplexity_api_key

# Smart Permit Generator APIs
EXA_API_KEY=your_exa_api_key
OPENAI_API_KEY=your_openai_api_key

# OpenSolar API (for future real JWT integration)
OPENSOLAR_API_KEY=s_TVRDFYU3KJGINUZ3JA3LNY42GATICWPX
OPENSOLAR_ORG_ID=183989
OPENSOLAR_PROJECT_ID=7481941
```

---

## 🚀 Frontend Integration

### Research Button Implementation
```javascript
const handleResearchButtonClick = async () => {
  const response = await fetch('https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/research-button', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      openSolarId: "7481941",
      openSolarOrgId: "183989"
    })
  });
  
  const result = await response.json();
  if (result.success) {
    // Store research ID for planset generation
    setResearchId(result.data.researchId);
    // Display research files
    setResearchFiles(result.data.researchFiles);
  }
};
```

### Planset Button Implementation
```javascript
const handlePlansetButtonClick = async (tonyFiles) => {
  const response = await fetch('https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/planset-button', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      researchId: researchId, // From previous research call
      tonyUploadFiles: tonyFiles // User uploaded files
    })
  });
  
  const result = await response.json();
  if (result.success) {
    // Download planset ZIP
    window.open(result.data.downloadUrl, '_blank');
  }
};
```

---

## ⚠️ Error Handling

### Common Error Responses
```json
{
  "success": false,
  "data": null,
  "message": "Specific error message",
  "error": {
    "code": "ERROR_CODE",
    "details": "Detailed error information"
  }
}
```

### Error Codes
- `MISSING_PARAMETERS` - Required input parameters missing
- `OPENSOLAR_AUTH_ERROR` - OpenSolar API authentication failed
- `PERPLEXITY_API_ERROR` - Perplexity API call failed
- `STORAGE_ERROR` - File upload/download failed
- `DATABASE_ERROR` - Database operation failed
- `RESEARCH_NOT_FOUND` - Research ID not found for planset generation

---

## 🧪 Testing

### Test Research Button
```bash
curl -X POST \
  'https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/research-button' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "openSolarId": "7481941",
    "openSolarOrgId": "183989"
  }'
```

### Test Planset Button
```bash
curl -X POST \
  'https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/planset-button' \
  -H 'Authorization: Bearer YOUR_ANON_KEY' \
  -H 'Content-Type: application/json' \
  -d '{
    "researchId": "research_1738123456789_abc123",
    "tonyUploadFiles": []
  }'
```

---

## 📊 Performance

### Research Button
- **16 Prompts**: ~2-3 minutes processing time
- **File Storage**: ~70KB total for all research files
- **API Calls**: 16 Perplexity API requests (sequential)
- **Rate Limiting**: 1-second delays between prompts

### Planset Button
- **Processing Time**: ~30-60 seconds
- **File Size**: ~15MB typical planset ZIP
- **API Calls**: Multiple Exa.ai + OpenAI requests for spec sheets
- **Components**: Processes up to 10 BOM components

---

## 🔄 Workflow Summary

1. **User clicks "Retrieve from OpenSolar API"** 
   → Calls `research-button` 
   → Returns 16 research files + project data

2. **User uploads Tony's first few pages**
   → User clicks "Generate Planset"
   → Calls `planset-button` with research ID + uploads
   → Returns complete planset ZIP download

This creates a complete end-to-end permit generation workflow ready for production use.
