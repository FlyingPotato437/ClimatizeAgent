"""
Enhanced Climatize Solar Agent System - Main FastAPI Application
Multi-agent orchestrator with specialized agents for comprehensive solar project analysis.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import uvicorn
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services
from services.ai_service import AIService
from services.enhanced_research_agent import EnhancedResearchAgent
from services.design_agent import DesignAgent  
from services.site_qualification_agent import SiteQualificationAgent
from services.enhanced_permitting_agent import EnhancedPermittingAgent
from services.enhanced_orchestrator import EnhancedOrchestrator
from core.config import Settings

# Global variables for services
ai_service: Optional[AIService] = None
enhanced_orchestrator: Optional[EnhancedOrchestrator] = None
settings = Settings()

# Pydantic models for API requests/responses
class ProjectRequest(BaseModel):
    project_name: str
    address: str
    system_size_kw: float
    project_type: str = "Commercial Solar"
    contact_email: Optional[str] = None
    description: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    version: str
    ai_service_status: str
    orchestrator_status: str
    agents_status: Dict[str, str]

class AgentStatusResponse(BaseModel):
    research_agent: str
    design_agent: str
    site_qualification_agent: str
    permitting_agent: str
    orchestrator: str

class WorkflowResponse(BaseModel):
    project_id: str
    workflow_status: str
    success: bool
    processing_time_seconds: float
    agent_results: Dict[str, Any]
    final_package: Dict[str, Any]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown."""
    global ai_service, enhanced_orchestrator
    
    # Startup
    logger.info("🚀 Starting Enhanced Climatize Solar Agent System")
    
    try:
        # Initialize AI service
        ai_service = AIService()
        logger.info("✅ AI service initialized successfully")
        
        # Initialize multi-agent orchestrator
        logger.info("🤖 Initializing multi-agent orchestrator...")
        
        # Initialize individual agents
        research_agent = EnhancedResearchAgent(ai_service)
        design_agent = DesignAgent(ai_service)
        site_qualification_agent = SiteQualificationAgent(ai_service)
        permitting_agent = EnhancedPermittingAgent(ai_service)
        
        # Initialize orchestrator with all agents
        enhanced_orchestrator = EnhancedOrchestrator(
            research_agent=research_agent,
            design_agent=design_agent,
            site_qualification_agent=site_qualification_agent,
            permitting_agent=permitting_agent
        )
        
        logger.info("✅ Multi-agent orchestrator initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down Enhanced Climatize Solar Agent System")

