
# Imports ------------------------------------------------------------
from pathlib import Path


# Functions ----------------------------------------------------------
def read_mutations_file(mutation_file_path: str | Path) -> list[str]:
    """Read `mutation_file_path` and return a list of mutations.
        - 1 single or multiple (separated by ':') mutations by line
        - each line is like 'MA13H' or 'MA13H:LA15G'
        - line starting with '#' will be skipped
        - empty lines will be skipped
        - lines can end with ';'
        - alternatively reads MuSiC-format mutations files like 'A13 MET LYS'
    """

    # Guardians
    if not Path(mutation_file_path).is_file():
        raise FileNotFoundError(f"Input mutation_file_path='{mutation_file_path}' file does not exist.")

    # Read input
    with open(mutation_file_path, "r") as fs:
        mutations = [
            line.strip().replace(";", "").replace(",", ":")
            for line in fs.readlines()
            if not line.startswith("#") and len(line) >= 4
        ]

    # Not valid mutations error
    if len(mutations) == 0:
        raise ValueError(f"No valid mutations lines in mutations file '{mutation_file_path}'.")

    # If needed, translate mutations from MuSiC format
    if len(mutations[0].split()) == 3:
        THREE_2_ONE = {
            "ALA": "A", "CYS": "C", "ASP": "D", "GLU": "E", "PHE": "F",
            "GLY": "G", "HIS": "H", "ILE": "I", "LYS": "K", "LEU": "L",
            "MET": "M", "ASN": "N", "PRO": "P", "GLN": "Q", "ARG": "R",
            "SER": "S", "THR": "T", "VAL": "V", "TRP": "W", "TYR": "Y",
        }
        for i, mut in enumerate(mutations):
            mut_components = mut.split()
            if len(mut_components) != 3:
                mut_str = mut if len(mut) < 20 else f"{mut[0:20]}..."
                raise ValueError(
                    f"Mutation [{i+1}/{len(mutations)}] '{mut_str}' is invalid: "
                    f"should have 3 components (not {len(mut_components)})."
                )
            resid, wt, mt = mut_components
            if wt not in THREE_2_ONE or mt not in THREE_2_ONE:
                mut_str = mut if len(mut) < 20 else f"{mut[0:20]}..."
                raise ValueError(
                    f"Mutation [{i+1}/{len(mutations)}] '{mut_str}' is invalid: "
                    f"wild-type or mutants amino acid is not a valid 3-letters-code amino acid.\n"
                    f" -> among {list(THREE_2_ONE.keys())}."
                )
            mut = THREE_2_ONE[wt] + resid + THREE_2_ONE[mt]
            mutations[i] = mut

    return mutations

def write_mutations_file(mutations_list: list[str], mutation_file_path: str | Path, music_format: bool=False) -> None:
    """Save a list of mutations to a file at `mutation_file_path`.
        - if `music_format` is True, save it in MuSiC-format (like 'A13 MET LYS')
    """

    # Init dir
    Path(mutation_file_path).parent.mkdir(parents=True, exist_ok=True)

    # Stringify mutations list
    if not music_format:
        mfile = "\n".join(mutations_list) + "\n"

    # Translate to MuSiC format    
    else:
        ONE_2_THREE = {
            "A": "ALA", "C": "CYS", "D": "ASP", "E": "GLU", "F": "PHE",
            "G": "GLY", "H": "HIS", "I": "ILE", "K": "LYS", "L": "LEU",
            "M": "MET", "N": "ASN", "P": "PRO", "Q": "GLN", "R": "ARG",
            "S": "SER", "T": "THR", "V": "VAL", "W": "TRP", "Y": "TYR",
        }
        mfile_list: list[str] = []
        for i, mutation in enumerate(mutations_list):
            if ":" in mutation:
                raise ValueError(f"Impossible to save multiple mutation '{mutation}' to MuSiC mfile format.")
            if len(mutation) < 4:
                raise ValueError(f"Invalid mutation '{mutation}': should be of length 4 of more.")
            wt, pos, mt = mutation[0], mutation[1:-1], mutation[-1]
            if wt not in ONE_2_THREE or mt not in ONE_2_THREE:
                raise ValueError(
                    f"Mutation [{i+1}/{len(mutations_list)}] '{mutation}' is invalid: "
                    f"wild-type or mutants amino acid is not a valid 1-letters-code amino acid.\n"
                    f" -> among {list(ONE_2_THREE.keys())}."
                )
            wt = ONE_2_THREE[wt]
            mt = ONE_2_THREE[mt]
            pos = mutation[1:-1]
            mut_str = f"{pos} {wt} {mt}"
            mfile_list.append(mut_str)
        mfile = "\n".join(mfile_list) + "\n"

    # Save
    with open(mutation_file_path, "w") as fs:
        fs.write(mfile)
