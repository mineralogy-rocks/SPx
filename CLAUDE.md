# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SPx is a Python-based tool for processing spectral data (including Near-Infrared), extracting features, generating visualizations and statistics, and applying linear spectral unmixing (LSUMx) to retrieve smectite content from measured NIR spectra.
It is a standalone project within the mineralogy-rocks ecosystem.

## Commands

### Running the Application
- `python -m src.base.main` - Run the main spectra processing pipeline
- `python -m src.base.main --no-plots` - Run without showing plots (batch mode)
- `python -m src.base.predict` - Run endmember prediction (linear spectral unmixing)

### Code Quality
- `ruff check .` - Run linting
- `ruff format .` - Format code
- `ruff check . --fix` - Fix auto-fixable linting issues

### Setup
- `python -m venv .venv && source .venv/bin/activate && pip install .` - Create venv and install dependencies

## Architecture

### Core Structure
- **src/base/main.py**: Main processing pipeline — generates spectra from CSV input, processes them (continuum removal, feature extraction, statistics), and exports results
- **src/base/predict.py**: Linear spectral unmixing — finds optimal endmember mixture coefficients using bounded minimization (SciPy)
- **src/config.py**: Environment-based configuration via `Settings` class; loads `.env`, validates paths, creates output directories
- **src/constants.py**: Project root path constant
- **src/choices.py**: Configurable spectral peak thresholds and endmember definitions

### Processing Pipeline
1. **Generate spectra**: Read CSV files from input, filter by wavelength thresholds, export as tab-separated text files
2. **Process spectra**: Plot original spectra, extract convex hull quotient features, generate statistics (FW, FWHM, asymmetry, depth), export to `results.xlsx`
3. **Continuum removal**: Export continuum-removed spectra as text files with plots
4. **Predict (separate command)**: Read endmembers from `data/endmembers.xlsx` and samples from `results.xlsx` sheet 2, run bounded minimization to find optimal mixture coefficients, export to `results_predicted.xlsx`

### Key Dependencies
- **pysptools**: Convex hull quotient for spectral feature extraction
- **pandas**: Data manipulation and I/O
- **matplotlib**: Visualization
- **scipy**: Optimization (minimize_scalar) for unmixing
- **tqdm**: Progress bars
- **coloredlogs**: Formatted logging

### Environment Configuration
- Uses `.env` file in project root (see `.env.example`)
- `PROJECT_DIRECTORY`: Absolute path to project directory
- `INPUT_FOLDER_NAME`: Folder with input CSV files (default: "input")
- `OUTPUT_FOLDER_NAME`: Folder for results (default: "output")

### Data Directory Structure
- `data/endmembers.xlsx` - Reference endmember data for unmixing
- `{OUTPUT}/data/` - Processed data files and results
- `{OUTPUT}/plots/` - Generated spectral plots

## Development Patterns

### Code Style
- Follow PEP-8 with ruff (line length: 120)
- Use tabs for indentation
- Single-line imports enforced by ruff
- Target Python 3.10+ (ruff config), requires Python 3.12+ (pyproject.toml)

### Spectral Thresholds
- Defined in `src/choices.py` as `THRESHOLDS` tuple
- Each threshold: name string + wavelength range tuple (nm)
- Modify these to adjust which spectral peaks are extracted
