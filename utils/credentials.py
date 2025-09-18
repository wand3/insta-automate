import json
from pathlib import Path
from typing import TypedDict


class Creds(TypedDict):
    username: str
    password: str


def load_credentials(platform: str) -> Creds:
    """
    Reads config/user_credentials.json and returns the creds for the given platform.
    Raises KeyError if platform not found.
    """
    config_path = Path(__file__).parent.parent / "config" / "user_credentials.json"
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return data[platform]
