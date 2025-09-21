from pathlib import Path


def ensure_parent_folder(folder_name: str) -> Path:
    """
    Creates (if needed) a folder named `folder_name`
    in the parent directory of this file’s project.

    Returns the Path object to that folder.
    """
    # __file__ → e.g. /path/to/project/utils/fs_utils.py
    project_root = Path(__file__).resolve().parent.parent
    target_folder = project_root / folder_name

    if not target_folder.exists():
        # Make folder (and any missing parents) if it does not exist
        target_folder.mkdir(parents=True, exist_ok=True)
    return target_folder
