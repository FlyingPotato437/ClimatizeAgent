import os
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_openai import ChatOpenAI
from pathlib import Path
import json
from typing import Dict, Any, List

class ResearchAnalysisOutputParser(BaseOutputParser):
    """Custom parser for permit analysis results"""
    
    def parse(self, text: str) -> Dict[str, Any]:
        try:
            # Try to parse as JSON first
            return json.loads(text)
        except:
            # Fallback to structured text parsing
            return {"analysis": text, "status": "parsed_as_text"}

class LangChainResearchAgent:
    """LangChain-powered research agent with ML automation"""
    
    def __init__(self, openai_api_key: str = None):
        # Initialize LangChain LLM only if API key is provided
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = None
        self.agent = None
        
        if self.openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-4.1",
                temperature=0.1,
                openai_api_key=self.openai_api_key
            )
            # Create tools for the agent
            self.tools = self._create_tools()

            # Create the agent
            self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for permit operations"""
        
        tools = [
            Tool(
                name="generate_development_memo",
                description="Generate a comprehensive solar project development memo. Input should be project details including address and system size (e.g., '8.5 MWac solar project at 123 Main St, San Jose, CA' or JSON with address, system_size_ac, and description fields).",
                func=self._generate_development_memo_tool
            ),
        ]
        
        return tools
    
    def _generate_development_memo_tool(self, project_data: str) -> str:
        """Tool for generating development memo"""
        try:
            # Try to parse as JSON first
            try:
                data = json.loads(project_data)
                project_address = data.get("address", "")
                system_size_ac = data.get("system_size_ac", 0)
                project_description = data.get("description", "")
            except json.JSONDecodeError:
                # If JSON parsing fails, try to extract info from plain text
                # Look for common patterns in the text
                lines = project_data.strip().split('\n')
                project_address = ""
                system_size_ac = 0
                project_description = project_data
                
                for line in lines:
                    line = line.strip()
                    if "address" in line.lower() or "location" in line.lower():
                        project_address = line.split(":", 1)[-1].strip()
                    elif "size" in line.lower() or "capacity" in line.lower() or "mw" in line.lower():
                        # Extract numeric value
                        import re
                        numbers = re.findall(r'\d+\.?\d*', line)
                        if numbers:
                            system_size_ac = float(numbers[0])
            
            result = self.generate_development_memo(
                project_address=project_address,
                system_size_ac=system_size_ac,
                project_description=project_description
            )
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error generating development memo: {str(e)}"
    
    def _create_agent(self):
        """Create the LangChain REACT agent"""
        
        # Read the prompt template from the external file
        prompt_template = Path("./prompts/agent_prompt.txt").read_text()
        
        # Define the prompt template
        prompt = PromptTemplate(
            input_variables=["tools", "tool_names", "input", "agent_scratchpad"],
            template=prompt_template
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
                    "error": "OpenAI API key required for full agent analysis.",
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
    
    def generate_development_memo(self, project_address: str, system_size_ac: float, project_description: str = "") -> Dict[str, Any]:
        """Generate a comprehensive solar project development memo with permitting matrix using LangChain"""
        try:
            # Check if agent is available (requires OpenAI API key)
            if not self.llm:
                return {
                    "status": "error",
                    "error": "OpenAI API key required for development memo generation.",
                    "analysis": "Please provide an OpenAI API key to use the development memo generation capabilities."
                }
            
            # Create the development memo prompt
            development_prompt = self._create_development_memo_prompt(project_address, system_size_ac, project_description)
            
            # Use the LLM directly instead of the agent to avoid recursion
            result = self.llm.invoke(development_prompt)
            
            return {
                "status": "success",
                "development_memo": result.content,
                "intermediate_steps": []
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _create_development_memo_prompt(self, project_address: str, system_size_ac: float, project_description: str) -> str:
        """Create the development memo prompt based on the provided template"""
        
        # Read the prompt template from the external file
        prompt_template = Path("./prompts/development_memo.txt").read_text()
        
        # Format the project description
        formatted_description = ""
        if project_description:
            formatted_description = f"**Additional Project Description: {project_description}**"
        
        # Format the prompt with the provided parameters
        prompt = prompt_template.format(
            project_address=project_address,
            system_size_ac=system_size_ac,
            project_description=formatted_description
        )
        
        return prompt
    
    def create_permit_workflow(self, project_address: str, system_size_ac: float, project_description: str = "") -> Dict[str, Any]:
        """Create a complete permit workflow including memo, review, and agency contacts"""
        try:
            # Step 1: Generate development memo
            memo_result = self.generate_development_memo(project_address, system_size_ac, project_description)
            
            if memo_result["status"] != "success":
                return memo_result
            
            return {
                "status": "success",
                "workflow": {
                    "development_memo": memo_result["development_memo"],
                    "workflow_summary": {
                        "project_address": project_address,
                        "system_size_ac": system_size_ac,
                        "next_steps": [
                            "nothing for now [to-do!]"
                        ]
                    }
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def analyze_solar_project(self, project_address: str, system_size_ac: float) -> Dict[str, Any]:
        """Simplified method to analyze a solar project with just address and system size"""
        try:
            # Check if agent is available (requires OpenAI API key)
            if not self.agent:
                return {
                    "status": "error",
                    "error": "OpenAI API key required for full agent analysis.",
                    "analysis": "Please provide an OpenAI API key to use the full agent reasoning capabilities."
                }
            
            # Create a simple prompt with just the essential information
            user_input = f"What permits do I need for a {system_size_ac} MWac solar project at {project_address} and how long will it take?"
            
            result = self.agent.invoke({"input": user_input})
            return {
                "status": "success",
                "analysis": result["output"],
                "intermediate_steps": result.get("intermediate_steps", []),
                "project_info": {
                    "address": project_address,
                    "system_size_ac": system_size_ac
                }
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "analysis": "Failed to complete analysis"
            }
        
def load_aurora_project_data(project_path: str) -> Dict[str, Any]:
    """Load and process Aurora project data from the specified project folder"""
    import json
    import csv
    from pathlib import Path
    
    project_dir = Path(project_path)
    
    # Load project information
    with open(project_dir / "retrieve_project.json", "r") as f:
        project_data = json.load(f)
    
    # Load design summary
    with open(project_dir / "retrieve_design_summary.json", "r") as f:
        design_data = json.load(f)
    
    # Load bill of materials
    bom_data = []
    with open(project_dir / "Bill-of-Materials.csv", "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bom_data.append(row)
    
    # Extract key information
    project_info = project_data["project"]
    design_info = design_data["design"]
    
    # Calculate system size in MWac
    total_dc_size = sum(array["size"] for array in design_info["arrays"])
    system_size_ac = total_dc_size / 1000  # Convert to MWac (approximate)
    
    # Extract address information
    location = project_info["location"]
    address = f"{location['property_address_components']['street_address']}, {location['property_address_components']['city']}, {location['property_address_components']['region']} {location['property_address_components']['postal_code']}"
    
    # Handle different inverter types safely
    inverter_info = "Unknown"
    if design_info.get("string_inverters") and len(design_info["string_inverters"]) > 0:
        inverter = design_info["string_inverters"][0]
        inverter_info = f"{inverter['name']} ({inverter['rated_power']}W)"
    elif design_info.get("microinverters") and len(design_info["microinverters"]) > 0:
        microinverter = design_info["microinverters"][0]
        inverter_info = f"{microinverter['name']} ({microinverter['rated_power']}W)"
    else:
        # Try to get inverter info from BOM
        for item in bom_data:
            if "inverter" in item.get("Type", "").lower():
                inverter_info = f"{item.get('Item', 'Unknown')} ({item.get('Manufacturer', 'Unknown')})"
                break
    
    # Create comprehensive project description
    project_description = f"""
