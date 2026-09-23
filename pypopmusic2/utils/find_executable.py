
# Imports ----------------------------------------------------------------------
import subprocess
import tempfile
from pathlib import Path


# Functions --------------------------------------------------------------------
def find_executable(
        path_list: list[str],
        output_required_str: str | None="# Welcome to MuSiC v",
    ) -> str:
    """Find a valid executable path or raise ERROR.
        -> If output_required_str is given, verify that it is contained in executable --help output
        -> If no valid executable if found, raises an Error
    """

    # Empty list error
    if len(path_list) == 0:
        raise ValueError(f"Input path_list is empty.")

    # Find valud executable
    errors = []
    for candidate_path in path_list:
        candidate_path = Path(candidate_path).absolute()
        try:
            verify_executable(candidate_path, output_required_str=output_required_str)
            return str(candidate_path)
        except Exception as err:
            errors.append(err)

    # Log all errors
    print("ERROR: No valid executable found among: ")
    for candidate_path, err in zip(path_list, errors):
        print(f"\n * '{candidate_path}': \n {err}")
    raise ValueError("No correct executable found.")
         
def verify_executable(
        executable: str | Path,
        output_required_str: str | None="# Welcome to MuSiC v",
    ) -> None:
    """Verify if MuSiC executable file is ok.
        -> If output_required_str is given, verify that it is contained in executable --help output
        -> If no, raises an Error
    """

    # Verify if file is present
    executable = Path(executable)
    executable_name = executable.name
    if not executable.is_file():
        raise FileNotFoundError(
            f"{executable_name} executable not found at '{executable}'.\n"
            f"-> Please ensure that {executable} is correctly compiled and "
            f"that its path is well set in './config.py'."
        )
    
    # Verify execution
    try:
        with tempfile.TemporaryDirectory() as tmp_dir:
            result = subprocess.run(
                [f"{executable}", "-h"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5,
                cwd=tmp_dir,
            )
    except Exception as err:
        raise RuntimeError(
            f"{executable_name} executable failed to run:\n"
            f"{err}\n"
            f"-> Check if '{executable}' is compatible with your system."
        ) from err

    if output_required_str is not None and output_required_str not in result.stdout:
        raise RuntimeError(
            f"{executable_name} executable did not produce expected output '{output_required_str}'.\n"
            f"-> Check if '{executable}' is a valid executable, "
            f"is compatible with your system."
        )
