"""
AI service for document generation and text processing using Azure OpenAI.
"""
import logging
from typing import Optional, Dict, Any
from openai import AzureOpenAI
from core.config import settings

logger = logging.getLogger(__name__)

class AIService:
    """Service for AI-powered document generation and text processing."""
    
    def __init__(self):
        self.client = None
        if settings.azure_openai_endpoint and settings.openai_api_key:
            self.client = AzureOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.openai_api_key,
                api_version=settings.azure_openai_api_version
            )
            logger.info("Azure OpenAI client initialized")
        else:
            logger.warning("Azure OpenAI not configured - AI features will be disabled")
    
    async def generate_letter_of_intent(self, project_data: Dict[str, Any]) -> str:
        """
        Generate a Letter of Intent for site control using AI.
        
        Args:
            project_data: Project information including address, system details, etc.
            
        Returns:
            Generated Letter of Intent text
        """
        if not self.client:
            return self._fallback_letter_of_intent(project_data)
        
        try:
            prompt = f"""
            Generate a professional Letter of Intent for a solar project with the following details:
            
            Project Name: {project_data.get('project_name', 'Solar Development Project')}
            Property Address: {project_data.get('address', 'TBD')}
            System Size: {project_data.get('system_size_kw', 'TBD')} kW
            Estimated Annual Production: {project_data.get('estimated_annual_production', 'TBD')} kWh
            
            The letter should:
            1. Express intent to lease/purchase the property for solar development
            2. Include professional legal language
            3. Mention key project benefits (clean energy, land lease income)
            4. Include standard contingencies (permits, interconnection, financing)
            5. Be formal and business-appropriate
            
            Format as a complete business letter.
            """
            
            response = self.client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": "You are a professional legal document assistant specializing in renewable energy projects."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            generated_text = response.choices[0].message.content
            logger.info("Successfully generated Letter of Intent using AI")
            return generated_text
            
        except Exception as e:
            logger.error(f"Error generating Letter of Intent with AI: {e}")
            return self._fallback_letter_of_intent(project_data)
    
    async def analyze_permit_requirements(self, jurisdiction: str, project_type: str = "solar") -> Dict[str, Any]:
        """
        Analyze permit requirements for a jurisdiction using AI.
        
        Args:
            jurisdiction: City/county jurisdiction
            project_type: Type of renewable energy project
            
        Returns:
            Analysis of permit requirements and process
        """
        if not self.client:
            return self._fallback_permit_analysis(jurisdiction, project_type)
        
        try:
            prompt = f"""
            Analyze the typical permit requirements for a {project_type} energy project in {jurisdiction}.
            
            Please provide:
            1. List of likely required permits
            2. Estimated timeline for permit approval
            3. Typical costs (if known)
            4. Key considerations or challenges
            5. Recommended next steps
            
            Format as structured JSON with clear categories.
            """
            
            response = self.client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": "You are an expert in renewable energy permitting and regulatory requirements."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.2
            )
            
            analysis_text = response.choices[0].message.content
            
            # Return structured analysis
            return {
                "jurisdiction": jurisdiction,
                "project_type": project_type,
                "analysis": analysis_text,
                "generated_by": "ai",
                "confidence": "medium"
            }
            
        except Exception as e:
            logger.error(f"Error analyzing permits with AI: {e}")
            return self._fallback_permit_analysis(jurisdiction, project_type)
    
    async def generate_feasibility_summary(self, project_data: Dict[str, Any]) -> str:
        """
        Generate a feasibility summary using AI analysis.
        
        Args:
            project_data: Complete project data including financial models
            
        Returns:
            AI-generated feasibility summary
        """
        if not self.client:
            return self._fallback_feasibility_summary(project_data)
        
        try:
            prompt = f"""
            Create a professional feasibility summary for this solar project:
            
            Project: {project_data.get('project_name', 'Solar Project')}
            System Size: {project_data.get('system_size_kw', 'TBD')} kW
            Total Cost: ${project_data.get('total_project_cost', 'TBD')}
            Annual Production: {project_data.get('estimated_annual_production', 'TBD')} kWh
            IRR: {project_data.get('irr_percent', 'TBD')}%
            Payback Period: {project_data.get('payback_years', 'TBD')} years
            
            Generate a 2-3 paragraph executive summary covering:
            1. Project viability and key strengths
            2. Financial attractiveness 
            3. Risk assessment and mitigation
            4. Overall recommendation
            
            Keep it professional and investor-focused.
            """
            
            response = self.client.chat.completions.create(
                model=settings.azure_openai_deployment,
                messages=[
                    {"role": "system", "content": "You are a renewable energy financial analyst creating executive summaries for investors."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.4
            )
            
            summary = response.choices[0].message.content
            logger.info("Successfully generated feasibility summary using AI")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating feasibility summary with AI: {e}")
            return self._fallback_feasibility_summary(project_data)
    
    def _fallback_letter_of_intent(self, project_data: Dict[str, Any]) -> str:
        """Fallback Letter of Intent template when AI is unavailable."""
        return f"""
LETTER OF INTENT
Solar Development Project

Date: [DATE]

Property Owner/Manager
{project_data.get('address', '[Property Address]')}

Dear Property Owner,

This Letter of Intent expresses our interest in developing a solar energy project on your property located at {project_data.get('address', '[Property Address]')}.

Project Overview:
- Project Name: {project_data.get('project_name', 'Solar Development Project')}
- Estimated System Size: {project_data.get('system_size_kw', '[TBD]')} kW
- Estimated Annual Production: {project_data.get('estimated_annual_production', '[TBD]')} kWh

This project will provide clean renewable energy while generating lease income for the property owner. We are prepared to move forward with this development subject to customary contingencies including permits, interconnection agreements, and project financing.

We look forward to discussing this opportunity further.

Sincerely,
[Developer Name]
[Contact Information]

Note: This is a template document. AI-powered generation is currently unavailable.
        """
    
    def _fallback_permit_analysis(self, jurisdiction: str, project_type: str) -> Dict[str, Any]:
        """Fallback permit analysis when AI is unavailable."""
        return {
            "jurisdiction": jurisdiction,
            "project_type": project_type,
            "analysis": f"Permit analysis for {project_type} projects in {jurisdiction} requires manual research. Common permits typically include: building permits, electrical permits, zoning approvals, and utility interconnection agreements. Recommend consulting local authorities for specific requirements.",
            "generated_by": "template",
            "confidence": "low"
        }
    
    def _fallback_feasibility_summary(self, project_data: Dict[str, Any]) -> str:
        """Fallback feasibility summary when AI is unavailable."""
        return f"""
FEASIBILITY SUMMARY - {project_data.get('project_name', 'Solar Project')}

This {project_data.get('system_size_kw', '[TBD]')} kW solar project shows preliminary feasibility based on initial analysis. The project economics indicate a {project_data.get('payback_years', '[TBD]')} year payback period with an estimated IRR of {project_data.get('irr_percent', '[TBD]')}%.

Key considerations include site suitability, utility interconnection capacity, and local permitting requirements. Further due diligence is recommended to validate technical and financial assumptions.

Note: This is a template summary. AI-powered analysis is currently unavailable.
        """

# Global service instance
_ai_service = None

def get_ai_service() -> AIService:
    """Get AI service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service