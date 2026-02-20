"""Configuration management for ApplyPilot."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

from models.schemas import PipelineConfig, Profile, SearchPreferences

DATA_DIR = Path(__file__).parent.parent / "data"
PROFILE_PATH = DATA_DIR / "profile.json"
PREFERENCES_PATH = DATA_DIR / "preferences.json"
JOBS_PATH = DATA_DIR / "jobs.json"
CONFIG_PATH = DATA_DIR / "config.json"
EMPLOYERS_PATH = Path(__file__).parent / "employers.yaml"


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def save_json(path: Path, data: Any) -> None:
    ensure_data_dir()
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def save_profile(profile: Profile) -> None:
    save_json(PROFILE_PATH, profile.model_dump())


def load_profile() -> Profile | None:
    data = load_json(PROFILE_PATH)
    if data:
        return Profile(**data)
    return None


def save_preferences(prefs: SearchPreferences) -> None:
    save_json(PREFERENCES_PATH, prefs.model_dump())


def load_preferences() -> SearchPreferences | None:
    data = load_json(PREFERENCES_PATH)
    if data:
        return SearchPreferences(**data)
    return None


def save_config(config: PipelineConfig) -> None:
    save_json(CONFIG_PATH, config.model_dump())


def load_config() -> PipelineConfig:
    data = load_json(CONFIG_PATH)
    if data:
        return PipelineConfig(**data)
    return PipelineConfig()


def load_employers() -> list[dict]:
    if not EMPLOYERS_PATH.exists():
        return []
    with open(EMPLOYERS_PATH) as f:
        data = yaml.safe_load(f)
    return data.get("employers", []) if data else []


def is_setup_complete() -> bool:
    profile = load_profile()
    config = load_config()
    if not profile or not config:
        return False
    return bool(profile.full_name and config.gemini_api_key)
