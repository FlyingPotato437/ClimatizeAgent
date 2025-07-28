# ClimatizeAI Permit Generator - Supabase Backend

This directory contains the Supabase Edge Functions and database schema for the ClimatizeAI permit generation system.

## Architecture Overview

The system implements a two-step workflow:

```
Frontend (Lovable) 
    ↓
Step 2: handle-project-submission
    → Check for uploaded permit + BOM
    → If missing → Return signed upload URLs  
    → If present → Parse & run Research Agent
    → If not feasible → Return rejection
    → If feasible → Return structured system config
    ↓
Step 3: generate-permit-packet  
    → Create docs from structured data
    → Upload to Supabase Storage
    → Return download URL
```

## Edge Functions

### 1. `handle-project-submission`
**Endpoint:** `https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/handle-project-submission`

**Purpose:** Processes project submissions and runs feasibility analysis

**Flow:**
1. Receives project metadata from frontend
2. Checks if permit PDF and BOM CSV are uploaded
3. If missing → Returns signed upload URLs
4. If present → Downloads and parses BOM
5. Runs Research Agent analysis using Perplexity API
6. Returns feasibility score and system configuration

**Request:**
```json
{
  "projectMetadata": {
    "projectName": "Solar Installation Project",
    "address": "123 Main St, City, State",
    "systemSize": 8.5,
    "panelCount": 24,
    "inverterType": "Enphase IQ8A",
    "mountingType": "Roof Mount",
    "utilityCompany": "PG&E",
    "jurisdictionName": "City Name",
    "customerInfo": {
      "name": "Customer Name",
      "email": "customer@email.com", 
      "phone": "555-1234"
    }
  },
  "hasFiles": {
    "permit": true,
    "bom": true
  }
}
```

**Response (Files Missing):**
```json
{
  "success": true,
  "data": {
    "projectId": "project_1234567890_abc123",
    "step": "upload_required"
  },
  "uploadUrls": {
    "permit": "https://signed-upload-url-for-permit.pdf",
    "bom": "https://signed-upload-url-for-bom.csv"
  }
}
```

**Response (Analysis Complete):**
```json
{
  "success": true,
  "data": {
    "projectId": "project_1234567890_abc123", 
    "systemConfig": {
      "projectInfo": {...},
      "components": [...],
      "feasibilityScore": 85,
      "issues": [],
      "recommendations": [...],
      "specifications": [...]
    },
    "step": "analysis_complete",
    "nextStep": "generate_permit_packet"
  }
}
```

### 2. `generate-permit-packet`
**Endpoint:** `https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/generate-permit-packet`

**Purpose:** Generates complete permit documentation package

**Flow:**
1. Retrieves system configuration from database
2. Generates permit documents using OpenSolar API
3. Creates comprehensive permit package
4. Uploads to Supabase Storage
5. Returns download URL

**Request:**
```json
{
  "projectId": "project_1234567890_abc123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "projectId": "project_1234567890_abc123",
    "downloadUrl": "https://storage-url/permit_package.zip",
    "permitPacket": {
      "applicationForm": "storage/permit-packets/.../application_form.pdf",
      "siteLayout": "storage/permit-packets/.../site_layout.pdf", 
      "electricalDiagram": "storage/permit-packets/.../electrical_diagram.pdf",
      "specifications": "storage/permit-packets/.../specifications.pdf",
      "metadata": {
        "generatedAt": "2025-01-28T15:49:36Z",
        "totalPages": 25,
        "packageSize": "15.2 MB"
      }
    },
    "generatedAt": "2025-01-28T15:49:36Z",
    "expiresAt": "2025-02-04T15:49:36Z"
  }
}
```

## Database Schema

### Tables

#### `system_configurations`
Stores project analysis results and configurations.

```sql
- id: UUID (primary key)
- project_id: TEXT (unique identifier)
- config: JSONB (system configuration data)
- status: TEXT (pending, ready_for_permit_generation, permit_package_generated)
- permit_package_url: TEXT (URL to generated package)
- created_at: TIMESTAMPTZ
- updated_at: TIMESTAMPTZ  
- generated_at: TIMESTAMPTZ
```

#### `permit_history`
Tracks all generated permit packages.

```sql
- id: UUID (primary key)
- project_id: TEXT
- package_url: TEXT
- system_config: JSONB
- status: TEXT
- generated_at: TIMESTAMPTZ
- downloaded_at: TIMESTAMPTZ
- download_count: INTEGER
```

