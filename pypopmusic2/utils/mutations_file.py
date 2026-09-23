
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

