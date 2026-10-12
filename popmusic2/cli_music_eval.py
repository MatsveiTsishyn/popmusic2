
# Imports ----------------------------------------------------------------------
import argparse
from pathlib import Path
from littlecsv import CSV
from popmusic2 import music_eval


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
        description="Compute MuSiC Potential Statistical Energy values ΔW and save output to a .csv file.",
        usage="music_eval pdb_path [-o csv_path] [options]",
        formatter_class=CustomHelpFormatter,
    )

    # Parse arguments
    parser.add_argument(
        "pdb_path", type=str,
        help="path to input 3D structure file (.pdb).",
    )
    parser.add_argument(
        "-o", "--output_path", type=str, default=None, metavar="<str>",
        help="output .csv file path. Set to './<pdb_name>_musiceval.csv' by default.",
    )
    parser.add_argument(
        "-c", "--chains", type=str, default=None, metavar="<str>",
        help="if set, first filter PDB on these chains before computing MuSiC energy scores.",
    )
    parser.add_argument(
        "--symmetric", type=int, choices=[0, 1], default=0, metavar="<0|1>",
        help="set to 1 to run the symmetric MuSiC potentials.",
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
        "-pot", "--custom_potentials_dir", type=str, default=None, metavar="<str>",
        help="path to a directory with custom potentials files (such as 'sd.enc').",
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
        help="show outputs.",
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
        pdb_name = pdb_path.name.removesuffix('.pdb')
        if args.chains is not None:
            pdb_name = f"{pdb_name}_{args.chains}"
        output_path = f"./{pdb_name}_musiceval.csv"
    output_path = Path(output_path)

    # Run popmusic2
    output = music_eval(
        pdb_path,
        chains=args.chains,
        symmetric=bool(args.symmetric),
        log_steps=bool(args.verbose),
        log_debug=bool(args.log_debug),
        custom_potentials_dir=args.custom_potentials_dir,
        save_path=output_path,
        sep=args.separator,
        music_output_dir=args.music_output_dir,
        custom_music_path=args.custom_music_path,
    )

    # Show
    if args.show:
        df = CSV(["potential", "energy"], name=pdb_path.name)
        for pot, val in output.items():
            df.add_entry({"potential": pot, "energy": val})
        df.show(20)


# Execution --------------------------------------------------------------------
if __name__ == "__main__":
    main()
