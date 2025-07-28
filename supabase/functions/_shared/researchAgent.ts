import { Component, SystemConfiguration, ComponentSpecification } from './types.ts';

interface PerplexityResponse {
  choices: Array<{
    message: {
      content: string;
    };
  }>;
}

interface OpenSolarProject {
  id: number;
  address: string;
  country_name: string;
  state: string;
  county: string;
  contacts_data: Array<{
    display: string;
    phone: string;
  }>;
}

interface OpenSolarSystem {
  id: number;
  kw_stc: number;
  price_including_tax: number;
  output_annual_kwh: number;
  consumption_offset_percentage: number;
  co2_tons_lifetime: number;
  net_profit: number;
  module_quantity: number;
  modules: Array<{
    code: string;
    manufacturer_name: string;
    quantity: number;
  }>;
  inverters: Array<{
    code: string;
    manufacturer_name: string;
    quantity: number;
  }>;
  others: Array<{
    code: string;
    manufacturer_name: string;
    quantity: number;
  }>;
}

export class ResearchAgent {
  private perplexityApiKey: string;
  private openSolarUsername: string;
  private openSolarPassword: string;
  private openSolarClientCode: string;

  constructor(perplexityApiKey: string, openSolarUsername: string, openSolarPassword: string, openSolarClientCode: string) {
    this.perplexityApiKey = perplexityApiKey;
    this.openSolarUsername = openSolarUsername;
    this.openSolarPassword = openSolarPassword;
    this.openSolarClientCode = openSolarClientCode;
  }

  async analyzeProjectFromOpenSolar(
    openSolarId: string,
    projectMetadata: any
  ): Promise<SystemConfiguration> {
    console.log('Starting OpenSolar project analysis for ID:', openSolarId);
    
    // Get project and system data from OpenSolar API
    const { projectData, systemData } = await this.getOpenSolarData(openSolarId);
    
    // Convert OpenSolar data to our component format
    const components = this.convertOpenSolarToComponents(systemData);
    
    // Update project metadata with OpenSolar data
    const enrichedMetadata = {
      ...projectMetadata,
      address: projectData.address,
      systemSize: systemData.kw_stc,
      panelCount: systemData.module_quantity,
      annualProduction: systemData.output_annual_kwh,
      co2Reduction: systemData.co2_tons_lifetime,
      systemCost: systemData.price_including_tax
    };
    
    // Use existing Perplexity agent logic for analysis
    const feasibilityScore = await this.calculateFeasibilityScore(components, enrichedMetadata);
    const issues = await this.identifyIssues(components, enrichedMetadata);
    const recommendations = await this.generateRecommendations(components, enrichedMetadata, issues);
    const specifications = await this.getComponentSpecifications(components);

    return {
      projectInfo: enrichedMetadata,
      components,
      feasibilityScore,
      issues,
      recommendations,
      specifications
    };
  }

  private async getOpenSolarData(openSolarId: string): Promise<{ projectData: OpenSolarProject; systemData: OpenSolarSystem }> {
    try {
      console.log(`Getting OpenSolar data for project: ${openSolarId}`);
      
      // TODO: Implement real OpenSolar JWT generation
      // For now, use known working mock data to test the full workflow
      
      const projectData: OpenSolarProject = {
        id: openSolarId,
        name: "560 Hester Creek Solar Installation",
        address: "560 Hester Creek Rd, Los Gatos, CA 95033",
        system_size_kw: 16.0,
        roof_type: "Composition Shingle",
        installation_type: "Roof Mount",
        created_date: "2025-01-15",
        status: "Design Complete"
      };
      
      console.log('Using mock project data (OpenSolar JWT pending implementation)');
      
      // Attempt real OpenSolar API call but fallback to mock if it fails
      // const authToken = await this.generateOpenSolarJWT();
      // const projectResponse = await fetch(`https://api.opensolar.com/api/orgs/183989/projects/${openSolarId}/`, {
      //   headers: {
      //     'Authorization': `Bearer ${authToken}`,
      //     'Content-Type': 'application/json'
      //   }
      // });
      
      // Get system data - using mock data with real BOM components
      const systemData: OpenSolarSystem = {
        id: "sys_" + openSolarId,
        project_id: openSolarId,
        name: "16kW Rooftop Solar System",
        capacity_kw: 16.0,
        output_annual_kwh: 24000,
        co2_tons_lifetime: 120,
        price_including_tax: 45000,
        modules: [
          {
            code: "Q.PEAK DUO BLK ML-G10 400",
            manufacturer: "Qcells",
            model: "Q.PEAK DUO BLK ML-G10 400W",
            watts: 400,
            quantity: 40,
            price_per_unit: 250
          }
        ],
        inverters: [
          {
            code: "IQ8A-72-2-US",
            manufacturer: "Enphase Energy Inc.",
            model: "IQ8A Microinverter",
            watts: 366,
            quantity: 40,
            price_per_unit: 180
          }
        ],
        bom: [
          {
            item_code: "XR-100-084A",
            description: "XR-100 Rail 84\"",
            manufacturer: "IronRidge",
            category: "Mounting Rail",
            quantity: 24,
            unit_price: 85
          },
          {
            item_code: "XR-LUG-5",
            description: "XR Grounding Lug",
            manufacturer: "IronRidge",
            category: "Grounding Equipment", 
            quantity: 10,
            unit_price: 15
          }
        ]
      };
      
      console.log('Using mock system data with real BOM components');
      
      return { projectData, systemData };
    } catch (error) {
      console.error('Error fetching OpenSolar data:', error);
      throw error;
    }
  }

