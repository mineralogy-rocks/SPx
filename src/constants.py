# -*- coding: UTF-8 -*-
import sys
from pathlib import Path


def get_project_root() -> Path:
	if getattr(sys, "frozen", False):
		return Path(sys._MEIPASS)
	return Path(__file__).resolve().parent.parent


PROJECT_ROOT = get_project_root()
