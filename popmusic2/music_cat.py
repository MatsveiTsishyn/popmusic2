
# Imports ----------------------------------------------------------------------
import subprocess
import tempfile
from pathlib import Path
import shutil
from popmusic2.utils import validate_pdb_path
from popmusic2.utils import parse_cat, write_table_to_csv
from popmusic2.config import CONFIG


# Main -------------------------------------------------------------------------
def music_cat(
        pdb_path: str | Path,
        save_path: str | Path | None = None,
        cat_path: str | Path | None = None,
        sep: str = ",",
        custom_music_path: str | Path | None = None,
    ) -> list[dict[str, str | float]]:
    """Run MuSiC CAT analysis (for RSA and secondary structure).

    Args:
        pdb_path: Input PDB structure.
        save_path: Optional '.csv' path to save CAT info
        cat_path: Opional path to initial MuSiC CAT file
        sep: Separator in the '.csv' file save_path
        custom_music_path: Optional path to a MuSiC executable.

    Returns:
        A list of by-residues CAT informations (like 'resid', 'aa_three', 'aa_one', 'secondary_structure' and 'RSA')
    """
    
    # Guardians
    validate_pdb_path(pdb_path)

    # Init
    music_path = CONFIG.get_music_executable_path(custom_music_path)  # algo will config it globally
    pdb_path = Path(pdb_path).absolute()
    pdb_name = pdb_path.name.removesuffix(".pdb")

    # Run
    with tempfile.TemporaryDirectory(prefix=f"popmusic2cat_{pdb_name}_") as tmp_dir:

        # Generate path.in file
        tmp_dir = Path(tmp_dir)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        tmp_cat_path = tmp_dir / f"{pdb_name}.cat"
        path_in_path = tmp_dir / "path.in"
        path_in_str = CONFIG.get_path_in(tmp_dir)
        with open(path_in_path, "w") as fs:
            fs.write(path_in_str)

        # Copy original PDB into working dir
        tmp_pdb_path = tmp_dir / f"{pdb_name}.pdb"
        tmp_pdb_path.write_bytes(pdb_path.read_bytes())

        # Run MuSiC
        cmd = [
            str(music_path),
            "-cat", pdb_name, "FULLATOM",
            "-init", str(path_in_path),
        ]
        process = subprocess.run(
            cmd,
            cwd=str(tmp_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if process.returncode != 0:
            raise RuntimeError(f"MuSiC failed with exit code {process.returncode}.")

        # Parse CAT
        cat = parse_cat(tmp_cat_path)

        # Save initial MuSiC CAT file
        if cat_path:
            Path(cat_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(tmp_cat_path, cat_path)

    # Save cat to .csv
    if save_path is not None:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        write_table_to_csv(cat, save_path, sep=sep)

    # Return
    return cat
