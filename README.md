<p>
  <img src="./assets/logo.png" alt="SPx logo" width="200" />
  <br />
  <br />
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/Python-3.10+-blue.svg" alt="Python 3.10+" /></a>
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT" /></a>
  <a href="https://colab.research.google.com/github/mineralogy-rocks/SPx/blob/main/notebook.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab" /></a>
</p>

**SPx** is a tool for processing spectral data (including but not limited to Near-Infrared (NIR)),
extracting features, generating visualizations and statistics, and applying linear spectral unmixing (LSUMx) to retrieve smectite content from measured NIR spectra.

The spectrum processing code (main) was adapted from [Cardoso-Fernandes et al. (2021)](http://doi.org/10.5281/zenodo.4575375), and the prediction and unmixing code was created based on this study [Gread et al. (2025)](https://doi.org/10.1016/j.clay.2025.107748).

## 📋 Table of Contents

- [Try in Browser](#-try-in-browser)
- [Getting Started](#-getting-started)
- [Using the Application](#-using-the-application)
- [Preparing Your Data](#-preparing-your-data)
- [Development](#-development)
- [Support](#-support)
- [License](#-license)

## 🌐 Try in Browser

Click **Open in Colab** above to launch the notebook in Google Colab — no installation needed. The first cell automatically clones the repository and installs all dependencies. Just run all cells from top to bottom.

## 🚀 Getting Started

### Download

Download the latest version of SPx from the [GitHub Releases](https://github.com/mineralogy-rocks/SPx/releases) page:

- **macOS**: Download `SPx.app.zip`, unzip it, and move `SPx.app` to your Applications folder
- **Windows**: Download `SPx.exe` and run it directly

> **macOS note**: The first time you open SPx, you may see a security warning. Right-click the app and select "Open" to bypass it, then click "Open" in the dialog. You only need to do this once.

### Launch

Double-click `SPx.app` (macOS) or `SPx.exe` (Windows) to start the application.

## 📖 Using the Application

### Step 1: Select a Project Directory

Click **Browse...** and choose a folder that contains your input data. This folder should have a subfolder named `input` with your CSV files inside it.

### Step 2: Set Folder Names

The default folder names are `input` and `output`. You can change them if your project uses different names.

### Step 3: (Optional) Adjust Thresholds and Endmembers File

- Click **Edit Thresholds** to change the wavelength ranges used for spectral peak extraction
- In the **Endmembers File** field, the default path (`data/endmembers.xlsx`) is pre-filled. Click **Browse...** to select a different `.xlsx` file

### Step 4: Run Processing

- Click **Process Spectra** to run the full spectral processing pipeline (feature extraction, statistics, visualizations)
- Click **Run Unmixing** to apply linear spectral unmixing using your endmember data

A progress bar will show that processing is running, and the **Log** tab displays real-time messages about what the application is doing.

### Step 5: Browse Results

When processing finishes, the app automatically switches to the **Output Files** tab. This built-in file explorer shows your results organized in two folders:

- **data/** — result spreadsheets (`.xlsx`, `.csv`, `.txt`)
- **plots/** — spectral plots (`.png`)

**Double-click** any file to open it directly — images open in Preview (macOS) or your default image viewer, spreadsheets open in Excel, and so on.

You can also click **Open Output Folder** at the bottom of the window to open the output directory in Finder or File Explorer.

Use the **Refresh** button in the Output Files tab to reload the file list if you've made changes outside the app.

## 📂 Preparing Your Data

### Input Files

Place your spectral CSV files in the `input` folder inside your project directory. The input folder cannot be empty.

### Customizing Thresholds

Click **Edit Thresholds** in the main window to adjust spectral peak wavelength ranges without editing any files. Changes apply immediately to the next **Process Spectra** run.

Default thresholds:

| Name   | Min (nm) | Max (nm) |
|--------|----------|----------|
| peak-1 | 5500     | 8000     |
| peak-2 | 4600     | 5540     |
| peak-3 | 4310     | 4788     |

### Endmembers

The **Endmembers File** field in the main window points to the `.xlsx` file containing your reference endmember data. The default path is `data/endmembers.xlsx` inside your project directory. Click **Browse...** to select a different file.

The endmembers file must have:
- First column: endmember name/ID
- Remaining columns: spectral parameters (e.g. `D`, `2D`, `3D`, `TAr/TFWH`, `Total Slope`)
- Exactly 2 rows of endmember data

### Prediction Requirements

To run spectral unmixing, you need:
1. A valid endmembers file (first column is sample ID)
2. Samples added to the second sheet of `results.xlsx` (first column is sample ID)
3. The number and order of parameters must match between both files

The output will be saved as `results_predicted.xlsx` in the `output/data` folder.

---

## 🛠 Development

This section is for developers who want to run SPx from source or contribute to the project.

### Requirements

- Python 3.10 or higher
- pip (Python package installer)
- Git

### Installing Git

Before cloning the repository, you need Git installed:

- **Windows**: Download from [Git for Windows](https://git-scm.com/download/win) and run the installer
- **macOS**: Run `brew install git` (with [Homebrew](https://brew.sh)) or download from [Git for macOS](https://git-scm.com/download/mac)
- **Linux (Debian/Ubuntu)**: `sudo apt update && sudo apt install git`
- **Linux (Fedora)**: `sudo dnf install git`

Verify with `git --version`.

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/mineralogy-rocks/SPx.git
   cd SPx
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv .venv
   ```

   On macOS/Linux:
   ```bash
   source .venv/bin/activate
   ```

   On Windows:
   ```bash
   .\.venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install .
   ```

### Configuration (Command Line)

When running from the command line, create a `.env` file in the project root using `.env.example` as a template:

```
PROJECT_DIRECTORY=/path/to/your/project
INPUT_FOLDER_NAME=input
OUTPUT_FOLDER_NAME=output
```

### Command-Line Usage

```bash
# Process spectra
python -m src.base.main

# Process spectra without showing plots
python -m src.base.main --no-plots

# Run spectral unmixing
python -m src.base.predict
```

### Building the Application

```bash
make clean && make build
```

The built application will be in the `dist/` directory.

## 🫶 Support

This project was supported through several sources:
- Project No. 3007/01/01 that received funding from the **European Union´s Horizon 2020 research and innovation programme** under the *Marie Skłodowska-Curie grant agreement No. 945478*.
- APVV-20-0175
- UK/3062/2024
- UK/1025/2025.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
