
# Imports ----------------------------------------------------------------------
from popmusic2.utils import validate_pdb_path, validate_chains
from pathlib import Path


# Main -------------------------------------------------------------------------
def filter_pdb_chains(
        input_path: str | Path,
        chains: str,
        output_path: str | Path | None = None,
    ):
    """Filter ATOM and HETATOM lines by `chains` from PDB file `input_path` and save to `output_path`.
    - Returns path of the new generated PDB file.
    """

    # Guardians
    validate_pdb_path(input_path)
    validate_chains(chains)
    input_path = Path(input_path)
    if output_path is None:
        output_path = input_path.parent / (input_path.name.removesuffix(".pdb") + f"_{chains}.pdb")
    if not str(output_path).endswith(".pdb"):
        raise ValueError(f"Input output_path='{output_path}' should end with '.pdb'.")

    # Initialize filtered PDBs
    pdb_lines: list[str] = []

    # Parse .pdb and filter chains
    model_counter = 0
    cryst1_line_is_missing = True
    chains_in_pdb = set()
    with open(input_path, 'r') as fs:
        line = fs.readline()
        while line:
            prefix = line[0:6]

            # Add ATOM lines in correct interactant and in complex
            if prefix == "ATOM  " or prefix == "HETATM":
                chain = line[21]
                chains_in_pdb.add(chain)
                if chain in chains:
                    pdb_lines.append(line)

            # Detect presence of CRYST1 line
            elif prefix == "CRYST1":
                cryst1_line_is_missing = False
                pdb_lines.append(line)

            # Count model(s) in PDB and break parsing after the 1st one
            elif prefix == "MODEL ":
                model_counter += 1
                if model_counter > 1:
                    break
            line = fs.readline()

    # Create PDB strings
    pdb_str = "".join(pdb_lines)

    # Add default CRYST1 line if it is missing
    if cryst1_line_is_missing:
        default_cryst1_line = "CRYST1    1.000    1.000    1.000  90.00  90.00  90.00 P 1           1          \n"
        pdb_str = default_cryst1_line + pdb_str

    # Guardiant for coherence between chains and PDB
    for chain in chains:
        if chain not in chains_in_pdb:
            raise ValueError(
                f"Input chain '{chain}' is not in PDB file '{input_path}' (with chains '{''.join(chains_in_pdb)}')."
            )

    # Save
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as fs:
        fs.write(pdb_str)

    return output_path
