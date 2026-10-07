
# Imports ----------------------------------------------------------------------
from pathlib import Path


# Functions --------------------------------------------------------------------
def validate_sep(sep: str) -> None:
    """Validate separator for a .csv file."""
    if not isinstance(sep, str):
        raise TypeError(f"Input set='{sep}' should be a string.")
    if len(sep) != 1:
        raise ValueError(f"Input sep='{sep}' should be of length 1.")
    if sep == ":":
        raise ValueError(f"Input sep='{sep}' can not be ':'.")

def validate_csv_path(csv_path: str | Path) -> None:
    """Validate input 'csv_path' and raise Error if validation failed."""
    if not Path(csv_path).suffix.lower() == ".csv":
        raise ValueError(f"Input csv_path='{csv_path}' should end with '.csv'.")

def validate_pdb_path(pdb_path: str | Path) -> None:
    """Validate input 'pdb_path' and raise Error if validation failed or file is missing."""
    if not Path(pdb_path).is_file():
        raise FileNotFoundError(f"Input pdb_path '{pdb_path}' file does not exist.")
    if not str(pdb_path).endswith(".pdb"):
        raise ValueError(f"Input pdb_path '{pdb_path}' should end with extention '.pdb'.")

def validate_interaction_chains(interaction_chains: str) -> tuple[str, str]:
    """Return left- and right- interactors chains. Raise Error input is inconsistent."""
    interactors = interaction_chains.split(":")
    if len(interactors) != 2:
        raise ValueError(f"Input interaction_chains='{interaction_chains}' should contains two chain interactors separated by ':'.")
    chains_left, chains_rights = interactors
    all_chains = chains_left + chains_rights
    if len(all_chains) != len(set(all_chains)):
        raise ValueError(f"Input interaction_chains='{interaction_chains}' can not contain any redundent chains.")
    if len(chains_left) == 0 or len(chains_rights) == 0:
        raise ValueError(f"Input interaction_chains='{interaction_chains}' should contain at least a single left- and right- interactor chain.")
    if chains_left == chains_rights:
        raise ValueError(f"Input interaction_chains='{interaction_chains}' should contain a different right- and left- interactor.")
    return chains_left, chains_rights

def validate_chains(chains: str) -> None:
    """Validate a set of PDB chains."""
    if len(chains) != len(set(chains)):
        raise ValueError(f"Input chains='{chains}' can not contain any redundent chains.")
    if len(chains) == 0:
        raise ValueError(f"Input chains='{chains}' should contain at least 1 chain.")

def validate_mutations_list(mutaions_list: list[str], pdb_path: str, chains: str | None = None) -> None:
    """Validate consistency between mutaions_list and 3D structure file pdb_path.
        -> Also verify consistency with chains if they are given
    """

    # Case : list is empty
    if len(mutaions_list) == 0:
        raise ValueError(f"Input mutaions_list is empty.")

    # List all existing mutations
    all_mutations = set(list_mutations(pdb_path))

    # Verify all mutations
    for i, mutation in enumerate(mutaions_list, start=1):
        if not isinstance(mutation, str):
            raise ValueError(f"Input mutation={mutation} should be a string.")
        single_mutations = mutation.split(":")
        for single_mutation in single_mutations:
            if single_mutation not in all_mutations:
                problem = explain_single_mutation_error(single_mutation, all_mutations)
                raise ValueError(
                    f"Input mutation '{mutation}' ({i}/{len(mutaions_list)}) contains single-mutation '{single_mutation}' "
                    f"that is not in the 3D structure '{Path(pdb_path).name}'"
                    f"\n -> {problem}"
                )
        positions = [m[1:-1] for m in single_mutations]
        if len(positions) != len(set(positions)):
            raise ValueError(
                f"Input mutation '{mutation}' contain redundencies in its positions."
            )

    # Validate mutations are in chains
    if chains is not None:
        all_chains_in_structure = set(m[1] for m in all_mutations)
        all_chains = chains.replace(":", "")
        for chain in all_chains:
            if chain not in all_chains_in_structure:
                raise ValueError(
                    f"Input chains='{chains}' contain chain '{chain}' that "
                    f"is not is 3D structure '{Path(pdb_path).name}' (with chains '{''.join(all_chains_in_structure)}')"
                )
        for mutation in mutaions_list:
            single_mutations = mutation.split(":")
            for single_mutation in single_mutations:
                mut_chain = single_mutation[1]
                if mut_chain not in all_chains:
                    raise ValueError(
                        f"Input mutation '{mutation}' contain single-mutation '{single_mutation}' "
                        f"that is not contained in target chains '{all_chains}'."
                    )

