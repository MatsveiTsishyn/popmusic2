
# Imports ----------------------------------------------------------------------
from contextlib import nullcontext
import subprocess
import time
import tempfile
from pathlib import Path
from popmusic2.utils import validate_pdb_path, validate_mutations_list, validate_csv_path, validate_sep
from popmusic2.utils import list_mutations, write_map_to_csv, write_music_mutations_file, parse_pop
from popmusic2.config import CONFIG


# Main -------------------------------------------------------------------------
def popmusic2(
        pdb_path: str | Path,
        symmetric: bool = False,
        mutations_list: list[str] | None = None,
        log_steps: bool = True,
        log_debug: bool = False,
        save_path: str | Path | None = None,
        sep: str=",",
        music_output_dir: str | Path | None = None,
        custom_music_path: str | Path | None = None,
    ) -> dict[str, float]:
    """Compute PoPMuSiC2 ΔΔG values (thermodynamic stability) for a set of mutations and return them as a dict.

    Args:
        pdb_path: Input PDB structure.
        symmetric: Set True to run PoPMuSiC2-symmetric
        mutations_list: Optional mutation list. Entries use the format "A123V" for a
            single substitution or multiple ones as "A123V:K204L". If omitted, all
            possible single missense mutations in the structure are evaluated.
        log_steps: Print progress messages.
        log_debug: Print MuSiC execution.
        save_path: Optional path to a '.csv' file to save output values
        sep: Separator in the '.csv' file save_path
        music_output_dir: Optional path to directory for MuSiC outputs (otherwise side-effects outputs will be deleted)
        custom_music_path: Optional path to a MuSiC executable.

    Returns: {mut (str): ΔΔG (float)}
        A dictionary mapping each mutation to the corresponding ΔΔG value.
    """
    
    # Guardians
    T1 = time.time()
    validate_pdb_path(pdb_path)
    if mutations_list is None:
        mutations_list = list_mutations(pdb_path)
    validate_mutations_list(mutations_list, pdb_path)
    if save_path is not None:
        validate_sep(sep)
        validate_csv_path(save_path)

    # Init
    music_path = CONFIG.get_music_executable_path(custom_music_path)  # algo will config it globally
    pdb_path = Path(pdb_path).absolute()
    pdb_name = pdb_path.name.removesuffix(".pdb")
    if log_steps:
        print(f"Run PoPMuSiC2 on {len(mutations_list)} mutations on '{pdb_name}' (symmetric={symmetric}): ")

    # Keep tmp directory alive until all stability calculations finish or use provided output directory
    if music_output_dir is None:
        tmp_dir = tempfile.TemporaryDirectory(prefix=f"popmusic2_{pdb_name}_")
    else:
        tmp_dir = nullcontext(Path(music_output_dir).absolute())

    with tmp_dir as tmp_dir_path:

        # Init file system
        io_dir = Path(tmp_dir_path)
        io_dir.mkdir(parents=True, exist_ok=True)
        mfile_name = f"{pdb_name}.in"
        mfile_path = io_dir / mfile_name
        ddg_path = io_dir / f"{pdb_name}.pop"
        path_in_path = io_dir / "path.in"
        log_path = io_dir / f"log_{pdb_name}.txt"
        if log_steps:
            print(f" - Create MuSiC input files in directory '{io_dir}' ...")

        # Generate path.in file
        path_in_str = CONFIG.get_path_in(io_dir, symmetric=symmetric)
        if log_debug:
            print(f"   - Generate path.in file to '{path_in_path}'")
        with open(path_in_path, "w") as fs:
            fs.write(path_in_str)

        # Generate mutation file
        if log_debug:
            print(f"   - Generate mfile to '{mfile_path}'")
        write_music_mutations_file(mutations_list, mfile_path)

        # Copy original PDB into working dir
        tmp_pdb_path = io_dir / f"{pdb_name}.pdb"
        if log_debug:
            print(f"   - Copy PDB file to '{tmp_pdb_path}'")
        tmp_pdb_path.write_bytes(pdb_path.read_bytes())

        # Run MuSiC
        if log_steps:
            print(f" - Run MuSiC -pop executable ...")
        cmd = [
            str(music_path),
            "-pop",
            "mfile",
            pdb_name,
            mfile_name,
            "-log",
            pdb_name,
            "-init",
            str(path_in_path),
        ]
        if log_debug:
            print(f"   -> '{' '.join(cmd)}'")
        process = subprocess.run(
            cmd,
            cwd=str(io_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
        )
        if log_debug and process.stdout:
            print(process.stdout)
        if process.returncode != 0:
            error_msg = f"MuSiC failed with exit code {process.returncode}.\nLog file: '{log_path}'"
            if log_path.exists():
                error_msg += f"\n\n{log_path.read_text()}"
            raise RuntimeError(error_msg)

        # Parse PoPMuSiC2 output file
        if log_steps:
            print(f" - Parse MuSiC output file '{ddg_path}' ...")
        try:
            ddg_map = parse_pop(ddg_path)
        except Exception as err:
            raise ValueError(
                f"Failed to parse PoPMuSiC2 output file '{ddg_path}': "
                f" error: {err}"
            )

    # Save output to a .csv file
    if save_path is not None:
        try:  # do not kill execution if only IO failed
            write_map_to_csv(ddg_map, save_path, key_name="mutation", value_name="DDG", sep=sep)
            if log_steps:
                print(f" - Saved PoPMuSiC2 results to '{save_path}'")
        except Exception as err:
            if log_steps:
                print(
                    f"Failed to save output to CSV file '{save_path}': \n"
                    f" -> {err}"
                )

    # Log conclusion
    T2 = time.time()
    if log_steps:
        print(f"PoPMuSiC2 runs done in {T2-T1:.2f} sec.")

    return ddg_map
