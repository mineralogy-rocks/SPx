# SPx

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**SPx** is a tool for processing spectral data (including but not limited to Near-Infrared (NIR)),
extracting features, generating visualizations and statistics, and applying linear spectral unmixing (LSUMx) to retrieve smectite content from measured NIR spectra.

The spectrum processing code (main) was adapted from [Cardoso-Fernandes et al. (2021)](http://doi.org/10.5281/zenodo.4575375), and the prediction and unmixing code was created based on this study [Gread et al. (2025)](https://doi.org/10.1016/j.clay.2025.107748).

## 📋 Table of Contents

- [Features](#-features)
- [Requirements](#-requirements)
- [Installing Git](#-installing-git)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Examples](#-examples)
- [Logging](#-logging)

## ✨ Features

- Process spectral data from CSV files (e.g., NIR data)
- Export processed data as text files
- Remove continuum and extract spectral feature's parameters
- Generate visualizations of original and processed spectra
- Generate statistics and parameters of original and processed spectrum
- Applying the linear spectral unmixing (LSUMx) model to retrieve smectite content from the measured NIR single-spectrum
- Comprehensive logging of all operations

## 📦 Requirements

- Python 3.10 or higher
- pip (Python package installer)
- Git

## 💻 Installing Git

Before you can clone the repository, you need to have Git installed on your system.

### Windows

1. Download the Git installer from [Git for Windows](https://git-scm.com/download/win)
2. Run the installer and follow the installation wizard
3. During installation, accept the default options unless you have specific preferences
4. After installation, open Git Bash or Command Prompt to verify installation:
   ```bash
   git --version
   ```

### macOS

1. **Using Homebrew (recommended)**:
   ```bash
   brew install git
   ```

2. **Using the installer**:
   - Download the latest Git installer from [Git for macOS](https://git-scm.com/download/mac)
   - Run the installer and follow the instructions

3. Verify installation:
   ```bash
   git --version
   ```

### Linux (Debian/Ubuntu)

1. Update your package index:
   ```bash
   sudo apt update
   ```

2. Install Git:
   ```bash
   sudo apt install git
   ```

3. Verify installation:
   ```bash
   git --version
   ```

### Linux (Fedora)

1. Install Git:
   ```bash
   sudo dnf install git
   ```

2. Verify installation:
   ```bash
   git --version
   ```

## 🚀 Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/your-username/SPx.git
   cd SPx
   ```

2. **Install pip (if not already installed)**

   Follow the installation instructions at [pip Documentation](https://pip.pypa.io/en/stable/installation/#installation).

3. **Create a virtual environment**

   ```bash
   python -m venv .venv
   ```

4. **Activate the virtual environment**

   On macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```

   On Windows:
   ```bash
   .\.venv\Scripts\activate
   ```

5. **Install dependencies**

   ```bash
   pip install .
   ```

## ⚙️ Configuration

1. **Create environment file**

   Create a `.env` file in the project root directory using `.env.example` as a template:

   ```
   PROJECT_DIRECTORY=/path/to/your/project
   INPUT_FOLDER_NAME=input
   OUTPUT_FOLDER_NAME=output
   ```

   - `PROJECT_DIRECTORY`: The absolute path to your project directory
   - `INPUT_FOLDER_NAME`: Name of the folder containing input CSV files (default: "input")
   - `OUTPUT_FOLDER_NAME`: Name of the folder where results will be saved (default: "output")

2. **Customizing Thresholds**

   You can customize the spectral peak thresholds by modifying the `THRESHOLDS` tuple in the `src/choices.py` file:

   ```python
   THRESHOLDS = (
       ('peak-1', (5500, 8000)),
       ('peak-2', (4600, 5540)),
       ('peak-3', (4310, 4788)),
   )
   ```

   Each threshold is defined as a tuple with:
   - A name identifier (e.g., 'peak-1')
   - A range represented as a tuple of two integers (e.g., (5500, 8000)) specifying the wavelength range in nanometers

3. **Prepare input data**

   Place your CSV files in the input folder. The input folder cannot be empty.

4. **Customize endmembers**

   You can modify the endmembers used for analysis by editing the `data/endmembers.xlsx` file. This file contains reference data for various minerals and compounds. Feel free to add, remove, or modify entries as needed for your specific analysis requirements.

## 🔧 Usage

Run SPx from the command line:

```bash
python -m src.base.main [options]
```

### Command-line options

- `--no-plots`: Do not show plots during processing (useful for batch processing)

### Predicting optimal mixtures

You can predict the optimal mixture of endmembers for your samples using:

```bash
python -m src.base.predict
```

This command requires:
1. A valid endmembers file (where the first column is sample ID)
2. Samples added to a second sheet of the `results.xlsx` file (where the first column is also sample ID)

Requirements:
- The number of parameters in the endmembers file and the sample sheet must be equal
- The order of parameters should be the same in both files

The command will run minimization and create a file called `results_predicted.xlsx` in the `output/data` path.

## 📝 Examples

**Run with default settings:**
```bash
python -m src.base.main
```

**Run without showing plots:**
```bash
python -m src.base.main --no-plots
```

**Predict optimal mixtures:**
```bash
python -m src.base.predict
```

## 🫶 Support

This project was supported through several sources:
- Project No. 3007/01/01 that received funding from the **European Union´s Horizon 2020 research and innovation programme** under the *Marie Skłodowska-Curie grant agreement No. 945478*.
- APVV-20-0175
- UK/3062/2024
- UK/1025/2025.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
