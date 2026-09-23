
# Imports ----------------------------------------------------------------------
from pathlib import Path
from pypopmusic2.utils import find_executable


# CONFIG -----------------------------------------------------------------------
class CONFIG:
    """Global pypopmusic2 values such as path to MuSiC executable."""


    # MuSiC candidate paths ----------------------------------------------------
    music_candidate_paths: list[str] = [
        "/home/user/INTERACTOME/softs/MuSiC-4.1/music_retro",    # ThinkPad Matsvei
    ]
    music_path: str | None = None


    # MuSiC executable path solver ---------------------------------------------
    @classmethod
    def get_music_executable_path(
            cls,
            custom_path: str | Path | None = None
        ) -> str:
        """Find a valid MuSiC executable file among CONFIG.music_candidate_paths and custom_path if given.
            - raises Error if such executable is not found
            - get globally CONFIG.music_path to the file that has been found as valid
            - so it will look for it only once by python run
        """

        # Case : path already resolved
        if cls.music_path is not None:
            return cls.music_path

        # Case : resolve path
        candidate_paths = cls.music_candidate_paths
        if custom_path is not None:
            candidate_paths = [str(custom_path)] + candidate_paths
        cls.music_path = find_executable(candidate_paths)
        return cls.music_path
