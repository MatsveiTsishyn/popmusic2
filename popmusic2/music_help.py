
# Imports ----------------------------------------------------------------------
import subprocess
import tempfile
from pathlib import Path
from popmusic2.config import CONFIG


# Main -------------------------------------------------------------------------
def music_help(
        custom_music_path: str | Path | None = None,
    ) -> None:
    """Log MuSiC executable --help message."""

    # Init
    music_path = CONFIG.get_music_executable_path(custom_music_path)  # algo will config it globally

    # Run MuSiC --help
    with tempfile.TemporaryDirectory(prefix=f"popmusic2_help_") as tmp_dir:

        # Generate path.in file
        tmp_dir = Path(tmp_dir)
        path_in_path = tmp_dir / "path.in"
        path_in_str = CONFIG.get_path_in(tmp_dir)
        with open(path_in_path, "w") as fs:
            fs.write(path_in_str)

        # Run MuSiC
        cmd = [
            str(music_path),
            "-help",
            "-init",
            str(path_in_path),
        ]
        process = subprocess.run(
            cmd,
            cwd=str(tmp_dir),
            text=True,
            check=False,
        )
        if process.returncode != 0:
            raise RuntimeError(f"MuSiC failed with exit code {process.returncode}.")
