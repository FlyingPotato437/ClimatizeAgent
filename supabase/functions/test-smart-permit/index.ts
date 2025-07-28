import { serve } from 'https://deno.land/std@0.168.0/http/server.ts';

serve(async (req) => {
  // Handle CORS
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS'
  };

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Get API keys from environment
    const exaApiKey = Deno.env.get('EXA_API_KEY');
    const openaiApiKey = Deno.env.get('OPENAI_API_KEY');
    const perplexityApiKey = Deno.env.get('PERPLEXITY_API_KEY');

    console.log('Environment check:');
    console.log('EXA_API_KEY:', exaApiKey ? '✅ Set' : '❌ Missing');
    console.log('OPENAI_API_KEY:', openaiApiKey ? '✅ Set' : '❌ Missing');
    console.log('PERPLEXITY_API_KEY:', perplexityApiKey ? '✅ Set' : '❌ Missing');

    if (!exaApiKey || !openaiApiKey) {
      return new Response(JSON.stringify({
        success: false,
        error: 'Missing API keys',
        details: {
          exa: exaApiKey ? 'Set' : 'Missing',
          openai: openaiApiKey ? 'Set' : 'Missing'
        }
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    // Test smart permit generator logic
    const testComponent = {
      part_number: 'Q.PEAK DUO BLK ML-G10 400',
      part_name: 'Q.PEAK DUO BLK ML-G10 400W Solar Panel',
      manufacturer: 'Qcells',
      category: 'Solar Module'
    };

    console.log('Testing Exa.ai search for:', testComponent.part_name);

    // Test Exa.ai search
    const exaResponse = await fetch('https://api.exa.ai/search', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${exaApiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        query: `${testComponent.part_number} solar panel datasheet PDF filetype:pdf`,
        type: 'keyword',
        numResults: 3,
        includeDomains: ['qcells.com'],
        contents: {
          text: true
        }
      })
    });

    let exaResults = null;
    if (exaResponse.ok) {
      exaResults = await exaResponse.json();
      console.log('Exa.ai search successful:', exaResults.results?.length, 'results found');
    } else {
      console.error('Exa.ai search failed:', exaResponse.status);
    }

    // Test OpenAI validation if we have results
    let openaiTest = null;
    if (exaResults?.results?.length > 0) {
      const testUrl = exaResults.results[0].url;
      
      const openaiResponse = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${openaiApiKey}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          model: 'gpt-4o-mini',
          messages: [{
            role: 'user',
            content: `Analyze this URL to determine if it's a legitimate manufacturer specification sheet (not a catalog):

URL: ${testUrl}
Component: ${testComponent.part_name}
Manufacturer: ${testComponent.manufacturer}

Return only 'YES' if it's a specific component datasheet/spec sheet, or 'NO' if it's a catalog, general page, or not relevant.`
          }],
          max_tokens: 10,
          temperature: 0
        })
      });

      if (openaiResponse.ok) {
        const openaiData = await openaiResponse.json();
        openaiTest = {
          url: testUrl,
          validation: openaiData.choices[0]?.message?.content?.trim(),
          isValid: openaiData.choices[0]?.message?.content?.trim().toUpperCase() === 'YES'
        };
        console.log('OpenAI validation result:', openaiTest.validation);
      }
    }

    return new Response(JSON.stringify({
      success: true,
      message: 'Smart Permit Generator APIs Working!',
      test_results: {
        component_tested: testComponent,
        exa_search: {
          status: exaResponse.ok ? 'success' : 'failed',
          results_found: exaResults?.results?.length || 0,
          sample_url: exaResults?.results?.[0]?.url
        },
        openai_validation: openaiTest,
        environment: {
          exa_api_key: '✅ Set',
          openai_api_key: '✅ Set',
          perplexity_api_key: perplexityApiKey ? '✅ Set' : '❌ Missing'
        }
      }
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Test function error:', error);
    return new Response(JSON.stringify({
      success: false,
      error: error.message,
      stack: error.stack
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});
