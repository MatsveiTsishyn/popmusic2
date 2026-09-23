
# Imports ----------------------------------------------------------------------
from pathlib import Path


# Main -------------------------------------------------------------------------
def parse_pop(output_path: str | Path) -> dict[str, float]:
    """Parse PoPMuSiC '.pop' output file.
        Returns: {mut (str): ΔΔG (float)}
    """

    # Default output if no output file
    if not Path(output_path).is_file():
        raise FileNotFoundError(f"No PoPMuSiC2 output file at '{output_path}'.")

    # Constants
    THREE_2_ONE = {
        "ALA": "A","CYS": "C","ASP": "D","GLU": "E","PHE": "F",
        "GLY": "G","HIS": "H","ILE": "I","LYS": "K","LEU": "L",
        "MET": "M","ASN": "N","PRO": "P","GLN": "Q","ARG": "R",
        "SER": "S","THR": "T","VAL": "V","TRP": "W","TYR": "Y",
    }

    # Read MuSiC output
    with open(output_path, "r") as fs:
        lines = [line for line in list(fs.readlines()) if line[0] != "#" and len(line) > 1]

    # Parse mutations
    output: dict[str, float] = {}
    for line in lines:
        pos = line[0:6].replace(" ", "")
        wt = THREE_2_ONE[line[7:10]]
        mt = THREE_2_ONE[line[11:14]]
        ddg = float(line.split()[-1])
        mut = wt + pos + mt
        output[mut] = ddg

    return output
