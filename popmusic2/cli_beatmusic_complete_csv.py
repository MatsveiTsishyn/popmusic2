
# Imports ----------------------------------------------------------------------
import argparse
from pathlib import Path
from littlecsv import CSV
from popmusic2 import beatmusic


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
        description="Compute BeAtMuSiC ΔΔGb values (thermodynamic binding affinity) and add values to a .csv file.",
        usage="beatmusic_complete_csv pdb_path chains csv_path [options]",
        formatter_class=CustomHelpFormatter,
    )

    # Parse arguments
    parser.add_argument(
        "pdb_path", type=str,
        help="path to input 3D structure file (.pdb).",
    )
    parser.add_argument(
        "chains", type=str,
        help="interacting chains such as 'AB:C'.",
    )
    parser.add_argument(
        "csv_path", type=str,
        help=".csv file to complete.",
    )
    parser.add_argument(
        "-m", "--mutation_property", type=str, default="mutation", metavar="<str>",
        help="property in the .csv that indentifies mutations.",
    )
    parser.add_argument(
        "-p", "--beatmusic_property", type=str, default="BeAtMuSiC", metavar="<str>",
        help="property in the .csv that indentifies output BeAtMuSiC value.",
    )
    parser.add_argument(
        "-s", "--separator", type=str, default=",", metavar="<str>",
        help="separator used in the .csv file.",
    )
    parser.add_argument(
        "-v", "--verbose", type=int, choices=[0, 1], default=1, metavar="<0|1>",
        help="enable logging.",
    )
    parser.add_argument(
        "-d", "--log_debug", type=int, choices=[0, 1], default=0, metavar="<0|1>",
        help="print MuSiC raw output for debugging.",
    )
    parser.add_argument(
        "--music_output_dir", type=str, default=None, metavar="<str>",
        help="optional directory for MuSiC output side-effect files; defaults to a temporary directory (files will be deleted).",
    )
    parser.add_argument(
        "--show", type=int, choices=[0, 1], default=1, metavar="<0|1>",
        help="show a sample of fist mutations output.",
    )
    parser.add_argument(
        "--custom_music_path", type=str, default=None, metavar="<str>",
        help="custom path to the MuSiC executable.",
    )
    args = parser.parse_args()

    # Read data
    data = CSV.read(args.csv_path, sep=args.separator)
    if args.mutation_property not in data.header():
        raise ValueError(
            f"Input mutation_property='{args.mutation_property}' is not contained in CSV file '{args.csv_path}'.\n"
            f" -> Header: {data.header()}"
        )

    # Run beatmusic
    output = beatmusic(
        args.pdb_path,
        args.chains,
        log_steps=bool(args.verbose),
        log_debug=bool(args.log_debug),
        music_output_dir=args.music_output_dir,
        custom_music_path=args.custom_music_path,
    )

    # Assign and save data
    data.add_empty_col(args.beatmusic_property, default_value="", allow_replacement=True)
    n_errors = 0
    for mutation_entry in data:
        mutation = mutation_entry[args.mutation_property]
        single_mutations = mutation.split(":")
        if not all(m in output for m in single_mutations):
            n_errors += 1
            continue
        mutation_entry[args.beatmusic_property] = sum([output[m] for m in single_mutations])
    data.write(args.csv_path)

    # Log
    if n_errors > 0:
        print(f"WARNING: {n_errors} / {len(data)} mutations values where not assigned to '{args.csv_path}'.")
    print(f"Save mutational data to '{args.csv_path}'.")

    # Show
    if args.show:
        data.show(5)


# Execution --------------------------------------------------------------------
if __name__ == "__main__":
    main()
