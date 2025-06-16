"""
Core project service for managing project lifecycle and business logic.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from ..models.project import UnifiedProjectModel, ProjectStatus
from ..core.database import get_db_client, get_storage_client
from .ai_service import AIService
from .scoring_service import ScoringService
from .permit_service import PermitService
from .financial_service import FinancialService

logger = logging.getLogger(__name__)


class ProjectService:
    """
    Core service for project management and orchestration.
    """
    
    def __init__(self):
        self.db = get_db_client()
        self.storage = get_storage_client()
        self.ai_service = AIService()
        self.scoring_service = ScoringService()
        self.permit_service = PermitService()
        self.financial_service = FinancialService()
    
    async def create_project_from_minimal_input(
        self, 
        zip_code: str, 
        system_size_kw: float,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create project from minimal input using AI expansion.
        
        Args:
            zip_code: Project location ZIP code
            system_size_kw: System size in kW DC
            additional_data: Optional additional parameters
            
        Returns:
            Project creation result with project_id and status
        """
        try:
            logger.info(f"Creating project from minimal input: {zip_code}, {system_size_kw}kW")
            
            # Auto-expand minimal input using AI
            expanded_data = await self.ai_service.auto_expand_minimal_input(
                zip_code, system_size_kw, additional_data or {}
            )
            
            # Create project model
            project = UnifiedProjectModel(**expanded_data)
            
            # Save to database
            await self.db.create_project(project.dict())
            
            # Start AI workflow asynchronously
            asyncio.create_task(self._process_project_ai_workflow(project.project_id))
            
            return {
                "project_id": project.project_id,
                "status": "processing_started",
                "estimated_completion": "5-10 minutes",
                "auto_expanded_data": {
                    "address": project.address.dict(),
                    "system_size_kw": project.system_specs.system_size_dc_kw
                }
            }
            
        except Exception as e:
            logger.error(f"Error creating project from minimal input: {e}")
            raise
    
    async def create_project_manual(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create project from manual input data.
        
        Args:
            project_data: Complete project data
            
        Returns:
            Created project data
        """
        try:
            logger.info("Creating project from manual input")
            
            # Validate and create project
            project_data['data_source'] = 'Manual'
            project = UnifiedProjectModel(**project_data)
            
            # Save to database
            result = await self.db.create_project(project.dict())
            
            # Start workflow
            asyncio.create_task(self._process_project_ai_workflow(project.project_id))
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating manual project: {e}")
            raise
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get project by ID."""
        return await self.db.get_project(project_id)
    
    async def get_all_projects(self) -> List[Dict[str, Any]]:
        """Get all projects with summary information."""
        projects = await self.db.get_all_projects()
        
        # Add computed fields for dashboard
        for project in projects:
            project['computed_progress'] = self._calculate_project_progress(project)
            project['computed_status'] = self._determine_project_status(project)
        
        return projects
    
    async def update_project(self, project_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Update project with new data."""
        updates['updated_date'] = datetime.now()
        return await self.db.update_project(project_id, updates)
    
    async def get_project_package(self, project_id: str) -> Dict[str, Any]:
        """
        Get complete AI-generated project package.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Complete project package or processing status
        """
        try:
            project = await self.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Check processing status
            processing_status = self._get_processing_status(project)
            
            if processing_status != "completed":
                return {
                    "project_id": project_id,
                    "status": processing_status,
                    "progress": self._calculate_progress_percentage(project),
                    "current_stage": self._get_current_processing_stage(project)
                }
            
            # Generate comprehensive package
            package = await self._format_project_as_ai_package(project)
            return package
            
        except Exception as e:
            logger.error(f"Error getting project package for {project_id}: {e}")
            raise
    
    async def generate_downloadable_package(self, project_id: str) -> str:
        """
        Generate downloadable ZIP package with all project documents.
        
        Args:
            project_id: Project identifier
            
        Returns:
            Download URL for the package
        """
        try:
            import zipfile
            import io
            import json
            
            project = await self.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Create in-memory ZIP file
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Project Overview JSON
                overview = await self._format_project_as_ai_package(project)
                zip_file.writestr(
                    "01_Project_Overview.json",
                    json.dumps(overview, default=str, indent=2)
                )
                
                # Site Control Documents
                site_control = project.get('project_documents', {}).get('site_control', {})
                if site_control.get('document_content'):
                    zip_file.writestr(
                        "02_Site_Control_LOI.txt",
                        site_control['document_content']
                    )
                
                # Permit Matrix
                permit_matrix = project.get('permit_matrix', {})
                if permit_matrix:
                    zip_file.writestr(
                        "03_Permit_Matrix.json",
                        json.dumps(permit_matrix, default=str, indent=2)
                    )
                
                # Financial Analysis
                financials = project.get('financials', {})
                if financials:
                    zip_file.writestr(
                        "04_Financial_Analysis.json",
                        json.dumps(financials, default=str, indent=2)
                    )
                
                # Development Checklist
                checklist = project.get('development_checklist', [])
                if checklist:
                    zip_file.writestr(
                        "05_Development_Checklist.json",
                        json.dumps(checklist, default=str, indent=2)
                    )
            
            # Upload to blob storage
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"project_package_{timestamp}.zip"
            
            zip_buffer.seek(0)
            blob_path = await self.storage.upload_document(
                project_id,
                filename,
                zip_buffer.getvalue()
            )
            
            return self.storage.get_document_url(blob_path)
            
        except Exception as e:
            logger.error(f"Error generating download package: {e}")
            raise
    
    async def _process_project_ai_workflow(self, project_id: str) -> None:
        """
        Process complete AI workflow for a project.
        
        Args:
            project_id: Project to process
        """
        try:
            logger.info(f"Starting AI workflow for project {project_id}")
            
            project = await self.get_project(project_id)
            if not project:
                logger.error(f"Project {project_id} not found for workflow")
                return
            
            # Step 1: Eligibility Screening
            await self._update_project_status(project_id, "eligibility_screening")
            eligibility_results = await self.ai_service.perform_eligibility_screening(project)
            
            await self.update_project({
                'eligibility_screening': eligibility_results,
                'milestones.screening': 'Completed'
            })
            
            if not eligibility_results.get('eligible', False):
                logger.info(f"Project {project_id} failed eligibility screening")
                await self._update_project_status(project_id, "ineligible")
                return
            
            # Step 2: System Design & Production Analysis
            await self._update_project_status(project_id, "system_analysis")
            production_metrics = await self.ai_service.generate_production_analysis(project)
            
            await self.update_project(project_id, {
                'production_metrics': production_metrics,
                'milestones.engineering': 'Conceptual Design'
            })
            
            # Step 3: Permit Matrix Generation
            await self._update_project_status(project_id, "permit_analysis")
            permit_matrix = await self.permit_service.generate_permit_matrix(project['address'])
            
            await self.update_project(project_id, {
                'permit_matrix': permit_matrix,
                'milestones.permitting': 'Matrix Generated'
            })
            
            # Step 4: Interconnection Analysis
            await self._update_project_status(project_id, "interconnection_analysis")
            interconnection_score = await self.ai_service.generate_interconnection_score(project)
            
            await self.update_project(project_id, {
                'interconnection_score': interconnection_score,
                'milestones.interconnection': 'Initial Screen'
            })
            
            # Step 5: Site Control Document Generation
            await self._update_project_status(project_id, "document_generation")
            site_control_doc = await self.ai_service.generate_site_control_document(project)
            
            await self.update_project(project_id, {
                'project_documents.site_control': site_control_doc,
                'milestones.site_control': 'LOI Drafted'
            })
            
            # Step 6: Financial Analysis
            await self._update_project_status(project_id, "financial_analysis")
            
            # Refresh project data
            project = await self.get_project(project_id)
            capital_stack, climatize_options = await self.financial_service.generate_capital_stack_analysis(project)
            
            await self.update_project(project_id, {
                'financials.capital_stack': capital_stack,
                'financials.climatize_funding_options': climatize_options,
                'milestones.financing': 'Initial Analysis'
            })
            
            # Step 7: Final Scoring & Package Generation
            await self._update_project_status(project_id, "final_scoring")
            
            # Refresh project data again
            project = await self.get_project(project_id)
            fundability_score, fundability_factors = await self.scoring_service.calculate_fundability_score(project)
            
            # Generate development checklist
            development_checklist = await self.ai_service.generate_development_checklist(project)
            
            await self.update_project(project_id, {
                'fundability_score': fundability_score,
                'fundability_factors': fundability_factors,
                'development_checklist': development_checklist,
                'status': ProjectStatus.DEVELOPMENT,
                'milestones.overall_completion_percentage': self._calculate_progress_percentage(project),
                'processing_completed_at': datetime.now().isoformat()
            })
            
            logger.info(f"AI workflow completed for project {project_id} with score {fundability_score}")
            
        except Exception as e:
            logger.error(f"Error in AI workflow for project {project_id}: {e}")
            await self.update_project(project_id, {
                'status': 'error',
                'error_message': str(e)
            })
    
    async def _update_project_status(self, project_id: str, status: str) -> None:
        """Update project processing status."""
        await self.update_project(project_id, {'processing_status': status})
    
    def _calculate_project_progress(self, project: Dict[str, Any]) -> int:
        """Calculate overall project progress percentage."""
        milestones = project.get('milestones', {})
        completed = 0
        total = 6
        
        milestone_stages = [
            'site_control', 'permitting', 'interconnection',
            'engineering', 'offtake', 'financing'
        ]
        
        for stage in milestone_stages:
            if milestones.get(stage, 'Not Started') != 'Not Started':
                completed += 1
        
        return int((completed / total) * 100)
    
    def _determine_project_status(self, project: Dict[str, Any]) -> str:
        """Determine human-readable project status."""
        if project.get('processing_completed_at'):
            return "Analysis Complete"
        elif project.get('processing_status'):
            status_map = {
                'eligibility_screening': 'Screening Eligibility',
                'system_analysis': 'Analyzing System Design',
                'permit_analysis': 'Reviewing Permits',
                'interconnection_analysis': 'Checking Interconnection',
                'document_generation': 'Generating Documents',
                'financial_analysis': 'Analyzing Financials',
                'final_scoring': 'Calculating Score'
            }
            return status_map.get(project['processing_status'], 'Processing')
        else:
            return "Initializing"
    
    def _get_processing_status(self, project: Dict[str, Any]) -> str:
        """Get processing status for API responses."""
        if project.get('processing_completed_at'):
            return "completed"
        elif project.get('processing_status'):
            return "processing"
        else:
            return "starting"
    
    def _calculate_progress_percentage(self, project: Dict[str, Any]) -> int:
        """Calculate processing progress percentage."""
        return self._calculate_project_progress(project)
    
    def _get_current_processing_stage(self, project: Dict[str, Any]) -> str:
        """Get current processing stage description."""
        return self._determine_project_status(project)
    
    async def _format_project_as_ai_package(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Format project as comprehensive AI package."""
        addr = project['address']
        full_address = f"{addr['street']}, {addr['city']}, {addr['state']} {addr['zip_code']}"
        
        return {
            "project_id": project['project_id'],
            "generation_date": datetime.now(),
            "project_overview": {
                "project_name": project['project_name'],
                "site_address": full_address,
                "system_size_kw": project['system_specs']['system_size_dc_kw'],
                "estimated_annual_production": project.get('production_metrics', {}).get('annual_production_kwh', 0),
                "fundability_score": project.get('fundability_score', 0),
                "data_source": project.get('data_source', 'AI_Generated')
            },
            "site_analysis": {
                "coordinates": {
                    "lat": addr.get('lat'),
                    "lon": addr.get('lon')
                },
                "roof_type": project['system_specs'].get('roof_type', 'flat'),
                "system_specs": project['system_specs'],
                "production_metrics": project.get('production_metrics', {})
            },
            "permit_analysis": project.get('permit_matrix', {}),
            "interconnection_analysis": project.get('interconnection_score', {}),
            "financial_analysis": {
                "capital_stack": project.get('financials', {}).get('capital_stack', {}),
                "incentives": project.get('financials', {}).get('incentives', []),
                "pro_forma": project.get('financials', {}).get('pro_forma', {})
            },
            "site_control_documents": project.get('project_documents', {}).get('site_control', {}),
            "development_checklist": project.get('development_checklist', []),
            "next_steps": project.get('next_steps', []),
            "climatize_funding_options": project.get('climatize_funding_options', []),
            "eligibility_screening": project.get('eligibility_screening', {}),
            "generation_method": "AI_Powered",
            "processing_time_seconds": self._calculate_processing_time(project)
        }
    
    def _calculate_processing_time(self, project: Dict[str, Any]) -> Optional[float]:
        """Calculate total processing time."""
        created = project.get('created_date')
        completed = project.get('processing_completed_at')
        
        if created and completed:
            if isinstance(created, str):
                created = datetime.fromisoformat(created.replace('Z', '+00:00'))
            if isinstance(completed, str):
                completed = datetime.fromisoformat(completed.replace('Z', '+00:00'))
            
            return (completed - created).total_seconds()
        
        return None