# Text2MCP

A powerful toolkit for generating MCP (Modular Communication Protocol) services from natural language descriptions.

## Key Features

- Generate complete MCP service code from natural language descriptions
- Support for OpenAI and compatible LLM providers with the OpenAI API interface
- One-click deployment and launch of generated MCP services
- Integrated dependency management with package installation support
- Custom template creation and reuse for consistent code generation
- Full command-line interface and Python API for all functionality
- Integrated dependency management with uv for efficient package installation
- Complete lifecycle management for MCP services

## Installation

```bash
pip install text2mcp
```

## Quick Start

### Configuration

First, set up your environment variables:

```bash
# Set environment variables
export OPENAI_API_KEY="your_api_key_here"
export OPENAI_MODEL="gpt-3.5-turbo"  # Optional
export OPENAI_BASE_URL="https://api.example.com/v1"  # Optional, for compatible APIs
```

Or pass parameters directly in code:

```python
from text2mcp import CodeGenerator

# Pass configuration directly
generator = CodeGenerator(
    api_key="your_api_key_here",
    model="gpt-3.5-turbo",
    base_url="https://api.example.com/v1"  # Optional, for compatible APIs
)
```

Or configure via command line:

```bash
text2mcp config --api-key "your_api_key" --model "gpt-4" --base-url "https://api.example.com/v1"
```

