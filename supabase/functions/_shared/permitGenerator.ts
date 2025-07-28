import { SystemConfiguration, PermitPacket, Component } from './types.ts';

export class PermitGenerator {
  private openSolarClientCode: string;
  private openSolarUsername: string;
  private openSolarPassword: string;
  private exaApiKey: string;
  private openaiApiKey: string;

  constructor(clientCode: string, username: string, password: string, exaApiKey: string, openaiApiKey: string) {
    this.openSolarClientCode = clientCode;
    this.openSolarUsername = username;
    this.openSolarPassword = password;
    this.exaApiKey = exaApiKey;
    this.openaiApiKey = openaiApiKey;
  }

  async generatePermitPacket(
    systemConfig: SystemConfiguration,
    projectId: string
  ): Promise<PermitPacket> {
    console.log('Starting smart permit packet generation for project:', projectId);

    try {
      // Step 1: Generate real component specifications using Exa.ai + OpenAI (smart_permit_generator logic)
      const realSpecifications = await this.generateRealSpecificationsPDF(systemConfig, projectId);
      
      // Step 2: Generate application form with real project data
      const applicationForm = await this.generateApplicationForm(systemConfig, projectId);
      
      // Step 3: Generate site layout using OpenSolar API
      const siteLayout = await this.generateSiteLayout(systemConfig, projectId);
      
      // Step 4: Generate electrical diagram
      const electricalDiagram = await this.generateElectricalDiagram(systemConfig, projectId);

      // Optional documents based on system requirements
      let structuralCalculations: string | undefined;
      let interconnectionApplication: string | undefined;

      if (this.requiresStructuralCalculations(systemConfig)) {
        structuralCalculations = await this.generateStructuralCalculations(systemConfig, projectId);
      }

      if (this.requiresInterconnectionApplication(systemConfig)) {
        interconnectionApplication = await this.generateInterconnectionApplication(systemConfig, projectId);
      }

      return {
        projectId,
        applicationForm,
        siteLayout,
        electricalDiagram,
        specifications: realSpecifications,
        structuralCalculations,
        interconnectionApplication,
        metadata: {
          generatedAt: new Date().toISOString(),
          totalPages: await this.calculateTotalPages(),
          packageSize: '15.2 MB' // Would calculate actual size
        }
      };

    } catch (error) {
      console.error('Error generating permit packet:', error);
      throw new Error(`Failed to generate permit packet: ${error.message}`);
    }
  }

  private async generateApplicationForm(systemConfig: SystemConfiguration, projectId: string): Promise<string> {
    console.log('Generating permit application form...');
    
    // Create permit application form based on project info
    const formData = {
      projectInfo: systemConfig.projectInfo,
      systemSize: systemConfig.projectInfo.systemSize,
      panelCount: systemConfig.projectInfo.panelCount,
      inverterType: systemConfig.projectInfo.inverterType,
      mountingType: systemConfig.projectInfo.mountingType,
      utilityCompany: systemConfig.projectInfo.utilityCompany,
      customerInfo: systemConfig.projectInfo.customerInfo,
      jurisdiction: systemConfig.projectInfo.jurisdictionName
    };

    // Generate PDF using a template (would integrate with a PDF generation library)
    const pdfContent = await this.createPDFFromTemplate('permit_application', formData);
    
    // Return storage URL (placeholder - would upload to Supabase Storage)
    return `storage/permit-packets/${projectId}/application_form.pdf`;
  }

  private async generateSiteLayout(systemConfig: SystemConfiguration, projectId: string): Promise<string> {
    console.log('Generating site layout diagram...');
    
    // Use OpenSolar API to generate site layout
    try {
      const layoutData = await this.callOpenSolarAPI('generate_layout', {
        address: systemConfig.projectInfo.address,
        systemSize: systemConfig.projectInfo.systemSize,
        panelCount: systemConfig.projectInfo.panelCount,
        mountingType: systemConfig.projectInfo.mountingType,
        components: systemConfig.components
      });

      // Process and save layout diagram
      const layoutUrl = await this.saveLayoutDiagram(layoutData, projectId);
      return layoutUrl;

    } catch (error) {
      console.error('Error generating site layout:', error);
      // Fallback to template-based layout
      return await this.generateTemplateLayout(systemConfig, projectId);
    }
  }

