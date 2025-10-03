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


def extract_post_users_from_json(filename, dict_key):
    """
    Most robust dictionary-only solution for extracting post_user values
    """
    storage_dir = ensure_parent_folder("results")
    filename = storage_dir / filename

    def try_parse_json_objects(text):
        """Try to parse multiple JSON objects from text"""
        objects = []
        current = ""
        stack = []
        in_string = False
        escaped = False

        for char in text:
            if escaped:
                current += char
                escaped = False
                continue

            if char == '\\':
                escaped = True
                current += char
                continue

            if char == '"' and not escaped:
                in_string = not in_string

            if not in_string:
                if char == '{':
                    stack.append(char)
                elif char == '}':
                    if stack and stack[-1] == '{':
                        stack.pop()

            current += char

            if not stack and not in_string and current.strip().startswith('{'):
                objects.append(current.strip())
                current = ""

        return objects

    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    post_users = []

    # Try different parsing strategies
    strategies = [
        # Strategy 1: Direct JSON load
        lambda: [json.loads(content)] if content.startswith('{') or content.startswith('[') else [],

        # Strategy 2: As JSON array
        lambda: json.loads(content) if content.startswith('[') else [],

        # Strategy 3: Multiple objects
        lambda: [json.loads(obj) for obj in try_parse_json_objects(content) if obj]
    ]

    for strategy in strategies:
        try:
            result = strategy()
            if result:
                if isinstance(result, list):
                    for item in result:
                        if isinstance(item, dict) and f'{dict_key}' in item:
                            post_users.append(item[f'{dict_key}'])
                elif isinstance(result, dict) and f'{dict_key}' in result:
                    post_users.append(result[f'{dict_key}'])

                if post_users:
                    break
        except:
            continue

    # Remove duplicates while preserving order
    seen = set()
    unique_users = []
    for user in post_users:
        if user and user not in seen:
            seen.add(user)
            unique_users.append(user)

    return unique_users


# save scraped user profile
def save_to_profile_json(self, profile, filename=None):
    """Save extracted data to JSON file"""
    if not filename:
        try:
            self.logger.info(f"saving to json profile data")
            storage_dir = ensure_parent_folder("results")
            filename = "profiles.json"
            file_path = storage_dir / filename

            # # Save to JSON
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(profile, f, ensure_ascii=False, indent=2)
            return
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
    existing.append(profile)

    # Write back entire list, nicely formatted
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    # with open(filepath, 'a', encoding='utf-8') as f:
    #     json.dump(self.data, f, indent=2, ensure_ascii=False)
    return str(filepath)

