from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_openai import ChatOpenAI
from permit_ml_generator import helioscope_permit_pipeline, SolarPermitAutomation
import json
from typing import Dict, Any, List

class PermitAnalysisOutputParser(BaseOutputParser):
    """Custom parser for permit analysis results"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        try:
            # Try to parse as JSON first
            return json.loads(text)
        except:
            # Fallback to structured text parsing
            return {"analysis": text, "status": "parsed_as_text"}

class LangChainPermitAgent:
    """LangChain-powered permit agent with ML automation"""
    
    def __init__(self, openai_api_key: str = None):
        # Initialize the ML automation
        self.ml_automation = SolarPermitAutomation()
        
        # Initialize LangChain LLM only if API key is provided
        self.openai_api_key = openai_api_key
        self.llm = None
        self.agent = None
        
        if openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-4.1",
                temperature=0.1,
                openai_api_key=openai_api_key
            )
            # Create tools for the agent
            self.tools = self._create_tools()
            # Create the agent
            self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for permit operations"""
        
        tools = [
            Tool(
                name="extract_solar_specifications",
                description="Extract technical solar system specifications from project description",
                func=self._extract_solar_specs_tool
            ),
            Tool(
                name="extract_electrical_specifications", 
                description="Extract electrical requirements and specifications from project description",
                func=self._extract_electrical_specs_tool
            ),
            Tool(
                name="extract_building_specifications",
                description="Extract building and structural specifications from project description", 
                func=self._extract_building_specs_tool
            ),
            Tool(
                name="predict_permit_requirements",
                description="Use ML to predict what permits will be required for a solar project",
                func=self._predict_permit_requirements_tool
            ),
            Tool(
                name="generate_permit_forms",
                description="Generate permit application forms based on project specifications",
                func=self._generate_permit_forms_tool
            ),
            Tool(
                name="estimate_timeline",
                description="Estimate permit approval timeline based on project complexity",
                func=self._estimate_timeline_tool
            ),
            Tool(
                name="helioscope_pipeline",
                description="Run the complete Helioscope permit automation pipeline",
                func=self._helioscope_pipeline_tool
            ),
            Tool(
                name="generate_development_memo",
                description="Generate a comprehensive solar project development memo with permitting matrix",
                func=self._generate_development_memo_tool
            ),
            Tool(
                name="review_and_analyze_permits",
                description="Review a development memo and analyze which permits apply to the project",
                func=self._review_permits_tool
            ),
            Tool(
                name="generate_agency_contacts",
                description="Generate contact information for relevant agencies based on project location and permits",
                func=self._generate_contacts_tool
            ),
            Tool(
                name="create_permit_workflow",
                description="Create a complete permit workflow including memo, review, and agency contacts",
                func=self._create_workflow_tool
            )
        ]
        
        return tools
    
    def _extract_solar_specs_tool(self, project_description: str) -> str:
        """Tool for extracting solar specifications"""
        try:
            specs = self.ml_automation.extract_solar_specs(project_description)
            return json.dumps(specs, indent=2)
        except Exception as e:
            return f"Error extracting solar specs: {str(e)}"
    
    def _extract_electrical_specs_tool(self, project_description: str) -> str:
        """Tool for extracting electrical specifications"""
        try:
            specs = self.ml_automation.extract_electrical_specs(project_description)
            return json.dumps(specs, indent=2)
        except Exception as e:
            return f"Error extracting electrical specs: {str(e)}"
    
    def _extract_building_specs_tool(self, project_description: str) -> str:
        """Tool for extracting building specifications"""
        try:
            specs = self.ml_automation.extract_building_specs(project_description)
            return json.dumps(specs, indent=2)
        except Exception as e:
            return f"Error extracting building specs: {str(e)}"
    
    def _predict_permit_requirements_tool(self, project_features: str) -> str:
        """Tool for ML permit prediction"""
        try:
            # Parse input features (expecting JSON string)
            features = json.loads(project_features)
            prediction = self.ml_automation.predict_solar_project(features)
            return json.dumps(prediction, indent=2)
        except Exception as e:
            return f"Error predicting permits: {str(e)}"
    
    def _generate_permit_forms_tool(self, project_data: str) -> str:
        """Tool for generating permit forms"""
        try:
            data = json.loads(project_data)
            forms = self.ml_automation.generate_permit_forms(data)
            return json.dumps(forms, indent=2)
        except Exception as e:
            return f"Error generating forms: {str(e)}"
    
    def _estimate_timeline_tool(self, forms_data: str) -> str:
        """Tool for estimating permit timeline"""
        try:
            forms = json.loads(forms_data)
            timeline = self.ml_automation._estimate_completion_time(forms)
            return json.dumps(timeline, indent=2)
        except Exception as e:
            return f"Error estimating timeline: {str(e)}"
    
    def _helioscope_pipeline_tool(self, project_data: str) -> str:
        """Tool for running complete pipeline"""
        try:
            data = json.loads(project_data)
            project_data = {
                "project_info": {
                    "description": data["description"],
                    "system_size_kw": data["system_size_kw"],
                    "panel_count": data["panel_count"],
                    "building_type": data["building_type"],
                    "roof_type": data["roof_type"],
                    "utility": data["utility"]
                }
            }
            result = helioscope_permit_pipeline(project_data)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error running pipeline: {str(e)}"
    
    def _generate_development_memo_tool(self, project_data: str) -> str:
        """Tool for generating development memo"""
        try:
            data = json.loads(project_data)
            result = self.generate_development_memo(
                project_address=data.get("address", ""),
                system_size_mwdc=data.get("system_size_mwdc", 0),
                project_description=data.get("description", "")
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error generating development memo: {str(e)}"
    
    def _review_permits_tool(self, development_memo: str) -> str:
        """Tool for reviewing and analyzing permits"""
        try:
            result = self.review_and_analyze_permits(development_memo)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error reviewing permits: {str(e)}"
    
    def _generate_contacts_tool(self, contact_data: str) -> str:
        """Tool for generating agency contacts"""
        try:
            data = json.loads(contact_data)
            result = self.generate_agency_contacts(
                project_address=data.get("address", ""),
                applicable_permits=data.get("permits", [])
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error generating agency contacts: {str(e)}"
    
    def _create_workflow_tool(self, project_data: str) -> str:
        """Tool for creating complete permit workflow"""
        try:
            data = json.loads(project_data)
            result = self.create_permit_workflow(
                project_address=data.get("address", ""),
                system_size_mwdc=data.get("system_size_mwdc", 0),
                project_description=data.get("description", "")
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error creating permit workflow: {str(e)}"
    
    def _create_agent(self):
        """Create the LangChain REACT agent"""
        
        # Define the prompt template
        prompt = PromptTemplate(
            input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
            template="""You are a solar permit automation expert. You help users analyze solar projects and determine permit requirements.

You have access to the following tools:
{tools}

Tool names: {tool_names}

When analyzing a solar project:
1. First extract technical specifications (solar, electrical, building)
2. Use ML predictions to determine required permits
3. Generate appropriate permit forms
4. Estimate timeline for approval
5. Provide clear recommendations

Use this format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Question: {input}
Thought: {agent_scratchpad}"""
        )
        
        # Create and return the agent
        agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=10
        )
    
    def analyze_project(self, user_input: str) -> Dict[str, Any]:
        """Main method to analyze a solar project"""
        try:
            # Check if agent is available (requires OpenAI API key)
            if not self.agent:
                return {
                    "status": "error",
                    "error": "OpenAI API key required for full agent analysis. Use quick_permit_analysis() for ML-only analysis.",
                    "analysis": "Please provide an OpenAI API key to use the full agent reasoning capabilities."
                }
            
            result = self.agent.invoke({"input": user_input})
            return {
                "status": "success",
                "analysis": result["output"],
                "intermediate_steps": result.get("intermediate_steps", [])
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "analysis": "Failed to complete analysis"
            }
    
    def quick_permit_analysis(self, project_description: str) -> Dict[str, Any]:
        """Quick analysis without full agent reasoning"""
        try:
            # Extract all specifications
            solar_specs = self.ml_automation.extract_solar_specs(project_description)
            electrical_specs = self.ml_automation.extract_electrical_specs(project_description)
            building_specs = self.ml_automation.extract_building_specs(project_description)
            
            # Prepare project data for pipeline
            project_data = {
                "project_info": {
                    "description": project_description,
                    "system_size_kw": solar_specs.get("dc_rating_kw", 0),
                    "panel_count": solar_specs.get("panel_count", 0),
                    "building_type": building_specs.get("building_type", "residential"),
                    "roof_type": building_specs.get("roof_type", "unknown"),
                    "utility": "default"
                }
            }
            
            # Run the pipeline
            pipeline_result = helioscope_permit_pipeline(project_data)
            
            return {
                "status": "success",
                "extracted_specs": {
                    "solar": solar_specs,
                    "electrical": electrical_specs,  
                    "building": building_specs
                },
                "pipeline_result": pipeline_result
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def generate_development_memo(self, project_address: str, system_size_mwdc: float, project_description: str = "") -> Dict[str, Any]:
        """Generate a comprehensive solar project development memo with permitting matrix using LangChain"""
        try:
            # Check if agent is available (requires OpenAI API key)
            if not self.agent:
                return {
                    "status": "error",
                    "error": "OpenAI API key required for development memo generation. Use quick_permit_analysis() for ML-only analysis.",
                    "analysis": "Please provide an OpenAI API key to use the development memo generation capabilities."
                }
            
            # Create the development memo prompt
            development_prompt = self._create_development_memo_prompt(project_address, system_size_mwdc, project_description)
            
            # Use the agent to generate the memo
            result = self.agent.invoke({"input": development_prompt})
            
            return {
                "status": "success",
                "development_memo": result["output"],
                "intermediate_steps": result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _create_development_memo_prompt(self, project_address: str, system_size_mwdc: float, project_description: str) -> str:
        """Create the development memo prompt based on the provided template"""
        
        prompt = f"""You are a solar project development expert.  
Write a development memo for a solar PV project based on the following inputs:

- **Project Location Address: {project_address}**
- **Nameplate Capacity (MWdc): {system_size_mwdc}**

{f"**Additional Project Description: {project_description}**" if project_description else ""}

The memo should include the following sections, written in a professional tone suitable for sharing with external partners and investors. Use real data and cite reliable sources with links. Where information is unavailable, clearly state that it must be confirmed.

Sections to include in the memo:

1. **Project Overview – summary of location, size, and memo content**
2. **Estimated Generation – annual and monthly generation (kWh), capacity factor, specific production (kWh/kWdc/year). Assume single-axis tracking bifacial modules with 14% system losses, default tilt = latitude, azimuth = 180°.**
3. **Real Estate – ownership and legal records (zoning, land use type, acreage, parcel ID, easements, deed restrictions), environmental constraints (wetlands, floodplains, habitat, slope), include key GIS resources and databases.**
4. **Electricity Grid Proximity and Capacity – distance to 3-phase lines and substations, estimated hosting capacity, interconnection queue activity, utility service provider and contact links.**
5. **Permitting and Regulatory Requirements – include local, state, and federal permits required, cost, time to secure, and agency contact info. Provide a permitting matrix.**
6. **Interconnection and Utility Programs – relevant procedures, studies (feasibility, SIS, facilities), application timelines, and links to documentation.**
7. **Development Timeline – sequential steps and estimated duration for each phase (site control to energization).**
8. **Estimated Pre-Development Costs – include line items like studies, legal, engineering, interconnection, etc.**
9. **EPC Build Cost – based on latest NREL or equivalent benchmarks (cite source and $/Wdc) and multiply by system size.**
10. **Electricity Rate Benchmarks – include average residential, commercial, and industrial retail rates for the project state and cite sources.**
11. **REC Market – is there a compliance or voluntary REC market? What are the current REC prices and tracking systems?**
12. **Avoided Cost / Merchant Rate – what is the utility avoided cost or merchant rate in ¢/kWh for this location? Include source or note if unavailable.**
13. **Decommissioning Requirements – check for any state or county mandates or bonds required. State clearly if there are none.**
14. **Climate and Weather Risk – summarize exposure to hurricanes, hail, snow, extreme heat, and variability in solar resource.**
15. **Favorability Index – rate the location from 0–10 based on solar resource, permitting, grid access, land cost, supportiveness, etc. Show a table and explain score.**
16. **Concerns and Trends – final summary of local/regional issues and what additional diligence may be required.**

For the permitting matrix in section 5, include the following key permits:
- Conditional Use Permit (County) - Required for all projects, same paperwork regardless of size
- FAA Permit - Online application for projects near airports
- Nationwide Permit (USACE) - Standard nationwide permit for water impacts
- Wetlands Permit (USACE/EPA) - Standard environmental requirements
- Wildlife Permit (USFWS) - Standard endangered species protection
- State/County specific permits - Vary by location

Format the output as a professional memo. Use clear headings and bullet points or tables where appropriate. Avoid filler language or speculation. Cite data with links and mark clearly when something is TBD."""
        
        return prompt
    
    def review_and_analyze_permits(self, development_memo: str) -> Dict[str, Any]:
        """Review the development memo and analyze which permits apply"""
        try:
            # Check if agent is available (requires OpenAI API key)
            if not self.agent:
                return {
                    "status": "error",
                    "error": "OpenAI API key required for permit review. Use quick_permit_analysis() for ML-only analysis.",
                    "analysis": "Please provide an OpenAI API key to use the permit review capabilities."
                }
            
            review_prompt = f"""You are a solar permit expert. Review the following development memo and analyze which permits apply to this project.

Development Memo:
{development_memo}

Please provide a detailed analysis including:

1. **Permit Applicability Matrix** - For each permit type, indicate:
   - Whether it applies to this project (Yes/No/Maybe)
   - Why it applies or doesn't apply
   - Any specific conditions that trigger the requirement

2. **Permit Priority Sequence** - Order permits by priority:
   - Conditional Use Permit (CUP) - Always first, can start immediately
   - FAA Permit - To be done online at oeaaa.faa.gov
   - Environmental Permits (USACE, EPA, USFWS) - Standard nationwide process, so if any of these are required, they should be done by you in conjunction with the CUP application
   - State/County specific permits - Vary by location
   - Construction Permits - After CUP approval

3. **Critical Path Analysis** - Which permits can be pursued in parallel vs. sequentially

4. **Risk Assessment** - Which permits pose the highest risk of delay or rejection

Format your response as a structured analysis with clear sections and actionable recommendations."""

            result = self.agent.invoke({"input": review_prompt})
            
            return {
                "status": "success",
                "permit_analysis": result["output"],
                "intermediate_steps": result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def generate_agency_contacts(self, project_address: str, applicable_permits: List[str]) -> Dict[str, Any]:
        """Generate contact information for relevant agencies based on project location and permits"""
        try:
            # Check if agent is available (requires OpenAI API key)
            if not self.agent:
                return {
                    "status": "error",
                    "error": "OpenAI API key required for agency contact generation.",
                    "analysis": "Please provide an OpenAI API key to use the agency contact capabilities."
                }
            
            contacts_prompt = f"""You are a solar development expert. Generate detailed contact information for agencies that handle the following permits for a project at this location:

Project Address: {project_address}
Applicable Permits: {', '.join(applicable_permits)}

For each applicable permit, provide:

1. **Agency Information**:
   - Agency name and department
   - Physical address
   - Phone number
   - Email address
   - Website URL
   - Contact person (if known)

2. **Application Process**:
   - How to apply (online, mail, in-person)
   - Required forms and documents
   - Application fees
   - Processing timeline
   - Any special requirements for this location

3. **Key Contacts**:
   - Primary contact person
   - Alternative contacts
   - Emergency contacts if applicable

4. **Local Requirements**:
   - Any state/county specific requirements
   - Local ordinances or regulations
   - Special considerations for this jurisdiction

Focus on providing accurate, up-to-date contact information that can be used immediately to start the permitting process. For standard nationwide permits (FAA, USACE, EPA, USFWS), provide the appropriate regional/district office contacts based on the project location.

For FAA permits specifically, note that the application is submitted online."""

            result = self.agent.invoke({"input": contacts_prompt})
            
            return {
                "status": "success",
                "agency_contacts": result["output"],
                "intermediate_steps": result.get("intermediate_steps", [])
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def create_permit_workflow(self, project_address: str, system_size_mwdc: float, project_description: str = "") -> Dict[str, Any]:
        """Create a complete permit workflow including memo, review, and agency contacts"""
        try:
            # Step 1: Generate development memo
            memo_result = self.generate_development_memo(project_address, system_size_mwdc, project_description)
            
            if memo_result["status"] != "success":
                return memo_result
            
            # Step 2: Review and analyze permits
            review_result = self.review_and_analyze_permits(memo_result["development_memo"])
            
            if review_result["status"] != "success":
                return review_result
            
            # Step 3: Extract applicable permits (simplified - in production, parse the review result)
            applicable_permits = [
                "Conditional Use Permit",
                "FAA Permit", 
                "Nationwide Permit (USACE)",
                "Wetlands Permit",
                "Wildlife Permit"
            ]
            
            # Step 4: Generate agency contacts
            contacts_result = self.generate_agency_contacts(project_address, applicable_permits)
            
            return {
                "status": "success",
                "workflow": {
                    "development_memo": memo_result["development_memo"],
                    "permit_analysis": review_result["permit_analysis"],
                    "agency_contacts": contacts_result.get("agency_contacts", "Contact generation failed"),
                    "workflow_summary": {
                        "project_address": project_address,
                        "system_size_mwdc": system_size_mwdc,
                        "applicable_permits": applicable_permits,
                        "next_steps": [
                            "1. Start Conditional Use Permit application immediately",
                            "2. Check FAA permit requirements (online application)",
                            "3. Begin environmental permit applications in parallel",
                            "4. Research state/county specific requirements",
                            "5. Prepare for form upload and filling (future feature)"
                        ]
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def prepare_form_upload_workflow(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare workflow for future form upload and filling capabilities"""
        try:
            # This is a placeholder for future functionality
            # When form upload is implemented, this will:
            # 1. Accept uploaded permit forms
            # 2. Extract form fields and requirements
            # 3. Pre-fill forms with project data
            # 4. Generate completion instructions
            
            workflow = {
                "status": "preparation",
                "message": "Form upload and filling workflow prepared for future implementation",
                "project_data": project_data,
                "future_capabilities": [
                    "Upload permit forms from state/county agencies",
                    "Extract form fields and requirements automatically",
                    "Pre-fill forms with project specifications",
                    "Generate step-by-step completion instructions",
                    "Track form completion status",
                    "Generate submission checklists"
                ],
                "current_workflow": [
                    "1. Generate development memo",
                    "2. Review and analyze applicable permits", 
                    "3. Generate agency contact information",
                    "4. Create permit application timeline",
                    "5. Prepare for form upload (future)"
                ]
            }
            
            return workflow
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

# Usage example
def create_permit_agent(openai_api_key: str = None) -> LangChainPermitAgent:
    """Factory function to create a permit agent"""
    return LangChainPermitAgent(openai_api_key=openai_api_key)

# Test function
def test_permit_agent():
    """Test the LangChain permit agent"""
    
    # Test project description
    project_description = """
    I need permits for a 8.5kW residential solar installation.
    The system will have 27 panels on a composition shingle roof.
    The house is 2,500 sq ft, built in 1995.
    We need to upgrade the electrical panel from 100A to 200A.
    The property is in San Jose, California.
    """
    
    # Test 1: ML-only analysis (no OpenAI API key needed)
    print("=== ML-Only Analysis (No OpenAI API Key) ===")
    agent_ml_only = create_permit_agent()  # No API key
    quick_result = agent_ml_only.quick_permit_analysis(project_description)
    print(json.dumps(quick_result, indent=2, default=str))
    
    # Test 2: Full agent analysis (requires OpenAI API key)
    print("\n=== Full Agent Analysis (Requires OpenAI API Key) ===")
    full_result = agent_ml_only.analyze_project(
        "What permits do I need for this solar project and how long will it take? " + 
        project_description
    )
    print(json.dumps(full_result, indent=2))
    
    # Test 3: Development Memo Generation (requires OpenAI API key)
    print("\n=== Development Memo Generation (Requires OpenAI API Key) ===")
    memo_result = agent_ml_only.generate_development_memo(
        project_address="123 Main St, San Jose, Santa Clara County, CA 95110",
        system_size_mwdc=8.5,
        project_description=project_description
    )
    print(json.dumps(memo_result, indent=2, default=str))
    
    # Test 4: Permit Review and Analysis (requires OpenAI API key)
    print("\n=== Permit Review and Analysis (Requires OpenAI API Key) ===")
    # This would normally use the memo from step 3, but for testing we'll use a placeholder
    review_result = agent_ml_only.review_and_analyze_permits("Sample development memo content")
    print(json.dumps(review_result, indent=2, default=str))
    
    # Test 5: Agency Contact Generation (requires OpenAI API key)
    print("\n=== Agency Contact Generation (Requires OpenAI API key) ===")
    contacts_result = agent_ml_only.generate_agency_contacts(
        project_address="123 Main St, San Jose, Santa Clara County, CA 95110",
        applicable_permits=["Conditional Use Permit", "FAA Permit", "Nationwide Permit (USACE)"]
    )
    print(json.dumps(contacts_result, indent=2, default=str))
    
    # Test 6: Complete Permit Workflow (requires OpenAI API key)
    print("\n=== Complete Permit Workflow (Requires OpenAI API key) ===")
    workflow_result = agent_ml_only.create_permit_workflow(
        project_address="123 Main St, San Jose, Santa Clara County, CA 95110",
        system_size_mwdc=8.5,
        project_description=project_description
    )
    print(json.dumps(workflow_result, indent=2, default=str))
    
    # Test 7: Form Upload Workflow Preparation (no API key needed)
    print("\n=== Form Upload Workflow Preparation (No API Key Needed) ===")
    form_workflow = agent_ml_only.prepare_form_upload_workflow({
        "address": "123 Main St, San Jose, CA",
        "system_size_mwdc": 8.5,
        "description": project_description
    })
    print(json.dumps(form_workflow, indent=2, default=str))

if __name__ == "__main__":
    test_permit_agent()