"""
Text2MCP's MCP server module, providing MCP interfaces for code generation, service startup, and package installation
"""
import os
import argparse
import logging
import asyncio
import uvicorn
import time
from fastapi.responses import JSONResponse
from mcp.server import FastMCP, Server
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route, Mount

from text2mcp.core.generator import CodeGenerator
from text2mcp.server.runner import ServiceRunner
from text2mcp.utils.installer import PackageInstaller

# Create MCP service
mcp = FastMCP("text2mcp_server")

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@mcp.tool()
async def generate_mcp_service(description: str, filename: str = "mcp_service.py", directory: str = "./mcp-services", 
                              api_key: str = None, model: str = None, base_url: str = None) -> str:
    """
    Generate MCP service code based on natural language description and save to file
    
    :param description: Natural language description of the MCP service
    :param filename: Filename to save
    :param directory: Directory path to save
    :param api_key: Optional OpenAI API key, takes precedence over environment variables and configuration files
    :param model: Optional LLM model name, takes precedence over environment variables and configuration files
    :param base_url: Optional OpenAI compatible interface base URL, takes precedence over environment variables and configuration files
    :return: Path of the saved file or error message
    """
    try:
        # Instantiate code generator
        generator = CodeGenerator(api_key=api_key, model=model, base_url=base_url)
        
        # Generate code
        logger.info("Starting code generation...")
        generated_code = generator.generate(description)
        
        if generated_code:
            # Save code to file
            logger.info("Saving generated code...")
            saved_path = generator.save_to_file(generated_code, filename, directory)
            
            if saved_path:
                success_msg = f"✅ Code generation successful! Saved to: {saved_path}"
                logger.info(success_msg)
                return saved_path
            else:
                error_msg = "❌ Code generation successful, but failed to save to file"
                logger.error(error_msg)
                return error_msg
        else:
            error_msg = "❌ Code generation failed"
            logger.error(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"❌ Error occurred during code generation: {e}"
        logger.error(error_msg, exc_info=True)
        return error_msg

@mcp.tool()
async def run_mcp_service(script_path: str, use_uv: bool = True) -> str:
    """
    Start MCP service
    
    :param script_path: Path to the Python script to start
    :param use_uv: Whether to use uv instead of python to run the script
    :return: Startup result information
    """
    try:
        runner = ServiceRunner()
        result = await runner.start_service(script_path, use_uv)
        return result
    except Exception as e:
        error_msg = f"❌ Error occurred while starting service: {e}"
        logger.error(error_msg, exc_info=True)
        return error_msg

@mcp.tool()
async def install_package(package: str = None, requirements: str = None) -> str:
    """
    Install Python package or dependencies from requirements file
    
    :param package: Name of the package to install
    :param requirements: Path to requirements file
    :return: Installation result information
    """
    try:
        if not package and not requirements:
            return "❌ Please provide package name or specify requirements file"
            
        return await PackageInstaller.install(package=package, requirements=requirements)
    except Exception as e:
        error_msg = f"❌ Error occurred while installing dependencies: {e}"
        logger.error(error_msg, exc_info=True)
        return error_msg

@mcp.tool()
async def configure_openai(api_key: str, model: str = "gpt-3.5-turbo", base_url: str = None) -> str:
    """
    Configure OpenAI or compatible interface settings
    
    :param api_key: OpenAI API key
    :param model: Model name, defaults to gpt-3.5-turbo
    :param base_url: Optional custom API base URL, for other services compatible with OpenAI interface
    :return: Configuration result information
    """
    try:
        from text2mcp.utils.config import load_config, save_config
        
        # Load current configuration
        config = load_config()
        
        # Update configuration
        if not config.get("llm_config"):
            from text2mcp.utils.config import LLMConfig
            config["llm_config"] = LLMConfig(api_key="", model="gpt-3.5-turbo")
        
        config["llm_config"].api_key = api_key
        config["llm_config"].model = model
        if base_url:
            config["llm_config"].base_url = base_url
        
        # Save configuration
        save_config(config)
        
        return f"✅ OpenAI configuration updated. Model: {model}" + (f", Custom URL: {base_url}" if base_url else "")
    except Exception as e:
        error_msg = f"❌ Error occurred while configuring OpenAI: {e}"
        logger.error(error_msg, exc_info=True)
        return error_msg

# Health check endpoint
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

async def main(host="0.0.0.0", port=8000):
    """
    Main function for starting the MCP server
    
    Args:
        host: Server host address
        port: Server port
    """
    mcp_server = mcp._mcp_server
    starlette_app = create_starlette_app(mcp_server, debug=True)
    
    logger.info(f"Starting Text2MCP service at http://{host}:{port}/sse")
    config = uvicorn.Config(starlette_app, host=host, port=port)
    server = uvicorn.Server(config)
    await server.serve()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Text2MCP server')
    parser.add_argument("--host", default="0.0.0.0", help="Server host")
    parser.add_argument("--port", default=8000, type=int, help="Server port")
    args = parser.parse_args()
    
    # Different event loop policy needed on Windows
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main(args.host, args.port)) 