#### `project_analytics`
Analytics and event tracking.

```sql
- id: UUID (primary key)
- project_id: TEXT
- event_type: TEXT (submission, analysis_complete, permit_generated, download)
- event_data: JSONB
- created_at: TIMESTAMPTZ
```

### Storage Buckets

#### `project-files` (Public)
- Uploaded permit PDFs and BOM CSVs
- Path: `{projectId}/permit.pdf`, `{projectId}/bom.csv`

#### `permit-packages` (Public)
- Final permit packages (ZIP files)
- Path: `permit_package_{projectId}_{timestamp}.zip`

#### `permit-documents` (Private)
- Individual permit documents before packaging
- Path: `{projectId}/application_form.pdf`, etc.

## Environment Variables

Set these secrets in the Supabase dashboard at:
`https://supabase.com/dashboard/project/rdzofqvpkdrbpygtfaxa/functions/secrets`

```
PERPLEXITY_API_KEY=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
OPENSOLAR_CLIENT_CODE=climatize-test-sdk-client-key  
OPENSOLAR_USERNAME=will@climatize.earth
OPENSOLAR_PASSWORD=MoExr7Kp24#8R%
EXA_API_KEY=your-exa-api-key
OPENAI_API_KEY=your-openai-api-key
```

## Deployment

### Prerequisites
1. Install Supabase CLI: `npm install -g supabase`
2. Ensure you have access to the Supabase project

### Deploy Steps

1. **Run the deployment script:**
   ```bash
   ./deploy.sh
   ```

2. **Set environment secrets in dashboard:**
   - Go to: https://supabase.com/dashboard/project/rdzofqvpkdrbpygtfaxa/functions/secrets
   - Add all required environment variables

3. **Verify deployment:**
   - Check function logs in dashboard
   - Test with sample requests

### Manual Deployment (Alternative)

```bash
# Login to Supabase
supabase login

# Link to project
supabase link --project-ref rdzofqvpkdrbpygtfaxa

# Deploy database migrations
supabase db push

# Deploy functions
supabase functions deploy handle-project-submission
supabase functions deploy generate-permit-packet

# Create storage buckets
supabase storage create project-files --public=true
supabase storage create permit-packages --public=true
supabase storage create permit-documents --public=false
```

## Testing

### Test handle-project-submission

```bash
curl -X POST \
  "https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/handle-project-submission" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "projectMetadata": {
      "projectName": "Test Solar Installation",
      "address": "123 Solar St, Sunnyville, CA",
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
```

### Test generate-permit-packet

```bash
curl -X POST \
  "https://rdzofqvpkdrbpygtfaxa.supabase.co/functions/v1/generate-permit-packet" \
  -H "Authorization: Bearer YOUR_ANON_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "projectId": "project_1234567890_abc123"
  }'
```

## Integration with Existing System

The functions integrate with your existing permit generation logic:

1. **Research Agent:** Uses the existing Perplexity-based analysis
2. **Spec Sheet Generation:** Leverages existing Exa.ai + Firecrawl integration
3. **PDF Generation:** Builds on existing PDF combination logic
4. **OpenSolar API:** Integrates with provided credentials for layout generation

## Monitoring & Logs

- **Function Logs:** https://supabase.com/dashboard/project/rdzofqvpkdrbpygtfaxa/functions
- **Database Queries:** Built-in views for project summaries
- **Analytics:** Event tracking in `project_analytics` table
- **Storage Usage:** Monitor bucket usage in dashboard

## Error Handling

The functions include comprehensive error handling:
- Validation of input parameters
- Graceful fallbacks for API failures
- Detailed error logging
- User-friendly error messages
- Retry logic for external API calls

## Security

- Row Level Security (RLS) enabled on all tables
- Service role access for Edge Functions
- Public bucket access for downloads only
- Signed URLs for secure uploads
- Environment variables for API keys

## Troubleshooting

### Common Issues

1. **Function deployment fails:** 
   - Check Supabase CLI version
   - Verify project permissions
   - Check function syntax

2. **Environment variables not working:**
   - Verify secrets are set in dashboard
   - Check exact variable names
   - Restart functions after setting secrets

3. **Storage upload fails:**
   - Check bucket policies
   - Verify file size limits
   - Check bucket existence

4. **API integration errors:**
   - Verify API credentials
   - Check network connectivity
   - Review API rate limits
