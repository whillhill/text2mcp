"""
Python package installation tool module, using uv for dependency management
"""
import os
import subprocess
import asyncio
import logging
from typing import Optional, List, Union

logger = logging.getLogger(__name__)

class PackageInstaller:
    """
    Python package installation tool class, using uv for dependency management
    """
    
    @staticmethod
    def check_uv_installed() -> bool:
        """
        Check if uv is installed
        
        Returns:
            bool: True if installed, False otherwise
        """
        try:
            subprocess.run(["uv", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("❌ uv is not installed, please install uv first:")
            logger.error("   pip install uv")
            return False
    
    @staticmethod
    async def install_package(package_name: str) -> str:
        """
        Install a single Python package
        
        Args:
            package_name: Name of the package to install
            
        Returns:
            str: Installation result information
            
        Raises:
            Exception: Raised when installation fails
        """
        if not PackageInstaller.check_uv_installed():
            raise Exception("❌ uv is not installed, please install uv first.")
            
        logger.info(f"📦 Installing package: {package_name}")
        process = await asyncio.create_subprocess_exec(
            "uv", "pip", "install", package_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"❌ Failed to install {package_name}: {error_msg}")
            raise Exception(f"Failed to install {package_name}: {error_msg}")
            
        logger.info(f"✅ {package_name} installed successfully")
        return f"{package_name} installed successfully"
    
    @staticmethod
    async def install_from_requirements(requirements_file: str) -> str:
        """
        Install dependencies from requirements file
        
        Args:
            requirements_file: Path to requirements file
            
        Returns:
            str: Installation result information
            
        Raises:
            Exception: Raised when installation fails
        """
        if not os.path.exists(requirements_file):
            logger.error(f"❌ File {requirements_file} does not exist")
            raise Exception(f"File {requirements_file} does not exist")
            
        if not PackageInstaller.check_uv_installed():
            raise Exception("❌ uv is not installed, please install uv first.")
            
        logger.info(f"📦 Installing dependencies from {requirements_file}")
        process = await asyncio.create_subprocess_exec(
            "uv", "pip", "install", "-r", requirements_file,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"❌ Dependency installation failed: {error_msg}")
            raise Exception(f"Dependency installation failed: {error_msg}")
            
        logger.info("✅ Dependencies installed successfully")
        return "Dependencies installed successfully"
    
    @staticmethod
    async def install(
        package: Optional[str] = None, 
        requirements: Optional[str] = None,
        packages: Optional[List[str]] = None
    ) -> str:
        """
        Install Python dependencies, supports multiple installation methods
        
        Args:
            package: Name of a single package to install
            requirements: Path to requirements file
            packages: List of package names to install
            
        Returns:
            str: Installation result information
            
        Raises:
            Exception: Raised when installation fails or parameters are invalid
        """
        if requirements:
            return await PackageInstaller.install_from_requirements(requirements)
        elif package:
            return await PackageInstaller.install_package(package)
        elif packages:
            results = []
            for pkg in packages:
                try:
                    result = await PackageInstaller.install_package(pkg)
                    results.append(result)
                except Exception as e:
                    results.append(f"Failed to install {pkg}: {str(e)}")
            return "\n".join(results)
        else:
            raise Exception("❌ Please provide package name, package list, or specify requirements file")
    
    @staticmethod
    def create_requirements_file(
        packages: List[str], 
        output_file: str = "requirements.txt"
    ) -> str:
        """
        Create requirements.txt file
        
        Args:
            packages: List of packages to include
            output_file: Output file path, defaults to requirements.txt in the current directory
            
        Returns:
            str: Creation result information
        """
        try:
            with open(output_file, "w", encoding="utf-8") as f:
                for package in packages:
                    f.write(f"{package}\n")
            
            logger.info(f"✅ Successfully created {output_file}")
            return f"Successfully created {output_file}"
        except Exception as e:
            error_msg = f"❌ Failed to create {output_file}: {str(e)}"
            logger.error(error_msg)
            return error_msg 
