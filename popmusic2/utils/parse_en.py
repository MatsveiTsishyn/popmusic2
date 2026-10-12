
# Imports ----------------------------------------------------------------------
from pathlib import Path


# Main -------------------------------------------------------------------------
def parse_en(output_path: str | Path) -> dict[str, float]:
    """Parse (PoP)MuSiC '.en' output file (for absolute Potentials Energy of a 3D structure).
        Returns: {pot (str): ΔW (float)}
    """

    # Default output if no output file
    if not Path(output_path).is_file():
        raise FileNotFoundError(f"No MuSiC2 output file at '{output_path}'.")

    # Read MuSiC output
    with open(output_path, "r") as fs:
        lines = [line.split() for line in list(fs.readlines()) if line[0] != "#" and len(line) > 5]

    # Parse mutations
    output: dict[str, float] = {}
    for line in lines:
        pot = line[1]
        val = float(line[2])
        output[pot] = val

    return output
