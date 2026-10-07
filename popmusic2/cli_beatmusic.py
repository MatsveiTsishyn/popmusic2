
# Imports ----------------------------------------------------------------------
import argparse
from pathlib import Path
from littlecsv import CSV
from popmusic2 import beatmusic, read_mutations_file


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
        description="Compute BeAtMuSiC ΔΔGb values (thermodynamic binding affinity) for all single mutations and save output to a .csv file.",
        usage="beatmusic pdb_path chains [-o csv_path] [options]",
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
        "-o", "--output_path", type=str, default=None, metavar="<str>",
        help="output .csv file path. Set to './<pdb_name>_beatmusic.csv' by default.",
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
        "-mf", "--mfile", type=str, default=None, metavar="<str>",
        help="Optionally specify a path to a mutations_file (1 mutations by line such as 'MA13H' or 'MA13H:LA15G').",
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

    # Pre-process arguments
    pdb_path = Path(args.pdb_path)
    output_path = args.output_path
    if output_path is None:
        pdb_name = pdb_path.name.removesuffix('.pdb')
        pdb_name = f"{pdb_name}_{args.chains.replace(':', '-')}"
        output_path = f"./{pdb_name}_beatmusic.csv"
    output_path = Path(output_path)
    mutations_list = None
    if args.mfile is not None:
        mutations_list = read_mutations_file(args.mfile)

    # Run beatmusic
    output = beatmusic(
        pdb_path,
        args.chains,
        mutations_list=mutations_list,
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
        beatmusic_property = "BeAtMuSiC"
        df = CSV(["mutation", beatmusic_property], name=pdb_path.name)
        for mut, ddgb in output.items():
            df.add_entry({"mutation": mut, beatmusic_property: ddgb})
        df.show(5)


# Execution --------------------------------------------------------------------
if __name__ == "__main__":
    main()
