"""
Command line entry module, providing the text2mcp command line tool
"""
import os
import sys
import argparse
import asyncio
import logging
from typing import List, Optional, Dict, Any
import importlib.metadata

from text2mcp.core.generator import CodeGenerator
from text2mcp.server.runner import ServiceRunner
from text2mcp.utils.installer import PackageInstaller
from text2mcp.utils.config import load_config, save_config, LLMConfig

# Set up logging format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Get version number
try:
    __version__ = importlib.metadata.version("text2mcp")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.1.0"  # Default version number

def get_parser() -> argparse.ArgumentParser:
    """
    Create command line argument parser
    
    Returns:
        argparse.ArgumentParser: Command line argument parser
    """
    parser = argparse.ArgumentParser(
        description="Text2MCP: Generate MCP services from natural language descriptions",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        '--version', 
        action='version', 
        version=f'%(prog)s {__version__}'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Subcommands')
    
    # generate command
    gen_parser = subparsers.add_parser('generate', help='Generate MCP service code')
    gen_parser.add_argument('description', help='Natural language description of the MCP service')
    gen_parser.add_argument('-o', '--output', help='Output filename', default='mcp_service.py')
    gen_parser.add_argument('-d', '--directory', help='Output directory', default='./')
    gen_parser.add_argument('-t', '--template', help='Template file path', default='example.md')
    gen_parser.add_argument('-c', '--config', help='Configuration file path')
    gen_parser.add_argument('-k', '--api-key', help='OpenAI API key, takes precedence over environment variables and configuration files')
    gen_parser.add_argument('-m', '--model', help='LLM model name, takes precedence over environment variables and configuration files')
    gen_parser.add_argument('-u', '--base-url', help='OpenAI compatible interface base URL, takes precedence over environment variables and configuration files')
    
    # run command
    run_parser = subparsers.add_parser('run', help='Run MCP service')
    run_parser.add_argument('script', help='Path to the Python script to run')
    run_parser.add_argument('--python', action='store_true', help='Use python instead of uv to run')
    run_parser.add_argument('--log-dir', help='Log directory', default='./service_logs')
    
    # install command
    install_parser = subparsers.add_parser('install', help='Install Python packages')
    install_parser.add_argument('package', nargs='?', help='Name of the package to install')
    install_parser.add_argument('-r', '--requirements', help='Path to requirements file')
    install_parser.add_argument('-p', '--packages', nargs='+', help='List of packages to install')
    
    # config command
    config_parser = subparsers.add_parser('config', help='Manage configuration')
    config_parser.add_argument('--api-key', help='OpenAI API key')
    config_parser.add_argument('--model', help='OpenAI model name (e.g., gpt-3.5-turbo, gpt-4)')
    config_parser.add_argument('--base-url', help='Custom API base URL (for services compatible with OpenAI interface)')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    config_parser.add_argument('-f', '--file', help='Configuration file path')
    
    # server command
    server_parser = subparsers.add_parser('server', help='Start MCP server')
    server_parser.add_argument('--host', default='0.0.0.0', help='Server host')
    server_parser.add_argument('--port', type=int, default=8000, help='Server port')
    server_parser.add_argument('--module', help='Python module to start as server')
    
    return parser

async def generate_code(args: argparse.Namespace) -> int:
    """
    Generate MCP service code
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code, 0 indicates success, non-zero indicates failure
    """
    try:
        generator = CodeGenerator(
            config_file=args.config,
            api_key=args.api_key,
            model=args.model,
            base_url=args.base_url
        )
        code = generator.generate(args.description, args.template)
        
        if code:
            saved_path = generator.save_to_file(code, args.output, args.directory)
            if saved_path:
                logger.info(f"✅ Code generation successful! Saved to: {saved_path}")
                return 0
            else:
                logger.error("❌ Code generation successful, but failed to save to file")
                return 1
        else:
            logger.error("❌ Code generation failed")
            return 1
    except Exception as e:
        logger.error(f"❌ Error occurred during code generation: {e}", exc_info=True)
        return 1

async def run_service(args: argparse.Namespace) -> int:
    """
    Run MCP service
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code, 0 indicates success, non-zero indicates failure
    """
    try:
        runner = ServiceRunner(args.log_dir)
        result = await runner.start_service(args.script, not args.python)
        
        if "success" in result.lower():
            logger.info(result)
            return 0
        else:
            logger.error(result)
            return 1
    except Exception as e:
        logger.error(f"❌ Error occurred while running service: {e}", exc_info=True)
        return 1

async def install_packages(args: argparse.Namespace) -> int:
    """
    Install Python packages
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code, 0 indicates success, non-zero indicates failure
    """
    try:
        result = await PackageInstaller.install(
            package=args.package,
            requirements=args.requirements,
            packages=args.packages
        )
        
        if "fail" in result.lower():
            logger.error(result)
            return 1
        else:
            logger.info(result)
            return 0
    except Exception as e:
        logger.error(f"❌ Error occurred while installing packages: {e}", exc_info=True)
        return 1

def manage_config(args: argparse.Namespace) -> int:
    """
    Manage configuration
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code, 0 indicates success, non-zero indicates failure
    """
    try:
        # Load existing configuration
        config = load_config(args.file)
        
        # Show configuration
        if args.show:
            llm_config = config.get("llm_config")
            if llm_config:
                print("\nOpenAI Configuration:")
                print(f"  API Key: {'*' * 8 + llm_config.api_key[-4:] if llm_config.api_key else 'Not set'}")
                print(f"  Model: {llm_config.model or 'Not set'}")
                if llm_config.base_url:
                    print(f"  Base URL: {llm_config.base_url}")
            else:
                print("\nLLM Configuration: Not set")
                
            print("\nTiming Settings:")
            print(f"  Heartbeat Interval: {config.get('heartbeat_interval')} seconds")
            print(f"  Heartbeat Timeout: {config.get('heartbeat_timeout')} seconds")
            print(f"  HTTP Timeout: {config.get('http_timeout')} seconds")
            print(f"  Reconnection Interval: {config.get('reconnection_interval')} seconds")
            return 0
        
        # Update configuration
        if any([args.api_key, args.model, args.base_url]):
            llm_config = config.get("llm_config", LLMConfig(api_key="", model="gpt-3.5-turbo"))
            
            if args.api_key:
                llm_config.api_key = args.api_key
            if args.model:
                llm_config.model = args.model
            if args.base_url:
                llm_config.base_url = args.base_url
                
            config["llm_config"] = llm_config
            save_config(config, args.file)
            logger.info("✅ Configuration updated")
            return 0
            
        # If no action specified, show configuration by default
        if not args.show:
            return manage_config(argparse.Namespace(show=True, file=args.file))
            
        return 0
    except Exception as e:
        logger.error(f"❌ Error occurred while managing configuration: {e}", exc_info=True)
        return 1

async def start_server(args: argparse.Namespace) -> int:
    """
    Start MCP server
    
    Args:
        args: Command line arguments
        
    Returns:
        int: Exit code, 0 indicates success, non-zero indicates failure
    """
    try:
        if args.module:
            # Load specified module and start its MCP server
            try:
                # Add current directory to Python path
                sys.path.append(os.getcwd())
                
                # Try to import module
                module_name = args.module
                module = __import__(module_name)
                
                # Run the module's main() function if it exists
                if hasattr(module, 'main'):
                    await module.main(args.host, args.port)
                else:
                    logger.error(f"❌ Module {module_name} does not have a main() function")
                    return 1
            except ImportError as e:
                logger.error(f"❌ Cannot import module {args.module}: {e}")
                return 1
        else:
            # TODO: Implement built-in MCP server if needed
            logger.error("❌ No module specified, built-in server not supported yet")
            return 1
    except Exception as e:
        logger.error(f"❌ Error occurred while starting server: {e}", exc_info=True)
        return 1

async def main_async() -> int:
    """
    Asynchronous main function
    
    Returns:
        int: Exit code
    """
    parser = get_parser()
    args = parser.parse_args()
    
    if args.command == 'generate':
        return await generate_code(args)
    elif args.command == 'run':
        return await run_service(args)
    elif args.command == 'install':
        return await install_packages(args)
    elif args.command == 'config':
        return manage_config(args)
    elif args.command == 'server':
        return await start_server(args)
    else:
        # If no command specified, show help
        parser.print_help()
        return 0

def main() -> None:
    """
    Command line entry point main function
    """
    try:
        # Different event loop policy needed on Windows
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            
        # Run asynchronous main function
        exit_code = asyncio.run(main_async())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Unhandled error occurred while executing command: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
