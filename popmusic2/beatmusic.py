
# Imports ----------------------------------------------------------------------
import time
from pathlib import Path
from popmusic2.utils import validate_pdb_path, validate_mutations_list, validate_csv_path, validate_sep, validate_music_energy_dir, validate_interaction_chains
from popmusic2.utils import list_mutations, write_map_to_csv
from popmusic2.config import CONFIG
from popmusic2 import popmusic2


# Main -------------------------------------------------------------------------
def beatmusic(
        pdb_path: str | Path,
        chains: str,
        mutations_list: list[str] | None = None,
        log_steps: bool = True,
        log_debug: bool = False,
        save_path: str | Path | None = None,
        sep: str=",",
        music_output_dir: str | Path | None = None,
        custom_music_path: str | Path | None = None,
    ) -> dict[str, float]:
    """Compute BeAtMuSiC ΔΔGb values (thermodynamic binding affinity) for a set of mutations and return them as a dict.

    Args:
        pdb_path: Input PDB structure.
        chains: Interacting chains such as 'AB:C'
        mutations_list: Optional mutation list. Entries use the format "A123V" for a
            single substitution or multiple ones as "A123V:K204L". If omitted, all
            possible single missense mutations in the structure are evaluated.
        log_steps: Print progress messages.
        log_debug: Print MuSiC execution.
        save_path: Optional path to a '.csv' file to save output values
        sep: Separator in the '.csv' file save_path
        music_output_dir: Optional path to directory for MuSiC outputs (otherwise side-effects outputs will be deleted)
        custom_music_path: Optional path to a MuSiC executable.

    Returns:
        A dictionary mapping each mutation to the corresponding ΔΔGb value.
        {mut (str): ΔΔGb (float)}
    """

    # Define constants
    V  = 1.25
    W1, W2 = (1.0, -0.7)
    
    # Guardians
    T1 = time.time()
    validate_pdb_path(pdb_path)
    left_chains, right_chains = validate_interaction_chains(chains)
    all_chains = left_chains + right_chains
    if mutations_list is None:
        mutations_list = list_mutations(pdb_path, all_chains)
    validate_mutations_list(mutations_list, pdb_path, all_chains)
    if save_path is not None:
        validate_sep(sep)
        validate_csv_path(save_path)
    validate_music_energy_dir(CONFIG.get_music_energy_dir())

    # List single mutations
    single_mutations_list: list[str] = []
    for mutation in mutations_list:
        for single_mutation in mutation.split(":"):
            single_mutations_list.append(single_mutation)
    single_mutations_list = list(dict.fromkeys(single_mutations_list))

    # Init
    pdb_path = Path(pdb_path).absolute()
    pdb_name = pdb_path.name.removesuffix(".pdb")
    if log_steps:
        print(f"Run BeAtMuSiC on {len(mutations_list)} mutations on '{pdb_name}' (chains={chains}): ")

    # Split mutations
    mutations_left: list[str] = []
    mutations_right: list[str] = []
    for single_mutation in single_mutations_list:
        chain = single_mutation[1]
        if chain in left_chains:
            mutations_left.append(single_mutation)
        elif chain in right_chains:
            mutations_right.append(single_mutation)

    # Run both PoPMuSiC interactors
    out_left: dict[str, float] = {}
    out_right: dict[str, float] = {}
    if len(mutations_left):
        out_left = popmusic2(
            pdb_path, chains=left_chains, mutations_list=mutations_left,
            log_steps=log_steps, log_debug=log_debug,
            music_output_dir=music_output_dir,
            custom_music_path=custom_music_path,
        )
    if len(mutations_right):
        out_right = popmusic2(
            pdb_path, chains=right_chains, mutations_list=mutations_right,
            log_steps=log_steps, log_debug=log_debug,
            music_output_dir=music_output_dir,
            custom_music_path=custom_music_path,
        )
    out_interactors = out_left | out_right
    out_complex = popmusic2(
        pdb_path, chains=None, mutations_list=single_mutations_list,
        log_steps=log_steps, log_debug=log_debug,
        music_output_dir=music_output_dir,
        custom_music_path=custom_music_path,
    )

    # Aggregate values
    ddgb_map_single: dict[str, float] = {
        mut: V*(W1*DDG_complex + W2*out_interactors[mut])
        for mut, DDG_complex in out_complex.items()
    }

    # Collects mutations values
    ddgb_map: dict[str, float] = {}
    for mutation in mutations_list:
        single_mutations = mutation.split(":")
        ddgb_map[mutation] = sum([ddgb_map_single[m] for m in single_mutations])

    # Save output to a .csv file
    if save_path is not None:
        try:  # do not kill execution if only IO failed
            beatmusic_property = "BeAtMuSiC"
            write_map_to_csv(ddgb_map, save_path, key_name="mutation", value_name=beatmusic_property, sep=sep)
            if log_steps:
                print(f" - Saved BeAtMuSiC results to '{save_path}'")
        except Exception as err:
            if log_steps:
                print(
                    f"Failed to save output to CSV file '{save_path}': \n"
                    f" -> {err}"
                )

    # Log conclusion
    T2 = time.time()
    if log_steps:
        print(f"BeAtMuSiC runs done in {T2-T1:.2f} sec.")

    return ddgb_map
