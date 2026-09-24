
# Imports ----------------------------------------------------------------------
from pathlib import Path


# Main -------------------------------------------------------------------------
def parse_cat(cat_path: str | Path) -> list[dict[str, str | float]]:
    """Parse MuSiC CAT output file.
    Return by-residue list like:
    
    {
        'resid': 'A1', 'aa_three': 'GLN', 'aa_one': 'Q',
        'secondary_structure': 'C', 'secondary_structure_grp': 'X', 'torsion': 'X',
        'ASA': 193.151359, 'RSA': 99.974824, 'pLDDT': 75.89,
    }
    """

    # Constants
    SEC_STR_GRP = {
        "H": "A",
        "G": "A",
        "E": "B",
        "B": "B",
        "T": "X",
        "S": "X",
        "C": "X",
    }
    SEC_STR_DEFAULT = "-"

    # Default output if no output file
    if not Path(cat_path).is_file():
        raise FileNotFoundError(f"No MuSiC '.cat' file at '{cat_path}'.")

    # Read residues lines
    residues_lines: list[str] = []
    with open(cat_path, "r") as fs:
        line = fs.readline()
        while line:
            if line.startswith("#RESIDUES"):
                break
            line = fs.readline()
        line = fs.readline()
        while line:
            if line.startswith("#"):
                break
            residues_lines.append(line.strip())
            line = fs.readline()

    # Parse residues lines
    cat: list[dict[str, str | float]] = []
    for line in residues_lines:
        entry = {
            "resid": line[0:6].replace(" ", ""),
            "aa_three": line[7:10],
            "aa_one": line[11],
            "secondary_structure": line[13],
            "secondary_structure_grp": SEC_STR_GRP.get(line[13], SEC_STR_DEFAULT),
            "torsion": line[15],
            "ASA": float(line[19:29]),
            "RSA": float(line[30:40]),
            "pLDDT": float(line[41:47]),
        }
        cat.append(entry)
    return cat