Project: {project_info['name']}
System Size: {system_size_ac:.2f} MWac ({total_dc_size/1000:.2f} MWdc)
Location: {address}
Annual Production: {design_info['energy_production']['annual']:.0f} kWh
Module Type: {design_info['arrays'][0]['module']['name']} ({design_info['arrays'][0]['module']['rating_stc']}W)
Inverter: {inverter_info}
Total Modules: {sum(array['module']['count'] for array in design_info['arrays'])}
Arrays: {len(design_info['arrays'])} arrays
"""
    
    return {
        "project_address": address,
        "system_size_ac": system_size_ac,
        "project_description": project_description,
        "raw_data": {
            "project": project_data,
            "design": design_data,
            "bom": bom_data
        }
    }

# Usage example
def create_research_agent(openai_api_key: str = None) -> LangChainResearchAgent:
    """Factory function to create a permit agent"""
    return LangChainResearchAgent(openai_api_key=openai_api_key)

def save_results_to_files(project_address: str, system_size_ac: float, openai_api_key: str = None):
    """Save research analysis results to formatted text files"""
    
    research_agent = create_research_agent(openai_api_key)
    
    # Create output directory
    output_dir = Path("./research_output")
    output_dir.mkdir(exist_ok=True)
    
    # Generate results
    print("Generating research analysis...")
    
    # 1. Simple Analysis
    simple_result = research_agent.analyze_solar_project(project_address, system_size_ac)
    if simple_result["status"] == "success":
        with open(output_dir / "simple_analysis.txt", "w") as f:
            f.write("SOLAR PROJECT PERMIT ANALYSIS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Project Address: {project_address}\n")
            f.write(f"System Size: {system_size_ac} MWac\n\n")
            f.write("ANALYSIS:\n")
            f.write("-" * 20 + "\n")
            f.write(simple_result["analysis"])
        print("✓ Simple analysis saved to research_output/simple_permit_analysis.txt")
    
    # 2. Development Memo
    memo_result = research_agent.generate_development_memo(project_address, system_size_ac)
    if memo_result["status"] == "success":
        with open(output_dir / "development_memo.txt", "w") as f:
            f.write(memo_result["development_memo"])
        print("✓ Development memo saved to research_output/development_memo.txt")
    
    # 3. Complete Workflow
    workflow_result = research_agent.create_permit_workflow(project_address, system_size_ac)
    if workflow_result["status"] == "success":
        with open(output_dir / "complete_workflow.txt", "w") as f:
            f.write("COMPLETE SOLAR PROJECT RESEARCH WORKFLOW\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Project Address: {project_address}\n")
            f.write(f"System Size: {system_size_ac} MWac\n\n")
            f.write("DEVELOPMENT MEMO:\n")
            f.write("-" * 20 + "\n")
            f.write(workflow_result["workflow"]["development_memo"])
            f.write("\n\n" + "=" * 50 + "\n\n")
            f.write("PERMIT ANALYSIS:\n")
            f.write("-" * 20 + "\n")
            f.write(workflow_result["workflow"]["permit_analysis"])
        print("✓ Complete workflow saved to research_output/complete_workflow.txt")
    
    print(f"\nAll results saved to {output_dir.absolute()}")

if __name__ == "__main__":
    # Load Aurora project data instead of using hardcoded values
    project = "1520_Mission_Blvd_Selman"
    aurora_project_path = f"./aurora_projects/{project}"
    aurora_data = load_aurora_project_data(aurora_project_path)
    
    print("Running research agent analysis with Aurora project data...")
    print(f"Project: {aurora_data['project_description'].split('Project: ')[1].split('\n')[0]}")
    print(f"Address: {aurora_data['project_address']}")
    print(f"System Size: {aurora_data['system_size_ac']:.2f} MWac\n")
    
    # Create agent once
    research_agent = create_research_agent()
    
    # Run analysis with Aurora data
    print("="*60)
    print("SIMPLIFIED SOLAR PROJECT ANALYSIS")
    print("="*60)
    simple_result = research_agent.analyze_solar_project(
        aurora_data["project_address"], 
        aurora_data["system_size_ac"]
    )
    print("Status:", simple_result["status"])
    if simple_result["status"] == "success":
        print("\nANALYSIS:")
        print("-" * 40)
        print(simple_result["analysis"])
    else:
        print("Error:", simple_result["error"])
    
    print("\n" + "="*60)
    print("DEVELOPMENT MEMO GENERATION")
    print("="*60)
    memo_result = research_agent.generate_development_memo(
        aurora_data["project_address"], 
        aurora_data["system_size_ac"],
        aurora_data["project_description"]
    )
    print("Status:", memo_result["status"])
    if memo_result["status"] == "success":
        print("\nDEVELOPMENT MEMO:")
        print("-" * 40)
        print(memo_result["development_memo"])
    else:
        print("Error:", memo_result["error"])
    
    print("\n" + "="*60)
    print("COMPLETE RESEARCH WORKFLOW")
    print("="*60)
    workflow_result = research_agent.create_permit_workflow(
        aurora_data["project_address"], 
        aurora_data["system_size_ac"],
        aurora_data["project_description"]
    )
    print("Status:", workflow_result["status"])
    if workflow_result["status"] == "success":
        print("\nWORKFLOW SUMMARY:")
        print("-" * 40)
        summary = workflow_result["workflow"]["workflow_summary"]
        print(f"Project Address: {summary['project_address']}")
        print(f"System Size: {summary['system_size_ac']} MWac")
        print(f"Next Steps: {summary['next_steps']}")
    else:
        print("Error:", workflow_result["error"])
    
    # Save results to files using Aurora data
    print("\n" + "="*60)
    print("SAVING RESULTS TO FILES")
    print("="*60)
    
    # Create output directory - Fixed the path issue
    output_dir = Path(f"./research_output/{project}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save results using the Aurora data
    if simple_result["status"] == "success":
        with open(output_dir / "simple_permit_analysis.md", "w") as f:
            f.write("# Solar Project Permit Analysis\n\n")
            f.write(f"**Project Address:** {aurora_data['project_address']}\n")
            f.write(f"**System Size:** {aurora_data['system_size_ac']:.2f} MWac\n\n")
            f.write("## Analysis\n\n")
            f.write(simple_result["analysis"])
        print("✓ Simple analysis saved to research_output/simple_permit_analysis.md")
    
    if memo_result["status"] == "success":
        with open(output_dir / "development_memo.md", "w") as f:
            f.write(memo_result["development_memo"])
        print("✓ Development memo saved to research_output/development_memo.md")
    
    if workflow_result["status"] == "success":
        with open(output_dir / "complete_workflow.md", "w") as f:
            f.write("# Complete Research Workflow\n\n")
            f.write(f"**Project Address:** {aurora_data['project_address']}\n")
            f.write(f"**System Size:** {aurora_data['system_size_ac']:.2f} MWac\n\n")
            f.write("## Development Memo\n\n")
            f.write(workflow_result["workflow"]["development_memo"])
            f.write("\n\n---\n\n")
        print("✓ Complete workflow saved to research_output/complete_workflow.md")
    
    print(f"\nAll results saved to {output_dir.absolute()}")