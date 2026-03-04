# -*- coding: UTF-8 -*-
import logging
from pathlib import Path

from src.constants import PROJECT_ROOT


logger = logging.getLogger(__name__)


class Settings:
	def __init__(self):
		self._configured = False
		self.PROJECT_DIRECTORY: Path = Path()
		self.INPUT_PATH: Path = Path()
		self.OUTPUT_PATH: Path = Path()
		self.ENDMEMBERS_PATH: Path = PROJECT_ROOT / "data" / "endmembers.xlsx"

	@property
	def is_configured(self) -> bool:
		return self._configured

	def configure(self, project_directory: str, input_folder: str = "input", output_folder: str = "output"):
		project_dir = Path(project_directory).expanduser().resolve()
		self.PROJECT_DIRECTORY = project_dir
		self.INPUT_PATH = project_dir / input_folder
		self.OUTPUT_PATH = project_dir / output_folder
		self._validate()
		self._configured = True

	def configure_from_env(self):
		import os

		from dotenv import load_dotenv

		env_path = PROJECT_ROOT / ".env"
		if env_path.exists():
			load_dotenv(dotenv_path=env_path, override=True)
		else:
			logger.error(f"Warning: Environment file not found: {env_path}")

		project_dir = os.getenv("PROJECT_DIRECTORY")
		if not project_dir:
			raise ValueError("PROJECT_DIRECTORY not set in environment variables.")

		input_folder = os.getenv("INPUT_FOLDER_NAME", "input")
		output_folder = os.getenv("OUTPUT_FOLDER_NAME", "output")
		self.configure(project_dir, input_folder, output_folder)

	def _validate(self):
		if not self.PROJECT_DIRECTORY.exists():
			raise ValueError(f"PROJECT_DIRECTORY not found: {self.PROJECT_DIRECTORY}")

		if not self.INPUT_PATH.exists():
			raise ValueError(f"INPUT_PATH not found: {self.INPUT_PATH}")

		if not self.INPUT_PATH.iterdir().__next__():
			raise ValueError(f"INPUT_PATH is empty: {self.INPUT_PATH}")

		self.OUTPUT_PATH.mkdir(parents=True, exist_ok=True)
		(self.OUTPUT_PATH / "data").mkdir(parents=True, exist_ok=True)
		(self.OUTPUT_PATH / "plots").mkdir(parents=True, exist_ok=True)


settings = Settings()