  private async generateElectricalDiagram(systemConfig: SystemConfiguration, projectId: string): Promise<string> {
    console.log('Generating electrical one-line diagram...');
    
    // Generate electrical diagram based on components
    const electricalData = {
      panels: systemConfig.components.filter(c => c.category?.toLowerCase().includes('panel')),
      inverters: systemConfig.components.filter(c => c.category?.toLowerCase().includes('inverter')),
      mounting: systemConfig.components.filter(c => c.category?.toLowerCase().includes('mount')),
      electrical: systemConfig.components.filter(c => 
        c.category?.toLowerCase().includes('electrical') ||
        c.category?.toLowerCase().includes('conduit') ||
        c.category?.toLowerCase().includes('disconnect')
      ),
      systemVoltage: this.calculateSystemVoltage(systemConfig),
      systemCurrent: this.calculateSystemCurrent(systemConfig)
    };

    const diagramContent = await this.createElectricalDiagram(electricalData);
    
    // Return storage URL
    return `storage/permit-packets/${projectId}/electrical_diagram.pdf`;
  }

  private async generateRealSpecificationsPDF(systemConfig: SystemConfiguration, projectId: string): Promise<string> {
    console.log('Generating REAL specifications PDF using smart permit generator logic...');
    
    try {
      // Use Exa.ai to find real manufacturer spec sheets for each component
      const realSpecSheets = [];
      
      for (const component of systemConfig.components) {
        try {
          const specUrl = await this.findRealSpecSheet(component);
          if (specUrl) {
            const specContent = await this.downloadAndValidateSpec(specUrl, component);
            if (specContent) {
              realSpecSheets.push({
                component,
                content: specContent,
                url: specUrl
              });
              console.log(`✅ Found REAL spec for ${component.part_name}: ${specUrl}`);
            }
          }
        } catch (error) {
          console.warn(`Could not find real spec for ${component.part_name}:`, error);
        }
      }

      if (realSpecSheets.length === 0) {
        throw new Error('No real manufacturer specifications found');
      }

      // Combine real PDFs using the validated specs
      const combinedPDF = await this.combineRealPDFs(realSpecSheets);
      
      console.log(`Generated specifications PDF with ${realSpecSheets.length} real manufacturer spec sheets`);
      
      // Return storage URL
      return `storage/permit-packets/${projectId}/real_specifications.pdf`;
    } catch (error) {
      console.error('Error generating real specifications:', error);
      // Fallback to basic specifications if real specs fail
      return await this.generateBasicSpecificationsPDF(systemConfig, projectId);
    }
  }

  private async generateBasicSpecificationsPDF(systemConfig: SystemConfiguration, projectId: string): Promise<string> {
    console.log('Generating basic specifications PDF as fallback...');
    
    // Combine all component spec sheets into one PDF
    const specSheets = [];
    
    for (const spec of systemConfig.specifications) {
      if (spec.specSheetUrl) {
        try {
          const specContent = await this.downloadSpecSheet(spec.specSheetUrl);
          specSheets.push({
            component: spec.component,
            content: specContent
          });
        } catch (error) {
          console.warn(`Could not download spec sheet for ${spec.component.part_name}:`, error);
        }
      }
    }

    // Combine PDFs
    const combinedPDF = await this.combinePDFs(specSheets);
    
    // Return storage URL
    return `storage/permit-packets/${projectId}/specifications.pdf`;
  }

  private async generateStructuralCalculations(systemConfig: SystemConfiguration, projectId: string): Promise<string> {
    console.log('Generating structural calculations...');
    
    // Calculate structural loads based on panel layout and mounting
    const structuralData = {
      panelWeight: this.calculateTotalPanelWeight(systemConfig),
      windLoad: this.calculateWindLoad(systemConfig),
      snowLoad: this.calculateSnowLoad(systemConfig),
      mountingType: systemConfig.projectInfo.mountingType,
      roofType: 'composition_shingle' // Would be determined from project data
    };

    const calculationsContent = await this.createStructuralCalculations(structuralData);
    
    // Return storage URL
    return `storage/permit-packets/${projectId}/structural_calculations.pdf`;
  }

  private async generateInterconnectionApplication(systemConfig: SystemConfiguration, projectId: string): Promise<string> {
    console.log('Generating utility interconnection application...');
    
    const interconnectionData = {
      utilityCompany: systemConfig.projectInfo.utilityCompany,
      systemSize: systemConfig.projectInfo.systemSize,
      inverterSpecs: systemConfig.specifications.filter(s => 
        s.component.category?.toLowerCase().includes('inverter')
      ),
      customerInfo: systemConfig.projectInfo.customerInfo,
      address: systemConfig.projectInfo.address
    };

    const applicationContent = await this.createInterconnectionApplication(interconnectionData);
    
    // Return storage URL
    return `storage/permit-packets/${projectId}/interconnection_application.pdf`;
  }

