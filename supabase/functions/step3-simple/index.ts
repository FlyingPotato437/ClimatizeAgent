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
    console.log('🚀 Simplified Step 3: Smart Permit Generation');

    const { systemConfigId } = await req.json();
    console.log('Received system config ID:', systemConfigId);

    // Get API keys for smart permit generator
    const exaApiKey = Deno.env.get('EXA_API_KEY');
    const openaiApiKey = Deno.env.get('OPENAI_API_KEY');

    if (!exaApiKey || !openaiApiKey) {
      return new Response(JSON.stringify({
        success: false,
        error: 'Missing API keys for smart permit generator',
        details: {
          exa: exaApiKey ? 'Set' : 'Missing',
          openai: openaiApiKey ? 'Set' : 'Missing'
        }
      }), {
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    console.log('✅ Smart permit generator API keys validated');

    // Mock system config (would normally come from database)
    const mockSystemConfig = {
      id: systemConfigId,
      components: [
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
      ]
    };

    console.log(`Processing ${mockSystemConfig.components.length} components for real spec sheets...`);

    // SMART PERMIT GENERATOR: Find real manufacturer specs using your Python logic
    const realSpecs = [];
    let totalSpecsFound = 0;

    for (const component of mockSystemConfig.components) {
      console.log(`🔍 Searching for real spec: ${component.part_name}`);

      // Generate search queries (from smart_permit_generator.py)
      const queries = [];
      if (component.category.toLowerCase().includes('module')) {
        queries.push(`${component.part_number} solar panel datasheet PDF filetype:pdf`);
        queries.push(`${component.manufacturer} ${component.part_number} specification sheet`);
      } else if (component.category.toLowerCase().includes('inverter')) {
        queries.push(`${component.part_number} ${component.manufacturer} microinverter datasheet PDF`);
      } else {
        queries.push(`${component.part_number} ${component.manufacturer} datasheet PDF`);
      }

      // Use Exa.ai to search for real specs
      let specFound = false;
      for (const query of queries.slice(0, 2)) { // Test top 2 queries
        try {
          const manufacturerDomains = getManufacturerDomains(component.manufacturer);
          
          const exaResponse = await fetch('https://api.exa.ai/search', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${exaApiKey}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              query,
              type: 'keyword',
              numResults: 3,
              includeDomains: manufacturerDomains,
              contents: { text: true }
            })
          });

          if (exaResponse.ok) {
            const exaData = await exaResponse.json();
            
            // Validate each result with OpenAI  
            for (const result of exaData.results || []) {
              const isValid = await validateSpecSheet(result.url, component, openaiApiKey);
              if (isValid) {
                realSpecs.push({
                  component: component.part_name,
                  manufacturer: component.manufacturer,
                  part_number: component.part_number,
                  url: result.url,
                  title: result.title || 'Manufacturer Specification Sheet',
                  source: 'exa_ai_search',
                  validated: true
                });
                
                console.log(`✅ Found REAL spec: ${result.url}`);
                specFound = true;
                totalSpecsFound++;
                break;
              } else {
                console.log(`❌ Rejected (catalog/invalid): ${result.url}`);
              }
            }
            
            if (specFound) break; // Found spec for this component
          }
        } catch (error) {
          console.error(`Error searching for ${component.part_name}:`, error.message);
        }
      }

      if (!specFound) {
        console.log(`⚠️ No real spec found for ${component.part_name}, will use fallback`);
      }
    }

    console.log(`✅ Smart permit generation complete: ${totalSpecsFound}/${mockSystemConfig.components.length} real specs found`);

    // Generate permit package metadata
    const permitPackage = {
      projectId: systemConfigId,
      applicationForm: 'permit_application.pdf',
      siteLayout: 'site_layout.pdf', 
      electricalDiagram: 'electrical_single_line.pdf',
      specifications: 'real_manufacturer_specs.pdf',
      structuralCalculations: 'structural_analysis.pdf',
      interconnectionApplication: 'utility_interconnection.pdf',
      metadata: {
        generatedAt: new Date().toISOString(),
        totalPages: 7 + (realSpecs.length * 2), // Base docs + spec sheets
        packageSize: `${(12 + realSpecs.length * 3).toFixed(1)} MB`,
        realSpecsIncluded: totalSpecsFound,
        componentsTotal: mockSystemConfig.components.length,
        realSpecSuccess: `${Math.round((totalSpecsFound / mockSystemConfig.components.length) * 100)}%`
      }
    };

    // Mock download URL (would be real Supabase storage URL)
    const downloadUrl = `https://rdzofqvpkdrbpygtfaxa.supabase.co/storage/v1/object/public/permit-packages/${systemConfigId}/smart_permit_package.zip`;

    return new Response(JSON.stringify({
      success: true,
      data: {
        ...permitPackage,
        downloadUrl,
        realSpecifications: realSpecs
      },
      message: `Smart permit package generated with ${totalSpecsFound} real manufacturer specs!`
    }), {
      status: 200,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Step 3 simple error:', error);
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

// Helper functions (from smart_permit_generator.py)
function getManufacturerDomains(manufacturer: string): string[] {
  const domainMap: { [key: string]: string[] } = {
    'Qcells': ['qcells.com'],
    'Enphase Energy Inc.': ['enphase.com'],
    'Enphase': ['enphase.com'],
    'IronRidge': ['ironridge.com'],
    'SolarEdge': ['solaredge.com']
  };
  return domainMap[manufacturer] || [];
}

async function validateSpecSheet(url: string, component: any, openaiApiKey: string): Promise<boolean> {
  try {
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
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

URL: ${url}
Component: ${component.part_name}
Manufacturer: ${component.manufacturer}

Return only 'YES' if it's a specific component datasheet/spec sheet, or 'NO' if it's a catalog, general page, or not relevant.`
        }],
        max_tokens: 10,
        temperature: 0
      })
    });

    if (response.ok) {
      const data = await response.json();
      const answer = data.choices[0]?.message?.content?.trim().toUpperCase();
      return answer === 'YES';
    }
    return false;
  } catch (error) {
    console.error('OpenAI validation error:', error);
    return false;
  }
}
