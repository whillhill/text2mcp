"""
Code generator module, used to generate MCP service code from natural language descriptions
"""
import os
import re
import logging
from typing import Optional, Dict, Any, Union, List

# Add conditional import for yaml
try:
    import yaml
except ImportError:
    logging.warning("PyYAML library not installed, YAML front matter functionality in Markdown templates will not be available")
    yaml = None

from text2mcp.utils.config import load_config, LLMConfig
from text2mcp.utils.llm_client import LLMClientFactory

logger = logging.getLogger(__name__)

class CodeGenerator:
    """
    Code generator class, responsible for converting natural language descriptions into MCP service code
    """
    
    def __init__(self, config_file: Optional[str] = None, api_key: Optional[str] = None, 
                 model: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize the code generator
        
        Args:
            config_file: Optional configuration file path, if not provided, default configuration lookup logic is used
            api_key: Optional OpenAI API key, directly passed parameters have highest priority
            model: Optional LLM model name, directly passed parameters have highest priority
            base_url: Optional OpenAI compatible interface base URL, directly passed parameters have highest priority
        """
        # Load configuration
        self.config = load_config(config_file)
        self.llm_config: LLMConfig = self.config.get("llm_config")
        
        # If parameters are passed directly, override the settings in the configuration
        if api_key or model or base_url:
            if not self.llm_config:
                # If there is no configuration, create a new one
                self.llm_config = LLMConfig(
                    api_key=api_key or "",
                    model=model or "gpt-3.5-turbo",
                    base_url=base_url
                )
                self.config["llm_config"] = self.llm_config
            else:
                # Use the passed parameters to override the existing configuration
                if api_key:
                    self.llm_config.api_key = api_key
                if model:
                    self.llm_config.model = model
                if base_url is not None:  # Allow explicit setting to None
                    self.llm_config.base_url = base_url
        
        if not self.llm_config:
            logger.warning("LLM configuration not found, code generation functionality will not be available")
        else:
            self.model = self.llm_config.model
            logger.info(f"Using model: {self.model}")
            
            # Initialize LLM client
            self.llm_client = LLMClientFactory.create_client(self.llm_config)
            if self.llm_client:
                logger.info(f"OpenAI client initialization successful")
            else:
                logger.warning("LLM client initialization failed")
    
    def _call_llm(self, prompt: str) -> str:
        """
        Call LLM API to generate code
        
        Args:
            prompt: Prompt text
            
        Returns:
            str: LLM response text
        """
        logger.info("Sending request to LLM...")
        try:
            # Call LLM API
            response = self.llm_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an assistant specialized in generating Python code. Output only the raw Python code based on the user's request, wrapped in ```python markdown blocks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Adjust the balance between creativity and determinism
            )
            logger.debug(f"LLM response: {response}")
            response_text = response.choices[0].message.content
            return response_text
        except Exception as e:
            logger.error(f"Error occurred when calling LLM: {e}", exc_info=True)
            return f"# Error calling LLM: {e}"
    
    def _extract_code(self, response_text: str) -> Optional[str]:
        """
        Extract code blocks from LLM response
        
        Args:
            response_text: LLM response text
            
        Returns:
            Optional[str]: Extracted code, or None if extraction fails
        """
        # Regular expression to find ```python ... ``` code blocks
        code_blocks = re.findall(r"```(?:python|Python)?\s*([\s\S]*?)\s*```", response_text)
        
        if code_blocks:
            logger.info("Successfully extracted Python code blocks")
            # If there are multiple code blocks, merge them
            return "\n".join(block.strip() for block in code_blocks)
        else:
            # Fallback: If no markdown blocks are found, maybe the model directly output raw code?
            # Use this approach with caution, as it might return explanatory text
            logger.warning("No ```python ... ``` blocks found in the response. Returning raw response (may contain non-code text).")
            # Simple check: Does this look like Python code? (very simple check)
            if "def " in response_text or "import " in response_text or "class " in response_text:
                return response_text.strip()
            else:
                logger.error("Fallback failed: Raw response doesn't look like Python code.")
                return None  # Indicate extraction failure
    
    def _extract_code_from_markdown(self, markdown_content: str) -> str:
        """
        Extract Python code blocks from Markdown content and integrate them
        
        Args:
            markdown_content: Markdown formatted content
            
        Returns:
            str: Integrated Python code
        """
        # Extract all Python code blocks
        code_blocks = re.findall(r"```(?:python|Python)\s*([\s\S]*?)\s*```", markdown_content)
        
        if not code_blocks:
            logger.warning("No Python code blocks found in the Markdown template")
            return self._get_default_template()
        
        # Try to extract YAML front matter
        yaml_metadata = {}
        yaml_match = re.match(r"---\s*([\s\S]*?)\s*---", markdown_content)
        metadata_comment = ["# Template metadata:"]
        
        if yaml_match:
            try:
                if yaml:  # Ensure yaml module is imported
                    yaml_metadata = yaml.safe_load(yaml_match.group(1))
                    # Add metadata as comments
                    if yaml_metadata and isinstance(yaml_metadata, dict):
                        for key, value in yaml_metadata.items():
                            metadata_comment.append(f"# {key}: {value}")
                    logger.info(f"Extracted metadata from Markdown template: {yaml_metadata}")
            except Exception as e:
                logger.warning(f"Error parsing YAML metadata: {e}")
        
        # Integrate all code blocks
        combined_code = []
        combined_code.append("\n".join(metadata_comment) + "\n")
        
        # Check if there are specific section markers in the Markdown
        sections = re.findall(r"#+\s*(.*?)\s*\n\s*```python\s*([\s\S]*?)\s*```", markdown_content)
        
        if sections:
            # If sections with headings are found, organize them in order
            logger.info(f"Extracted {len(sections)} code blocks with headings from Markdown")
            
            # Check if there is an imports section, ensure it's at the front
            imports_section = None
            other_sections = []
            
            for section_title, section_code in sections:
                if re.search(r"import|imports|modules", section_title.lower()):
                    imports_section = section_code.strip()
                else:
                    other_sections.append((section_title, section_code.strip()))
            
            # If there is an imports section, add it first
            if imports_section:
                combined_code.append(f"# {'-' * 40}")
                combined_code.append(f"# Import section")
                combined_code.append(f"# {'-' * 40}\n")
                combined_code.append(imports_section)
            
            # Then add other sections
            for title, code in other_sections:
                combined_code.append(f"\n# {'-' * 40}")
                combined_code.append(f"# {title}")
                combined_code.append(f"# {'-' * 40}\n")
                combined_code.append(code)
        else:
            # If no sections with headings are found, combine all code blocks in order
            logger.info("No code blocks with headings found, combining all code blocks directly")
            for i, block in enumerate(code_blocks):
                if i > 0:
                    combined_code.append(f"\n# {'-' * 40}")
                    combined_code.append(f"# Code block {i+1}")
                    combined_code.append(f"# {'-' * 40}\n")
                combined_code.append(block.strip())
        
        result = "\n".join(combined_code)
        
        # Validate the generated code
        try:
            compile(result, "<string>", "exec")  # Validate syntax
            logger.info("Code generated from Markdown passed syntax validation")
        except SyntaxError as e:
            logger.warning(f"Syntax error in code generated from Markdown: {e}")
            # Log the error but continue using the generated code, as LLM might be able to fix these issues
        
        return result
    
    def _load_template(self, template_file: str) -> str:
        """
        Load template file (supports .py and .md formats)
        
        Args:
            template_file: Template filename or path
            
        Returns:
            str: Template file content
        """
        # Infer file extension
        original_template_file = template_file
        if not template_file.endswith('.py') and not template_file.endswith('.md'):
            # Try both extensions
            if os.path.exists(template_file + '.md'):
                template_file = template_file + '.md'
            else:
                template_file = template_file + '.py'
        
        # Define list of possible template paths
        package_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        possible_paths = [
            template_file,  # Current directory/absolute path
            os.path.join(package_dir, "templates", template_file),  # templates in package installation directory
            os.path.join(package_dir, "..", "examples", template_file),  # examples in project root directory
            # Try paths with the other extension
            original_template_file + ('.py' if template_file.endswith('.md') else '.md'),
            os.path.join(package_dir, "templates", original_template_file + ('.py' if template_file.endswith('.md') else '.md')),
            os.path.join(package_dir, "..", "examples", original_template_file + ('.py' if template_file.endswith('.md') else '.md'))
        ]
        
        # Iterate through possible paths
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    logger.info(f"Successfully loaded template file: {path}")
                    
                    # If it's a Markdown file, extract code blocks
                    if path.endswith('.md'):
                        return self._extract_code_from_markdown(content)
                        
                    return content
                except Exception as e:
                    logger.error(f"Error reading template file {path}: {e}", exc_info=True)
                    # Continue trying the next possible path
        
        # If all paths fail, use default template
        logger.warning(f"Template file not found: {original_template_file}, will use simple template")
        return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """
        Get default MCP service template
        
        Returns:
            str: Default template content
        """
        return '''
import argparse
import logging
import uvicorn
import time
from fastapi.responses import JSONResponse
from mcp.server import FastMCP, Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount

mcp = FastMCP("example.py")

logger = logging.getLogger(__name__)

@mcp.tool()
async def example_function(param1: str, param2: int):
    """
    Example MCP tool
    :param param1: Input parameter 1
    :param param2: Input parameter 2
    :return: Output result
    """
    # Implement code logic
    result = f"Process {param1} and {param2}"
    return result

async def health_check(request):
    """Health check endpoint"""
    return JSONResponse({"status": "healthy", "timestamp": int(time.time())}) 

def create_starlette_app(mcp_server: Server, *, debug: bool = False):
    """Create a Starlette application that provides MCP service"""
    sse = SseServerTransport("/messages/")
    
    async def handle_sse(request):
        async with sse.connect_sse(
            request.scope,
            request.receive,
            request._send,
        ) as (read_stream, write_stream):
            await mcp_server.run(
                read_stream,
                write_stream,
                mcp_server.create_initialization_options(),
            )
    
    return Starlette(
        debug=debug,
        routes=[
            Route("/sse", endpoint=handle_sse),
            Mount("/messages/", app=sse.handle_post_message),
            Route("/sse/health", endpoint=health_check, methods=["GET"])
        ],
    )    

if __name__ == "__main__":
    mcp_server = mcp._mcp_server

    parser = argparse.ArgumentParser(description='Run MCP SSE server')
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", default=12345, type=int, help="Server port")
    args = parser.parse_args()
 
    starlette_app = create_starlette_app(mcp_server, debug=True)
    uvicorn.run(starlette_app, host=args.host, port=args.port)
'''
    
    def generate(self, description: str, template_file: str = "example.md") -> Optional[str]:
        """
        Generate MCP service code based on natural language description
        
        Args:
            description: Text describing the required code functionality
            template_file: Optional template file name
            
        Returns:
            Optional[str]: Generated code, or None if generation fails
        """
        if not self.llm_client:
            logger.error("Cannot generate code: LLM client not initialized")
            return None
        
        example_code = self._load_template(template_file)
        prompt = f"Generate Python code for the following task:\n\n{description}\n\nEnsure the code is complete, correct, and follows best practices. Output only the code itself. Please strictly implement the MCP service according to the following template example:\n\n{example_code}\n\nDo not output any explanatory content, only the code"
        
        logger.info("Requesting code generation...")
        raw_response = self._call_llm(prompt)
        
        if raw_response and not raw_response.startswith("# Error"):
            extracted_code = self._extract_code(raw_response)
            return extracted_code
        else:
            logger.error(f"Failed to get valid response from LLM. Raw response: {raw_response}")
            return None
    
    def save_to_file(self, code: str, filename: str, directory: str = "./") -> Optional[str]:
        """
        Save generated code to file
        
        Args:
            code: Code to save
            filename: Target filename
            directory: Target directory path
            
        Returns:
            Optional[str]: Full path of the saved file, or None if saving fails
        """
        if not code:
            logger.error("Cannot save empty code")
            return None
            
        if not filename.endswith(".py"):
            filename += ".py"
            logger.info(f"Added '.py' extension. Filename is now: {filename}")
        
        absolute_directory = os.path.abspath(directory)
        full_path = os.path.join(absolute_directory, filename).replace("\\", "/")

        try:
            # Create directory if it doesn't exist
            os.makedirs(directory, exist_ok=True) 
            
            # Write code to file
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(code)
            logger.info(f"Code successfully saved to: {full_path}")
            return full_path
        except OSError as e:
            logger.error(f"Error creating directory '{directory}': {e}")
            return None
        except IOError as e:
            logger.error(f"Error writing code to file '{full_path}': {e}")
            return None
        except Exception as e:
             logger.error(f"Unexpected error when saving file: {e}", exc_info=True)
             return None 