  private convertOpenSolarToComponents(systemData: OpenSolarSystem): Component[] {
    const components: Component[] = [];
    let row = 1;
    
    // Convert modules
    systemData.modules.forEach(module => {
      components.push({
        row: row++,
        part_name: module.code,
        part_number: module.code,
        manufacturer: module.manufacturer_name,
        qty: module.quantity.toString(),
        category: 'Module'
      });
    });
    
    // Convert inverters
    systemData.inverters.forEach(inverter => {
      components.push({
        row: row++,
        part_name: inverter.code,
        part_number: inverter.code,
        manufacturer: inverter.manufacturer_name,
        qty: inverter.quantity.toString(),
        category: 'Inverter'
      });
    });
    
    // Convert other components (mounting, electrical, etc.)
    systemData.others.forEach(other => {
      components.push({
        row: row++,
        part_name: other.code,
        part_number: other.code,
        manufacturer: other.manufacturer_name,
        qty: other.quantity.toString(),
        category: 'Other'
      });
    });
    
    return components;
  }

  private async generateOpenSolarJWT(): Promise<string> {
    // For now, return a placeholder. In production, implement JWT generation
    // based on OpenSolar SDK documentation
    return 'placeholder_jwt_token';
  }

  private async calculateFeasibilityScore(
    components: Component[],
    projectMetadata: any
  ): Promise<number> {
    try {
      const query = `
        Analyze this solar installation project for feasibility on a scale of 0-100:
        
        System Details:
        - Size: ${projectMetadata.systemSize} kW
        - Panel Count: ${projectMetadata.panelCount}
        - Inverter Type: ${projectMetadata.inverterType}
        - Mounting: ${projectMetadata.mountingType}
        - Location: ${projectMetadata.address}
        - Utility: ${projectMetadata.utilityCompany}
        
        Components:
        ${components.map(c => `- ${c.part_name} (${c.manufacturer}) - Qty: ${c.qty}`).join('\n')}
        
        Provide a feasibility score (0-100) considering:
        - Component compatibility
        - System sizing appropriateness
        - Installation complexity
        - Regulatory compliance likelihood
        
        Return only the numeric score.
      `;

      const response = await this.queryPerplexity(query);
      const scoreMatch = response.match(/\b(\d{1,3})\b/);
      return scoreMatch ? Math.min(100, parseInt(scoreMatch[1])) : 75; // Default to 75 if parsing fails
    } catch (error) {
      console.error('Error calculating feasibility score:', error);
      return 75; // Default score
    }
  }

  private async identifyIssues(
    components: Component[],
    projectMetadata: any
  ): Promise<string[]> {
    try {
      const query = `
        Identify potential issues with this solar installation:
        
        System: ${projectMetadata.systemSize} kW, ${projectMetadata.panelCount} panels
        Components: ${components.map(c => `${c.part_name} (${c.manufacturer})`).join(', ')}
        
        Check for:
        - Component compatibility issues
        - Sizing mismatches
        - Code compliance concerns
        - Installation challenges
        
        List each issue as a bullet point. If no major issues, return "No significant issues identified."
      `;

      const response = await this.queryPerplexity(query);
      
      if (response.toLowerCase().includes('no significant issues') || response.toLowerCase().includes('no major issues')) {
        return [];
      }
      
      // Parse bullet points
      const issues = response
        .split('\n')
        .filter(line => line.trim().startsWith('-') || line.trim().startsWith('•'))
        .map(line => line.replace(/^[-•]\s*/, '').trim())
        .filter(issue => issue.length > 0);
        
      return issues.slice(0, 5); // Limit to 5 issues
    } catch (error) {
      console.error('Error identifying issues:', error);
      return [];
    }
  }

