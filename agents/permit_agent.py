import os
from langchain.agents import Tool, AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.schema import BaseOutputParser
from langchain_openai import ChatOpenAI
from pathlib import Path
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
        # Initialize LangChain LLM only if API key is provided
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.llm = None
        self.agent = None
        
        if self.openai_api_key:
            self.llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                api_key=self.openai_api_key
            )
            # Create tools for the agent
            self.tools = self._create_tools()

            # Create the agent
            self.agent = self._create_agent()
    
    def _create_tools(self) -> List[Tool]:
        """Create LangChain tools for permit operations"""
        
        tools = [
            Tool(
                name="predict_required_permits",
                description="Use ML to predict what permits will be required for a solar project",
                func=self._predict_required_permits_tool
            ),
            Tool(
                name="generate_permit_forms",
                description="Generate permit application forms based on project specifications",
                func=self._generate_permit_forms_tool
            ),
            Tool(
                name="generate_permit_matrix",
                description="Generate a detailed permit matrix based on project specifications",
                func=self._generate_permit_matrix_tool
            ),
            Tool(
                name="generate_development_memo",
                description="Generate a comprehensive solar project development memo. Input should be project details including address and system size (e.g., '8.5 MWac solar project at 123 Main St, San Jose, CA' or JSON with address, system_size_ac, and description fields).",
                func=self._generate_development_memo_tool
            ),
            Tool(
                name="review_and_analyze_permits",
                description="Review permit matrix and analyze which permits apply to the project",
                func=self._review_permits_tool
            ),
        ]
        
        return tools
    
    def _generate_permit_matrix_tool(self, project_data: str) -> str:
        """Tool for generating a detailed permit matrix"""
        try:
            # Try to parse as JSON first
            try:
                data = json.loads(project_data)
                formatted_project_data = json.dumps(data, indent=2)
            except json.JSONDecodeError:
                # If JSON parsing fails, treat as plain text
                formatted_project_data = project_data.strip()
            
            # Load the permit matrix prompt template
            prompt_template = Path("./prompts/permit_matrix_prompt.txt").read_text()
            
            # Insert the project data into the prompt
            prompt = prompt_template.replace(
                "{Insert structured project data here (location, size, design, equipment, site, simulation, etc.)}",
                formatted_project_data
            )
            
            # Call the LLM with the formatted prompt
            if not self.llm:
                return json.dumps({
                    "status": "error",
                    "error": "OpenAI API key required for permit matrix generation.",
                    "analysis": "Please provide an OpenAI API key to use the permit matrix generation capabilities."
                }, indent=2)
            
            result = self.llm.invoke(prompt)
            return result.content  # This should be the Markdown table
        except Exception as e:
            return f"Error generating permit matrix: {str(e)}"
    
    #TODO: Implement this
    def _predict_required_permits_tool(self, project_features: str) -> str:
        """Tool for ML permit prediction"""
        try:
            return "Need to implement predict_permit_requirements_tool"
        except Exception as e:
            return f"Error predicting permits: {str(e)}"
    
    #TODO: Implement this
    def _generate_permit_forms_tool(self, project_data: str) -> str:
        """Tool for generating permit forms"""
        try:
            return "Need to implement generate_permit_forms_tool"
        except Exception as e:
            return f"Error generating forms: {str(e)}"
    
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
    
    def _review_permits_tool(self, development_memo: str) -> str:
        """Tool for reviewing and analyzing permits"""
        try:
            result = self.review_and_analyze_permits(development_memo)
            return json.dumps(result, indent=2)
        except Exception as e:
            return f"Error reviewing permits: {str(e)}"
    
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
                    "error": "OpenAI API key required for development memo generation. Use quick_permit_analysis() for ML-only analysis.",
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
    
    def review_and_analyze_permits(self, development_memo: str) -> Dict[str, Any]:
        """Review the development memo and analyze which permits apply"""
        try:
            # Check if agent is available (requires OpenAI API key)
            if not self.llm:
                return {
                    "status": "error",
                    "error": "OpenAI API key required for permit review.",
                    "analysis": "Please provide an OpenAI API key to use the permit review capabilities."
                }
            
            # Read the review prompt template
            review_prompt_template = Path("./prompts/review_permit_mx.txt").read_text()
            
            # Create the full prompt with the development memo
            full_prompt = f"{review_prompt_template}\n\nDevelopment Memo to Review:\n{development_memo}"
            
            # Use the LLM directly instead of the agent to avoid recursion
            result = self.llm.invoke(full_prompt)
            
            return {
                "status": "success",
                "permit_analysis": result.content,
                "intermediate_steps": []
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    def create_permit_workflow(self, project_address: str, system_size_ac: float, project_description: str = "") -> Dict[str, Any]:
        """Create a complete permit workflow including memo, review, and agency contacts"""
        try:
            # Step 1: Generate development memo
            memo_result = self.generate_development_memo(project_address, system_size_ac, project_description)
            
            if memo_result["status"] != "success":
                return memo_result
            
            # Step 2: Review and analyze permits
            review_result = self.review_and_analyze_permits(memo_result["development_memo"])
            
            if review_result["status"] != "success":
                return review_result
            
            # Step 3: Extract applicable permits (simplified - in production, parse the review result)
            applicable_permits = []

            
            return {
                "status": "success",
                "workflow": {
                    "development_memo": memo_result["development_memo"],
                    "permit_analysis": review_result["permit_analysis"],
                    "workflow_summary": {
                        "project_address": project_address,
                        "system_size_ac": system_size_ac,
                        "applicable_permits": applicable_permits,
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

    def generate_permit_matrix(self, project_data: dict) -> str:
        """
        Core function to generate a permit matrix for a solar project using the LLM and the detailed prompt.
        """
        try:
            # Load the permit matrix prompt template
            prompt_template = Path("./prompts/permit_matrix_prompt.txt").read_text()
            
            # Format the project data as pretty JSON for the prompt
            formatted_project_data = json.dumps(project_data, indent=2)
            
            # Insert the project data into the prompt
            prompt = prompt_template.replace(
                "{Insert structured project data here (location, size, design, equipment, site, simulation, etc.)}",
                formatted_project_data
            )
            
            # Call the LLM with the formatted prompt
            if not self.llm:
                return json.dumps({
                    "status": "error",
                    "error": "OpenAI API key required for permit matrix generation.",
                    "analysis": "Please provide an OpenAI API key to use the permit matrix generation capabilities."
                }, indent=2)
            
            result = self.llm.invoke(prompt)
            return result.content  # This should be the Markdown table
        except Exception as e:
            return f"Error generating permit matrix: {str(e)}"

    def save_permit_matrix_to_files(self, permit_matrix_content: str, output_dir: str = "./permit_output") -> Dict[str, str]:
        """
        Save permit matrix content to both Markdown and CSV files.
        Attempts to extract CSV data from the LLM response if it contains CSV format.
        """
        try:
            from pathlib import Path
            import re
            
            output_path = Path(output_dir)
            output_path.mkdir(exist_ok=True)
            
            # Save Markdown file
            md_file_path = output_path / "permit_matrix.md"
            with open(md_file_path, "w") as f:
                f.write(permit_matrix_content)
            
            # Try to extract and save CSV data
            csv_file_path = None
            csv_content = self._extract_csv_from_response(permit_matrix_content)
            
            if csv_content:
                csv_file_path = output_path / "permit_matrix.csv"
                with open(csv_file_path, "w") as f:
                    f.write(csv_content)
            
            return {
                "markdown_file": str(md_file_path),
                "csv_file": str(csv_file_path) if csv_file_path else None,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def _extract_csv_from_response(self, response_content: str) -> str:
        """
        Extract CSV data from the LLM response if it contains CSV format.
        Looks for CSV blocks marked with ```csv or similar patterns.
        """
        import re
        
        # Look for CSV blocks in the response
        csv_patterns = [
            r'```csv\s*\n(.*?)\n```',  # ```csv ... ```
            r'```\s*\n(.*?)\n```',     # ``` ... ``` (generic code block)
            r'CSV Data:\s*\n(.*?)(?=\n\n|\n[A-Z]|$)',  # CSV Data: ... followed by new section
        ]
        
        for pattern in csv_patterns:
            match = re.search(pattern, response_content, re.DOTALL | re.IGNORECASE)
            if match:
                csv_content = match.group(1).strip()
                # Basic validation - check if it looks like CSV
                if ',' in csv_content and '\n' in csv_content:
                    return csv_content
        
        return ""

    @staticmethod
    def combine_project_and_design_json(project_json_path: str, design_json_path: str) -> dict:
        """
        Helper method to combine two JSON files (project and design) into a single dictionary
        with 'project' and 'design' as top-level keys.
        """
        import json
        with open(project_json_path, 'r') as f:
            project_data = json.load(f)
        with open(design_json_path, 'r') as f:
            design_data = json.load(f)
        # Combine under top-level keys
        combined = {
            "project": project_data.get("project", project_data),
            "design": design_data.get("design", design_data)
        }
        return combined

# Usage example
def create_permit_agent(openai_api_key: str = None) -> LangChainPermitAgent:
    """Factory function to create a permit agent"""
    return LangChainPermitAgent(openai_api_key=openai_api_key)

# Test function
def test_permit_agent():
    """Test the LangChain permit agent for permit matrix generation only"""
    import os
    # Create ML Agent
    permit_agent_ml = create_permit_agent()

    # Combine example Aurora project and design JSONs
    project_json_path = "./eg_json_inputs/aurora_proj.json"
    design_json_path = "./eg_json_inputs/aurora_design.json"
    combined_data = LangChainPermitAgent.combine_project_and_design_json(project_json_path, design_json_path)

    print("\n" + "="*60)
    print("PERMIT MATRIX GENERATION TEST")
    print("="*60)
    # Generate the permit matrix (core function, returns Markdown table)
    permit_matrix = permit_agent_ml.generate_permit_matrix(combined_data)
    print("\nPERMIT MATRIX:\n" + "-" * 40)
    print(permit_matrix)

    # Save the permit matrix to both Markdown and CSV files
    save_result = permit_agent_ml.save_permit_matrix_to_files(permit_matrix)
    if save_result["status"] == "success":
        print(f"\u2713 Permit matrix saved to {save_result['markdown_file']}")
        if save_result['csv_file']:
            print(f"\u2713 CSV data saved to {save_result['csv_file']}")
        else:
            print("ℹ No CSV data found in response")
    else:
        print(f"✗ Error saving files: {save_result.get('error', 'Unknown error')}")

def save_results_to_files(openai_api_key: str = None):
    """
    Save permit matrix results to both Markdown and CSV files.
    Uses the example Aurora project and design JSONs in ./eg_json_inputs.
    """
    from pathlib import Path

    permit_agent = create_permit_agent(openai_api_key)

    # Combine example Aurora project and design JSONs
    project_json_path = "./eg_json_inputs/aurora_proj.json"
    design_json_path = "./eg_json_inputs/aurora_design.json"
    combined_data = LangChainPermitAgent.combine_project_and_design_json(project_json_path, design_json_path)

    # Generate the permit matrix
    print("Generating permit matrix...")
    permit_matrix = permit_agent.generate_permit_matrix(combined_data)

    # Save the permit matrix to both Markdown and CSV files
    save_result = permit_agent.save_permit_matrix_to_files(permit_matrix)
    if save_result["status"] == "success":
        print(f"✓ Permit matrix saved to {save_result['markdown_file']}")
        if save_result['csv_file']:
            print(f"✓ CSV data saved to {save_result['csv_file']}")
        else:
            print("ℹ No CSV data found in response")
    else:
        print(f"✗ Error saving files: {save_result.get('error', 'Unknown error')}")

if __name__ == "__main__":
    print("Running permit agent analysis...")
    print("This will display the permit matrix in the terminal AND save it to both Markdown and CSV files.\n")

    # Create agent
    permit_agent = create_permit_agent()

    # Combine example Aurora project and design JSONs
    project_json_path = "./eg_json_inputs/aurora_proj.json"
    design_json_path = "./eg_json_inputs/aurora_design.json"
    combined_data = LangChainPermitAgent.combine_project_and_design_json(project_json_path, design_json_path)

    print("="*60)
    print("PERMIT MATRIX GENERATION")
    print("="*60)
    # Generate the permit matrix (core function, returns Markdown table)
    permit_matrix = permit_agent.generate_permit_matrix(combined_data)
    print("\nPERMIT MATRIX:\n" + "-" * 40)
    print(permit_matrix)

    # Save the permit matrix to both Markdown and CSV files
    save_result = permit_agent.save_permit_matrix_to_files(permit_matrix)
    if save_result["status"] == "success":
        print(f"\n✓ Permit matrix saved to {save_result['markdown_file']}")
        if save_result['csv_file']:
            print(f"✓ CSV data saved to {save_result['csv_file']}")
        else:
            print("ℹ No CSV data found in response")
    else:
        print(f"\n✗ Error saving files: {save_result.get('error', 'Unknown error')}")