"""
Core project service for managing project lifecycle and business logic.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from models.project_simple import UnifiedProjectModel, ProjectStatus
from core.database import get_db_client, get_storage_client
from .ai_service import AIService
from .scoring_service import ScoringService
from .permit_service import PermitService
from .financial_service import FinancialService
from .feasibility_analysis_service import get_feasibility_engine
from .workflow_state_service import get_workflow_state_service

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
        self.feasibility_engine = get_feasibility_engine()
        self.workflow_state = get_workflow_state_service()
    
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
    
    async def trigger_permit_matrix_generation(self, project_id: str) -> Dict[str, Any]:
        """Trigger permit matrix generation for a project."""
        try:
            logger.info(f"Triggering permit matrix generation for project {project_id}")
            
            project = await self.db.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Use permit service to generate matrix
            permit_matrix = await self.permit_service.generate_permit_matrix(project)
            
            # Update project with permit matrix
            project['permit_matrix'] = permit_matrix
            project['milestones']['permitting'] = 'Matrix Generated'
            project['updated_date'] = datetime.now()
            
            await self.db.update_project(project_id, project)
            
            logger.info(f"Permit matrix generated for project {project_id}")
            return permit_matrix
            
        except Exception as e:
            logger.error(f"Error generating permit matrix for {project_id}: {str(e)}")
            raise
    
    async def trigger_site_control_generation(self, project_id: str) -> Dict[str, Any]:
        """Trigger site control document (LOI) generation for a project."""
        try:
            logger.info(f"Triggering site control generation for project {project_id}")
            
            project = await self.db.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Generate LOI using AI service
            loi_document = await self.ai_service.generate_letter_of_intent(project)
            
            # Store document in blob storage
            document_url = await self.storage.upload_document(
                f"projects/{project_id}/loi.pdf",
                loi_document
            )
            
            # Update project with site control document
            project['project_documents']['site_control'] = {
                'document_type': 'LOI',
                'status': 'Draft',
                'generated_date': datetime.now(),
                'document_url': document_url
            }
            project['milestones']['site_control'] = 'LOI Drafted'
            project['updated_date'] = datetime.now()
            
            await self.db.update_project(project_id, project)
            
            logger.info(f"Site control document generated for project {project_id}")
            return {'document_url': document_url, 'status': 'completed'}
            
        except Exception as e:
            logger.error(f"Error generating site control for {project_id}: {str(e)}")
            raise
    
    async def trigger_capex_modeling(self, project_id: str) -> Dict[str, Any]:
        """Trigger CAPEX modeling and financial analysis for a project."""
        try:
            logger.info(f"Triggering CAPEX modeling for project {project_id}")
            
            project = await self.db.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Generate financial analysis
            financial_analysis = await self.financial_service.calculate_capex_and_returns(project)
            
            # Update project with financial data
            project['financials'].update(financial_analysis)
            project['milestones']['financing'] = 'Package Prepared'
            project['updated_date'] = datetime.now()
            
            await self.db.update_project(project_id, project)
            
            logger.info(f"CAPEX modeling completed for project {project_id}")
            return financial_analysis
            
        except Exception as e:
            logger.error(f"Error in CAPEX modeling for {project_id}: {str(e)}")
            raise
    
    async def process_helioscope_feasibility(self, project_id: str, run_id: str) -> Dict[str, Any]:
        """
        Process feasibility analysis specifically for Helioscope-sourced projects.
        This is the enhanced workflow mentioned in the Aurora Solar meeting.
        
        Core value: Reduces project failure rates from 70-80% to ~30% through proper feasibility analysis.
        """
        try:
            logger.info(f"Processing Helioscope feasibility for project {project_id}, run {run_id}")
            
            # Mark feasibility_analysis as processing with idempotency check
            if not self.workflow_state.mark_step_processing_with_idempotency(project_id, run_id, "feasibility_analysis"):
                logger.info(f"Feasibility analysis already processed for run {run_id}, skipping")
                existing_state = self.workflow_state.get_workflow_state(project_id, run_id)
                if existing_state and "feasibility_analysis" in existing_state.get("Steps", {}):
                    return existing_state["Steps"]["feasibility_analysis"].get("output", {})
                raise ValueError("Feasibility analysis already in progress or failed")
            
            project = await self.db.get_project(project_id)
            if not project:
                self.workflow_state.update_step_status(
                    project_id, run_id, "feasibility_analysis", "Failed", 
                    error_details=f"Project {project_id} not found"
                )
                raise ValueError(f"Project {project_id} not found")
            
            if project.get('data_source') != 'Helioscope':
                logger.warning(f"Project {project_id} is not from Helioscope, but processing anyway")
            
            # CORE FEASIBILITY ANALYSIS - This is the key business value
            logger.info(f"Running core feasibility analysis for project {project_id}")
            feasibility_analysis = self.feasibility_engine.analyze_project(project)
            
            # Check if project is viable before continuing with expensive operations
            if not feasibility_analysis["is_viable"]:
                logger.info(f"Project {project_id} failed feasibility analysis: {feasibility_analysis['viability_reason']}")
                
                # Mark feasibility as completed with non-viable result
                self.workflow_state.update_step_status(
                    project_id, run_id, "feasibility_analysis", "Completed", 
                    output={
                        "feasibility_analysis": feasibility_analysis,
                        "workflow_status": "completed_non_viable"
                    }
                )
                
                # Update project status
                project['feasibility_analysis'] = feasibility_analysis
                project['project_status'] = 'not_viable'
                project['updated_date'] = datetime.now()
                await self.db.update_project(project_id, project)
                
                return {
                    'project_id': project_id,
                    'feasibility_analysis': feasibility_analysis,
                    'workflow_status': 'completed_non_viable',
                    'message': 'Project failed feasibility analysis - workflow stopped'
                }
            
            # Project passed feasibility - continue with full workflow
            logger.info(f"Project {project_id} passed feasibility analysis - continuing with full workflow")
            
            # Execute the complete workflow in sequence
            # 1. Permit matrix analysis
            permit_matrix = await self.trigger_permit_matrix_generation(project_id)
            
            # 2. Site control document generation (LOI)
            site_control = await self.trigger_site_control_generation(project_id)
            
            # 3. CAPEX modeling and financial analysis
            financial_analysis = await self.trigger_capex_modeling(project_id)
            
            # 4. Calculate overall project score
            fundability_score = await self.scoring_service.calculate_fundability_score(project)
            
            # 5. Update final project status
            project = await self.db.get_project(project_id)  # Refresh project data
            project['feasibility_analysis'] = feasibility_analysis
            project['fundability_score'] = fundability_score
            project['readiness_score'] = self._calculate_readiness_score(project)
            project['next_steps'] = self._generate_next_steps(project)
            project['project_status'] = 'viable'
            project['updated_date'] = datetime.now()
            
            await self.db.update_project(project_id, project)
            
            # Compile complete feasibility package
            feasibility_package = {
                'project_id': project_id,
                'feasibility_analysis': feasibility_analysis,
                'permit_matrix': permit_matrix,
                'site_control': site_control,
                'financial_analysis': financial_analysis,
                'fundability_score': fundability_score,
                'readiness_score': project['readiness_score'],
                'next_steps': project['next_steps'],
                'workflow_status': 'completed_viable'
            }
            
            # Mark feasibility analysis as completed
            self.workflow_state.update_step_status(
                project_id, run_id, "feasibility_analysis", "Completed", 
                output=feasibility_package
            )
            
            logger.info(f"Helioscope feasibility analysis completed for project {project_id}, run {run_id}")
            return feasibility_package
            
        except Exception as e:
            logger.error(f"Error in Helioscope feasibility processing for {project_id}, run {run_id}: {str(e)}")
            
            # Mark step as failed
            self.workflow_state.update_step_status(
                project_id, run_id, "feasibility_analysis", "Failed", 
                error_details=str(e)
            )
            
            raise
    
    def _calculate_readiness_score(self, project: Dict[str, Any]) -> int:
        """Calculate project readiness score based on milestone completion."""
        total_milestones = 6
        completed_milestones = 0
        
        milestones = project.get('milestones', {})
        if milestones.get('site_control') not in ['Not Started']:
            completed_milestones += 1
        if milestones.get('permitting') not in ['Not Started']:
            completed_milestones += 1
        if milestones.get('interconnection') not in ['Not Started']:
            completed_milestones += 1
        if milestones.get('engineering') not in ['Not Started']:
            completed_milestones += 1
        if milestones.get('offtake') not in ['Not Started']:
            completed_milestones += 1
        if milestones.get('financing') not in ['Not Started']:
            completed_milestones += 1
        
        return int((completed_milestones / total_milestones) * 100)
    
    def _generate_next_steps(self, project: Dict[str, Any]) -> List[str]:
        """Generate next steps based on current project status."""
        next_steps = []
        milestones = project.get('milestones', {})
        
        if milestones.get('site_control') == 'Not Started':
            next_steps.append("Complete site control agreements (LOI or lease)")
        elif milestones.get('site_control') == 'LOI Drafted':
            next_steps.append("Send LOI to landowner for signature")
        
        if milestones.get('permitting') == 'Not Started':
            next_steps.append("Begin permit application process")
        elif milestones.get('permitting') == 'Matrix Generated':
            next_steps.append("Submit permit applications to relevant authorities")
        
        if milestones.get('interconnection') == 'Not Started':
            next_steps.append("Submit interconnection application to utility")
        
        if milestones.get('financing') == 'Not Started':
            next_steps.append("Prepare financing package for investors")
        
        if not next_steps:
            next_steps.append("Project is ready for construction phase")
        
        return next_steps
    
    async def generate_complete_permitting_package(self, project_id: str) -> Dict[str, Any]:
        """
        Generate complete permitting package including all deliverables mentioned in the Aurora meeting:
        - Single line diagrams
        - Interconnection applications  
        - Land use reports
        - Site control documents
        - CAPEX modeling
        """
        try:
            logger.info(f"Generating complete permitting package for project {project_id}")
            
            project = await self.db.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            package_documents = {}
            
            # 1. Single Line Diagram
            if project.get('data_source') == 'Helioscope' and project.get('project_documents', {}).get('one_line_diagram'):
                package_documents['single_line_diagram'] = project['project_documents']['one_line_diagram']
            else:
                # Generate single line diagram from system specs
                single_line_diagram = await self._generate_single_line_diagram(project)
                package_documents['single_line_diagram'] = single_line_diagram
            
            # 2. Interconnection Application
            interconnection_app = await self._generate_interconnection_application(project)
            package_documents['interconnection_application'] = interconnection_app
            
            # 3. Land Use Report
            land_use_report = await self._generate_land_use_report(project)
            package_documents['land_use_report'] = land_use_report
            
            # 4. Site Control Documents (LOI/Lease)
            if not project.get('project_documents', {}).get('site_control'):
                site_control = await self.trigger_site_control_generation(project_id)
                package_documents['site_control'] = site_control
            else:
                package_documents['site_control'] = project['project_documents']['site_control']
            
            # 5. CAPEX Model and Financial Package
            if not project.get('financials', {}).get('pro_forma'):
                financial_package = await self.trigger_capex_modeling(project_id)
                package_documents['financial_package'] = financial_package
            else:
                package_documents['financial_package'] = project['financials']
            
            # 6. System Layout and DXF Files (if from Helioscope)
            if project.get('data_source') == 'Helioscope':
                dxf_files = project.get('project_documents', {}).get('dxf_files')
                if dxf_files:
                    package_documents['system_layout_dxf'] = dxf_files
                
                site_images = project.get('project_documents', {}).get('pv_layout_pdf_url')
                if site_images:
                    package_documents['pv_layout'] = site_images
            
            # Create comprehensive package zip
            package_url = await self._create_package_zip(project_id, package_documents)
            
            # Update project with complete package
            project['project_documents']['full_package_zip_url'] = package_url
            project['milestones']['permitting'] = 'Applications Drafted'
            project['updated_date'] = datetime.now()
            
            await self.db.update_project(project_id, project)
            
            result = {
                'project_id': project_id,
                'package_url': package_url,
                'documents_included': list(package_documents.keys()),
                'status': 'completed',
                'generated_date': datetime.now()
            }
            
            logger.info(f"Complete permitting package generated for project {project_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating permitting package for {project_id}: {str(e)}")
            raise
    
    async def _generate_single_line_diagram(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Generate single line electrical diagram."""
        try:
            system_specs = project.get('system_specs', {})
            
            # Use AI service to generate diagram content
            diagram_content = await self.ai_service.generate_single_line_diagram(
                project_name=project.get('project_name'),
                system_size_kw=system_specs.get('system_size_dc_kw'),
                inverter_type=system_specs.get('inverter_type'),
                module_count=system_specs.get('module_count'),
                address=project.get('address')
            )
            
            # Store diagram
            diagram_url = await self.storage.upload_document(
                f"projects/{project['project_id']}/single_line_diagram.pdf",
                diagram_content
            )
            
            return {
                'document_type': 'Single Line Diagram',
                'document_url': diagram_url,
                'generated_date': datetime.now(),
                'status': 'Draft'
            }
            
        except Exception as e:
            logger.error(f"Error generating single line diagram: {str(e)}")
            raise
    
    async def _generate_interconnection_application(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Generate utility interconnection application."""
        try:
            # Use AI service to generate interconnection application
            app_content = await self.ai_service.generate_interconnection_application(project)
            
            # Store application
            app_url = await self.storage.upload_document(
                f"projects/{project['project_id']}/interconnection_application.pdf",
                app_content
            )
            
            # Update milestone
            project['milestones']['interconnection'] = 'Application Drafted'
            
            return {
                'document_type': 'Interconnection Application',
                'document_url': app_url,
                'generated_date': datetime.now(),
                'status': 'Draft',
                'utility_name': project.get('interconnection_score', {}).get('utility_name', 'TBD')
            }
            
        except Exception as e:
            logger.error(f"Error generating interconnection application: {str(e)}")
            raise
    
    async def _generate_land_use_report(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Generate land use and environmental impact report."""
        try:
            # Use AI service to generate land use report
            report_content = await self.ai_service.generate_land_use_report(project)
            
            # Store report
            report_url = await self.storage.upload_document(
                f"projects/{project['project_id']}/land_use_report.pdf",
                report_content
            )
            
            return {
                'document_type': 'Land Use Report',
                'document_url': report_url,
                'generated_date': datetime.now(),
                'status': 'Draft'
            }
            
        except Exception as e:
            logger.error(f"Error generating land use report: {str(e)}")
            raise
    
    async def _create_package_zip(self, project_id: str, documents: Dict[str, Any]) -> str:
        """Create a comprehensive ZIP package of all project documents."""
        try:
            # Create zip archive with all documents
            zip_content = await self.storage.create_document_package(project_id, documents)
            
            # Upload zip to storage
            zip_url = await self.storage.upload_document(
                f"projects/{project_id}/complete_package.zip",
                zip_content
            )
            
            return zip_url
            
        except Exception as e:
            logger.error(f"Error creating package zip for {project_id}: {str(e)}")
            raise