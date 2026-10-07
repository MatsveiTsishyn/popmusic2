
# Imports ----------------------------------------------------------------------
from contextlib import nullcontext
import subprocess
import time
import tempfile
from pathlib import Path
from popmusic2.utils import validate_pdb_path, validate_mutations_list, validate_csv_path, validate_sep, validate_music_energy_dir, validate_chains
from popmusic2.utils import list_mutations, write_map_to_csv, parse_pop, write_mutations_file, filter_pdb_chains, parse_potentials_output, write_table_to_csv
from popmusic2.config import CONFIG


# Main -------------------------------------------------------------------------
def popmusic2(
        pdb_path: str | Path,
        chains: str | None = None,
        symmetric: bool = False,
        mutations_list: list[str] | None = None,
        log_steps: bool = True,
        log_debug: bool = False,
        all_potentials: bool = False,
        custom_potentials_dir: str | Path | None = None,
        save_path: str | Path | None = None,
        sep: str=",",
        music_output_dir: str | Path | None = None,
        custom_music_path: str | Path | None = None,
    ) -> dict[str, float] | list[dict[str, float | str]]:
    """Compute PoPMuSiC2 ΔΔG values (thermodynamic stability) for a set of mutations and return them as a dict.

    Args:
        pdb_path: Input PDB structure.
        chains: If set, first filter PDB on these chains before computing PoPMuSiC2 mutational scores.
        symmetric: Set True to run PoPMuSiC2-symmetric
        mutations_list: Optional mutation list. Entries use the format "A123V" for a
            single substitution or multiple ones as "A123V:K204L". If omitted, all
            possible single missense mutations in the structure are evaluated.
        log_steps: Print progress messages.
        log_debug: Print MuSiC execution.
        all_potentials: Output all potentials ΔΔW values.
        custom_potentials_dir: path to a directory with custom potentials files (such as 'sd.enc')
        save_path: Optional path to a '.csv' file to save output values
        sep: Separator in the '.csv' file save_path
        music_output_dir: Optional path to directory for MuSiC outputs (otherwise side-effects outputs will be deleted)
        custom_music_path: Optional path to a MuSiC executable.

    Returns:
        A dictionary mapping each mutation to the corresponding ΔΔG value.
        {mut (str): ΔΔG (float)}
        If `all_potentials`, then returns the list of all potentials values by mutations
        [{"mutation": "MA13K", "PoPMuSiC2": 1.52, "RSA": 85.01, "sd": 0.54, ...}, ...]
    """
    
    # Guardians
    T1 = time.time()
    validate_pdb_path(pdb_path)
    if mutations_list is None:
        mutations_list = list_mutations(pdb_path, chains)
    validate_mutations_list(mutations_list, pdb_path, chains)
    if save_path is not None:
        validate_sep(sep)
        validate_csv_path(save_path)
    validate_music_energy_dir(CONFIG.get_music_energy_dir(symmetric=symmetric, custom_potentials_dir=custom_potentials_dir))
    if chains is not None:
        validate_chains(chains)

    # List single mutations
    single_mutations_list: list[str] = []
    for mutation in mutations_list:
        for single_mutation in mutation.split(":"):
            single_mutations_list.append(single_mutation)
    single_mutations_list = list(dict.fromkeys(single_mutations_list))

    # Init
    music_path = CONFIG.get_music_executable_path(custom_music_path)  # algo will config it globally
    pdb_path = Path(pdb_path).absolute()
    pdb_name = pdb_path.name.removesuffix(".pdb")
    if chains is not None:
        pdb_name = f"{pdb_name}_{chains}"
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
        ddw_path = io_dir / f"{pdb_name}.popddg"
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

        # Generate mutation file
        if log_debug:
            print(f"   - Generate mfile to '{mfile_path}'")
        write_mutations_file(single_mutations_list, mfile_path, music_format=True)

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
            print(f" - Run MuSiC -pop executable ...")
        cmd = [
            str(music_path),
            "-pop", "mfile", pdb_name, mfile_name,
            "-log", pdb_name,
            "-init", str(path_in_path),
        ]
        if all_potentials:
            cmd = cmd + ["-export", "ddg"]
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
        if not all_potentials:
            if log_steps:
                print(f" - Parse MuSiC output file '{ddg_path}' ...")
            try:
                ddg_map_single = parse_pop(ddg_path)
            except Exception as err:
                raise ValueError(
                    f"Failed to parse PoPMuSiC2 output file '{ddg_path}': "
                    f" error: {err}"
                )
        else:
            if log_steps:
                print(f" - Parse MuSiC output file '{ddw_path}' ...")
            try:
                mutations_single = parse_potentials_output(ddw_path)
            except Exception as err:
                raise ValueError(
                    f"Failed to parse PoPMuSiC2 output file '{ddw_path}': "
                    f" error: {err}"
                )

    # Collects mutations values
    if not all_potentials:
        output: dict[str, float] = {}
        for mutation in mutations_list:
            single_mutations = mutation.split(":")
            output[mutation] = sum([ddg_map_single[m] for m in single_mutations])
    else:
        output: list[dict[str, float | str]] = []
        mutations_single_map = {m["mutation"]: m for m in mutations_single}
        for mutation in mutations_list:
            single_mutations = mutation.split(":")
            single_mutations_data = [mutations_single_map[m] for m in single_mutations]
            mutation_entry: dict[str, float | str] = {}
            for key, val in single_mutations_data[0].items():
                if key in ["mutation", "RSA"]:
                    mutation_entry[key] = ":".join(str(m[key]) for m in single_mutations_data)
                else:
                    mutation_entry[key] = sum(m[key] for m in single_mutations_data)
            output.append(mutation_entry)

    # Save output to a .csv file
    if save_path is not None:
        if not all_potentials:
            try:  # do not kill execution if only IO failed
                popmusic2_property = "PoPMuSiC2-sym" if symmetric else "PoPMuSiC2"
                write_map_to_csv(output, save_path, key_name="mutation", value_name=popmusic2_property, sep=sep)
                if log_steps:
                    print(f" - Saved PoPMuSiC2 results to '{save_path}'")
            except Exception as err:
                if log_steps:
                    print(
                        f"Failed to save output to CSV file '{save_path}': \n"
                        f" -> {err}"
                    )
        else:
            try:  # do not kill execution if only IO failed
                write_table_to_csv(output, save_path, sep=sep)
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

    return output
