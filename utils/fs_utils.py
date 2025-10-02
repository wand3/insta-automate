from pathlib import Path
import json


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


def save_to_json(self, post, filename=None):
    """Save extracted data to JSON file"""
    if not filename:
        try:
            self.logger.info(f"saving to json post data")
            storage_dir = ensure_parent_folder("results")
            filename = "posts_details.json"
            file_path = storage_dir / filename

            # # Save to JSON
            # with open(file_path, "w", encoding="utf-8") as f:
            #     json.dump(post, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Couldn't save results {e}")

    # file_path = storage_dir / filename
    base_folder = Path(__name__).resolve().parent
    results_dir = base_folder / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    # Now, define the full path to the file itself
    filepath = results_dir / filename
    # Load existing data (if file exists), else start fresh
    if filepath.exists():
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                existing = json.load(f)
                if not isinstance(existing, list):
                    # handle corrupted/non-list file
                    existing = []
        except json.JSONDecodeError:
            existing = []
    else:
        existing = []

    # Append new record
    existing.append(post)

    # Write back entire list, nicely formatted
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    # with open(filepath, 'a', encoding='utf-8') as f:
    #     json.dump(self.data, f, indent=2, ensure_ascii=False)
    return str(filepath)
