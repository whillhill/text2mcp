"""
Text2MCP - A tool for generating MCP (Modular Communication Protocol) services from natural language descriptions

Text2MCP uses OpenAI or OpenAI-compatible language models to convert natural language descriptions into complete MCP service code.

Main exported interfaces:
- CodeGenerator: Core code generation class
- ServiceRunner: Service runner
- PackageInstaller: Dependency installation tool

Main command line entry point: text2mcp
"""
import importlib.metadata

from text2mcp.core.generator import CodeGenerator
from text2mcp.server.runner import ServiceRunner
from text2mcp.utils.installer import PackageInstaller

# Try to get version number
try:
    __version__ = importlib.metadata.version("text2mcp")
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.1.0"  # Default version number

__all__ = [
    "CodeGenerator",
    "ServiceRunner",
    "PackageInstaller",
] 
