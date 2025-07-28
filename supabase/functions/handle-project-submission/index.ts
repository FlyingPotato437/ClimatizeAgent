import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';
import { createSupabaseClient, corsHeaders, createApiResponse, getSignedUploadUrl, downloadFileFromStorage, parseCSVBOM } from '../_shared/utils.ts';
import { ResearchAgent } from '../_shared/researchAgent.ts';
import { ProjectMetadata, Component, SystemConfiguration, ApiResponse } from '../_shared/types.ts';

serve(async (req) => {
  // Handle CORS preflight requests
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    console.log('Request method:', req.method);
    console.log('Request headers:', Object.fromEntries(req.headers.entries()));
    
    if (req.method !== 'POST') {
      return createApiResponse(false, null, 'Method not allowed');
    }

    const { projectMetadata, openSolarId } = await req.json() as {
      projectMetadata: ProjectMetadata;
      openSolarId: string;
    };

    console.log('Received project submission:', { projectMetadata, openSolarId });

    if (!openSolarId) {
      return createApiResponse(false, null, 'OpenSolar ID is required');
    }

    const supabase = createSupabaseClient();
    const projectId = `project_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    console.log('Processing OpenSolar project:', openSolarId);

    // Get API credentials
    const perplexityApiKey = Deno.env.get('PERPLEXITY_API_KEY');
    const openSolarUsername = Deno.env.get('OPENSOLAR_USERNAME');
    const openSolarPassword = Deno.env.get('OPENSOLAR_PASSWORD');
    const openSolarClientCode = Deno.env.get('OPENSOLAR_CLIENT_CODE');
    
    if (!perplexityApiKey || !openSolarUsername || !openSolarPassword || !openSolarClientCode) {
      return createApiResponse(false, null, 'API credentials missing');
    }

    console.log('Creating ResearchAgent with API keys...');
    const researchAgent = new ResearchAgent(
      perplexityApiKey,
      openSolarClientCode,
      openSolarUsername,
      openSolarPassword
    );

    console.log('Starting project analysis...');
    console.log('OpenSolar ID:', openSolarId);
    console.log('Project metadata:', JSON.stringify(projectMetadata, null, 2));
    
    let systemConfig;
    try {
      systemConfig = await researchAgent.analyzeProjectFromOpenSolar(openSolarId, projectMetadata);
      console.log('Analysis complete. System config generated:', !!systemConfig);
    } catch (analysisError) {
      console.error('Analysis failed:', analysisError.message);
      console.error('Full error:', analysisError);
      return createApiResponse(false, null, 'Failed to analyze project feasibility');
    }
      
    console.log(`Analysis complete. Feasibility score: ${systemConfig.feasibilityScore}`);

    // Step 4: Check feasibility threshold
    if (systemConfig.feasibilityScore < 60) {
      console.log('Project not feasible, returning rejection');
        
      return createApiResponse(false, {
        projectId,
        feasibilityScore: systemConfig.feasibilityScore,
        issues: systemConfig.issues,
        reason: 'Project feasibility score below acceptable threshold'
      }, 'Project not feasible for automatic permit generation');
    }

    // Step 5: Store system configuration for permit generation
    const { error: storageError } = await supabase
      .from('system_configurations')
      .upsert({
        project_id: projectId,
        config: systemConfig,
        created_at: new Date().toISOString(),
        status: 'ready_for_permit_generation'
      });

    if (storageError) {
      console.error('Error storing system configuration:', storageError);
      return createApiResponse(false, null, 'Failed to store system configuration');
    }

    // Step 6: Return successful analysis
    return createApiResponse(true, {
      projectId,
      systemConfig,
      step: 'analysis_complete',
      nextStep: 'generate_permit_packet'
    });

  } catch (error) {
    console.error('Error in handleProjectSubmission:', error);
    return createApiResponse(false, null, 'Internal server error');
  }
});

/* 
 * Function Overview:
 * 
 * This Edge Function implements Step 2 of the permit generation workflow:
 * 
 * 1. Receives project metadata from Lovable frontend
 * 2. Checks if permit PDF and BOM CSV files are uploaded
 * 3. If missing → Returns signed upload URLs for file upload
 * 4. If present → Downloads and parses the BOM
 * 5. Runs Research Agent analysis using Perplexity API
 * 6. Calculates feasibility score and identifies issues
 * 7. If not feasible (score < 60) → Returns rejection with reasons
 * 8. If feasible → Stores system configuration in database
 * 9. Returns structured system config for permit generation
 * 
 * Environment Variables Required:
 * - SUPABASE_URL
 * - SUPABASE_SERVICE_ROLE_KEY  
 * - PERPLEXITY_API_KEY
 * 
 * Database Tables:
 * - system_configurations (project_id, config, created_at, status)
 * 
 * Storage Buckets:
 * - project-files (for permit PDFs and BOM CSVs)
 */
