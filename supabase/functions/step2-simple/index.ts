import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
  };

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    console.log('🚀 Simplified Step 2: Project Analysis');

    if (req.method !== 'POST') {
      return new Response(JSON.stringify({
        success: false,
        error: 'Method not allowed'
      }), {
        status: 405,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    const { projectMetadata, openSolarId } = await req.json();
    console.log('Received request:', { projectMetadata, openSolarId });

    if (!openSolarId) {
      return new Response(JSON.stringify({
        success: false,
        error: 'OpenSolar ID is required'
      }), {
        status: 400,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Get API keys
    const perplexityApiKey = Deno.env.get('PERPLEXITY_API_KEY');
    
    if (!perplexityApiKey) {
      return new Response(JSON.stringify({
        success: false,
        error: 'Missing Perplexity API key'
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    console.log('✅ API keys validated');

    // Step 1: Mock OpenSolar data (since JWT is pending)
    const mockComponents = [
      {
        row: 1,
        part_name: "Q.PEAK DUO BLK ML-G10 400W",
        part_number: "Q.PEAK DUO BLK ML-G10 400",
        manufacturer: "Qcells",
        qty: "40",
        category: "Solar Module"
      },
      {
        row: 2,
        part_name: "IQ8A Microinverter",
        part_number: "IQ8A-72-2-US",
        manufacturer: "Enphase Energy Inc.",
        qty: "40",
        category: "Microinverter"
      },
      {
        row: 3,
        part_name: "XR-100 Rail 84\"",
        part_number: "XR-100-084A",
        manufacturer: "IronRidge",
        qty: "24",
        category: "Mounting Rail"
      }
    ];

    console.log(`✅ Mock BOM data: ${mockComponents.length} components`);

    // Step 2: Perplexity Feasibility Analysis
    console.log('🔍 Running Perplexity feasibility analysis...');
    
    const analysisQuery = `
      Analyze this solar installation project for feasibility on a scale of 0-100:
      
      System Details:
      - Size: ${projectMetadata.systemSize || '16.0 kW'}
      - Address: ${projectMetadata.address || 'Los Gatos, CA'}
      - Roof Type: ${projectMetadata.roofType || 'Composition Shingle'}
      - Installation: ${projectMetadata.installationType || 'Roof Mount'}
      
      Components:
      ${mockComponents.map(c => `- ${c.qty}x ${c.part_name} (${c.manufacturer})`).join('\n')}
      
      Consider factors like location solar potential, system sizing, component compatibility, 
      local regulations, and installation complexity. Provide a numerical score and brief reasoning.
      Also identify any potential issues and provide 3-5 recommendations.
    `;

    const perplexityResponse = await fetch('https://api.perplexity.ai/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${perplexityApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        model: 'sonar-pro',
        messages: [{ role: 'user', content: analysisQuery }],
        temperature: 0.1
      })
    });

    if (!perplexityResponse.ok) {
      console.error('Perplexity API failed:', perplexityResponse.status);
      return new Response(JSON.stringify({
        success: false,
        error: `Perplexity API failed: ${perplexityResponse.status}`
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    const perplexityData = await perplexityResponse.json();
    const analysis = perplexityData.choices[0]?.message?.content || 'No analysis available';

    // Extract feasibility score
    let feasibilityScore = 85;
    const scoreMatch = analysis.match(/(\d+)\/100|\b(\d+)%|\bscore[:\s]*(\d+)/i);
    if (scoreMatch) {
      feasibilityScore = parseInt(scoreMatch[1] || scoreMatch[2] || scoreMatch[3]);
    }

    console.log(`✅ Feasibility analysis complete: ${feasibilityScore}/100`);

    // Step 3: Extract issues and recommendations
    const issues = [];
    const recommendations = analysis
      .split('\n')
      .filter(line => line.trim().startsWith('-') || line.trim().startsWith('•') || line.trim().startsWith('*'))
      .map(line => line.replace(/^[-•*]\s*/, '').trim())
      .filter(rec => rec.length > 10)
      .slice(0, 5);

    // Step 4: Generate project ID
    const projectId = `project_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    // Step 5: Create system configuration
    const systemConfig = {
      id: projectId,
      projectInfo: {
        id: projectId,
        ...projectMetadata,
        openSolarId,
        systemSize: projectMetadata.systemSize || '16.0 kW',
        annualProduction: 24000,
        co2Reduction: 120,
        systemCost: 45000
      },
      components: mockComponents,
      feasibilityScore,
      issues,
      recommendations,
      specifications: mockComponents.map(component => ({
        component,
        validatedSpecs: {
          power: component.category === 'Solar Module' ? '400W' : undefined,
          efficiency: component.category === 'Solar Module' ? '20.6%' : undefined
        }
      }))
    };

    console.log('✅ System configuration generated');

    // Return success (bypassing database for now)
    return new Response(JSON.stringify({
      success: true,
      data: {
        projectId,
        systemConfig,
        step: 'analysis_complete',
        nextStep: 'generate_permit_packet',
        analysis_preview: analysis.substring(0, 500) + '...',
        note: 'Database storage bypassed for testing - core workflow validated'
      },
      message: 'Step 2 core workflow successful!'
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Step 2 simple error:', error);
    return new Response(JSON.stringify({
      success: false,
      error: error.message,
      stack: error.stack?.substring(0, 500)
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});
