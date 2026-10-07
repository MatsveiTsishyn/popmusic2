
# Imports ----------------------------------------------------------------------
from pathlib import Path


# Main -------------------------------------------------------------------------

# Constants
TREE_TO_ONE = {
    "ALA": "A","CYS": "C","ASP": "D","GLU": "E","PHE": "F",
    "GLY": "G","HIS": "H","ILE": "I","LYS": "K","LEU": "L",
    "MET": "M","ASN": "N","PRO": "P","GLN": "Q","ARG": "R",
    "SER": "S","THR": "T","VAL": "V","TRP": "W","TYR": "Y",
}

def parse_potentials_output(pot_path: Path | str) -> list[dict[str, float | str]]:
    """Parse PoPMuSiC output.
        -> return potentials values by mutations.
    """

    # Default output if no output file
    if not Path(pot_path).is_file():
        raise FileNotFoundError(f"No PoPMuSiC2 output file at '{pot_path}'.")

    # Read file
    with open(pot_path) as fs:
        lines = fs.readlines()
    lines = lines[6:] # remove comments lines (just pray that this number stays constant)
    lines = [line.removesuffix("\n") for line in lines] # remove end line break

    # Process lines
    header = lines[0]
    header = header.replace("( )", "").replace("(c)", "").replace("(t)", "").split()[2:] # because fuck it
    mut_lines = lines[1:]
    mut_lines = [line[:57] + line[57:62].replace(" ", "") + line[62:] for line in mut_lines] # because fuck it
    mut_lines = [line.split()[2:] for line in mut_lines]

    # Format output
    n_failed = 0
    out_list: list[dict[str, float | str]] = []
    for mut_line in mut_lines:
        try:
            out = parse_mut_line(header, mut_line)
            out_list.append(out)
        except Exception:
            n_failed += 1
    
    return out_list

def parse_mut_line(
        header: list[str],
        mut_line: list[str]
    ) -> dict[str, float | str]:
    """Parse a mutation line with its potentials and DDG values."""
    out_raw = {key: val for key, val in zip(header, mut_line)}
    mut = TREE_TO_ONE[out_raw["RES_nat"]] + out_raw["RES_id"] +  TREE_TO_ONE[out_raw["RES_mut"]]
    out = {
        "mutation": mut,
        "RSA": float(out_raw["accsol"]),
        "PoPMuSiC2": float(out_raw["ΔΔG"]),
        #"DV": float(out_raw["DV1"]),
        "n_muts": int(out_raw["mut_nbr"]),
    }
    for key, val in out_raw.items():
        if all([char in "stad" for char in key]): # if key is a potential
            out[key] = float(val)
        if key == "DV1":
            out["DV"] = float(val)
    return out