  // Helper methods
  private requiresStructuralCalculations(systemConfig: SystemConfiguration): boolean {
    // Determine if structural calculations are needed based on system size, mounting type, etc.
    return systemConfig.projectInfo.systemSize > 10 || // Systems > 10kW typically need structural
           systemConfig.projectInfo.mountingType.toLowerCase().includes('ground') ||
           systemConfig.projectInfo.mountingType.toLowerCase().includes('ballast');
  }

  private requiresInterconnectionApplication(systemConfig: SystemConfiguration): boolean {
    // Determine if utility interconnection application is needed
    return systemConfig.projectInfo.systemSize > 5; // Systems > 5kW typically need interconnection
  }

  private async calculateTotalPages(): Promise<number> {
    // Calculate total pages across all documents
    return 25; // Placeholder
  }

  private calculateSystemVoltage(systemConfig: SystemConfiguration): number {
    // Calculate system DC voltage based on panel configuration
    const panelVoltage = 40; // Would extract from panel specs
    const seriesCount = Math.ceil(systemConfig.projectInfo.panelCount / 2);
    return panelVoltage * seriesCount;
  }

  private calculateSystemCurrent(systemConfig: SystemConfiguration): number {
    // Calculate system DC current
    const panelCurrent = 10; // Would extract from panel specs
    const parallelStrings = 2; // Would calculate based on layout
    return panelCurrent * parallelStrings;
  }

  private calculateTotalPanelWeight(systemConfig: SystemConfiguration): number {
    // Calculate total weight of all panels
    const panelWeight = 40; // Would extract from panel specs (lbs)
    return panelWeight * systemConfig.projectInfo.panelCount;
  }

  private calculateWindLoad(systemConfig: SystemConfiguration): number {
    // Calculate wind load based on location and panel tilt
    return 30; // PSF - would use actual wind load calculations
  }

  private calculateSnowLoad(systemConfig: SystemConfiguration): number {
    // Calculate snow load based on location
    return 25; // PSF - would use actual snow load data for location
  }

  // Placeholder methods for actual implementations
  private async createPDFFromTemplate(template: string, data: any): Promise<Uint8Array> {
    // Would use a PDF generation library like jsPDF or integrate with document generation service
    return new Uint8Array();
  }

