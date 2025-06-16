"""
Helioscope integration service for solar design and analysis.
"""
import logging
from typing import Dict, Any, Optional
import asyncio
import requests
from ..core.database import get_db_client
from ..core.config import settings

logger = logging.getLogger(__name__)

class HelioscoperService:
    """Service for Helioscope API integration and design processing."""
    
    def __init__(self):
        self.db_client = get_db_client()
        self.api_base_url = "https://api.helioscope.com/v1"
        self.api_key = settings.HELIOSCOPE_API_KEY
    
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
            
            # Trigger next stage
            await self._trigger_battery_sizing(project_id)
            
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
            response = requests.post(
                f"{self.api_base_url}/designs",
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
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
    
    async def _trigger_battery_sizing(self, project_id: str):
        """Trigger the battery sizing engine."""
        # In Azure Functions, this would use queue trigger
        # For now, we'll implement as direct call
        try:
            from .battery_service import BatteryService
            battery_service = BatteryService()
            await battery_service.sizing_engine(project_id)
        except Exception as e:
            logger.warning(f"Failed to trigger battery sizing: {str(e)}")
    
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
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.get(
                f"{self.api_base_url}/designs/{design_id}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Helioscope design {design_id}: {str(e)}")
            raise 