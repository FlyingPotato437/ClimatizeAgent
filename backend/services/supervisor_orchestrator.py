"""
Climatize Solar Agent Supervisor Orchestrator
Implements the multi-agent workflow with a Supervisor coordinating 4 specialized agents in sequence.
"""
import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

# Import services and configurations
from core.config import settings
from core.database import get_db_client
from models.project_simple import UnifiedProjectModel
from services.ai_service import AIService

# Import specialized agents
from services.general_research_agent import GeneralResearchAgent
from services.engineering_design_agent import EngineeringDesignAgent
from services.site_qualification_agent import SiteQualificationAgent
from services.permitting_agent import PermittingAgent

logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    """Defines the sequential stages of the solar project workflow."""
    INITIAL_CONTEXT = "initial_context_feasibility"
    ENGINEERING_DESIGN = "engineering_design" 
    SITE_QUALIFICATION = "site_selection_qualification"
    PERMITTING = "permitting_documentation"
    COMPLETE = "workflow_complete"


class SupervisorOrchestrator:
    """
    Supervisor that orchestrates the multi-agent workflow for solar project development.
    Manages the sequential flow: Research → Design → Site Qualification → Permitting
    """
    
    def __init__(self):
        """Initialize the Supervisor with all specialized agents."""
        self.db = get_db_client()
        self.ai_service = AIService()
        
        # Initialize specialized agents
        self.general_research_agent = GeneralResearchAgent(self.ai_service)
        self.engineering_design_agent = EngineeringDesignAgent(self.ai_service)
        self.site_qualification_agent = SiteQualificationAgent(self.ai_service)
        self.permitting_agent = PermittingAgent(self.ai_service)
        
        # Workflow state tracking
        self.current_stage = WorkflowStage.INITIAL_CONTEXT
        
        logger.info("🎯 Supervisor Orchestrator initialized with 4 specialized agents")
    
    def _convert_api_data_to_unified_model(self, project_data: Dict[str, Any]) -> UnifiedProjectModel:
        """Convert simple API data to structured UnifiedProjectModel."""
        from models.project_simple import Address, SystemSpecs, Financials, RoofType
        
        # Parse address string to Address object
        address_str = project_data.get("address", "")
        address_parts = address_str.split(", ")
        
        if len(address_parts) >= 3:
            street = address_parts[0]
            city = address_parts[1]
            state_zip = address_parts[2].split(" ")
            state = state_zip[0] if len(state_zip) > 0 else "CA"
            zip_code = state_zip[1] if len(state_zip) > 1 else "95060"
        else:
            street = address_str
            city = "Santa Cruz"
            state = "CA"
            zip_code = "95060"
        
        address = Address(
            street=street,
            city=city,
            state=state,
            zip_code=zip_code
        )
        
        # Create basic system specs
        system_size_kw = project_data.get("system_size_kw", 100.0)
        system_specs = SystemSpecs(
            system_size_dc_kw=system_size_kw,
            system_size_ac_kw=system_size_kw * 0.9,  # Typical DC to AC ratio
            module_count=int(system_size_kw * 2.5),  # Approx 400W modules
            inverter_type="string",
            roof_type=RoofType.FLAT  # Default assumption
        )
        
        # Create basic financials
        financials = Financials(
            estimated_capex=system_size_kw * 2500,  # $2.50/W estimate
            price_per_watt=2.50
        )
        
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return UnifiedProjectModel(
            project_id=project_id,
            project_name=project_data.get("project_name", "Unnamed Project"),
            data_source="Manual",  # Required field
            address=address,
            system_specs=system_specs,  # Required field
            financials=financials,
            system_size_kw=system_size_kw,
            created_date=datetime.now(),
            updated_date=datetime.now()
        )

    async def run_complete_workflow(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the complete multi-agent workflow for a solar project.
        
        Args:
            project_data: Initial project information including:
                - project_name: Name of the solar project
                - address: Project location/address
                - system_size_kw: Proposed system size in kW
                - project_type: Type of project (e.g., "Commercial Solar")
                
        Returns:
            Complete feasibility and permitting package
        """
        # Initialize Unified Project Model with proper data conversion
        unified_project = self._convert_api_data_to_unified_model(project_data)
        project_id = unified_project.project_id
        
        logger.info(f"🚀 Starting supervised workflow for project {project_id}")
        workflow_results = {}
        
        try:
            # Stage 1: Initial Context & Feasibility (General Research Agent)
            self.current_stage = WorkflowStage.INITIAL_CONTEXT
            logger.info("📊 Stage 1: Initial Context & Feasibility Analysis")
            
            research_result = await self.general_research_agent.analyze_feasibility(
                unified_project.dict()
            )
            
            # Check if project is feasible
            if not research_result.get("feasible", False):
                logger.warning(f"Project {project_id} failed feasibility screening")
                unified_project.status = "ineligible"
                unified_project.feasibility_analysis = research_result
                await self._save_project(unified_project.dict())
                
                return {
                    "project_id": project_id,
                    "status": "ineligible",
                    "reason": research_result.get("ineligibility_reason", "Failed feasibility screening"),
                    "analysis": research_result
                }
            
            workflow_results["research"] = research_result
            unified_project.feasibility_analysis = research_result
            
            # Stage 2: Engineering Design (System Design Agent)
            self.current_stage = WorkflowStage.ENGINEERING_DESIGN
            logger.info("🔧 Stage 2: Engineering Design")
            
            design_result = await self.engineering_design_agent.create_system_design(
                unified_project.dict()
            )
            
            workflow_results["design"] = design_result
            unified_project.system_specs = design_result.get("system_specs", {})
            unified_project.production_metrics = design_result.get("production_metrics", {})
            
            # Stage 3: Site Selection & Qualification (Site Context Agent)
            self.current_stage = WorkflowStage.SITE_QUALIFICATION
            logger.info("📍 Stage 3: Site Selection & Qualification")
            
            site_result = await self.site_qualification_agent.evaluate_site(
                unified_project.dict()
            )
            
            workflow_results["site_qualification"] = site_result
            unified_project.site_qualification = site_result
            
            # Generate Letter of Intent if site is qualified
            if site_result.get("site_qualified", False):
                loi = await self.ai_service.generate_letter_of_intent(unified_project.dict())
                unified_project.project_documents = {"letter_of_intent": loi}
            
            # Stage 4: Permitting & Documentation (Permitting Agent)
            self.current_stage = WorkflowStage.PERMITTING
            logger.info("📋 Stage 4: Permitting & Documentation")
            
            permit_result = await self.permitting_agent.compile_permit_package(
                unified_project.dict()
            )
            
            workflow_results["permitting"] = permit_result
            unified_project.permit_matrix = permit_result.get("permit_matrix", {})
            
            # Stage 5: Complete - Assemble Final Package
            self.current_stage = WorkflowStage.COMPLETE
            logger.info("✅ Assembling final feasibility and permitting package")
            
            final_package = await self._assemble_final_package(
                unified_project, workflow_results
            )
            
            # Save completed project to database
            unified_project.status = "ready_for_development"
            unified_project.updated_date = datetime.now()
            await self._save_project(unified_project.dict())
            
            logger.info(f"🎉 Workflow completed successfully for project {project_id}")
            
            return {
                "project_id": project_id,
                "status": "success",
                "unified_project_model": unified_project.dict(),
                "agent_results": workflow_results,
                "final_package": final_package,
                "processing_time": self._calculate_processing_time()
            }
            
        except Exception as e:
            logger.error(f"❌ Workflow failed at stage {self.current_stage.value}: {e}")
            return {
                "project_id": project_id,
                "status": "error",
                "failed_at_stage": self.current_stage.value,
                "error": str(e),
                "partial_results": workflow_results
            }
    
    async def _assemble_final_package(self, project: UnifiedProjectModel, 
                                     agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assemble the comprehensive feasibility and permitting package.
        
        Args:
            project: Unified project model with all agent outputs
            agent_results: Results from each agent
            
        Returns:
            Complete project package ready for handoff
        """
        research = agent_results.get("research", {})
        design = agent_results.get("design", {})
        site = agent_results.get("site_qualification", {})
        permits = agent_results.get("permitting", {})
        
        # Calculate overall project score
        feasibility_score = research.get("feasibility_score", 0.5)
        design_confidence = design.get("design_confidence", 0.5)
        site_score = site.get("site_suitability_score", 0.5)
        permit_complexity = 1 - permits.get("complexity_score", 0.5)  # Invert for scoring
        
        overall_score = (feasibility_score + design_confidence + site_score + permit_complexity) / 4
        
        return {
            "executive_summary": {
                "project_name": project.project_name,
                "location": project.address,
                "system_size": f"{project.system_specs.system_size_dc_kw} kW",
                "overall_recommendation": "PROCEED" if overall_score >= 0.7 else "PROCEED WITH CAUTION" if overall_score >= 0.5 else "RECONSIDER",
                "confidence_score": round(overall_score * 100, 1),
                "estimated_timeline": permits.get("total_timeline", "12-18 months"),
                "estimated_cost": design.get("total_system_cost", 0)
            },
            "technical_package": {
                "system_design": design.get("system_design", {}),
                "annual_production": design.get("estimated_annual_production", 0),
                "equipment_specs": design.get("equipment_specs", {}),
                "single_line_diagram": design.get("diagrams", {}).get("single_line", None)
            },
            "site_package": {
                "site_assessment": site.get("site_assessment", {}),
                "jurisdiction": site.get("jurisdiction", {}),
                "utility_info": site.get("utility_interconnection", {}),
                "letter_of_intent": project.project_documents.get("letter_of_intent", None)
            },
            "permitting_package": {
                "permit_matrix": permits.get("permit_matrix", {}),
                "critical_path": permits.get("critical_path", []),
                "draft_applications": permits.get("draft_documents", {}),
                "estimated_fees": permits.get("total_fees", 0),
                "timeline": permits.get("permit_timeline", {})
            },
            "financial_summary": {
                "system_cost": design.get("total_system_cost", 0),
                "available_incentives": research.get("incentives", {}),
                "estimated_roi": research.get("roi_projection", "TBD"),
                "payback_period": research.get("payback_period", "TBD")
            },
            "risk_assessment": {
                "technical_risks": design.get("technical_risks", []),
                "regulatory_risks": permits.get("regulatory_risks", []),
                "site_risks": site.get("site_risks", []),
                "mitigation_strategies": self._compile_mitigation_strategies(agent_results)
            },
            "next_steps": [
                "Review and validate all analysis results with stakeholders",
                "Secure site control through LOI execution",
                "Submit interconnection application to utility",
                "Begin detailed engineering and permit application preparation",
                "Finalize project financing structure"
            ],
            "generated_documents": {
                "letter_of_intent": project.project_documents.get("letter_of_intent", None),
                "permit_applications": permits.get("draft_documents", {}),
                "technical_reports": design.get("reports", {})
            }
        }
    
    def _compile_mitigation_strategies(self, agent_results: Dict[str, Any]) -> List[str]:
        """Compile risk mitigation strategies from all agents."""
        strategies = []
        
        # Add strategies from each agent's analysis
        for agent_name, results in agent_results.items():
            if "mitigation_strategies" in results:
                strategies.extend(results["mitigation_strategies"])
            if "risk_mitigation" in results:
                strategies.extend(results["risk_mitigation"])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_strategies = []
        for strategy in strategies:
            if strategy not in seen:
                seen.add(strategy)
                unique_strategies.append(strategy)
        
        return unique_strategies[:10]  # Top 10 strategies
    
    async def _save_project(self, project_data: Dict[str, Any]) -> None:
        """Save project data to database."""
        try:
            await self.db.create_project(project_data)
            logger.info(f"Project {project_data['project_id']} saved to database")
        except Exception as e:
            logger.error(f"Failed to save project: {e}")
    
    def _calculate_processing_time(self) -> float:
        """Calculate realistic processing time for the workflow."""
        # Simulated processing times for each stage
        stage_times = {
            WorkflowStage.INITIAL_CONTEXT: 3.5,
            WorkflowStage.ENGINEERING_DESIGN: 4.2,
            WorkflowStage.SITE_QUALIFICATION: 3.8,
            WorkflowStage.PERMITTING: 4.5
        }
        
        # Add some randomness for realism
        import random
        total_time = sum(stage_times.values()) + random.uniform(0.5, 2.0)
        return round(total_time, 1)


# Singleton instance
_supervisor = None

def get_supervisor_orchestrator() -> SupervisorOrchestrator:
    """Get or create the Supervisor Orchestrator singleton."""
    global _supervisor
    if _supervisor is None:
        _supervisor = SupervisorOrchestrator()
    return _supervisor 