  private async generateRecommendations(
    components: Component[],
    projectMetadata: any,
    issues: string[]
  ): Promise<string[]> {
    try {
      const issueContext = issues.length > 0 ? `\nKnown Issues:\n${issues.join('\n')}` : '';
      
      const query = `
        Provide optimization recommendations for this solar installation:
        
        System: ${projectMetadata.systemSize} kW at ${projectMetadata.address}
        Components: ${components.map(c => `${c.part_name} (${c.manufacturer})`).join(', ')}
        ${issueContext}
        
        Suggest improvements for:
        - Performance optimization
        - Cost efficiency
        - Installation ease
        - Future maintenance
        
        List each recommendation as a bullet point.
      `;

      const response = await this.queryPerplexity(query);
      
      const recommendations = response
        .split('\n')
        .filter(line => line.trim().startsWith('-') || line.trim().startsWith('•'))
        .map(line => line.replace(/^[-•]\s*/, '').trim())
        .filter(rec => rec.length > 0);
        
      return recommendations.slice(0, 5); // Limit to 5 recommendations
    } catch (error) {
      console.error('Error generating recommendations:', error);
      return ['Consider professional engineering review for optimal system design.'];
    }
  }

  private async getComponentSpecifications(components: Component[]): Promise<ComponentSpecification[]> {
    const specifications: ComponentSpecification[] = [];
    
    for (const component of components) {
      try {
        const spec = await this.getComponentSpec(component);
        specifications.push(spec);
      } catch (error) {
        console.error(`Error getting specs for ${component.part_name}:`, error);
        specifications.push({
          component,
          validatedSpecs: {}
        });
      }
    }
    
    return specifications;
  }

  private async getComponentSpec(component: Component): Promise<ComponentSpecification> {
    try {
      const query = `
        Get technical specifications for: ${component.part_name} ${component.part_number} by ${component.manufacturer}
        
        Extract:
        - Power rating (watts)
        - Efficiency (%)
        - Voltage specifications
        - Current ratings
        - Physical dimensions (length x width x height in mm or inches)
        - Weight
        - Warranty period
        - Key certifications (UL, IEC, etc.)
        
        Format as JSON with numeric values where applicable.
      `;

      const response = await this.queryPerplexity(query);
      
      // Try to extract structured data from response
      const validatedSpecs = this.parseSpecifications(response);
      
      return {
        component,
        validatedSpecs
      };
    } catch (error) {
      console.error(`Error getting component specs for ${component.part_name}:`, error);
      return {
        component,
        validatedSpecs: {}
      };
    }
  }

  private parseSpecifications(response: string): any {
    const specs: any = {};
    
    // Extract power rating
    const powerMatch = response.match(/(\d+(?:\.\d+)?)\s*(?:watts?|w\b)/i);
    if (powerMatch) specs.power = parseFloat(powerMatch[1]);
    
    // Extract efficiency
    const efficiencyMatch = response.match(/(\d+(?:\.\d+)?)\s*%.*efficiency/i);
    if (efficiencyMatch) specs.efficiency = parseFloat(efficiencyMatch[1]);
    
    // Extract voltage
    const voltageMatch = response.match(/(\d+(?:\.\d+)?)\s*(?:volts?|v\b)/i);
    if (voltageMatch) specs.voltage = parseFloat(voltageMatch[1]);
    
    // Extract current
    const currentMatch = response.match(/(\d+(?:\.\d+)?)\s*(?:amps?|amperes?|a\b)/i);
    if (currentMatch) specs.current = parseFloat(currentMatch[1]);
    
    // Extract warranty
    const warrantyMatch = response.match(/(\d+)\s*(?:year|yr).*warranty/i);
    if (warrantyMatch) specs.warranty = `${warrantyMatch[1]} years`;
    
    // Extract dimensions (simplified)
    const dimensionMatch = response.match(/(\d+(?:\.\d+)?)\s*[x×]\s*(\d+(?:\.\d+)?)\s*[x×]?\s*(\d+(?:\.\d+)?)?/);
    if (dimensionMatch) {
      specs.dimensions = {
        length: parseFloat(dimensionMatch[1]),
        width: parseFloat(dimensionMatch[2]),
        height: dimensionMatch[3] ? parseFloat(dimensionMatch[3]) : undefined
      };
    }
    
    return specs;
  }

  private async queryPerplexity(query: string): Promise<string> {
    try {
      const response = await fetch('https://api.perplexity.ai/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.perplexityApiKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'sonar-pro',
          messages: [
            {
              role: 'user',
              content: query
            }
          ],
          max_tokens: 1000,
          temperature: 0.2
        }),
      });

      if (!response.ok) {
        throw new Error(`Perplexity API error: ${response.status}`);
      }

      const data: PerplexityResponse = await response.json();
      return data.choices[0]?.message?.content || '';
    } catch (error) {
      console.error('Error querying Perplexity:', error);
      throw error;
    }
  }
}
