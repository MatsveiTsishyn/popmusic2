
# Imports ----------------------------------------------------------------------
from contextlib import nullcontext
import subprocess
import time
import tempfile
from pathlib import Path
from popmusic2.utils import validate_pdb_path, validate_csv_path, validate_sep, validate_music_energy_dir, validate_chains
from popmusic2.utils import write_map_to_csv, parse_en, filter_pdb_chains
from popmusic2.config import CONFIG


# Main -------------------------------------------------------------------------
def music_eval(
        pdb_path: str | Path,
        chains: str | None = None,
        symmetric: bool = False,
        log_steps: bool = True,
        log_debug: bool = False,
        custom_potentials_dir: str | Path | None = None,
        save_path: str | Path | None = None,
        sep: str=",",
        music_output_dir: str | Path | None = None,
        custom_music_path: str | Path | None = None,
    ) -> dict[str, float]:
    """Compute MuSiC Potential Statistical Energy values ΔW and return them as a dict. 
    
    Args:
        pdb_path: Input PDB structure.
        chains: If set, first filter PDB on these chains before computing MuSiC -eval scores.
        symmetric: Set True to run MuSiC-symmetric potentials
        log_steps: Print progress messages.
        log_debug: Print MuSiC execution.
        custom_potentials_dir: path to a directory with custom potentials files (such as 'sd.enc')
        save_path: Optional path to a '.csv' file to save output values
        sep: Separator in the '.csv' file save_path
        music_output_dir: Optional path to directory for MuSiC outputs (otherwise side-effects outputs will be deleted)
        custom_music_path: Optional path to a MuSiC executable.

    Returns:
        A dictionary mapping each potential type to the corresponding ΔW value.
        {pot (str): ΔW (float)}
    """
    
    # Guardians
    T1 = time.time()
    validate_pdb_path(pdb_path)
    if save_path is not None:
        validate_sep(sep)
        validate_csv_path(save_path)
    validate_music_energy_dir(CONFIG.get_music_energy_dir(symmetric=symmetric, custom_potentials_dir=custom_potentials_dir))
    if chains is not None:
        validate_chains(chains)

    # Init
    music_path = CONFIG.get_music_executable_path(custom_music_path)  # algo will config it globally
    pdb_path = Path(pdb_path).absolute()
    pdb_name = pdb_path.name.removesuffix(".pdb")
    if chains is not None:
        pdb_name = f"{pdb_name}_{chains}"
    if log_steps:
        print(f"Run MuSiC -eval on '{pdb_name}' (symmetric={symmetric}): ")

    # Keep tmp directory alive until all stability calculations finish or use provided output directory
    if music_output_dir is None:
        tmp_dir = tempfile.TemporaryDirectory(prefix=f"popmusic2_{pdb_name}_")
    else:
        tmp_dir = nullcontext(Path(music_output_dir).absolute())

    with tmp_dir as tmp_dir_path:

        # Init file system
        io_dir = Path(tmp_dir_path)
        io_dir.mkdir(parents=True, exist_ok=True)
        dw_path = io_dir / f"{pdb_name}.en"
        path_in_path = io_dir / "path.in"
        log_path = io_dir / f"log_{pdb_name}.txt"
        if log_steps:
            print(f" - Create MuSiC input files in directory '{io_dir}' ...")

        # Generate path.in file
        path_in_str = CONFIG.get_path_in(io_dir, symmetric=symmetric, custom_potentials_dir=custom_potentials_dir)
        if log_debug:
            print(f"   - Generate path.in file to '{path_in_path}'")
        with open(path_in_path, "w") as fs:
            fs.write(path_in_str)

        # Copy original PDB into working dir
        tmp_pdb_path = io_dir / f"{pdb_name}.pdb"
        if log_debug:
            print(f"   - Copy PDB file to '{tmp_pdb_path}'")
        if chains is None:
            tmp_pdb_path.write_bytes(pdb_path.read_bytes())
        else:
            filter_pdb_chains(pdb_path, chains, tmp_pdb_path)

        # Run MuSiC
        if log_steps:
            print(f" - Run MuSiC -eval executable ...")
        cmd = [
            str(music_path),
            "-eval", pdb_name,
            "-log", pdb_name,
            "-init", str(path_in_path),
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

        # Parse MuSiC output file
        if log_steps:
            print(f" - Parse MuSiC output file '{dw_path}' ...")
        try:
            output = parse_en(dw_path)
        except Exception as err:
            raise ValueError(
                f"Failed to parse MuSiC output energy file '{dw_path}': "
                f" error: {err}"
            )

    # Save output to a .csv file
    if save_path is not None:
        try:  # do not kill execution if only IO failed
            write_map_to_csv(output, save_path, key_name="potential", value_name="energy", sep=sep)
            if log_steps:
                print(f" - Saved MuSiC -eval results to '{save_path}'")
        except Exception as err:
            if log_steps:
                print(
                    f"Failed to save output to CSV file '{save_path}': \n"
                    f" -> {err}"
                )


    # Log conclusion
    T2 = time.time()
    if log_steps:
        print(f"MuSiC -eval done in {T2-T1:.2f} sec.")

    return output
