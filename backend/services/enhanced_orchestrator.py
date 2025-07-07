"""
Enhanced Orchestrator for multi-agent solar project analysis.
Coordinates research, design, site qualification, and permitting agents.
"""
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from services.ai_service import AIService

logger = logging.getLogger(__name__)

class EnhancedOrchestrator:
    """Enhanced orchestrator for coordinating all agent workflows."""
    
    def __init__(self, research_agent, design_agent, site_qualification_agent, permitting_agent):
        """Initialize orchestrator with all specialized agents."""
        self.research_agent = research_agent
        self.design_agent = design_agent
        self.site_qualification_agent = site_qualification_agent
        self.permitting_agent = permitting_agent
        logger.info("Enhanced Orchestrator initialized with all agent services")
    
    async def run_complete_workflow(self, project_name: str, address: str, system_size_kw: float, 
                                   project_type: str = "Commercial Solar", 
                                   contact_email: Optional[str] = None, 
                                   description: Optional[str] = None) -> Dict[str, Any]:
        """Run complete multi-agent workflow for solar project analysis."""
        project_id = f"proj_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting enhanced workflow for project {project_id}")
        
        try:
            # Stage 1: Research Agent - Feasibility Screening
            logger.info(f"Stage 1: Running feasibility screening for {project_id}")
            research_result = await self.research_agent.run_feasibility_screening(
                project_name, address, system_size_kw
            )
            
            # Stage 2: Design Agent - System Design
            logger.info(f"Stage 2: Running engineering design for {project_id}")
            design_result = await self.design_agent.generate_system_design(
                project_name, address, system_size_kw
            )
            
            # Stage 3: Site Qualification Agent
            logger.info(f"Stage 3: Running site qualification for {project_id}")
            site_qualification_result = await self.site_qualification_agent.analyze_site_qualification(
                project_name, address, system_size_kw
            )
            
            # Stage 4: Permitting Agent
            logger.info(f"Stage 4: Running permitting analysis for {project_id}")
            permitting_result = await self.permitting_agent.analyze_permitting_requirements(
                project_name, address, system_size_kw
            )
            
            # Stage 5: Assemble Final Package
            logger.info(f"Stage 5: Assembling final package for {project_id}")
            final_package = await self._assemble_final_package(
                project_id, research_result, design_result, 
                site_qualification_result, permitting_result
            )
            
            logger.info(f"Workflow completed successfully for project {project_id}")
            
            return {
                "project_id": project_id,
                "success": True,
                "agent_results": {
                    "research": research_result,
                    "design": design_result,
                    "site_qualification": site_qualification_result,
                    "permitting": permitting_result
                },
                "final_package": final_package
            }
            
        except Exception as e:
            logger.error(f"Workflow failed for project {project_id}: {e}")
            return {
                "project_id": project_id,
                "success": False,
                "error": str(e),
                "agent_results": {},
                "final_package": {}
            }
    
    async def _assemble_final_package(self, project_id: str, research_result: Dict[str, Any], 
                                     design_result: Dict[str, Any], site_qualification_result: Dict[str, Any],
                                     permitting_result: Dict[str, Any]) -> Dict[str, Any]:
        """Assemble final comprehensive package from all agent results."""
        
        # Calculate overall recommendation
        feasibility_score = research_result.get("feasibility_score", 0.5)
        design_confidence = design_result.get("design_confidence", 0.5)
        site_suitability = site_qualification_result.get("site_suitability_score", 0.5)
        permitting_complexity = permitting_result.get("permitting_complexity_score", 0.5)
        
        overall_score = (feasibility_score + design_confidence + site_suitability + (1 - permitting_complexity)) / 4
        
        recommendation = "PROCEED" if overall_score >= 0.7 else "CAUTION" if overall_score >= 0.5 else "DEFER"
        
        final_package = {
            "project_id": project_id,
            "analysis_timestamp": datetime.now().isoformat(),
            "overall_recommendation": {
                "recommendation": recommendation,
                "confidence_score": round(overall_score * 100, 1),
                "key_factors": {
                    "feasibility": round(feasibility_score * 100, 1),
                    "design_confidence": round(design_confidence * 100, 1),
                    "site_suitability": round(site_suitability * 100, 1),
                    "permitting_simplicity": round((1 - permitting_complexity) * 100, 1)
                }
            },
            "executive_summary": {
                "project_viability": research_result.get("executive_summary", "Analysis completed"),
                "technical_design": design_result.get("design_summary", "Design completed"),
                "site_assessment": site_qualification_result.get("site_summary", "Site assessment completed"),
                "permitting_outlook": permitting_result.get("permitting_summary", "Permitting analysis completed")
            },
            "financial_projections": {
                "estimated_project_cost": design_result.get("estimated_cost", 0),
                "estimated_annual_production": design_result.get("estimated_annual_production", 0),
                "payback_period": research_result.get("payback_period", "TBD"),
                "roi_projection": research_result.get("roi_projection", "TBD")
            },
            "implementation_timeline": {
                "permitting_phase": permitting_result.get("estimated_timeline", "6-12 months"),
                "construction_phase": "3-6 months",
                "commissioning_phase": "1-2 months",
                "total_project_duration": "10-20 months"
            },
            "risk_assessment": {
                "technical_risks": design_result.get("technical_risks", []),
                "regulatory_risks": permitting_result.get("regulatory_risks", []),
                "market_risks": research_result.get("market_risks", []),
                "overall_risk_level": "Low" if overall_score >= 0.7 else "Medium" if overall_score >= 0.5 else "High"
            },
            "next_steps": [
                "Review and validate all analysis results",
                "Conduct detailed site survey if not already completed",
                "Initiate permitting process for highest priority permits",
                "Develop detailed financial model",
                "Secure project financing commitments"
            ]
        }
        
        return final_package