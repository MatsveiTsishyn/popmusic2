
# Imports ----------------------------------------------------------------------
from pathlib import Path
from popmusic2.utils import find_executable


# CONFIG -----------------------------------------------------------------------
class CONFIG:
    """Global popmusic2 values such as path to MuSiC executable."""


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

    @classmethod
    def get_music_dir(cls) -> str:
        """Return path to MuSiC source code directory."""
        music_executable_path = Path(cls.get_music_executable_path())
        music_dir = music_executable_path.parent
        if not music_dir.is_dir():
            raise ValueError(f"MuSiC source code directory '{music_dir}' not found.")
        return str(music_dir)

    @classmethod
    def get_music_data_dir(cls) -> str:
        """Return path to MuSiC 'Data' directory."""
        music_dir = Path(cls.get_music_dir())
        music_data_dir = music_dir / "MuSiC" / "Data"
        if not music_data_dir.is_dir():
            raise ValueError(f"MuSiC Data directory '{music_data_dir}' not found.")
        return str(music_data_dir)

    @classmethod
    def get_music_energy_dir(cls, symmetric: bool=False, custom_potentials_dir: str | Path | None = None) -> str:
        """Return path to MuSiC energy directory (for standard or symmetric energy potentials)."""
        if custom_potentials_dir is None:
            pot_folder = "energy_music_sym" if symmetric else "energy_music"
            music_data_dir = Path(cls.get_music_data_dir())
            music_energy_dir = music_data_dir / pot_folder
        else:
            music_energy_dir = Path(custom_potentials_dir).expanduser().resolve()
        if not music_energy_dir.is_dir():
            raise ValueError(f"MuSiC Energy directory '{music_energy_dir}' not found.")
        return str(music_energy_dir)

    @classmethod
    def get_path_in(cls, tmp_dir: str | Path, symmetric: bool=False, custom_potentials_dir: str | Path | None = None) -> str:
        """Return path to MuSiC energy directory (for standard or symmetric energy potentials)."""
        tmp_dir = Path(tmp_dir).absolute()
        music_data_dir = cls.get_music_data_dir()
        music_energy_dir = cls.get_music_energy_dir(symmetric=symmetric, custom_potentials_dir=custom_potentials_dir)
        path_in = "\n".join([
            f"DATA    {music_data_dir}/",
            f"POT     {music_energy_dir}/",
            f"PDB     {tmp_dir}/",
            f"CAT     {tmp_dir}/",
            f"MUT     {tmp_dir}/",
            f"OUTPUT  {tmp_dir}/",
        ])
        return path_in