def list_mutations(pdb_path: str | Path, chains: str | None = None) -> list[str]:
    """List all possible missense mutations of a PDB.
        -> filter by chains if chains is given
    """

    # Constants
    TREE_TO_ONE = {
        "ALA": "A","CYS": "C","ASP": "D","GLU": "E","PHE": "F",
        "GLY": "G","HIS": "H","ILE": "I","LYS": "K","LEU": "L",
        "MET": "M","ASN": "N","PRO": "P","GLN": "Q","ARG": "R",
        "SER": "S","THR": "T","VAL": "V","TRP": "W","TYR": "Y",
    }
    AMINO_ACIDS = list(TREE_TO_ONE.values())

    # Guardians
    validate_pdb_path(pdb_path)

    # Read ATOM lines
    with open(pdb_path, "r") as fs:
        atom_lines = [line for line in fs.readlines() if line.startswith("ATOM")]

    # List all residues
    residues = [] # pairs of (aa, resid)
    resid_set = set()
    for atom_line in atom_lines:
        aa3 = atom_line[17:20]
        if aa3 not in TREE_TO_ONE: continue
        aa = TREE_TO_ONE[aa3]
        resid = atom_line[21:26].replace(" ", "")
        if resid in resid_set: continue
        resid_set.add(resid)
        residues.append((aa, resid))

    # List mutations
    mutations = []
    for aa_wt, resid in residues:
        for aa_mt in AMINO_ACIDS:
            if aa_wt == aa_mt: continue
            mutations.append(aa_wt + resid + aa_mt)

    # Filter by chains
    if chains is not None:
        all_chains = chains.replace(":", "")
        mutations = [m for m in mutations if m[1] in all_chains]

    return mutations

def explain_single_mutation_error(single_mutation: str, mutations_set: set[str]) -> str:
    """Return a string that explains why single_mutation is inconsistent."""
    if not isinstance(single_mutation, str):
        return "mutation is not a string object"
    if len(single_mutation) < 4:
        return "mutation is of insufficient length to be a valid mutation (such as 'MA7K')"
    AAS = "ACDEFGHIKLMNPQRSTVWY"
    wt, mt = single_mutation[0], single_mutation[-1]
    if wt not in AAS:
        return f"wild-type amino acid '{wt}' should be among '{AAS}'"
    if mt not in AAS:
        return f"mutant amino acid '{mt}' should be among '{AAS}'"
    if wt == mt:
        return f"mutation wild-type and mutant amino acid are the same ='{wt}'"
    wt_aa_map = {m[1:-1]: m[0] for m in mutations_set}
    resid = single_mutation[1:-1]
    if resid not in wt_aa_map:
        return f"mutation position '{resid}' is not in 3D structure"
    else:
        wt_real = wt_aa_map[resid]
        return f"mutation wild-type amino acid '{wt}' does not match amino acid in 3D structure '{wt_real}' at position '{resid}'"
    
def validate_music_energy_dir(music_energy_dir: str | Path) -> None:
    """Verify is `music_energy_dir` is valid potentials directory."""

    # Search PM_coeff.in
    coeff_path = Path(music_energy_dir) / "PM_coeff.in"
    if not coeff_path.is_file():
        raise FileNotFoundError(f"No MuSiC-energy coefficients ('PM_coeff.in') file found in '{music_energy_dir}'.")
    sd_path = Path(music_energy_dir) / "sd.enc"
    if not sd_path.is_file():
        raise FileNotFoundError(f"No MuSiC-energy sd-potential ('sd.enc') file found in '{music_energy_dir}'.")
    if not has_at_least_n_lines(sd_path, 200):
        raise ValueError(
            f"Invalid MuSiC 'sd.enc' potential energy file '{sd_path}': \n"
            f"file contains less than 200 lines, which indicates that potentials energies files are probably empty."
        )

def has_at_least_n_lines(filepath: str | Path, n: int) -> bool:
    with open(filepath, "r") as fs:
        for i, line in enumerate(fs, start=1):
            if i >= n:
                return True
    return False