> **Tip**: Text2MCP supports any LLM service with an OpenAI-compatible interface. See the [Using Third-Party OpenAI Compatible APIs](#using-third-party-openai-compatible-apis) section for details.

### Generating MCP Services

#### Using Python API

```python
from text2mcp import CodeGenerator

# Initialize code generator
generator = CodeGenerator()

# Generate service
code = generator.generate("Create a calculator service that supports addition, subtraction, multiplication, and division")

# Save to file
generator.save_to_file(code, "calculator_service.py")
```

#### Using Custom Templates

```python
from text2mcp import CodeGenerator

# Initialize code generator
generator = CodeGenerator()

# Generate service using custom template
code = generator.generate(
    "Create a database query service that supports CRUD operations",
    template_file="my_template.md"
)

# Save to specified directory
generator.save_to_file(code, "db_service.py", directory="./services")
```

### Running MCP Services

```python
from text2mcp import ServiceRunner

# Initialize service runner
runner = ServiceRunner()

# Start service
runner.start_service("calculator_service.py")
```

### Installing Dependencies

```python
import asyncio
from text2mcp import PackageInstaller

async def install_deps():
    # Install a single package
    await PackageInstaller.install(package="requests")
    
    # Install multiple packages
    await PackageInstaller.install(packages=["numpy", "pandas"])
    
    # Install from requirements file
    await PackageInstaller.install(requirements="requirements.txt")

# Run installation
asyncio.run(install_deps())
```

### Command-Line Usage

#### Generating Services

```bash
# Basic usage
text2mcp generate "Create a calculator service that supports addition, subtraction, multiplication, and division" --output calculator_service.py

# Specify output directory
text2mcp generate "Create a weather query service" --output weather_service.py --directory ./services

# Use custom template
text2mcp generate "Create a data processing service" --template my_template.md --output data_service.py

# Use custom config file
text2mcp generate "Create a file conversion service" --config my_config.toml --output converter_service.py
```

#### Running Services

```bash
# Run service
text2mcp run calculator_service.py

# Specify host and port
text2mcp run calculator_service.py --host 0.0.0.0 --port 8080

# Use uv for enhanced performance
text2mcp run calculator_service.py --use-uv

# Run service in the background
text2mcp run calculator_service.py --daemon
```

#### Dependency Management

```bash
# Install a single package
text2mcp install requests

# Install multiple packages
text2mcp install numpy pandas matplotlib

# Install from requirements file
text2mcp install --requirements requirements.txt

# Create requirements file
text2mcp install --create-requirements --packages numpy,pandas,matplotlib
```

#### Configuration Management

```bash
# Set API key
text2mcp config --api-key "your_api_key"

# Set model
text2mcp config --model "gpt-4"

# Set custom API endpoint
text2mcp config --base-url "https://api.example.com/v1"

# Display current configuration
text2mcp config --show

# Reset configuration
text2mcp config --reset
```

#### Other Commands

```bash
# Check version
text2mcp --version

# View help
text2mcp --help
text2mcp generate --help
```

## Advanced Usage

### Custom Templates

You can create your own MCP service templates to ensure generated code follows your project structure and requirements. Templates can be Python files or Markdown files.

#### Markdown Templates (Recommended)

Markdown templates provide a more user-friendly format for creating templates, allowing you to include code, documentation, and configuration information in a single file.

```markdown
---
service_name: my_service
description: My custom service
author: Your Name
version: 1.0.0
---

# My MCP Service Template

## Import Section

```python
import argparse
import logging
from mcp.server import FastMCP

# Other imports...
```

## Service Initialization

```python
# Create MCP service
mcp = FastMCP("custom_service")

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## MCP Tool Definition

```python
@mcp.tool()
async def example_tool(param: str):
    """
    Example tool function
    :param param: Parameter description
    :return: Return value description
    """
    # Implementation code...
    return result
```

## Main Function

```python
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    # Start service...
```
```

When using Markdown templates, the system will automatically:
1. Extract YAML front matter metadata (if present)
2. Recognize all Python code blocks and combine them in order
3. Preserve heading structure as code comments
4. Prioritize "Import" related sections

### Using Templates

Whether using Python or Markdown templates, the usage is the same:

```bash
# Using Markdown template
text2mcp generate "Create a data processing service" --template my_template.md --output data_service.py
```

You can also omit the extension, and the system will automatically find the corresponding file:

```bash
text2mcp generate "Create a data processing service" --template my_template --output data_service.py
```

### Using Third-Party OpenAI Compatible APIs

Text2MCP supports any LLM service that implements the OpenAI API interface specification. Here's an example using a third-party API:

#### Configuration Validation

First, create a `config.toml` file:

```toml
[tool.llm]
api_key = "your-api-key-here"
base_url = "https://api.third-party-provider.com/v1"
model = "third-party-model-name"
```

Then write a simple script to verify the configuration is loaded correctly:

```python
from text2mcp.utils.config import load_config

# Load from environment variables
config1 = load_config()
print("Config from environment:", config1)

# Load from config file
config2 = load_config("config.toml")
print("Config from file:", config2)
```

#### Code Generation Example

Using a third-party API to generate MCP service code:

```python
from text2mcp import CodeGenerator
import os

# Create code generator with third-party provider config
generator = CodeGenerator(
    api_key="your-api-key-here",
    base_url="https://api.third-party-provider.com/v1",
    model="third-party-model-name"
)

# Generate a simple calculator service
service_description = """
Create a simple calculator service that supports the four basic operations:
addition, subtraction, multiplication, and division.
Each operation should be a separate API endpoint.
"""

# Define output directory
output_dir = "generated/calculator_service"
os.makedirs(output_dir, exist_ok=True)

# Generate code
generated_code = generator.generate(service_description, template_file="example.md")

if generated_code:
    # Save to file
    file_path = generator.save_to_file(generated_code, "calculator_service.py", directory=output_dir)
    if file_path:
        print(f"Service code generated and saved to: {file_path}")
    else:
        print("Error saving code to file")
else:
    print("Code generation failed")
```

> **Note**: When using third-party APIs, ensure the `model` parameter matches the model name supported by that API provider.

### Integration with Custom Applications

You can integrate Text2MCP into your applications to provide dynamic MCP service generation capabilities:

```python
from text2mcp import CodeGenerator, ServiceRunner
import asyncio

async def dynamic_service_creation(description, service_name):
    """Dynamically create and run an MCP service"""
    # Generate code
    generator = CodeGenerator()
    code = generator.generate(description)
    
    if code:
        # Save to file
        path = generator.save_to_file(code, f"{service_name}.py", "./services")
        
        # Start service
        runner = ServiceRunner()
        result = await runner.start_service(path)
        
        return {"status": "success", "service_path": path, "result": result}
    else:
        return {"status": "error", "message": "Code generation failed"}

# Usage example
asyncio.run(dynamic_service_creation(
    "Create a file processing service that supports reading, writing, and modifying text files.",
    "file_processor"
))
```

## FAQ

### 1. Why isn't my API key working?

Ensure your API key is in the correct format and has sufficient permissions and quota. OpenAI API keys typically start with "sk-".

### 2. How do I use a custom LLM provider?

As long as the LLM provider offers an OpenAI-compatible interface, you can use it by setting the `base_url` parameter:

```bash
text2mcp config --base-url "https://your-provider.com/v1"
```

For common third-party providers, here are some configuration examples:

```bash
# Command line configuration
text2mcp config --api-key "your-provider-key" --base-url "https://api.provider.com/v1" --model "provider-model-name"

# Or using environment variables
export OPENAI_API_KEY="your-provider-key"
export OPENAI_BASE_URL="https://api.provider.com/v1"
export OPENAI_MODEL="provider-model-name"

# Or passing parameters directly in code
generator = CodeGenerator(
    api_key="your-provider-key",
    base_url="https://api.provider.com/v1",
    model="provider-model-name"
)
```

### 3. What if the generated code quality is poor?

Try providing more detailed descriptions or use a more advanced model like GPT-4. You can also improve code quality by creating custom templates.

### 4. Why are dependency installations failing?

If using `uv` for dependency installation fails, ensure `uv` is installed:

```bash
pip install uv
```

Or add the `--no-uv` parameter to use standard pip:

```bash
text2mcp install requests --no-uv
```

## Contributing

Contributions are welcome! Please see the [contribution guidelines](CONTRIBUTING.md) for how to participate in the project's development.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details. 
11
