# -*- coding: UTF-8 -*-
import logging
import os
from pathlib import Path

from dotenv import load_dotenv

from src.constants import PROJECT_ROOT

logger = logging.getLogger(__name__)


class Settings:
    def __init__(self):
        self._load_env()

        project_dir = os.path.expanduser(os.getenv("PROJECT_DIRECTORY"))
        self.PROJECT_DIRECTORY: Path = Path(project_dir)

        self.INPUT_PATH: Path = self.PROJECT_DIRECTORY / os.getenv("INPUT_FOLDER_NAME")
        self.OUTPUT_PATH: Path = self.PROJECT_DIRECTORY / os.getenv("OUTPUT_FOLDER_NAME")

        self.ENDMEMBERS_PATH: Path = PROJECT_ROOT / "data" / "endmembers.xlsx"

        self._validate()

    def _load_env(self):
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(dotenv_path=env_path, override=True)
        else:
            logger.error(f"Warning: Environment file not found: {env_path}")

    def _validate(self):
        if not self.PROJECT_DIRECTORY:
            raise ValueError("PROJECT_DIRECTORY not set in environment variables.")

        if not self.PROJECT_DIRECTORY.exists():
            raise ValueError(f"PROJECT_DIRECTORY not found: {self.PROJECT_DIRECTORY}")

        if not self.OUTPUT_PATH.exists():
            logger.info(f"Creating the output directory: {self.OUTPUT_PATH}")
            self.OUTPUT_PATH.mkdir(parents=True, exist_ok=True)

        if not self.INPUT_PATH.exists():
            raise ValueError(f"INPUT_PATH not set in environment variables: {self.INPUT_PATH}")

        if not (self.OUTPUT_PATH / "data").exists():
            (self.OUTPUT_PATH / "data").mkdir(parents=True, exist_ok=True)

        if not (self.OUTPUT_PATH / "plots").exists():
            (self.OUTPUT_PATH / "plots").mkdir(parents=True, exist_ok=True)

        if self.INPUT_PATH.exists() and not any(self.INPUT_PATH.iterdir()):
            logger.error(f"Warning: Input directory is empty: {self.INPUT_PATH}")
            raise ValueError(f"INPUT_PATH is empty: {self.INPUT_PATH}")


settings = Settings()
