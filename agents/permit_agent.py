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
            r'CSV:\s*\n(.*?)(?=\n\n|\n[A-Z]|$)',  # CSV: ... followed by new section
        ]
        
        for pattern in csv_patterns:
            match = re.search(pattern, response_content, re.DOTALL | re.IGNORECASE)
            if match:
                csv_content = match.group(1).strip()
                # Basic validation - check if it looks like CSV
                if ',' in csv_content and '\n' in csv_content:
                    return csv_content
        
        # If no CSV block found, try to extract table data and convert to CSV
        # Look for markdown table and convert it
        table_pattern = r'\|.*\|.*\|\n\|[\s\-:|]+\|\n(.*?)(?=\n\n|\n[A-Z]|$)'
        table_match = re.search(table_pattern, response_content, re.DOTALL)
        if table_match:
            table_content = table_match.group(1).strip()
            # Convert markdown table to CSV
            csv_lines = []
            for line in table_content.split('\n'):
                if line.strip() and '|' in line:
                    # Remove leading/trailing | and split by |
                    cells = [cell.strip() for cell in line.strip('|').split('|')]
                    csv_lines.append(','.join(f'"{cell}"' for cell in cells))
            
            if csv_lines:
                return '\n'.join(csv_lines)
        
        return ""
    
    def validate_permit_urls(self, permit_matrix_content: str) -> Dict[str, Any]:
        """
        Validate all URLs in the permit matrix by actually attempting to access them.
        This catches hallucinated URLs and ensures only real, accessible sources are included.
        """
        import re
        import requests
        from urllib.parse import urlparse
        
        try:
            # Extract URLs from the permit matrix
            url_pattern = r'https?://[^\s|\)]+'
            urls = re.findall(url_pattern, permit_matrix_content)
            
            validation_results = {
                "total_urls_found": len(urls),
                "valid_urls": [],
                "invalid_urls": [],
                "validation_errors": []
            }
            
            for url in urls:
                try:
                    # Clean the URL
                    clean_url = url.strip().rstrip('.,;:!?')
                    
                    # Skip common non-downloadable URLs
                    if any(skip in clean_url.lower() for skip in ['wikipedia', 'google', 'example.com', 'placeholder']):
                        validation_results["invalid_urls"].append({
                            "url": clean_url,
                            "reason": "Generic/non-agency URL"
                        })
                        continue
                    
                    # Test the URL
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }
                    response = requests.get(clean_url, timeout=10, headers=headers, allow_redirects=True)
                    
                    if response.status_code == 200:
                        # Check for "Page not found" or similar error messages in the content
                        content_lower = response.text.lower()
                        page_not_found_indicators = [
                            'page not found', '404', 'not found', 'error 404', 
                            'page does not exist', 'file not found', 'document not found',
                            'the requested page could not be found', 'page unavailable'
                        ]
                        
                        is_page_not_found = any(indicator in content_lower for indicator in page_not_found_indicators)
                        
                        if is_page_not_found:
                            validation_results["invalid_urls"].append({
                                "url": clean_url,
                                "reason": "Page not found (404 content detected)"
                            })
                            continue
                        
                        # Look for download links on the page
                        download_links = self._find_download_links(response.text, clean_url)
                        
                        # Check if the URL itself is directly downloadable
                        content_type = response.headers.get('content-type', '').lower()
                        is_directly_downloadable = any(ext in clean_url.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']) or \
                                                 'application/' in content_type
                        
                        validation_results["valid_urls"].append({
                            "url": clean_url,
                            "status_code": response.status_code,
                            "content_type": content_type,
                            "is_directly_downloadable": is_directly_downloadable,
                            "download_links_found": len(download_links),
                            "download_links": download_links,
                            "content_length": len(response.text)
                        })
                    else:
                        validation_results["invalid_urls"].append({
                            "url": clean_url,
                            "reason": f"HTTP {response.status_code}"
                        })
                        
                except requests.exceptions.RequestException as e:
                    validation_results["invalid_urls"].append({
                        "url": clean_url if 'clean_url' in locals() else url,
                        "reason": f"Connection error: {str(e)}"
                    })
                except Exception as e:
                    validation_results["validation_errors"].append({
                        "url": clean_url if 'clean_url' in locals() else url,
                        "error": str(e)
                    })
            
            # Calculate validation summary
            validation_results["summary"] = {
                "valid_count": len(validation_results["valid_urls"]),
                "invalid_count": len(validation_results["invalid_urls"]),
                "error_count": len(validation_results["validation_errors"]),
                "success_rate": len(validation_results["valid_urls"]) / max(len(urls), 1) * 100
            }
            
            return validation_results
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"URL validation failed: {str(e)}"
            }
    
    def _find_download_links(self, html_content: str, base_url: str) -> List[Dict[str, str]]:
        """
        Find download links on a webpage that might contain permit forms.
        """
        import re
        from urllib.parse import urljoin
        
        download_links = []
        
        # Common patterns for download links
        download_patterns = [
            r'<a[^>]*href=["\']([^"\']*\.(?:pdf|doc|docx|xls|xlsx))["\'][^>]*>([^<]*)</a>',
            r'<a[^>]*href=["\']([^"\']*download[^"\']*)["\'][^>]*>([^<]*)</a>',
            r'<a[^>]*href=["\']([^"\']*form[^"\']*)["\'][^>]*>([^<]*)</a>',
            r'<a[^>]*href=["\']([^"\']*permit[^"\']*)["\'][^>]*>([^<]*)</a>',
            r'<a[^>]*href=["\']([^"\']*application[^"\']*)["\'][^>]*>([^<]*)</a>',
        ]
        
        for pattern in download_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for match in matches:
                href, text = match
                if href:
                    # Make relative URLs absolute
                    full_url = urljoin(base_url, href)
                    
                    # Clean up the link text
                    clean_text = re.sub(r'<[^>]*>', '', text).strip()
                    
                    download_links.append({
                        "url": full_url,
                        "text": clean_text,
                        "type": "download_link"
                    })
        
        return download_links
    
    def _download_file(self, url: str, output_path: Path, filename_prefix: str) -> Dict[str, Any]:
        """
        Download a file from a URL and save it with a descriptive filename.
        """
        import requests
        from urllib.parse import urlparse
        
        try:
            # Download the file
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            
            # Determine file extension from URL or content-type
            parsed_url = urlparse(url)
            url_path = parsed_url.path.lower()
            
            # Try to get extension from URL first
            if any(ext in url_path for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']):
                for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']:
                    if ext in url_path:
                        file_extension = ext
                        break
            else:
                # Try to get from content-type
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' in content_type:
                    file_extension = '.pdf'
                elif 'word' in content_type or 'document' in content_type:
                    file_extension = '.docx'
                elif 'excel' in content_type or 'spreadsheet' in content_type:
                    file_extension = '.xlsx'
                else:
                    file_extension = '.pdf'  # Default to PDF
            
            # Create filename
            safe_prefix = "".join(c for c in filename_prefix if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_prefix}{file_extension}"
            filepath = output_path / filename
            
            # Save the file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return {
                "url": url,
                "filepath": str(filepath),
                "file_size": len(response.content),
                "content_type": response.headers.get('content-type', ''),
                "status": "success"
            }
            
        except Exception as e:
            return None
    
    def download_validated_forms(self, permit_matrix_content: str, output_dir: str = "./downloads/permits") -> Dict[str, Any]:
        """
        Download permit forms from validated URLs in the permit matrix.
        Only attempts downloads from URLs that passed validation.
        """
        import re
        import requests
        from pathlib import Path
        from urllib.parse import urlparse
        
        try:
            # First validate URLs
            validation_results = self.validate_permit_urls(permit_matrix_content)
            
            if validation_results.get("status") == "error":
                return validation_results
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            download_results = {
                "validation_summary": validation_results["summary"],
                "downloads": [],
                "errors": []
            }
            
            # Download from valid URLs and their download links
            for valid_url_info in validation_results["valid_urls"]:
                page_url = valid_url_info["url"]
                
                # First, try to download from the page URL if it's directly downloadable
                if valid_url_info.get("is_directly_downloadable"):
                    try:
                        download_result = self._download_file(page_url, output_path, "page_direct")
                        if download_result:
                            download_results["downloads"].append(download_result)
                    except Exception as e:
                        download_results["errors"].append({
                            "url": page_url,
                            "error": f"Direct download failed: {str(e)}"
                        })
                
                # Then, try to download from any download links found on the page
                download_links = valid_url_info.get("download_links", [])
                for link_info in download_links:
                    download_url = link_info["url"]
                    link_text = link_info["text"]
                    
                    try:
                        # Create a descriptive filename based on the link text
                        safe_text = "".join(c for c in link_text if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        filename_prefix = safe_text[:30] if safe_text else "download"
                        
                        download_result = self._download_file(download_url, output_path, filename_prefix)
                        if download_result:
                            download_result["source_page"] = page_url
                            download_result["link_text"] = link_text
                            download_results["downloads"].append(download_result)
                    except Exception as e:
                        download_results["errors"].append({
                            "url": download_url,
                            "source_page": page_url,
                            "error": f"Download link failed: {str(e)}"
                        })
            
            return download_results
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Download process failed: {str(e)}"
            }

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
    print("Running permit agent analysis with URL VALIDATION...")
    print("This will generate a permit matrix and validate all URLs to catch hallucinations.\n")

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

    print("\n" + "="*60)
    print("URL VALIDATION - CATCHING HALLUCINATIONS")
    print("="*60)
    # Validate all URLs in the permit matrix
    validation_result = permit_agent.validate_permit_urls(permit_matrix)
    print("\nURL VALIDATION RESULTS:\n" + "-" * 40)
    print(json.dumps(validation_result, indent=2))

    print("\n" + "="*60)
    print("DOWNLOADING VALIDATED FORMS")
    print("="*60)
    # Download forms from validated URLs
    download_result = permit_agent.download_validated_forms(permit_matrix)
    print("\nDOWNLOAD RESULTS:\n" + "-" * 40)
    print(json.dumps(download_result, indent=2))

    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    if validation_result.get("summary"):
        summary = validation_result["summary"]
        print(f"Total URLs found: {validation_result.get('total_urls_found', 0)}")
        print(f"Valid URLs: {summary.get('valid_count', 0)}")
        print(f"Invalid URLs: {summary.get('invalid_count', 0)}")
        print(f"Success rate: {summary.get('success_rate', 0):.1f}%")
        
        if summary.get('success_rate', 0) < 50:
            print("⚠️  WARNING: Low success rate indicates potential hallucinations!")
        else:
            print("✓ Good success rate - likely real permit sources")
    
    if download_result.get("downloads"):
        print(f"\nSuccessfully downloaded {len(download_result['downloads'])} permit forms")
        for download in download_result["downloads"]:
            print(f"  ✓ {download['filepath']}")