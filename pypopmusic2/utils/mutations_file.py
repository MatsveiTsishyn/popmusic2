
# Imports ------------------------------------------------------------
from pathlib import Path


# Functions ----------------------------------------------------------
def read_mutations_file(mutation_file_path: str | Path) -> list[str]:
    """Read mutation_file_path and return a list of mutations.
        - 1 single or multiple mutations by line
        - each line is like 'MA13H' or 'MA13H:LA15G'
        - line starting with "#" will be skipped
        - empty lines will be skipped
    """

    # Guardians
    if not Path(mutation_file_path).is_file():
        raise FileNotFoundError(f"Input mutation_file_path='{mutation_file_path}' file does not exist.")

    # Read input
    with open(mutation_file_path, "r") as fs:
        mutations = [line.strip() for line in fs.readlines()]

    # Clear (remove spaces, if mutations are separated by comma ',' so it will work too, and remove ';' in case lines are finishing by it)
    mutations = [m.replace(" ", "").replace(",", ":").replace(";", "") for m in mutations]

    # Filter
    mutations = [m for m in mutations if not m.startswith("#") and len(m) > 1]

    return mutations

def write_mutations_file(mutations_list: list[str], mutation_file_path: str | Path) -> None:
    """Save a list of mutations to a file."""

    # Init dir
    Path(mutation_file_path).parent.mkdir(parents=True, exist_ok=True)

    # Save
    with open(mutation_file_path, "w") as fs:
        fs.write("\n".join(mutations_list))

def write_music_mutations_file(mutations_list: list[str], mutation_file_path: str | Path) -> None:
    """Save a list of mutations to a file in MuSiC format."""

    # Init dir
    Path(mutation_file_path).parent.mkdir(parents=True, exist_ok=True)

    # Constants
    ONE_2_THREE = {
        "A": "ALA", "C": "CYS", "D": "ASP", "E": "GLU", "F": "PHE",
        "G": "GLY", "H": "HIS", "I": "ILE", "K": "LYS", "L": "LEU",
        "M": "MET", "N": "ASN", "P": "PRO", "Q": "GLN", "R": "ARG",
        "S": "SER", "T": "THR", "V": "VAL", "W": "TRP", "Y": "TYR",
    }

    # Format mutations
    mfile: list[str] = []
    for mutation in mutations_list:
        if ":" in mutation:
            raise ValueError(f"Impossible to save multiple mutation '{mutation}' to MuSiC mfile format.")
        wt = ONE_2_THREE[mutation[0]]
        mt = ONE_2_THREE[mutation[-1]]
        pos = mutation[1:-1]
        mut_str = f"{pos} {wt} {mt}"
        mfile.append(mut_str)

    # Save
    with open(mutation_file_path, "w") as fs:
        fs.write("\n".join(mfile))
