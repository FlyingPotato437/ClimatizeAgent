"""
Helioscope integration service for solar design and analysis.
"""
import logging
from typing import Dict, Any, Optional, List
import asyncio
import httpx
import uuid
from datetime import datetime
from core.database import get_db_client
from core.config import settings
from .workflow_state_service import get_workflow_state_service

logger = logging.getLogger(__name__)

class HelioscoperService:
    """Service for Helioscope API integration and design processing."""
    
    def __init__(self):
        self.db_client = get_db_client()
        self.workflow_state = get_workflow_state_service()
        self.api_base_url = "https://api.helioscope.com/v1"
        self.api_key = settings.helioscope_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    async def design_engine(self, project_id: str) -> Dict[str, Any]:
        """
        Main Helioscope design engine processing.
        
        Args:
            project_id: The project ID to process
            
        Returns:
            Dict containing design results
        """
        try:
            logger.info(f"Starting Helioscope design engine for project {project_id}")
            
            # Get project from database
            project = await self.db_client.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Update milestones
            project['milestones']['design'] = 'In Progress'
            await self.db_client.update_project(project_id, project)
            
            # Create Helioscope design
            design_result = await self._create_helioscope_design(project)
            
            # Process design results
            processed_design = self._process_design_results(design_result)
            
            # Update project with design data
            project['system_specs'].update(processed_design['system_specs'])
            project['production_metrics'] = processed_design['production_metrics']
            project['milestones']['design'] = 'Completed'
            
            await self.db_client.update_project(project_id, project)
            
            # Trigger next stage (for now, we'll use a generated run_id)
            await self._trigger_battery_sizing(project_id, str(uuid.uuid4()))
            
            logger.info(f"Completed Helioscope design for project {project_id}")
            return processed_design
            
        except Exception as e:
            logger.error(f"Error in Helioscope design engine for {project_id}: {str(e)}")
            # Update milestone to failed
            project = await self.db_client.get_project(project_id)
            if project:
                project['milestones']['design'] = 'Failed'
                await self.db_client.update_project(project_id, project)
            raise
    
    async def _create_helioscope_design(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Create a design using Helioscope API."""
        address = project.get('address', {})
        system_specs = project.get('system_specs', {})
        
        payload = {
            "site": {
                "latitude": address.get('latitude'),
                "longitude": address.get('longitude'),
                "address": f"{address.get('street', '')} {address.get('city', '')} {address.get('state', '')}",
                "roof_type": system_specs.get('roof_type', 'flat')
            },
            "system": {
                "dc_capacity_kw": system_specs.get('system_size_dc_kw', 100),
                "module_type": system_specs.get('module_type', 'mono-si'),
                "inverter_type": system_specs.get('inverter_type', 'string')
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/designs",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Helioscope API error: {str(e)}")
            # Return fallback design
            return self._create_fallback_design(project)
    
    def _create_fallback_design(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Create a fallback design when API is unavailable."""
        system_specs = project.get('system_specs', {})
        system_size_kw = system_specs.get('system_size_dc_kw', 100)
        
        # Simple calculations for fallback
        module_power_w = 450  # Typical module power
        module_count = int(system_size_kw * 1000 / module_power_w)
        annual_production = system_size_kw * 1400  # Rough estimate
        
        return {
            "design_id": f"fallback_{project['project_id']}",
            "system": {
                "dc_capacity_kw": system_size_kw,
                "module_count": module_count,
                "annual_production_kwh": annual_production
            },
            "performance": {
                "specific_yield": 1.4,
                "performance_ratio": 0.85
            }
        }
    
    def _process_design_results(self, design_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Helioscope design results into our format."""
        system = design_data.get('system', {})
        performance = design_data.get('performance', {})
        
        return {
            "system_specs": {
                "module_count": system.get('module_count', 0),
                "dc_capacity_kw": system.get('dc_capacity_kw', 0),
                "ac_capacity_kw": system.get('ac_capacity_kw', 0)
            },
            "production_metrics": {
                "annual_production_kwh": system.get('annual_production_kwh', 0),
                "specific_yield": performance.get('specific_yield', 1.4),
                "performance_ratio": performance.get('performance_ratio', 0.85),
                "monthly_production": self._calculate_monthly_production(
                    system.get('annual_production_kwh', 0)
                )
            }
        }
    
    def _calculate_monthly_production(self, annual_kwh: float) -> list:
        """Calculate monthly production distribution."""
        # Simplified monthly distribution (actual would use irradiance data)
        monthly_factors = [0.07, 0.08, 0.09, 0.1, 0.11, 0.12, 
                          0.12, 0.11, 0.1, 0.09, 0.08, 0.07]
        return [round(annual_kwh * factor) for factor in monthly_factors]
    
    async def _trigger_battery_sizing(self, project_id: str, run_id: str):
        """Trigger the battery sizing engine."""
        # In Azure Functions, this would use queue trigger
        # For now, we'll implement as direct call
        try:
            from .battery_service import BatteryService
            battery_service = BatteryService()
            await battery_service.sizing_engine(project_id)
        except Exception as e:
            logger.warning(f"Failed to trigger battery sizing for {project_id}, run {run_id}: {str(e)}")
    
    async def parse_helioscope_response(self, project_id: str, helioscope_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and process Helioscope webhook response."""
        try:
            logger.info(f"Parsing Helioscope data for project {project_id}")
            
            # Transform Helioscope data to our format
            transformed_data = self.transform_helioscope_data(helioscope_data)
            
            # Update project with new data
            project = await self.db_client.get_project(project_id)
            if project:
                project.update(transformed_data)
                await self.db_client.update_project(project_id, project)
            
            return transformed_data
            
        except Exception as e:
            logger.error(f"Error parsing Helioscope data for {project_id}: {str(e)}")
            raise
    
    def transform_helioscope_data(self, helioscope_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Helioscope API response to our project format."""
        design = helioscope_data.get('design', {})
        performance = helioscope_data.get('performance', {})
        
        return {
            "system_specs": {
                "system_size_dc_kw": design.get('dc_capacity_kw', 0),
                "system_size_ac_kw": design.get('ac_capacity_kw', 0),
                "module_count": design.get('module_count', 0),
                "inverter_count": design.get('inverter_count', 1),
                "tilt_angle": design.get('tilt_angle', 20),
                "azimuth": design.get('azimuth', 180)
            },
            "production_metrics": {
                "annual_production_kwh": performance.get('annual_yield_kwh', 0),
                "monthly_production": performance.get('monthly_yield', []),
                "specific_yield": performance.get('specific_yield', 1.4),
                "performance_ratio": performance.get('performance_ratio', 0.85)
            },
            "milestones": {
                "design": "Completed"
            }
        }
    
    async def fetch_design_data(self, design_id: str) -> Dict[str, Any]:
        """Fetch design data from Helioscope API."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/designs/{design_id}",
                    headers=self.headers,
                    timeout=30
                )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch Helioscope design {design_id}: {str(e)}")
            raise
    
    async def fetch_project_info(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Fetch complete project information from Helioscope API using client credentials.
        This is the main endpoint for pulling design specs and project data.
        """
        try:
            # Use client's credentials for this request
            client_headers = {
                "Authorization": f"Bearer {helioscope_credentials.get('api_token')}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/projects/{project_id}",
                    headers=client_headers,
                    timeout=30
                )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch Helioscope project {project_id}: {str(e)}")
            raise
    
    async def fetch_dxf_files(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Fetch DXF files for the project."""
        try:
            client_headers = {
                "Authorization": f"Bearer {helioscope_credentials.get('api_token')}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/projects/{project_id}/files/dxf",
                    headers=client_headers,
                    timeout=60
                )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch DXF files for project {project_id}: {str(e)}")
            raise
    
    async def fetch_site_images(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Fetch site images for the project."""
        try:
            client_headers = {
                "Authorization": f"Bearer {helioscope_credentials.get('api_token')}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/projects/{project_id}/images",
                    headers=client_headers,
                    timeout=60
                )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch site images for project {project_id}: {str(e)}")
            raise
    
    async def fetch_simulation_data(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """
        Fetch simulation data including shade report, production report, 
        irradiance, and soiling data.
        """
        try:
            client_headers = {
                "Authorization": f"Bearer {helioscope_credentials.get('api_token')}",
                "Content-Type": "application/json"
            }
            
            # Fetch all simulation endpoints
            simulation_data = {}
            
            async with httpx.AsyncClient() as client:
                # Production report
                response = await client.get(
                    f"{self.api_base_url}/projects/{project_id}/simulation/production",
                    headers=client_headers,
                    timeout=60
                )
                if response.status_code == 200:
                    simulation_data['production_report'] = response.json()
                
                # Shade report
                response = await client.get(
                    f"{self.api_base_url}/projects/{project_id}/simulation/shading", 
                    headers=client_headers,
                    timeout=60
                )
                if response.status_code == 200:
                    simulation_data['shade_report'] = response.json()
                
                # Irradiance data
                response = await client.get(
                    f"{self.api_base_url}/projects/{project_id}/simulation/irradiance",
                    headers=client_headers,
                    timeout=60
                )
                if response.status_code == 200:
                    simulation_data['irradiance'] = response.json()
                
                # Soiling data
                response = await client.get(
                    f"{self.api_base_url}/projects/{project_id}/simulation/soiling",
                    headers=client_headers,
                    timeout=60
                )
                if response.status_code == 200:
                    simulation_data['soiling'] = response.json()
            
            return simulation_data
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch simulation data for project {project_id}: {str(e)}")
            raise
    
    async def fetch_line_item_quantities(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Fetch line item quantities for wiring, inverters, and modules."""
        try:
            client_headers = {
                "Authorization": f"Bearer {helioscope_credentials.get('api_token')}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/projects/{project_id}/bom",
                    headers=client_headers,
                    timeout=30
                )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to fetch BOM for project {project_id}: {str(e)}")
            raise
    
    async def generate_one_line_diagram(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Generate one-line diagram from Helioscope data."""
        try:
            client_headers = {
                "Authorization": f"Bearer {helioscope_credentials.get('api_token')}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/projects/{project_id}/diagrams/single-line",
                    headers=client_headers,
                    timeout=60
                )
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            logger.error(f"Failed to generate one-line diagram for project {project_id}: {str(e)}")
            raise
    
    async def process_complete_helioscope_data(self, project_id: Optional[str], helioscope_project_id: str, 
                                             helioscope_credentials: Dict[str, str], run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main method to fetch and process all Helioscope data for a project.
        This is the primary integration point for the workflow described in the meeting.
        """
        try:
            # Generate run_id if not provided
            if run_id is None:
                run_id = str(uuid.uuid4())
            
            # If no project_id, generate one for new projects
            if project_id is None:
                project_id = str(uuid.uuid4())
            
            logger.info(f"Processing complete Helioscope data for project {project_id}, run {run_id}")
            
            # Create workflow run state
            self.workflow_state.create_workflow_run(project_id, run_id, "helioscope_processing")
            
            # Mark helioscope_fetch as processing with idempotency check
            if not self.workflow_state.mark_step_processing_with_idempotency(project_id, run_id, "helioscope_fetch"):
                logger.info(f"Helioscope fetch already processed for run {run_id}, skipping")
                existing_state = self.workflow_state.get_workflow_state(project_id, run_id)
                if existing_state and existing_state.get("RunStatus") == "Completed":
                    return existing_state.get("Results", {})
                raise ValueError("Helioscope fetch already in progress or failed")
            
            # Fetch all data in parallel where possible
            project_info = await self.fetch_project_info(helioscope_project_id, helioscope_credentials)
            simulation_data = await self.fetch_simulation_data(helioscope_project_id, helioscope_credentials)
            bom_data = await self.fetch_line_item_quantities(helioscope_project_id, helioscope_credentials)
            
            # Optional data (may not be available for all projects)
            dxf_files = None
            site_images = None
            one_line_diagram = None
            
            try:
                dxf_files = await self.fetch_dxf_files(helioscope_project_id, helioscope_credentials)
            except Exception as e:
                logger.warning(f"Could not fetch DXF files: {str(e)}")
            
            try:
                site_images = await self.fetch_site_images(helioscope_project_id, helioscope_credentials)
            except Exception as e:
                logger.warning(f"Could not fetch site images: {str(e)}")
            
            try:
                one_line_diagram = await self.generate_one_line_diagram(helioscope_project_id, helioscope_credentials)
            except Exception as e:
                logger.warning(f"Could not generate one-line diagram: {str(e)}")
            
            # Transform to unified project model
            unified_data = self.transform_complete_helioscope_data({
                'project_info': project_info,
                'simulation_data': simulation_data,
                'bom_data': bom_data,
                'dxf_files': dxf_files,
                'site_images': site_images,
                'one_line_diagram': one_line_diagram
            })
            
            # Create or update project in database
            if project_id is None:
                # Create new project
                import uuid
                project_id = str(uuid.uuid4())
                
                # Create base project structure
                new_project = {
                    'project_id': project_id,
                    'project_name': f"Helioscope Project {helioscope_project_id}",
                    'data_source': 'Helioscope',
                    'helioscope_project_id': helioscope_project_id,
                    'created_date': datetime.now(),
                    'updated_date': datetime.now()
                }
                new_project.update(unified_data)
                
                await self.db_client.create_project(new_project)
            else:
                # Update existing project
                project = await self.db_client.get_project(project_id)
                if project:
                    project.update(unified_data)
                    project['helioscope_project_id'] = helioscope_project_id
                    project['data_source'] = 'Helioscope'
                    project['updated_date'] = datetime.now()
                    await self.db_client.update_project(project_id, project)
            
            # Add project_id and run_id to return data
            unified_data['project_id'] = project_id
            unified_data['run_id'] = run_id
            
            # Mark helioscope_fetch as completed
            self.workflow_state.update_step_status(
                project_id, run_id, "helioscope_fetch", "Completed", 
                output={"unified_data": unified_data}
            )
            
            # Trigger next workflow steps
            await self._trigger_feasibility_analysis(project_id, run_id)
            
            logger.info(f"Successfully processed Helioscope data for project {project_id}, run {run_id}")
            return unified_data
            
        except Exception as e:
            logger.error(f"Error processing complete Helioscope data for project {project_id}, run {run_id}: {str(e)}")
            
            # Mark step as failed if we have the IDs
            if 'project_id' in locals() and 'run_id' in locals():
                try:
                    self.workflow_state.update_step_status(
                        project_id, run_id, "helioscope_fetch", "Failed", 
                        error_details=str(e)
                    )
                except Exception as state_error:
                    logger.error(f"Failed to update state on error: {state_error}")
            
            raise
    
    def transform_complete_helioscope_data(self, helioscope_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform complete Helioscope data to unified project model."""
        project_info = helioscope_data.get('project_info', {})
        simulation_data = helioscope_data.get('simulation_data', {})
        bom_data = helioscope_data.get('bom_data', {})
        
        # Extract production metrics from simulation data
        production_report = simulation_data.get('production_report', {})
        
        return {
            "system_specs": {
                "system_size_dc_kw": project_info.get('system', {}).get('dc_capacity_kw', 0),
                "system_size_ac_kw": project_info.get('system', {}).get('ac_capacity_kw', 0),
                "module_count": bom_data.get('modules', {}).get('quantity', 0),
                "inverter_count": bom_data.get('inverters', {}).get('quantity', 1),
                "bill_of_materials": self._transform_bom_data(bom_data)
            },
            "production_metrics": {
                "annual_production_kwh": production_report.get('annual_yield_kwh', 0),
                "specific_yield": production_report.get('specific_yield', 1.4),
                "performance_ratio": production_report.get('performance_ratio', 0.85),
                "kwh_per_kw": production_report.get('kwh_per_kw', 1400),
                "capacity_factor": production_report.get('capacity_factor', 0.16),
                "monthly_production": production_report.get('monthly_yield', [])
            },
            "project_documents": {
                "pv_layout_pdf_url": helioscope_data.get('site_images', {}).get('layout_url'),
                "dxf_files": helioscope_data.get('dxf_files', {}),
                "one_line_diagram": helioscope_data.get('one_line_diagram', {})
            },
            "milestones": {
                "engineering": "Completed",
                "design": "Completed"
            }
        }
    
    def _transform_bom_data(self, bom_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform Helioscope BOM data to our format."""
        bom_items = []
        
        # Modules
        if 'modules' in bom_data:
            modules = bom_data['modules']
            bom_items.append({
                'component_type': 'module',
                'manufacturer': modules.get('manufacturer'),
                'model': modules.get('model'),
                'quantity': modules.get('quantity', 0),
                'unit_cost': modules.get('unit_cost')
            })
        
        # Inverters
        if 'inverters' in bom_data:
            inverters = bom_data['inverters']
            bom_items.append({
                'component_type': 'inverter',
                'manufacturer': inverters.get('manufacturer'),
                'model': inverters.get('model'),
                'quantity': inverters.get('quantity', 0),
                'unit_cost': inverters.get('unit_cost')
            })
        
        # Wiring/other components
        if 'wiring' in bom_data:
            wiring = bom_data['wiring']
            bom_items.append({
                'component_type': 'wiring',
                'manufacturer': wiring.get('manufacturer'),
                'model': wiring.get('type'),
                'quantity': wiring.get('length_feet', 0),
                'unit_cost': wiring.get('cost_per_foot')
            })
        
        return bom_items
    
    async def _trigger_feasibility_analysis(self, project_id: str, run_id: str):
        """Trigger comprehensive feasibility analysis for Helioscope projects."""
        try:
            # Use the enhanced Helioscope feasibility workflow
            from .project_service import ProjectService
            project_service = ProjectService()
            feasibility_result = await project_service.process_helioscope_feasibility(project_id, run_id)
            
            logger.info(f"Comprehensive feasibility analysis completed for {project_id}, run {run_id}")
            return feasibility_result
            
        except Exception as e:
            logger.warning(f"Failed to trigger feasibility analysis for {project_id}, run {run_id}: {str(e)}")
            raise 