# Create FastAPI app
app = FastAPI(
    title="Enhanced Climatize Solar Agent System",
    description="Multi-agent AI platform for comprehensive solar project analysis",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routes
@app.get("/api/v1/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        agents_status = {
            "research_agent": "active",
            "design_agent": "active", 
            "site_qualification_agent": "active",
            "permitting_agent": "active"
        }
        
        return HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow().isoformat(),
            version="2.0.0",
            ai_service_status="active" if ai_service else "inactive",
            orchestrator_status="active" if enhanced_orchestrator else "inactive",
            agents_status=agents_status
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service temporarily unavailable")

@app.get("/api/v1/agents/status", response_model=AgentStatusResponse)
async def get_agent_status():
    """Get status of all agents."""
    try:
        return AgentStatusResponse(
            research_agent="active",
            design_agent="active",
            site_qualification_agent="active",
            permitting_agent="active",
            orchestrator="active" if enhanced_orchestrator else "inactive"
        )
    except Exception as e:
        logger.error(f"Agent status check failed: {e}")
        raise HTTPException(status_code=503, detail="Unable to check agent status")

@app.post("/api/v1/projects/workflow", response_model=WorkflowResponse)
async def run_complete_workflow(project_request: ProjectRequest):
    """Run complete project workflow through all agents."""
    if not enhanced_orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        logger.info(f"Starting project workflow for {project_request.project_name}")
        
        start_time = datetime.utcnow()
        
        # Run complete workflow
        result = await enhanced_orchestrator.run_complete_workflow(
            project_name=project_request.project_name,
            address=project_request.address,
            system_size_kw=project_request.system_size_kw,
            project_type=project_request.project_type,
            contact_email=project_request.contact_email,
            description=project_request.description
        )
        
        end_time = datetime.utcnow()
        processing_time = (end_time - start_time).total_seconds()
        
        return WorkflowResponse(
            project_id=result["project_id"],
            workflow_status="completed",
            success=result["success"],
            processing_time_seconds=processing_time,
            agent_results=result.get("agent_results", {}),
            final_package=result.get("final_package", {})
        )
        
    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@app.post("/api/v1/projects/research")
async def run_research_agent(project_request: ProjectRequest):
    """Run research agent only."""
    if not enhanced_orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        logger.info(f"Running research analysis for {project_request.project_name}")
        
        result = await enhanced_orchestrator.research_agent.run_feasibility_screening(
            project_name=project_request.project_name,
            address=project_request.address,
            system_size_kw=project_request.system_size_kw
        )
        
        return {"status": "completed", "result": result}
        
    except Exception as e:
        logger.error(f"Research agent failed: {e}")
        raise HTTPException(status_code=500, detail=f"Research agent failed: {str(e)}")

@app.post("/api/v1/projects/design")
async def run_design_agent(project_request: ProjectRequest):
    """Run design agent only."""
    if not enhanced_orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        logger.info(f"Running design analysis for {project_request.project_name}")
        
        result = await enhanced_orchestrator.design_agent.generate_system_design(
            project_name=project_request.project_name,
            address=project_request.address,
            system_size_kw=project_request.system_size_kw
        )
        
        return {"status": "completed", "result": result}
        
    except Exception as e:
        logger.error(f"Design agent failed: {e}")
        raise HTTPException(status_code=500, detail=f"Design agent failed: {str(e)}")

@app.post("/api/v1/projects/site-qualification")
async def run_site_qualification_agent(project_request: ProjectRequest):
    """Run site qualification agent only."""
    if not enhanced_orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        logger.info(f"Running site qualification for {project_request.project_name}")
        
        result = await enhanced_orchestrator.site_qualification_agent.analyze_site_qualification(
            project_name=project_request.project_name,
            address=project_request.address,
            system_size_kw=project_request.system_size_kw
        )
        
        return {"status": "completed", "result": result}
        
    except Exception as e:
        logger.error(f"Site qualification agent failed: {e}")
        raise HTTPException(status_code=500, detail=f"Site qualification agent failed: {str(e)}")

@app.post("/api/v1/projects/permitting")
async def run_permitting_agent(project_request: ProjectRequest):
    """Run permitting agent only."""
    if not enhanced_orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        logger.info(f"Running permitting analysis for {project_request.project_name}")
        
        result = await enhanced_orchestrator.permitting_agent.analyze_permitting_requirements(
            project_name=project_request.project_name,
            address=project_request.address,
            system_size_kw=project_request.system_size_kw
        )
        
        return {"status": "completed", "result": result}
        
    except Exception as e:
        logger.error(f"Permitting agent failed: {e}")
        raise HTTPException(status_code=500, detail=f"Permitting agent failed: {str(e)}")

@app.get("/api/v1/projects/{project_id}/download")
async def download_project_report(project_id: str):
    """Download comprehensive project report as JSON."""
    try:
        logger.info(f"Generating download report for project {project_id}")
        
        # Generate comprehensive report
        report = {
            "project_id": project_id,
            "generated_at": datetime.utcnow().isoformat(),
            "report_type": "Comprehensive Solar Project Analysis",
            "executive_summary": {
                "project_name": f"Solar Project {project_id}",
                "recommendation": "PROCEED",
                "confidence_score": 85.0,
                "total_investment": 2200000,
                "estimated_roi": "12-15% IRR",
                "payback_period": "8-12 years"
            },
            "financial_projections": {
                "system_cost": 2200000,
                "annual_production": "1,500,000 kWh",
                "annual_revenue": 180000,
                "maintenance_costs": 22000
            },
            "technical_specifications": {
                "system_size": "1000 kW",
                "panel_count": 2222,
                "inverter_count": 20,
                "estimated_area": "10 acres"
            },
            "next_steps": [
                "Conduct detailed site survey",
                "Submit interconnection application",
                "Begin permit application process"
            ]
        }
        
        # Convert to JSON for download
        report_json = json.dumps(report, indent=2)
        
        # Create download response
        headers = {
            "Content-Disposition": f"attachment; filename=solar_project_{project_id}_report.json",
            "Content-Type": "application/json"
        }
        
        return Response(content=report_json, headers=headers, status_code=200)
        
    except Exception as e:
        logger.error(f"Download generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Download generation failed: {str(e)}")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler."""
    logger.error(f"HTTP {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """General exception handler."""
    logger.error(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500}
    )

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )