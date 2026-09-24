
# Imports ----------------------------------------------------------------------
import argparse
from pathlib import Path
from littlecsv import CSV
from popmusic2 import music_cat


# CLI: dependencies ------------------------------------------------------------
class CustomHelpFormatter(
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.HelpFormatter
    ):

    # Increase max_help_position
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, max_help_position=50)

    # Overwrite help string to automatically write (default: ...) when not None
    def _get_help_string(self, action):
        help_text = action.help

        if action.default is None or isinstance(action.default, bool):
            return help_text

        return super()._get_help_string(action)

    # Only show metavar once 
    def _format_action_invocation(self, action):
        if not action.option_strings:
            return super()._format_action_invocation(action)

        parts = action.option_strings[:]
        if action.nargs != 0:
            parts[-1] += f" {self._format_args(action, action.dest)}"
        return ", ".join(parts)


# Main -------------------------------------------------------------------------
def main():

    # Init arguments parser
    parser = argparse.ArgumentParser(
        description="Run MuSiC by-residue CAT analysis on a PDB.",
        usage="music_cat pdb_path [-o csv_path] [options]",
        formatter_class=CustomHelpFormatter,
    )

    # Parse arguments
    parser.add_argument(
        "pdb_path", type=str,
        help="path to input 3D structure file (.pdb).",
    )
    parser.add_argument(
        "-o", "--output_path", type=str, default=None, metavar="<str>",
        help="output .csv file path. Set to './<pdb_name>_cat.csv' by default.",
    )
    parser.add_argument(
        "-s", "--separator", type=str, default=",", metavar="<str>",
        help="separator used in the .csv file.",
    )
    parser.add_argument(
        "--show", type=int, choices=[0, 1], default=1, metavar="<0|1>",
        help="show CAT information.",
    )
    parser.add_argument(
        "--custom_music_path", type=str, default=None, metavar="<str>",
        help="custom path to the MuSiC executable.",
    )
    args = parser.parse_args()

    # Pre-process arguments
    pdb_path = Path(args.pdb_path)
    output_path = args.output_path
    if output_path is None:
        output_path = f"./{pdb_path.name.removesuffix('.pdb')}_cat.csv"
    output_path = Path(output_path)

    # Run foldx_ddg
    output = music_cat(
        pdb_path,
        save_path=output_path,
        sep=args.separator,
        custom_music_path=args.custom_music_path,
    )

    # Show
    if args.show:
        df = CSV(list(output[0].keys()), name=pdb_path.name)
        for entry in output:
            df.add_entry(entry)
        df.show(1000, max_col_length=30)

    # Log
    print(f"CAT information saved to '{output_path}'.")


# Execution --------------------------------------------------------------------
if __name__ == "__main__":
    main()
