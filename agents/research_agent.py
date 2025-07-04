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

# Usage example
def create_research_agent(openai_api_key: str = None) -> LangChainResearchAgent:
    """Factory function to create a permit agent"""
    return LangChainResearchAgent(openai_api_key=openai_api_key)

# Test function
def test_research_agent():
    """Test the LangChain permit agent"""
    
    # Create ML Agent
    research_agent_ml = create_research_agent()
    
    # Test 1: Simplified analysis with just address and system size (requires OpenAI API key)
    print("\n" + "="*60)
    print("SIMPLIFIED SOLAR PROJECT ANALYSIS")
    print("="*60)
    simple_result = research_agent_ml.analyze_solar_project(
        project_address="123 Main St, San Jose, Santa Clara County, CA 95110",
        system_size_ac=8.5
    )
    print("Status:", simple_result["status"])
    if simple_result["status"] == "success":
        print("\nANALYSIS:")
        print("-" * 40)
        print(simple_result["analysis"])
    else:
        print("Error:", simple_result["error"])
    
    # Test 2: Development Memo Generation (requires OpenAI API key)
    print("\n" + "="*60)
    print("DEVELOPMENT MEMO GENERATION")
    print("="*60)
    memo_result = research_agent_ml.generate_development_memo(
        project_address="123 Main St, San Jose, Santa Clara County, CA 95110",
        system_size_ac=8.5
    )
    print("Status:", memo_result["status"])
    if memo_result["status"] == "success":
        print("\nDEVELOPMENT MEMO:")
        print("-" * 40)
        print(memo_result["development_memo"])
    else:
        print("Error:", memo_result["error"])
    
    # Test 3: Complete Solar Project Reseach Workflow (requires OpenAI API key)
    print("\n" + "="*60)
    print("COMPLETE SOLAR PROJECT RESEARCH WORKFLOW")
    print("="*60)
    workflow_result = research_agent_ml.create_permit_workflow(
        project_address="123 Main St, San Jose, Santa Clara County, CA 95110",
        system_size_ac=8.5
    )
    print("Status:", workflow_result["status"])
    if workflow_result["status"] == "success":
        print("\nWORKFLOW SUMMARY:")
        print("-" * 40)
        summary = workflow_result["workflow"]["workflow_summary"]
        print(f"Project Address: {summary['project_address']}")
        print(f"System Size: {summary['system_size_ac']} MWac")
        print(f"Applicable Permits: {len(summary['applicable_permits'])} found")
        print(f"Next Steps: {summary['next_steps']}")
        
        print("\nPERMIT ANALYSIS:")
        print("-" * 40)
        print(workflow_result["workflow"]["permit_analysis"])
    else:
        print("Error:", workflow_result["error"])

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
    # Run both pretty print and save to files
    print("Running research agent analysis...")
    print("This will display results in terminal AND save to files.\n")
    
    # Create agent once
    research_agent = create_research_agent()
    project_address = "123 Main St, San Jose, Santa Clara County, CA 95110"
    system_size_ac = 8.5
    
    # Run analysis once and store results
    print("="*60)
    print("SIMPLIFIED SOLAR PROJECT ANALYSIS")
    print("="*60)
    simple_result = research_agent.analyze_solar_project(project_address, system_size_ac)
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
    memo_result = research_agent.generate_development_memo(project_address, system_size_ac)
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
    workflow_result = research_agent.create_permit_workflow(project_address, system_size_ac)
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
    
    # Save results to files using the already-generated results
    print("\n" + "="*60)
    print("SAVING RESULTS TO FILES")
    print("="*60)
    
    # Create output directory
    output_dir = Path("./research_output")
    output_dir.mkdir(exist_ok=True)
    
    # Save results using the data we already have
    if simple_result["status"] == "success":
        with open(output_dir / "simple_permit_analysis.txt", "w") as f:
            f.write("SOLAR PROJECT PERMIT ANALYSIS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Project Address: {project_address}\n")
            f.write(f"System Size: {system_size_ac} MWac\n\n")
            f.write("ANALYSIS:\n")
            f.write("-" * 20 + "\n")
            f.write(simple_result["analysis"])
        print("✓ Simple analysis saved to research_output/simple_permit_analysis.txt")
    
    if memo_result["status"] == "success":
        with open(output_dir / "development_memo.txt", "w") as f:
            f.write(memo_result["development_memo"])
        print("✓ Development memo saved to research_output/development_memo.txt")
    
    if workflow_result["status"] == "success":
        with open(output_dir / "complete_workflow.txt", "w") as f:
            f.write("COMPLETE RESEARCH WORKFLOW\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Project Address: {project_address}\n")
            f.write(f"System Size: {system_size_ac} MWac\n\n")
            f.write("DEVELOPMENT MEMO:\n")
            f.write("-" * 20 + "\n")
            f.write(workflow_result["workflow"]["development_memo"])
            f.write("\n\n" + "=" * 50 + "\n\n")
        print("✓ Complete workflow saved to research_output/complete_workflow.txt")
    
    print(f"\nAll results saved to {output_dir.absolute()}")