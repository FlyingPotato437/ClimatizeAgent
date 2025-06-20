"""
Minimal financial service for cost modeling and analysis.
"""
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class FinancialService:
    """Service for financial modeling and analysis."""
    
    def __init__(self):
        pass
    
    async def calculate_capex(self, system_specs: Dict[str, Any]) -> float:
        """Calculate capital expenditure for a system."""
        system_size_kw = system_specs.get('system_size_dc_kw', 0)
        
        # Simplified cost calculation: $3/W
        capex = system_size_kw * 1000 * 3.0
        
        logger.info(f"Calculated CAPEX: ${capex:,.2f} for {system_size_kw}kW system")
        return capex
    
    async def generate_pro_forma(self, project: Dict[str, Any]) -> Dict[str, Any]:
        """Generate financial pro forma."""
        system_size_kw = project.get('system_specs', {}).get('system_size_dc_kw', 0)
        capex = await self.calculate_capex(project.get('system_specs', {}))
        
        # Simplified pro forma
        return {
            "capex_total": capex,
            "capex_per_watt": 3.0,
            "itc_percentage": 0.30,
            "itc_amount": capex * 0.30,
            "simple_payback_years": 8.5,
            "irr_band_low": 0.12,
            "irr_band_high": 0.18,
            "lcoe_cents_per_kwh": 6.5,
            "net_present_value": capex * 0.25
        }
    
    async def calculate_financing_options(self, capex: float) -> List[Dict[str, Any]]:
        """Calculate available financing options."""
        return [
            {
                "source_type": "climatize_loan",
                "amount": capex * 0.80,
                "rate": 0.065,
                "terms": "15 years"
            },
            {
                "source_type": "equity",
                "amount": capex * 0.20,
                "rate": 0.0,
                "terms": "Owner equity"
            }
        ] 