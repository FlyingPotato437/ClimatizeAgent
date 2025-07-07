// API client for the Climatize Solar Agent System

const API_BASE_URL = 'http://localhost:8000/api/v1';

export interface ProjectRequest {
  project_name: string;
  address: string;
  system_size_kw: number;
  project_type: string;
  contact_email?: string;
  description?: string;
}

export interface WorkflowResponse {
  project_id: string;
  workflow_status: string;
  success: boolean;
  processing_time_seconds: number;
  agent_results: {
    research?: any;
    design?: any;
    site_qualification?: any;
    permitting?: any;
  };
  final_package: any;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  ai_service_status: string;
  orchestrator_status: string;
  agents_status: Record<string, string>;
}

export interface AgentStatusResponse {
  research_agent: string;
  design_agent: string;
  site_qualification_agent: string;
  permitting_agent: string;
  orchestrator: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error ${response.status}: ${error}`);
    }

    return response.json();
  }

  // Health check
  async healthCheck(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/health');
  }

  // Agent status
  async getAgentStatus(): Promise<AgentStatusResponse> {
    return this.request<AgentStatusResponse>('/agents/status');
  }

  // Run complete workflow
  async runProjectWorkflow(data: ProjectRequest): Promise<WorkflowResponse> {
    return this.request<WorkflowResponse>('/projects/workflow', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  // Run individual agents
  async runResearchAgent(data: ProjectRequest): Promise<any> {
    return this.request('/projects/research', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async runDesignAgent(data: ProjectRequest): Promise<any> {
    return this.request('/projects/design', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async runSiteQualificationAgent(data: ProjectRequest): Promise<any> {
    return this.request('/projects/site-qualification', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async runPermittingAgent(data: ProjectRequest): Promise<any> {
    return this.request('/projects/permitting', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }
}

export const api = new ApiClient();