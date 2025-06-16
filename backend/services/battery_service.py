"""
Battery sizing and energy storage service.
"""
import logging
from typing import Dict, Any, List, Optional
from ..core.database import get_db_client
from ..models.project import BatterySpecs

logger = logging.getLogger(__name__)

class BatteryService:
    """Service for battery sizing and energy storage calculations."""
    
    def __init__(self):
        self.db_client = get_db_client()
    
    async def sizing_engine(self, project_id: str) -> Dict[str, Any]:
        """
        Main battery sizing engine processing.
        
        Args:
            project_id: The project ID to process
            
        Returns:
            Dict containing battery sizing results
        """
        try:
            logger.info(f"Starting battery sizing for project {project_id}")
            
            # Get project from database
            project = await self.db_client.get_project(project_id)
            if not project:
                raise ValueError(f"Project {project_id} not found")
            
            # Update milestones
            if 'milestones' not in project:
                project['milestones'] = {}
            project['milestones']['battery_sizing'] = 'In Progress'
            await self.db_client.update_project(project_id, project)
            
            # Perform battery sizing analysis
            battery_analysis = self._calculate_optimal_battery_size(project)
            
            # Update project with battery data
            project['battery_specs'] = battery_analysis['battery_specs']
            project['energy_storage_analysis'] = battery_analysis['analysis']
            project['milestones']['battery_sizing'] = 'Completed'
            
            await self.db_client.update_project(project_id, project)
            
            # Trigger next stage
            await self._trigger_interconnection_scoring(project_id)
            
            logger.info(f"Completed battery sizing for project {project_id}")
            return battery_analysis
            
        except Exception as e:
            logger.error(f"Error in battery sizing for {project_id}: {str(e)}")
            # Update milestone to failed
            project = await self.db_client.get_project(project_id)
            if project:
                project['milestones']['battery_sizing'] = 'Failed'
                await self.db_client.update_project(project_id, project)
            raise
    
    def _calculate_optimal_battery_size(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal battery size based on project requirements."""
        system_specs = project.get('system_specs', {})
        production_metrics = project.get('production_metrics', {})
        address = project.get('address', {})
        
        # Get system size and production
        system_size_kw = system_specs.get('system_size_dc_kw', 100)
        annual_production_kwh = production_metrics.get('annual_production_kwh', system_size_kw * 1400)
        annual_load_kwh = system_specs.get('annual_kwh_load', annual_production_kwh * 0.8)
        
        # Calculate battery sizing options
        battery_options = self._generate_battery_options(system_size_kw, annual_load_kwh)
        
        # Select optimal option based on economics and requirements
        optimal_battery = self._select_optimal_battery(battery_options, project)
        
        # Calculate energy storage benefits
        storage_benefits = self._calculate_storage_benefits(optimal_battery, project)
        
        return {
            "battery_specs": optimal_battery,
            "analysis": {
                "options_considered": battery_options,
                "selection_criteria": self._get_selection_criteria(),
                "economic_benefits": storage_benefits,
                "backup_duration_hours": optimal_battery.get('backup_duration_hours', 4),
                "daily_cycles": 1.2,
                "round_trip_efficiency": 0.95
            }
        }
    
    def _generate_battery_options(self, system_size_kw: float, annual_load_kwh: float) -> List[Dict[str, Any]]:
        """Generate different battery sizing options."""
        daily_load_kwh = annual_load_kwh / 365
        
        options = []
        
        # Option 1: Backup essentials (4 hours)
        backup_essentials = {
            "name": "Backup Essentials",
            "capacity_kwh": min(20, daily_load_kwh * 0.3),
            "power_rating_kw": min(10, system_size_kw * 0.3),
            "backup_duration_hours": 4,
            "use_case": "Emergency backup for essential loads",
            "estimated_cost": 15000,
            "annual_savings": 500
        }
        options.append(backup_essentials)
        
        # Option 2: Partial self-consumption (8 hours)
        partial_consumption = {
            "name": "Partial Self-Consumption",
            "capacity_kwh": min(40, daily_load_kwh * 0.6),
            "power_rating_kw": min(15, system_size_kw * 0.5),
            "backup_duration_hours": 8,
            "use_case": "Time-of-use arbitrage + backup",
            "estimated_cost": 25000,
            "annual_savings": 1200
        }
        options.append(partial_consumption)
        
        # Option 3: Full self-consumption (12+ hours)
        full_consumption = {
            "name": "Full Self-Consumption",
            "capacity_kwh": min(80, daily_load_kwh),
            "power_rating_kw": min(25, system_size_kw * 0.8),
            "backup_duration_hours": 12,
            "use_case": "Maximum independence + backup",
            "estimated_cost": 45000,
            "annual_savings": 2000
        }
        options.append(full_consumption)
        
        return options
    
    def _select_optimal_battery(self, options: List[Dict[str, Any]], project: Dict[str, Any]) -> Dict[str, Any]:
        """Select the optimal battery option based on project criteria."""
        address = project.get('address', {})
        system_specs = project.get('system_specs', {})
        
        # Get state for incentive considerations
        state = address.get('state', '').upper()
        
        # Score each option
        scored_options = []
        for option in options:
            score = self._score_battery_option(option, project, state)
            scored_options.append({**option, "score": score})
        
        # Select highest scoring option
        optimal = max(scored_options, key=lambda x: x['score'])
        
        # Convert to BatterySpecs format
        return {
            "battery_type": "lithium_ion",
            "capacity_kwh": optimal['capacity_kwh'],
            "power_rating_kw": optimal['power_rating_kw'],
            "manufacturer": "Tesla",  # Default premium option
            "model": "Powerwall 2",
            "warranty_years": 10,
            "cycles_warranty": 10000,
            "round_trip_efficiency": 0.95,
            "backup_duration_hours": optimal['backup_duration_hours'],
            "estimated_cost": optimal['estimated_cost'],
            "selection_rationale": f"Selected {optimal['name']} based on optimal ROI and use case fit"
        }
    
    def _score_battery_option(self, option: Dict[str, Any], project: Dict[str, Any], state: str) -> float:
        """Score a battery option based on multiple criteria."""
        score = 0
        
        # Economic score (ROI)
        roi = option['annual_savings'] / option['estimated_cost'] if option['estimated_cost'] > 0 else 0
        score += roi * 30  # Weight economic factors heavily
        
        # State incentive bonus
        if state in ['CA', 'NY', 'MA', 'HI']:  # States with storage incentives
            score += 5
        
        # Backup duration score
        if option['backup_duration_hours'] >= 8:
            score += 3
        elif option['backup_duration_hours'] >= 4:
            score += 1
        
        # Size appropriateness (not too big, not too small)
        system_size = project.get('system_specs', {}).get('system_size_dc_kw', 100)
        if 0.3 <= (option['capacity_kwh'] / system_size) <= 0.8:
            score += 2
        
        return score
    
    def _calculate_storage_benefits(self, battery_specs: Dict[str, Any], project: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate the economic and operational benefits of energy storage."""
        capacity_kwh = battery_specs.get('capacity_kwh', 0)
        power_kw = battery_specs.get('power_rating_kw', 0)
        
        # Calculate annual cycling and savings
        daily_cycles = 1.2  # Typical for solar + storage
        annual_cycles = daily_cycles * 365
        
        # Time-of-use arbitrage savings
        tou_savings = capacity_kwh * daily_cycles * 0.15 * 365  # $0.15/kWh arbitrage
        
        # Demand charge reduction
        demand_savings = power_kw * 12 * 15  # $15/kW/month typical
        
        # Backup value (harder to quantify)
        backup_value = 1000  # Annual value of backup capability
        
        total_savings = tou_savings + demand_savings + backup_value
        
        return {
            "annual_savings": round(total_savings),
            "tou_arbitrage_savings": round(tou_savings),
            "demand_charge_savings": round(demand_savings),
            "backup_value": backup_value,
            "payback_period_years": round(battery_specs.get('estimated_cost', 0) / total_savings, 1) if total_savings > 0 else 99,
            "lifetime_savings": round(total_savings * 10),  # 10-year analysis
            "environmental_benefits": {
                "co2_avoided_lbs_annually": capacity_kwh * annual_cycles * 0.85,  # lbs CO2/kWh grid
                "renewable_energy_stored_kwh": capacity_kwh * annual_cycles * 0.8
            }
        }
    
    def _get_selection_criteria(self) -> List[str]:
        """Get the criteria used for battery selection."""
        return [
            "Return on investment (ROI)",
            "Backup duration requirements",
            "System size compatibility", 
            "State incentive availability",
            "Use case alignment",
            "Technology maturity and warranty"
        ]
    
    async def _trigger_interconnection_scoring(self, project_id: str):
        """Trigger the interconnection scoring engine."""
        try:
            from .interconnection_service import InterconnectionService
            interconnection_service = InterconnectionService()
            await interconnection_service.scoring_engine(project_id)
        except Exception as e:
            logger.warning(f"Failed to trigger interconnection scoring: {str(e)}")
    
    def calculate_storage_economics(self, battery_specs: Dict[str, Any], utility_rates: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate detailed storage economics based on utility rates."""
        capacity_kwh = battery_specs.get('capacity_kwh', 0)
        
        # Time-of-use rate differential
        peak_rate = utility_rates.get('peak_rate', 0.25)
        off_peak_rate = utility_rates.get('off_peak_rate', 0.12)
        rate_differential = peak_rate - off_peak_rate
        
        # Daily arbitrage potential
        daily_arbitrage = capacity_kwh * rate_differential * 0.95  # 95% efficiency
        annual_arbitrage = daily_arbitrage * 300  # 300 cycling days per year
        
        return {
            "daily_arbitrage_value": round(daily_arbitrage, 2),
            "annual_arbitrage_value": round(annual_arbitrage),
            "rate_differential": round(rate_differential, 3),
            "cycling_days_per_year": 300
        } 