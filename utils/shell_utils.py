import subprocess
import logging
import shlex
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

def run_shell_command(command_args: List[str], check_error: bool = True, timeout: Optional[int] = 120) -> Tuple[str, str, int]:
    """
    Executes a shell command and returns its stdout, stderr, and return code.

    Args:
        command_args (List[str]): A list of strings representing the command and its arguments.
                                   Example: ['ffmpeg', '-i', 'input.mp4', 'output.mp4']
        check_error (bool): If True, raises a RuntimeError if the command returns a non-zero exit code.
        timeout (Optional[int]): Maximum time in seconds to wait for the command to complete.

    Returns:
        Tuple[str, str, int]: A tuple containing (stdout, stderr, returncode).

    Raises:
        RuntimeError: If check_error is True and the command fails, or if the command is not found.
        subprocess.TimeoutExpired: If the command times out.
    """
    command_for_log = shlex.join(command_args)
    logger.info(f"Executing command: {command_for_log}")

    try:
        result = subprocess.run(
            command_args,
            capture_output=True,
            text=True,
            check=False, # We handle check_error manually
            timeout=timeout
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        returncode = result.returncode

        if returncode != 0:
            logger.error(f"Command failed with exit code {returncode}: {command_for_log}\nSTDOUT: {stdout}\nSTDERR: {stderr}")
            if check_error:
                raise RuntimeError(f"Command failed with exit code {returncode}: {command_for_log}\nSTDOUT: {stdout}\nSTDERR: {stderr}")
        else:
            logger.info(f"Command executed successfully (exit code {returncode}): {command_for_log}")
            if stdout:
                logger.info(f"STDOUT: {stdout}")
            if stderr:
                logger.warning(f"STDERR: {stderr}")

        return stdout, stderr, returncode

    except FileNotFoundError:
        logger.critical(f"Command not found. Make sure the executable is in your PATH: {command_args[0]}")
        raise RuntimeError(f"Command not found: {command_args[0]}")
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out after {timeout} seconds: {command_for_log}")
        result.kill() # Terminate the process
        result.wait() # Wait for it to terminate
        raise
    except Exception as e:
        logger.critical(f"An unexpected error occurred while running command {command_for_log}: {e}", exc_info=True)
        raise
