"""
MCP service runner module, used to start generated MCP services
"""
import os
import asyncio
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class ServiceRunner:
    """
    Service runner class, responsible for starting generated MCP services
    """
    
    def __init__(self, log_dir: str = "./service_logs"):
        """
        Initialize service runner
        
        Args:
            log_dir: Log directory path
        """
        self.log_dir = os.path.abspath(log_dir)
        
        # Ensure log directory exists
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
                logger.info(f"Log directory created: {self.log_dir}")
        except OSError as e:
            logger.error(f"Cannot create log directory {self.log_dir}: {e}")
            raise
    
    async def start_service(self, script_path: str, use_uv: bool = True) -> str:
        """
        Start MCP service
        
        Args:
            script_path: Path to Python script
            use_uv: Whether to use uv runner, if False then use python
            
        Returns:
            str: Message indicating success or failure of startup
        """
        # Verify path exists
        if not os.path.isfile(script_path):
            error_msg = f"Error: Script not found at {script_path}"
            logger.error(error_msg)
            return error_msg
            
        # Prepare log file
        script_filename = os.path.basename(script_path)
        log_file_path = os.path.join(self.log_dir, f"{script_filename}.log")
        
        # Determine run command
        if use_uv:
            command = ["uv", "run", script_path]
        else:
            command = ["python", script_path]
            
        # Determine script directory
        script_directory = os.path.dirname(script_path) or '.'
        
        process = None
        try:
            logger.info(f"Attempting to start service in background: {' '.join(command)} in directory '{script_directory}'")
            logger.info(f"Service logs will be output to: {log_file_path}")
            
            # Open log file in append mode
            with open(log_file_path, 'ab') as log_file:
                # Create subprocess
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=log_file,
                    stderr=log_file,
                    cwd=script_directory,
                )
                
            pid = process.pid
            success_msg = f"Service started successfully, PID: {pid}. Logs are recorded in: {log_file_path}"
            logger.info(success_msg)
            return success_msg
            
        except FileNotFoundError:
            # Command or script not found
            error_msg = f"Error: '{command[0]}' command not found or script '{script_path}' not found."
            if use_uv:
                error_msg += " Please ensure 'uv' is installed and in PATH."
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            # Catch other exceptions
            error_msg = f"Error occurred when trying to start process for '{script_path}': {e}"
            logger.error(error_msg, exc_info=True)
            return f"Service startup failed. Error: {e}"
    
    def check_service_running(self, pid: int) -> bool:
        """
        Check if service is still running
        
        Args:
            pid: Process ID
            
        Returns:
            bool: True if service is still running, otherwise False
        """
        try:
            # Windows system
            if os.name == 'nt':
                # Use tasklist to check process
                result = os.system(f"tasklist /FI \"PID eq {pid}\" 2>NUL | find \"{pid}\" >NUL")
                return result == 0
            # Linux/Unix system
            else:
                # Use kill -0 to check process
                os.kill(pid, 0)
                return True
        except (OSError, ProcessLookupError):
            return False
    
    def stop_service(self, pid: int) -> bool:
        """
        Stop running service
        
        Args:
            pid: Process ID
            
        Returns:
            bool: True if service was successfully stopped, otherwise False
        """
        try:
            # Windows system
            if os.name == 'nt':
                os.system(f"taskkill /F /PID {pid}")
            # Linux/Unix system
            else:
                os.kill(pid, 15)  # SIGTERM
                
            logger.info(f"Termination signal sent to process {pid}")
            return True
        except (OSError, ProcessLookupError) as e:
            logger.error(f"Error stopping process {pid}: {e}")
            return False 
