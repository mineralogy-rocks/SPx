# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "SPx @ git+https://github.com/mineralogy-rocks/SPx.git",
#     "pandas==3.0.1",
#     "matplotlib==3.10.8",
#     "openpyxl",
#     "marimo",
# ]
# ///

import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    import marimo as mo

    return (mo,)


@app.cell
def _(mo):
    import subprocess as _subprocess
    import sys as _sys

    try:
        import src as _src_check
    except ImportError:
        with mo.status.spinner("Installing SPx..."):
            _subprocess.check_call([
                _sys.executable, "-m", "pip", "install",
                "SPx @ git+https://github.com/mineralogy-rocks/SPx.git",
            ])
        import importlib as _importlib
        _importlib.invalidate_caches()
    return ()


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # SPx — Spectral Processing

    **SPx** is a tool for processing spectral data (including but not limited to Near-Infrared (NIR)),
    extracting features, generating visualizations and statistics, and applying linear spectral unmixing
    (LSUMx) to retrieve smectite content from measured NIR spectra.

    The spectrum processing code was adapted from
    [Cardoso-Fernandes et al. (2021)](http://doi.org/10.5281/zenodo.4575375), and the prediction and
    unmixing code was created based on [Gread et al. (2025)](https://doi.org/10.1016/j.clay.2025.107748).

    This notebook runs the **processing** stage of the pipeline:

    1. **Generate spectra** — read CSV files, filter by wavelength thresholds, export as tab-separated text
    2. **Process spectra** — plot original spectra, extract convex hull quotient features, generate statistics (FW, FWHM, asymmetry, depth), export to `results.xlsx`
    3. **Continuum removal** — export continuum-removed spectra as text files with plots

    [![Open in Marimo](https://marimo.io/shield.svg)](https://marimo.io/p/@mineralogy-rocks/spx-processing)

    ---

    ### Preparing Your Data

    Place your spectral **CSV files** in the upload area below. Each CSV should have two columns:
    wavelength and reflectance values.

    Need sample data? Download from the [sample files on GitHub](https://github.com/mineralogy-rocks/SPx/tree/main/data/samples).

    ### Default Thresholds

    Spectral peak wavelength ranges (nm) used to filter input data. You can adjust these below.

    | Peak | Min (nm) | Max (nm) |
    |------|----------|----------|
    | peak-1 | 5500 | 8000 |
    | peak-2 | 4600 | 5540 |
    | peak-3 | 4310 | 4788 |

    ### Results

    After processing, you will find:

    - **data/** — result spreadsheets (`.xlsx`, `.csv`, `.txt`)
    - **plots/** — spectral plots (`.png`)
    """)
    return


@app.cell
def _():
    import logging
    import os
    import tempfile

    import matplotlib

    matplotlib.use("agg")

    from src.base.main import run_pipeline
    from src.config import settings

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    return os, run_pipeline, settings, tempfile


@app.cell
def _(os, settings, tempfile):
    _tmpdir = tempfile.mkdtemp(prefix="spx_")
    INPUT_DIR = os.path.join(_tmpdir, "input")
    OUTPUT_DIR = os.path.join(_tmpdir, "output")

    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    _original_validate = settings._validate
    settings._validate = lambda: None
    settings.configure(_tmpdir, "input", "output")
    settings._validate = _original_validate

    (settings.OUTPUT_PATH / "data").mkdir(parents=True, exist_ok=True)
    (settings.OUTPUT_PATH / "plots").mkdir(parents=True, exist_ok=True)
    return (INPUT_DIR,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Upload Data
    """)
    return


@app.cell
def _(mo):
    file_upload = mo.ui.file(filetypes=[".csv"], multiple=True, kind="area")
    file_upload
    return (file_upload,)


@app.cell
def _(INPUT_DIR, file_upload, os):
    if file_upload.value:
        for f in file_upload.value:
            with open(os.path.join(INPUT_DIR, f.name), "wb") as fh:
                fh.write(f.contents)
    uploaded_files = sorted(
        [
            {"name": f.name, "size": f"{os.path.getsize(os.path.join(INPUT_DIR, f.name)) / 1024:.1f} KB"}
            for f in os.scandir(INPUT_DIR)
            if f.is_file()
        ],
        key=lambda x: x["name"],
    )
    return (uploaded_files,)


@app.cell
def _(mo, uploaded_files):
    if not uploaded_files:
        mo.md("No files uploaded yet.")
    else:
        mo.ui.table(uploaded_files, selection=None, label=f"{len(uploaded_files)} file(s) in input")
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Thresholds

    Adjust spectral peak wavelength ranges (nm) used to filter input data.
    """)
    return


@app.cell
def _(mo):
    peak1_min = mo.ui.number(start=1000, stop=10000, value=5500, step=1, label="peak-1 min (nm)")
    peak1_max = mo.ui.number(start=1000, stop=10000, value=8000, step=1, label="peak-1 max (nm)")
    peak2_min = mo.ui.number(start=1000, stop=10000, value=4600, step=1, label="peak-2 min (nm)")
    peak2_max = mo.ui.number(start=1000, stop=10000, value=5540, step=1, label="peak-2 max (nm)")
    peak3_min = mo.ui.number(start=1000, stop=10000, value=4310, step=1, label="peak-3 min (nm)")
    peak3_max = mo.ui.number(start=1000, stop=10000, value=4788, step=1, label="peak-3 max (nm)")

    mo.vstack([
        mo.hstack([peak1_min, peak1_max], justify="start"),
        mo.hstack([peak2_min, peak2_max], justify="start"),
        mo.hstack([peak3_min, peak3_max], justify="start"),
    ])
    return peak1_max, peak1_min, peak2_max, peak2_min, peak3_max, peak3_min


@app.cell
def _(peak1_max, peak1_min, peak2_max, peak2_min, peak3_max, peak3_min):
    thresholds = [
        ("peak-1", (peak1_min.value, peak1_max.value)),
        ("peak-2", (peak2_min.value, peak2_max.value)),
        ("peak-3", (peak3_min.value, peak3_max.value)),
    ]
    return (thresholds,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Axis Labels

    Customize chart axis labels for original and continuum-removed spectra plots.
    """)
    return


@app.cell
def _(mo):
    orig_x = mo.ui.text(value="Wavelength (nm)", full_width=True)
    orig_y = mo.ui.text(value="Reflectance (%)", full_width=True)
    cr_x = mo.ui.text(value="Wavelength (nm)", full_width=True)
    cr_y = mo.ui.text(value="Continuum removed reflectance", full_width=True)

    mo.hstack([
        mo.vstack([mo.md("**Original — X axis**"), orig_x, mo.md("**Original — Y axis**"), orig_y]),
        mo.vstack([mo.md("**Continuum removed — X axis**"), cr_x, mo.md("**Continuum removed — Y axis**"), cr_y]),
    ], justify="start", gap=2)
    return cr_x, cr_y, orig_x, orig_y


@app.cell
def _(cr_x, cr_y, orig_x, orig_y):
    axis_labels = {
        "original": (orig_x.value, orig_y.value),
        "continuum_removed": (cr_x.value, cr_y.value),
    }
    return (axis_labels,)


@app.cell
def _(mo):
    run_button = mo.ui.run_button(label="Run Processing Pipeline")
    run_button
    return (run_button,)


@app.cell
def _(axis_labels, mo, run_button, run_pipeline, settings, thresholds):
    import io as _io
    import logging as _logging

    mo.stop(not run_button.value, mo.md("Click **Run Processing Pipeline** above to start."))

    _log_buf = _io.StringIO()
    _handler = _logging.StreamHandler(_log_buf)
    _handler.setLevel(_logging.INFO)
    _handler.setFormatter(_logging.Formatter("%(asctime)s %(levelname)s %(message)s"))

    _root = _logging.getLogger()
    _root.addHandler(_handler)

    try:
        with mo.status.spinner("Running processing pipeline..."):
            run_pipeline(show_plots=False, thresholds=thresholds, axis_labels=axis_labels)
    finally:
        _root.removeHandler(_handler)

    pipeline_done = True
    output_path = settings.OUTPUT_PATH
    pipeline_log = _log_buf.getvalue()
    return output_path, pipeline_done, pipeline_log


@app.cell
def _(mo, pipeline_done, pipeline_log):
    mo.stop(not pipeline_done)
    mo.accordion({"Pipeline Log": mo.md(f"```\n{pipeline_log}\n```")})
    return


@app.cell
def _(mo, output_path, pipeline_done):
    import zipfile
    from io import BytesIO
    from pathlib import Path

    import pandas as pd

    mo.stop(not pipeline_done)

    _results_path = output_path / "data" / "results.xlsx"
    _plots_dir = output_path / "plots"
    _data_dir = output_path / "data"

    _elements = []

    # Zip the entire output folder
    _zip_buf = BytesIO()
    with zipfile.ZipFile(_zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for _f in sorted(Path(output_path).rglob("*")):
            if _f.is_file():
                zf.write(_f, _f.relative_to(output_path))
    _zip_buf.seek(0)
    _elements.append(mo.download(data=_zip_buf.getvalue(), filename="spx_results.zip", label="Download all results (.zip)"))

    # Results table
    if _results_path.exists():
        _df = pd.read_excel(_results_path)
        _elements.append(mo.md("### Results Data"))
        _elements.append(mo.ui.table(_df))

    # Files table with individual download links
    _all_files = []
    for _subdir in ["data", "plots"]:
        _dir = output_path / _subdir
        if _dir.exists():
            for _f in sorted(_dir.iterdir()):
                if _f.is_file():
                    _all_files.append({
                        "folder": _subdir,
                        "file": _f.name,
                        "size": f"{_f.stat().st_size / 1024:.1f} KB",
                        "download": mo.download(data=_f.read_bytes(), filename=_f.name, label="Download"),
                    })

    if _all_files:
        _elements.append(mo.md("### All Output Files"))
        _elements.append(mo.ui.table(
            _all_files,
            selection=None,
        ))

    # Plots grid (3 per row)
    if _plots_dir.exists():
        _plot_files = sorted(_plots_dir.glob("*.png"))
        if _plot_files:
            _elements.append(mo.md("### Plots"))
            _row = []
            for _i, _p in enumerate(_plot_files):
                _row.append(mo.vstack([
                    mo.md(f"**{_p.stem}**"),
                    mo.image(src=_p, width=300),
                ]))
                if len(_row) == 3:
                    _elements.append(mo.hstack(_row, justify="start", gap=1))
                    _row = []
            if _row:
                _elements.append(mo.hstack(_row, justify="start", gap=1))

    mo.vstack(_elements)
    return


if __name__ == "__main__":
    app.run()
