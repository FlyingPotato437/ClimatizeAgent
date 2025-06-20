"""
Mock Helioscope adapter for development and testing.
Provides realistic sample data without requiring actual Helioscope API access.
"""
import logging
from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class MockHelioscopeAdapter:
    """Mock adapter that returns realistic Helioscope API responses for development."""
    
    def __init__(self):
        self.api_base_url = "https://api.helioscope.com/v1"  # For consistency
        
    async def fetch_project_info(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Mock project info response."""
        await asyncio.sleep(0.5)  # Simulate API delay
        
        return {
            "project_id": project_id,
            "name": f"Solar Project {project_id[-4:]}",
            "status": "completed",
            "created_date": "2024-01-15T10:30:00Z",
            "site": {
                "address": "123 Solar Street, San Francisco, CA 94107",
                "latitude": 37.7749,
                "longitude": -122.4194,
                "elevation_m": 15,
                "roof_type": "flat",
                "roof_area_sqm": 1200
            },
            "system": {
                "dc_capacity_kw": 150.5,
                "ac_capacity_kw": 125.2,
                "module_count": 335,
                "inverter_count": 5,
                "tilt_angle": 20,
                "azimuth": 180,
                "design_type": "commercial_rooftop"
            },
            "weather_data": {
                "annual_irradiance_kwh_m2": 1650,
                "weather_station": "San Francisco Airport",
                "climate_zone": "3C"
            }
        }
    
    async def fetch_dxf_files(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Mock DXF files response."""
        await asyncio.sleep(0.3)
        
        return {
            "files": [
                {
                    "filename": f"layout_{project_id}.dxf",
                    "file_type": "layout",
                    "size_bytes": 245760,
                    "download_url": f"https://mock-storage.helioscope.com/files/{project_id}/layout.dxf",
                    "created_date": "2024-01-15T10:35:00Z"
                },
                {
                    "filename": f"single_line_{project_id}.dxf", 
                    "file_type": "single_line_diagram",
                    "size_bytes": 89120,
                    "download_url": f"https://mock-storage.helioscope.com/files/{project_id}/single_line.dxf",
                    "created_date": "2024-01-15T10:36:00Z"
                }
            ]
        }
    
    async def fetch_site_images(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Mock site images response."""
        await asyncio.sleep(0.2)
        
        return {
            "images": [
                {
                    "filename": f"aerial_view_{project_id}.jpg",
                    "image_type": "aerial",
                    "size_bytes": 1456789,
                    "download_url": f"https://mock-storage.helioscope.com/images/{project_id}/aerial.jpg",
                    "width": 2048,
                    "height": 1536,
                    "created_date": "2024-01-15T10:32:00Z"
                },
                {
                    "filename": f"layout_overlay_{project_id}.png",
                    "image_type": "layout_overlay", 
                    "size_bytes": 987654,
                    "download_url": f"https://mock-storage.helioscope.com/images/{project_id}/layout_overlay.png",
                    "width": 2048,
                    "height": 1536,
                    "created_date": "2024-01-15T10:37:00Z"
                }
            ],
            "layout_url": f"https://mock-storage.helioscope.com/images/{project_id}/layout_overlay.png"
        }
    
    async def fetch_simulation_data(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Mock simulation data with production, shading, irradiance, and soiling data."""
        await asyncio.sleep(1.0)  # Simulation data takes longer
        
        # Generate realistic monthly production data
        monthly_production = [8450, 9920, 13150, 15200, 16800, 17500, 
                            17200, 16100, 14300, 11800, 9200, 7900]
        
        return {
            "production_report": {
                "annual_yield_kwh": 157520,
                "specific_yield": 1046,  # kWh/kWp
                "performance_ratio": 0.84,
                "kwh_per_kw": 1046,
                "capacity_factor": 0.119,
                "monthly_yield": monthly_production,
                "dcac_ratio": 1.20,
                "clipping_percentage": 2.3,
                "system_degradation_rate": 0.005
            },
            "shade_report": {
                "annual_shade_loss_percentage": 3.2,
                "near_field_shading": 1.8,
                "far_field_shading": 1.4,
                "self_shading": 0.8,
                "monthly_shade_loss": [4.1, 3.8, 3.5, 2.9, 2.4, 2.1, 
                                     2.2, 2.6, 3.1, 3.7, 4.0, 4.3]
            },
            "irradiance": {
                "global_horizontal_irradiance": 1650,
                "direct_normal_irradiance": 1420,
                "diffuse_horizontal_irradiance": 580,
                "plane_of_array_irradiance": 1710,
                "monthly_ghi": [95, 115, 165, 210, 240, 265, 
                              250, 225, 185, 145, 105, 85]
            },
            "soiling": {
                "annual_soiling_loss_percentage": 2.1,
                "cleaning_schedule": "quarterly",
                "soil_type": "urban_dust",
                "rainfall_cleaning_factor": 0.7,
                "monthly_soiling_loss": [2.8, 2.5, 2.1, 1.8, 1.6, 1.9,
                                       2.3, 2.7, 2.4, 2.0, 2.2, 2.6]
            }
        }
    
    async def fetch_line_item_quantities(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Mock Bill of Materials data."""
        await asyncio.sleep(0.4)
        
        return {
            "modules": {
                "manufacturer": "Canadian Solar",
                "model": "CS7N-450MS",
                "power_rating_w": 450,
                "quantity": 335,
                "unit_cost": 0.42,
                "total_cost": 62790
            },
            "inverters": {
                "manufacturer": "SMA",
                "model": "SC 25000TL-US",
                "power_rating_w": 25000,
                "quantity": 5,
                "unit_cost": 2100,
                "total_cost": 10500
            },
            "wiring": {
                "manufacturer": "Encore Wire",
                "type": "THWN-2 12 AWG",
                "length_feet": 2850,
                "cost_per_foot": 1.25,
                "total_cost": 3562.50
            },
            "racking": {
                "manufacturer": "IronRidge",
                "type": "XR1000 Ballasted",
                "quantity": 168,
                "unit_cost": 45,
                "total_cost": 7560
            },
            "electrical": {
                "combiner_boxes": 8,
                "disconnect_switches": 2,
                "monitoring_system": 1,
                "conduit_feet": 450,
                "total_electrical_cost": 8950
            },
            "total_material_cost": 93362.50,
            "labor_cost_estimate": 22500,
            "total_system_cost": 115862.50,
            "cost_per_watt": 0.77
        }
    
    async def generate_one_line_diagram(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Mock one-line diagram generation."""
        await asyncio.sleep(0.6)
        
        return {
            "diagram_url": f"https://mock-storage.helioscope.com/diagrams/{project_id}/single_line.pdf",
            "diagram_type": "single_line_electrical",
            "file_format": "pdf",
            "size_bytes": 156890,
            "created_date": datetime.now(timezone.utc).isoformat(),
            "components": {
                "pv_modules": 335,
                "string_inverters": 5,
                "combiner_boxes": 8,
                "disconnect_switches": 2,
                "utility_meter": 1,
                "monitoring_system": 1
            }
        }
    
    async def fetch_design_data(self, design_id: str) -> Dict[str, Any]:
        """Mock design data fetch."""
        await asyncio.sleep(0.3)
        
        return {
            "design_id": design_id,
            "status": "completed",
            "created_date": "2024-01-15T10:30:00Z",
            "system": {
                "dc_capacity_kw": 150.5,
                "ac_capacity_kw": 125.2,
                "module_count": 335,
                "annual_production_kwh": 157520
            },
            "performance": {
                "specific_yield": 1046,
                "performance_ratio": 0.84
            }
        }


class MockHelioscopeServiceDecorator:
    """
    Decorator that can wrap the real HelioscoperService to use mock data in development.
    This allows easy switching between mock and real API calls.
    """
    
    def __init__(self, real_service, use_mock: bool = True):
        self.real_service = real_service
        self.mock_adapter = MockHelioscopeAdapter()
        self.use_mock = use_mock
        
        # Copy other attributes from real service
        self.db_client = real_service.db_client
        self.workflow_state = real_service.workflow_state
        self.api_base_url = real_service.api_base_url
        self.api_key = real_service.api_key
        self.headers = real_service.headers
    
    async def fetch_project_info(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Use mock or real data based on configuration."""
        if self.use_mock:
            logger.info(f"Using MOCK data for fetch_project_info: {project_id}")
            return await self.mock_adapter.fetch_project_info(project_id, helioscope_credentials)
        else:
            return await self.real_service.fetch_project_info(project_id, helioscope_credentials)
    
    async def fetch_dxf_files(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Use mock or real data based on configuration."""
        if self.use_mock:
            logger.info(f"Using MOCK data for fetch_dxf_files: {project_id}")
            return await self.mock_adapter.fetch_dxf_files(project_id, helioscope_credentials)
        else:
            return await self.real_service.fetch_dxf_files(project_id, helioscope_credentials)
    
    async def fetch_site_images(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Use mock or real data based on configuration."""
        if self.use_mock:
            logger.info(f"Using MOCK data for fetch_site_images: {project_id}")
            return await self.mock_adapter.fetch_site_images(project_id, helioscope_credentials)
        else:
            return await self.real_service.fetch_site_images(project_id, helioscope_credentials)
    
    async def fetch_simulation_data(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Use mock or real data based on configuration."""
        if self.use_mock:
            logger.info(f"Using MOCK data for fetch_simulation_data: {project_id}")
            return await self.mock_adapter.fetch_simulation_data(project_id, helioscope_credentials)
        else:
            return await self.real_service.fetch_simulation_data(project_id, helioscope_credentials)
    
    async def fetch_line_item_quantities(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Use mock or real data based on configuration."""
        if self.use_mock:
            logger.info(f"Using MOCK data for fetch_line_item_quantities: {project_id}")
            return await self.mock_adapter.fetch_line_item_quantities(project_id, helioscope_credentials)
        else:
            return await self.real_service.fetch_line_item_quantities(project_id, helioscope_credentials)
    
    async def generate_one_line_diagram(self, project_id: str, helioscope_credentials: Dict[str, str]) -> Dict[str, Any]:
        """Use mock or real data based on configuration."""
        if self.use_mock:
            logger.info(f"Using MOCK data for generate_one_line_diagram: {project_id}")
            return await self.mock_adapter.generate_one_line_diagram(project_id, helioscope_credentials)
        else:
            return await self.real_service.generate_one_line_diagram(project_id, helioscope_credentials)
    
    async def fetch_design_data(self, design_id: str) -> Dict[str, Any]:
        """Use mock or real data based on configuration."""
        if self.use_mock:
            logger.info(f"Using MOCK data for fetch_design_data: {design_id}")
            return await self.mock_adapter.fetch_design_data(design_id)
        else:
            return await self.real_service.fetch_design_data(design_id)
    
    def __getattr__(self, name):
        """Delegate any other method calls to the real service."""
        return getattr(self.real_service, name)