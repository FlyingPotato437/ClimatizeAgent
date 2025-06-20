"""
Feasibility Analysis Engine for Solar Projects.
This is the core business value component that reduces project failure rates.
"""
import logging
from typing import Dict, Any, List, Optional, Protocol
from abc import ABC, abstractmethod
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class FeasibilityRule(Protocol):
    """Protocol defining the structure for all feasibility rules."""
    
    rule_id: str
    description: str
    severity: str  # 'critical', 'high', 'medium', 'low'
    category: str  # 'production', 'financial', 'technical', 'regulatory'
    
    def evaluate(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluates a rule against project data.
        
        Returns:
            Dict with keys: 'pass' (bool), 'score' (0-100), 'message' (str), 'details' (dict)
        """
        ...


class ProductionThresholdRule:
    """Checks if annual production meets minimum kWh/kWp threshold."""
    
    rule_id = "PROD_001"
    description = "Annual production must meet minimum specific yield threshold"
    severity = "critical"
    category = "production"
    
    def __init__(self, min_specific_yield: float = 1000.0):
        self.min_specific_yield = min_specific_yield
    
    def evaluate(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        production_metrics = project_data.get("production_metrics", {})
        specific_yield = production_metrics.get("specific_yield")
        
        if specific_yield is None:
            return {
                "pass": False,
                "score": 0,
                "message": "Specific yield data not available",
                "details": {"threshold": self.min_specific_yield}
            }
        
        is_pass = specific_yield >= self.min_specific_yield
        score = min(100, (specific_yield / self.min_specific_yield) * 100)
        
        return {
            "pass": is_pass,
            "score": round(score, 1),
            "message": f"Specific yield: {specific_yield} kWh/kWp (threshold: {self.min_specific_yield})",
            "details": {
                "actual_yield": specific_yield,
                "threshold": self.min_specific_yield,
                "delta": specific_yield - self.min_specific_yield
            }
        }


class PerformanceRatioRule:
    """Checks if system performance ratio is acceptable."""
    
    rule_id = "PROD_002"
    description = "System performance ratio must be above minimum threshold"
    severity = "high"
    category = "production"
    
    def __init__(self, min_performance_ratio: float = 0.75):
        self.min_performance_ratio = min_performance_ratio
    
    def evaluate(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        production_metrics = project_data.get("production_metrics", {})
        performance_ratio = production_metrics.get("performance_ratio")
        
        if performance_ratio is None:
            return {
                "pass": False,
                "score": 0,
                "message": "Performance ratio data not available",
                "details": {"threshold": self.min_performance_ratio}
            }
        
        is_pass = performance_ratio >= self.min_performance_ratio
        score = min(100, (performance_ratio / self.min_performance_ratio) * 100)
        
        return {
            "pass": is_pass,
            "score": round(score, 1),
            "message": f"Performance ratio: {performance_ratio:.2f} (threshold: {self.min_performance_ratio:.2f})",
            "details": {
                "actual_ratio": performance_ratio,
                "threshold": self.min_performance_ratio,
                "delta": performance_ratio - self.min_performance_ratio
            }
        }


class InverterClippingRule:
    """Checks if inverter clipping is within acceptable limits."""
    
    rule_id = "TECH_001"
    description = "Inverter clipping must be below maximum threshold"
    severity = "medium"
    category = "technical"
    
    def __init__(self, max_clipping_percentage: float = 5.0):
        self.max_clipping_percentage = max_clipping_percentage
    
    def evaluate(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        simulation_data = project_data.get("simulation_data", {})
        production_report = simulation_data.get("production_report", {})
        clipping_percentage = production_report.get("clipping_percentage")
        
        if clipping_percentage is None:
            # If clipping data not available, calculate from DC/AC ratio
            system_specs = project_data.get("system_specs", {})
            dc_capacity = system_specs.get("system_size_dc_kw", 0)
            ac_capacity = system_specs.get("system_size_ac_kw", 0)
            
            if dc_capacity > 0 and ac_capacity > 0:
                dc_ac_ratio = dc_capacity / ac_capacity
                # Estimate clipping based on DC/AC ratio
                if dc_ac_ratio > 1.3:
                    clipping_percentage = (dc_ac_ratio - 1.3) * 10  # Rough estimate
                else:
                    clipping_percentage = 0
            else:
                return {
                    "pass": False,
                    "score": 0,
                    "message": "Clipping data not available and cannot be estimated",
                    "details": {"threshold": self.max_clipping_percentage}
                }
        
        is_pass = clipping_percentage <= self.max_clipping_percentage
        # Score inversely related to clipping percentage
        score = max(0, 100 - (clipping_percentage / self.max_clipping_percentage) * 100)
        
        return {
            "pass": is_pass,
            "score": round(score, 1),
            "message": f"Inverter clipping: {clipping_percentage:.1f}% (max: {self.max_clipping_percentage}%)",
            "details": {
                "actual_clipping": clipping_percentage,
                "threshold": self.max_clipping_percentage,
                "delta": self.max_clipping_percentage - clipping_percentage
            }
        }


class SystemSizeRule:
    """Checks if system size is within reasonable bounds."""
    
    rule_id = "TECH_002"
    description = "System size must be within reasonable bounds for site"
    severity = "high"
    category = "technical"
    
    def __init__(self, min_size_kw: float = 10.0, max_size_kw: float = 5000.0):
        self.min_size_kw = min_size_kw
        self.max_size_kw = max_size_kw
    
    def evaluate(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        system_specs = project_data.get("system_specs", {})
        system_size = system_specs.get("system_size_dc_kw")
        
        if system_size is None or system_size <= 0:
            return {
                "pass": False,
                "score": 0,
                "message": "System size not specified or invalid",
                "details": {"min_size": self.min_size_kw, "max_size": self.max_size_kw}
            }
        
        is_pass = self.min_size_kw <= system_size <= self.max_size_kw
        
        # Score based on how reasonable the size is
        if is_pass:
            score = 100
        elif system_size < self.min_size_kw:
            score = (system_size / self.min_size_kw) * 100
        else:  # system_size > self.max_size_kw
            score = max(0, 100 - ((system_size - self.max_size_kw) / self.max_size_kw) * 50)
        
        return {
            "pass": is_pass,
            "score": round(score, 1),
            "message": f"System size: {system_size:.1f} kW (range: {self.min_size_kw}-{self.max_size_kw} kW)",
            "details": {
                "actual_size": system_size,
                "min_threshold": self.min_size_kw,
                "max_threshold": self.max_size_kw
            }
        }


class ShadingLossRule:
    """Checks if shading losses are within acceptable limits."""
    
    rule_id = "PROD_003"
    description = "Annual shading losses must be below maximum threshold"
    severity = "medium"
    category = "production"
    
    def __init__(self, max_shading_loss: float = 10.0):
        self.max_shading_loss = max_shading_loss
    
    def evaluate(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        simulation_data = project_data.get("simulation_data", {})
        shade_report = simulation_data.get("shade_report", {})
        shading_loss = shade_report.get("annual_shade_loss_percentage")
        
        if shading_loss is None:
            return {
                "pass": False,
                "score": 50,  # Neutral score when data unavailable
                "message": "Shading analysis data not available",
                "details": {"threshold": self.max_shading_loss}
            }
        
        is_pass = shading_loss <= self.max_shading_loss
        score = max(0, 100 - (shading_loss / self.max_shading_loss) * 100)
        
        return {
            "pass": is_pass,
            "score": round(score, 1),
            "message": f"Annual shading loss: {shading_loss:.1f}% (max: {self.max_shading_loss}%)",
            "details": {
                "actual_loss": shading_loss,
                "threshold": self.max_shading_loss,
                "delta": self.max_shading_loss - shading_loss
            }
        }


class FinancialViabilityRule:
    """Basic financial viability check based on cost per watt."""
    
    rule_id = "FIN_001"
    description = "Cost per watt must be within reasonable market range"
    severity = "high"
    category = "financial"
    
    def __init__(self, min_cost_per_watt: float = 0.5, max_cost_per_watt: float = 3.0):
        self.min_cost_per_watt = min_cost_per_watt
        self.max_cost_per_watt = max_cost_per_watt
    
    def evaluate(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        system_specs = project_data.get("system_specs", {})
        bom = system_specs.get("bill_of_materials", [])
        
        # Try to get cost from BOM or simulation data
        cost_per_watt = None
        
        # Look for cost data in various places
        simulation_data = project_data.get("simulation_data", {})
        if "cost_per_watt" in simulation_data:
            cost_per_watt = simulation_data["cost_per_watt"]
        elif isinstance(bom, list) and bom:
            # Calculate from BOM if available
            total_cost = sum(item.get("total_cost", 0) for item in bom)
            system_size_w = system_specs.get("system_size_dc_kw", 0) * 1000
            if total_cost > 0 and system_size_w > 0:
                cost_per_watt = total_cost / system_size_w
        
        if cost_per_watt is None:
            return {
                "pass": False,
                "score": 50,
                "message": "Cost data not available for analysis",
                "details": {"min_cost": self.min_cost_per_watt, "max_cost": self.max_cost_per_watt}
            }
        
        is_pass = self.min_cost_per_watt <= cost_per_watt <= self.max_cost_per_watt
        
        # Score based on how reasonable the cost is (optimal around $1.50/W)
        optimal_cost = 1.5
        if is_pass:
            score = max(70, 100 - abs(cost_per_watt - optimal_cost) * 20)
        else:
            score = 30  # Below threshold for out-of-range costs
        
        return {
            "pass": is_pass,
            "score": round(score, 1),
            "message": f"Cost per watt: ${cost_per_watt:.2f}/W (range: ${self.min_cost_per_watt}-${self.max_cost_per_watt}/W)",
            "details": {
                "actual_cost": cost_per_watt,
                "min_threshold": self.min_cost_per_watt,
                "max_threshold": self.max_cost_per_watt,
                "optimal_cost": optimal_cost
            }
        }


class FeasibilityAnalysisEngine:
    """Main engine that orchestrates all feasibility rules and generates final assessment."""
    
    def __init__(self, rules: Optional[List[FeasibilityRule]] = None):
        if rules is None:
            # Default rule set with reasonable thresholds
            self.rules = [
                ProductionThresholdRule(min_specific_yield=900),  # kWh/kWp
                PerformanceRatioRule(min_performance_ratio=0.75),
                InverterClippingRule(max_clipping_percentage=5.0),  # %
                SystemSizeRule(min_size_kw=10.0, max_size_kw=5000.0),
                ShadingLossRule(max_shading_loss=15.0),  # %
                FinancialViabilityRule(min_cost_per_watt=0.5, max_cost_per_watt=3.0)
            ]
        else:
            self.rules = rules
    
    def analyze_project(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive feasibility analysis on a project.
        
        Returns:
            Dict containing overall feasibility assessment
        """
        rule_results = []
        critical_failures = 0
        high_failures = 0
        total_score = 0
        total_weight = 0
        
        # Weight rules by severity
        severity_weights = {
            "critical": 4.0,
            "high": 2.0, 
            "medium": 1.0,
            "low": 0.5
        }
        
        for rule in self.rules:
            try:
                result = rule.evaluate(project_data)
                
                # Add rule metadata to result
                result.update({
                    "rule_id": rule.rule_id,
                    "description": rule.description,
                    "severity": rule.severity,
                    "category": rule.category
                })
                
                rule_results.append(result)
                
                # Track failures by severity
                if not result["pass"]:
                    if rule.severity == "critical":
                        critical_failures += 1
                    elif rule.severity == "high":
                        high_failures += 1
                
                # Calculate weighted score
                weight = severity_weights.get(rule.severity, 1.0)
                total_score += result["score"] * weight
                total_weight += weight
                
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
                rule_results.append({
                    "rule_id": rule.rule_id,
                    "description": rule.description,
                    "severity": rule.severity,
                    "category": rule.category,
                    "pass": False,
                    "score": 0,
                    "message": f"Rule evaluation failed: {str(e)}",
                    "details": {}
                })
        
        # Calculate overall score
        overall_score = round(total_score / total_weight if total_weight > 0 else 0, 1)
        
        # Determine overall viability
        is_viable = True
        viability_reason = "Project meets all feasibility criteria"
        
        if critical_failures > 0:
            is_viable = False
            viability_reason = f"Project has {critical_failures} critical failure(s)"
        elif high_failures >= 2:
            is_viable = False
            viability_reason = f"Project has {high_failures} high-severity failures"
        elif overall_score < 60:
            is_viable = False
            viability_reason = f"Overall feasibility score too low ({overall_score}/100)"
        
        # Generate risk assessment
        risk_level = self._assess_risk_level(overall_score, critical_failures, high_failures)
        recommendations = self._generate_recommendations(rule_results)
        
        return {
            "is_viable": is_viable,
            "overall_score": overall_score,
            "viability_reason": viability_reason,
            "risk_level": risk_level,
            "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
            "summary": {
                "total_rules": len(self.rules),
                "passed_rules": sum(1 for r in rule_results if r["pass"]),
                "critical_failures": critical_failures,
                "high_failures": high_failures,
                "average_score": overall_score
            },
            "rule_results": rule_results,
            "recommendations": recommendations
        }
    
    def _assess_risk_level(self, overall_score: float, critical_failures: int, high_failures: int) -> str:
        """Assess overall project risk level."""
        if critical_failures > 0:
            return "CRITICAL"
        elif high_failures >= 2 or overall_score < 50:
            return "HIGH"
        elif high_failures == 1 or overall_score < 70:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _generate_recommendations(self, rule_results: List[Dict[str, Any]]) -> List[str]:
        """Generate actionable recommendations based on rule failures."""
        recommendations = []
        
        failed_rules = [r for r in rule_results if not r["pass"]]
        
        for rule in failed_rules:
            rule_id = rule["rule_id"]
            severity = rule["severity"]
            
            if rule_id == "PROD_001":
                recommendations.append("Consider relocating project to higher irradiance location or optimizing system design")
            elif rule_id == "PROD_002":
                recommendations.append("Review system design for performance optimization - check component selection and layout")
            elif rule_id == "TECH_001":
                recommendations.append("Reduce DC/AC ratio or consider higher capacity inverters to minimize clipping losses")
            elif rule_id == "TECH_002":
                recommendations.append("Adjust system size to match site constraints and economic viability")
            elif rule_id == "PROD_003":
                recommendations.append("Investigate shading sources and consider layout optimization or micro-inverters")
            elif rule_id == "FIN_001":
                recommendations.append("Review project costs and explore value engineering opportunities")
            
            if severity == "critical":
                recommendations.append(f"CRITICAL: {rule['description']} must be addressed before proceeding")
        
        if not recommendations:
            recommendations.append("Project appears feasible - proceed with detailed engineering and permitting")
        
        return recommendations


# Singleton instance
_feasibility_engine = None


def get_feasibility_engine() -> FeasibilityAnalysisEngine:
    """Get feasibility analysis engine singleton."""
    global _feasibility_engine
    if _feasibility_engine is None:
        _feasibility_engine = FeasibilityAnalysisEngine()
    return _feasibility_engine