
# Imports ----------------------------------------------------------------------
from pathlib import Path
import csv
from .validation import validate_csv_path, validate_sep


# Functions --------------------------------------------------------------------
def write_map_to_csv(
        data_map: dict,
        csv_path: str | Path,
        key_name: str,
        value_name: str,
        sep: str=",",
    ) -> None:
    """Write a dictionary to a '.csv' file."""

    # Guardians
    validate_csv_path(csv_path)
    validate_sep(sep)
    if sep in key_name:
        raise ValueError(f"Input sep='{sep}' can not be in key_name='{key_name}'.")
    if sep in value_name:
        raise ValueError(f"Input sep='{sep}' can not be in value_name='{value_name}'.")
    if key_name == value_name:
        raise ValueError(f"Input key_name can not be same as value_name (='{value_name}').")

    # Save
    csv_path = Path(csv_path)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="") as csv_file:
        writer = csv.writer(csv_file, delimiter=sep)
        writer.writerow([key_name, value_name])
        for key, value in data_map.items():
            writer.writerow([key, value])