  private async callOpenSolarAPI(endpoint: string, data: any): Promise<any> {
    // Would integrate with OpenSolar API using provided credentials
    const response = await fetch(`https://api.opensolar.com/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${await this.generateOpenSolarJWT()}`
      },
      body: JSON.stringify(data)
    });

    if (!response.ok) {
      throw new Error(`OpenSolar API error: ${response.status}`);
    }

    return response.json();
  }

  private async generateOpenSolarJWT(): Promise<string> {
    // Generate JWT for OpenSolar API authentication
    // Would implement JWT generation as per OpenSolar documentation
    return 'placeholder_jwt_token';
  }

  private async saveLayoutDiagram(layoutData: any, projectId: string): Promise<string> {
    // Save layout diagram to Supabase Storage
    return `storage/permit-packets/${projectId}/site_layout.pdf`;
  }

  private async generateTemplateLayout(systemConfig: SystemConfiguration, projectId: string): Promise<string> {
    // Generate basic layout using template
    return `storage/permit-packets/${projectId}/site_layout.pdf`;
  }

  private async createElectricalDiagram(electricalData: any): Promise<Uint8Array> {
    // Create electrical one-line diagram
    return new Uint8Array();
  }

  private async downloadSpecSheet(url: string): Promise<Uint8Array> {
    try {
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to download spec sheet: ${response.status}`);
      }
      return new Uint8Array(await response.arrayBuffer());
    } catch (error) {
      console.error('Error downloading spec sheet:', error);
      throw error;
    }
  }

  // Smart Permit Generator Exa.ai Integration Methods
  private async findRealSpecSheet(component: Component): Promise<string | null> {
    try {
      console.log(`Searching for real spec sheet: ${component.part_name} (${component.manufacturer})`);
      
      // Generate specific search queries based on component type
      const queries = this.generateExaQueries(component);
      
      for (const query of queries) {
        try {
          const response = await fetch('https://api.exa.ai/search', {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${this.exaApiKey}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              query,
              type: 'keyword',
              numResults: 5,
              includeDomains: this.getManufacturerDomains(component.manufacturer),
              contents: {
                text: true
              }
            })
          });
          
          if (!response.ok) {
            console.error(`Exa API error: ${response.status}`);
            continue;
          }
          
          const data = await response.json();
          
          // Filter and validate results using LLM
          for (const result of data.results) {
            if (await this.validateSpecSheetURL(result.url, component)) {
              return result.url;
            }
          }
        } catch (error) {
          console.error(`Error searching with query "${query}":`, error);
        }
      }
      
      return null;
    } catch (error) {
      console.error(`Error finding spec sheet for ${component.part_name}:`, error);
      return null;
    }
  }
  
  private generateExaQueries(component: Component): string[] {
    const queries: string[] = [];
    const { part_number, part_name, manufacturer } = component;
    
    // Component-specific search strategies (from smart_permit_generator.py)
    if (component.category?.toLowerCase().includes('module') || component.category?.toLowerCase().includes('panel')) {
      queries.push(`${part_number} solar panel datasheet PDF filetype:pdf`);
      queries.push(`${manufacturer} ${part_number} specification sheet`);
      queries.push(`${part_name} ${manufacturer} datasheet`);
    } else if (component.category?.toLowerCase().includes('inverter')) {
      queries.push(`${part_number} ${manufacturer} microinverter datasheet PDF`);
      queries.push(`${manufacturer} ${part_number} specification`);
    } else {
      queries.push(`${part_number} ${manufacturer} datasheet PDF`);
      queries.push(`${manufacturer} ${part_name} specification sheet`);
    }
    
    return queries;
  }
  
  private getManufacturerDomains(manufacturer: string): string[] {
    // Vendor domain mapping from smart_permit_generator.py
    const domainMap: { [key: string]: string[] } = {
      'Qcells': ['qcells.com'],
      'Enphase Energy Inc.': ['enphase.com'],
      'Enphase': ['enphase.com'],
      'IronRidge': ['ironridge.com'],
      'SolarEdge': ['solaredge.com'],
      'Canadian Solar': ['canadiansolar.com']
    };
    
    return domainMap[manufacturer] || [];
  }
  
  private async validateSpecSheetURL(url: string, component: Component): Promise<boolean> {
    try {
      // Use OpenAI to validate if this is a real spec sheet (not catalog)
      const response = await fetch('https://api.openai.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${this.openaiApiKey}`,
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
      
      if (!response.ok) {
        console.error('OpenAI validation failed:', response.status);
        return false;
      }
      
      const data = await response.json();
      const answer = data.choices[0]?.message?.content?.trim().toUpperCase();
      
      return answer === 'YES';
    } catch (error) {
      console.error('Error validating spec sheet URL:', error);
      return false;
    }
  }
  
  private async downloadAndValidateSpec(url: string, component: Component): Promise<Uint8Array | null> {
    try {
      const response = await fetch(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
      });
      
      if (!response.ok) {
        console.error(`Failed to download spec: ${response.status}`);
        return null;
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType?.includes('pdf')) {
        console.warn(`URL is not a PDF: ${url}`);
        return null;
      }
      
      const arrayBuffer = await response.arrayBuffer();
      const content = new Uint8Array(arrayBuffer);
      
      // Validate file size (max 10MB per smart_permit_generator.py)
      if (content.length > 10 * 1024 * 1024) {
        console.warn(`Spec sheet too large (${content.length} bytes): ${url}`);
        return null;
      }
      
      return content;
    } catch (error) {
      console.error(`Error downloading spec from ${url}:`, error);
      return null;
    }
  }
  
  private async combineRealPDFs(specSheets: Array<{ component: Component; content: Uint8Array; url: string }>): Promise<Uint8Array> {
    // Combine multiple real PDFs into one
    // For now, return the first PDF as a placeholder
    // In production, would use pdf-lib to properly combine PDFs
    if (specSheets.length > 0) {
      console.log(`Combining ${specSheets.length} real specification PDFs`);
      return specSheets[0].content;
    }
    return new Uint8Array();
  }

  private async combinePDFs(specSheets: Array<{ component: Component; content: Uint8Array }>): Promise<Uint8Array> {
    // Combine multiple PDFs into one
    // Would use a PDF library like pdf-lib
    return new Uint8Array();
  }

  private async createStructuralCalculations(structuralData: any): Promise<Uint8Array> {
    // Generate structural calculation document
    return new Uint8Array();
  }

  private async createInterconnectionApplication(interconnectionData: any): Promise<Uint8Array> {
    // Generate utility interconnection application
    return new Uint8Array();
  }
}
