export interface Component {
  row: number;
  part_name: string;
  part_number: string;
  manufacturer: string;
  qty: string;
  category: string;
}

export interface ProjectMetadata {
  projectName: string;
  address: string;
  systemSize: number;
  panelCount: number;
  inverterType: string;
  mountingType: string;
  utilityCompany: string;
  jurisdictionName: string;
  customerInfo: {
    name: string;
    email: string;
    phone: string;
  };
}

export interface SystemConfiguration {
  projectInfo: ProjectMetadata;
  components: Component[];
  feasibilityScore: number;
  issues: string[];
  recommendations: string[];
  specifications: ComponentSpecification[];
}

export interface ComponentSpecification {
  component: Component;
  specSheetUrl?: string;
  specSheetPages?: number;
  validatedSpecs: {
    efficiency?: number;
    power?: number;
    voltage?: number;
    current?: number;
    dimensions?: {
      length: number;
      width: number;
      height: number;
    };
    weight?: number;
    warranty?: string;
    certifications?: string[];
  };
}

export interface PermitPacket {
  projectId: string;
  applicationForm: string; // URL to generated application
  siteLayout: string; // URL to site layout diagram
  electricalDiagram: string; // URL to electrical one-line diagram
  specifications: string; // URL to combined spec sheets PDF
  structuralCalculations?: string; // URL if needed
  interconnectionApplication?: string; // URL if needed
  metadata: {
    generatedAt: string;
    totalPages: number;
    packageSize: string;
  };
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  uploadUrls?: {
    permit?: string;
    bom?: string;
  };
}
