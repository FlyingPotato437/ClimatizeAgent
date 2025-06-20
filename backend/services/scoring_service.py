"""
Minimal scoring service for project evaluation.
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ScoringService:
    """Service for scoring and evaluating projects."""
    
    def __init__(self):
        pass
    
    async def calculate_fundability_score(self, project: Dict[str, Any]) -> int:
        """Calculate fundability score (0-100)."""
        # Simplified scoring logic
        score = 50  # Base score
        
        # Add points for key factors
        if project.get('system_specs', {}).get('system_size_dc_kw', 0) > 100:
            score += 20
        
        if project.get('interconnection_score', {}).get('score', 0) > 70:
            score += 15
        
        if project.get('permit_matrix', {}).get('risk_factors'):
            score -= len(project['permit_matrix']['risk_factors']) * 5
        
        return max(0, min(100, score))
    
    async def calculate_readiness_score(self, project: Dict[str, Any]) -> int:
        """Calculate project readiness score (0-100)."""
        # Simplified readiness calculation
        completed_milestones = 0
        total_milestones = 6
        
        milestones = project.get('milestones', {})
        if milestones.get('site_control') != "Not Started":
            completed_milestones += 1
        if milestones.get('permitting') != "Not Started":
            completed_milestones += 1
        if milestones.get('interconnection') != "Not Started":
            completed_milestones += 1
        if milestones.get('engineering') != "Not Started":
            completed_milestones += 1
        if milestones.get('offtake') != "Not Started":
            completed_milestones += 1
        if milestones.get('financing') != "Not Started":
            completed_milestones += 1
        
        return int((completed_milestones / total_milestones) * 100) 