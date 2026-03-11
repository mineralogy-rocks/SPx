# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pysptools>=0.15.0",
#     "pandas>=2.3.0",
#     "matplotlib==3.10.8",
#     "scipy==1.14",
#     "scipy-stubs>=1.15.3.0",
#     "openpyxl",
#     "tqdm==4.67.3",
#     "tzdata==2025.2",
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
    import shutil
    import tempfile
    from pathlib import Path

    import matplotlib
    import matplotlib.pyplot as plt
    import pandas as pd
    from pysptools.spectro import FeaturesConvexHullQuotient, SpectrumConvexHullQuotient
    from tqdm import tqdm

    matplotlib.use("agg")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    _logger = logging.getLogger(__name__)

    THRESHOLDS = (
        ("peak-1", (5500, 8000)),
        ("peak-2", (4600, 5540)),
        ("peak-3", (4310, 4788)),
    )

    AXIS_LABELS = {
        "original": ("Wavelength (nm)", "Reflectance (%)"),
        "continuum_removed": ("Wavelength (nm)", "Continuum removed reflectance"),
    }

    class CustomFeaturesConvexHullQuotient(FeaturesConvexHullQuotient):
        """
        Custom implementation of FeaturesConvexHullQuotient with additional functionality.
        """
        def _area(self, y):
            from scipy.integrate import trapezoid
            # Before the integration:
            # flip the crs curve to x axis
            # and start at y=0
            yy = [abs(p - 1) for p in y]
            deltax = self.wvl[1] - self.wvl[0]
            area = trapezoid(yy, dx=deltax)
            return area



    class Settings:
        def __init__(self):
            self.INPUT_PATH = Path()
            self.OUTPUT_PATH = Path()

        def configure(self, project_directory, input_folder="input", output_folder="output"):
            project_dir = Path(project_directory).expanduser().resolve()
            self.INPUT_PATH = project_dir / input_folder
            self.OUTPUT_PATH = project_dir / output_folder

        def _validate(self):
            pass

    settings = Settings()

    def _save_fig(fig_id, tight_layout=True, fig_extension="png", resolution=300):
        path = os.path.join(settings.OUTPUT_PATH / "plots", fig_id + "." + fig_extension)
        if tight_layout:
            plt.tight_layout()
        plt.savefig(path, format=fig_extension, dpi=resolution)

    def _get_files(path):
        _files = []
        for file in os.listdir(path):
            if not file.startswith(".~lock."):
                _files.append(file)
        return _files

    def _cleanup(path):
        if path.exists():
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    _logger.error(f"Failed to delete {file_path}. Reason: {e}")
        else:
            _logger.warning(f"Path {path} does not exist. Cannot delete.")

    def generate_spectra(thresholds=None):
        if thresholds is None:
            thresholds = THRESHOLDS

        _path = settings.INPUT_PATH
        _filenames = [f for f in _get_files(_path) if f.endswith(".csv") or f.endswith(".CSV")]

        for _filename in tqdm(_filenames, desc="Generating spectra", unit="file"):
            _df = pd.read_csv(os.path.join(_path, _filename))
            _df = _df.rename(columns={_df.columns[0]: "wavelength", _df.columns[1]: "reflectance"})
            _df = _df[["wavelength", "reflectance"]]
            _df = _df.apply(pd.to_numeric, errors="coerce")
            _df = _df.dropna()

            for _threshold, _limits in thresholds:
                _peak_filename = f'{_filename.split(".")[0]}-{_threshold}'
                _df_peak = _df.loc[(_df["wavelength"] >= _limits[0]) & (_df["wavelength"] <= _limits[1])]
                _df_peak = _df_peak.reset_index(drop=True)
                _df_peak.rename(columns={"wavelength": "Wavelength", "reflectance": _peak_filename}, inplace=True)
                _df_peak.to_csv(
                    os.path.join(settings.OUTPUT_PATH, "data", f"{_peak_filename}.txt"),
                    sep="\t",
                    index=False,
                    header=True,
                )

    def process_spectra(show_plots=True, axis_labels=None):
        if axis_labels is None:
            axis_labels = AXIS_LABELS
        _data_path = settings.OUTPUT_PATH / "data"
        _plots_path = settings.OUTPUT_PATH / "plots"

        os.makedirs(_plots_path, exist_ok=True)

        spectra_paths = [
            os.path.join(_data_path, f)
            for f in os.listdir(_data_path)
            if os.path.isfile(os.path.join(_data_path, f))
        ]
        spectra_paths.sort()

        if not spectra_paths:
            _logger.error(f"No files found in {_data_path}")
            return

        names = [os.path.splitext(os.path.basename(x))[0] for x in spectra_paths]

        _logger.info(f"Found {len(names)} spectra files.")

        spectra = {}

        for i in tqdm(range(len(names)), desc="Reading spectra files", unit="file"):
            try:
                spectra[names[i]] = pd.read_table(spectra_paths[i], sep="\t", names=("Wvl", "Reflect. %"), skiprows=1)
            except Exception as e:
                _logger.error(f"Error reading file {spectra_paths[i]}: {str(e)}")
                continue

        for key, value in tqdm(spectra.items(), desc="Plotting original spectra", unit="plot"):
            plt.figure()
            ax = plt.gca()
            spectra[key].plot(kind="line", x="Wvl", y="Reflect. %", ax=ax)
            plt.xlabel(axis_labels["original"][0], fontsize=14)
            plt.xticks(size=14)
            plt.ylabel(axis_labels["original"][1], fontsize=14)
            plt.yticks(size=14)
            plt.title(key, fontsize=16, pad=10)
            ax.get_legend().remove()
            if show_plots:
                plt.show()
            _save_fig(key)
            if show_plots:
                plt.pause(1)
            plt.close()

        params = {
            "legend.fontsize": "xx-large",
            "lines.linewidth": 3,
            "lines.markersize": 13,
            "figure.figsize": (14, 11),
            "figure.dpi": 300,
            "figure.titlesize": "xx-large",
            "axes.labelsize": "xx-large",
            "axes.titlesize": "xx-large",
            "axes.labelpad": 15,
            "axes.titlepad": 15,
            "xtick.labelsize": "x-large",
            "ytick.labelsize": "x-large",
        }
        plt.rcParams.update(params)

        for key, value in tqdm(spectra.items(), desc="Extracting features", unit="spectrum"):
            pixel = value["Reflect. %"]
            wvl = value["Wvl"]
            spectrum = pixel.tolist()
            wvl_list = wvl.tolist()
            try:
                spectra_features = CustomFeaturesConvexHullQuotient(spectrum=spectrum, wvl=wvl_list, baseline=0.99)
                spectra_features.plot(path=_plots_path, plot_name=key, feature="all")
            except Exception as e:
                _logger.error(f"Error extracting features for {key}: {str(e)}")

        _full_data = pd.DataFrame()

        for key, value in tqdm(spectra.items(), desc="Generating statistics", unit="spectrum"):
            try:
                pixel = value["Reflect. %"]
                pixel = pixel / 100
                wvl = value["Wvl"]
                spectrum = pixel.tolist()
                wvl_list = wvl.tolist()
                spectra_features = CustomFeaturesConvexHullQuotient(spectrum=spectrum, wvl=wvl_list, baseline=0.99)
                b = spectra_features.features_all
                b_stats = pd.DataFrame(b)
                is_keep = b_stats["state"] == "keep"
                b_stats_keep = b_stats[is_keep]
                csv_path = os.path.join(_data_path, key + ".csv")
                b_stats_keep.to_csv(csv_path, sep=",", index=False)

                _data = b_stats_keep.loc[:]
                _data["filename"] = key
                _data["peak"] = key.split("-peak-")[-1]
                _data["hx_1"] = _data["hx"].apply(lambda x: x[0] if x is not None else None)
                _data["hx_2"] = _data["hx"].apply(lambda x: x[1] if x is not None else None)
                _data["hy_1"] = _data["hy"].apply(lambda x: x[0] if x is not None else None)
                _data["hy_2"] = _data["hy"].apply(lambda x: x[1] if x is not None else None)
                _data["FWHM_x_1"] = _data["FWHM_x"].apply(lambda x: x[0] if x is not None else None)
                _data["FWHM_x_2"] = _data["FWHM_x"].apply(lambda x: x[1] if x is not None else None)
                _data["FWHM_y"] = _data["FWHM_y"].apply(lambda x: x[0] if x is not None else None)

                _data["FW"] = _data["cstop_wvl"] - _data["cstart_wvl"]
                _data["FW_left_width"] = _data["abs_wvl"] - _data["cstart_wvl"]
                _data["FW_right_width"] = _data["cstop_wvl"] - _data["abs_wvl"]
                _data["FW_assymetry"] = _data["FW_left_width"] / _data["FW_right_width"]

                _data["FWHM_left_width"] = _data["abs_wvl"] - _data["FWHM_x_1"]
                _data["FWHM_right_width"] = _data["FWHM_x_2"] - _data["abs_wvl"]
                _data["FWHM_assymetry"] = _data["FWHM_left_width"] / _data["FWHM_right_width"]

                _data["D"] = 1 - _data["abs_depth"]
                _data["E"] = _data["FW"] / _data["D"]
                _data["E*"] = _data["FWHM_delta"] / _data["D"]

                _data.drop(
                    columns=["seq", "id", "state", "spectrum", "wvl", "crs", "hx", "hy", "FWHM_x"], inplace=True
                )
                _full_data = pd.concat([_full_data, _data], axis=0)
            except Exception as e:
                _logger.error(f"Error generating statistics for {key}: {str(e)}")

        if not _full_data.empty:
            cols = _full_data.columns.tolist()
            cols.insert(0, cols.pop(cols.index("peak")))
            cols.insert(1, cols.pop(cols.index("filename")))
            _full_data = _full_data[cols]
        _full_data.to_excel(os.path.join(_data_path, "results.xlsx"), index=False)

        plt.rcParams.update(plt.rcParamsDefault)
        for key, value in tqdm(spectra.items(), desc="Exporting continuum removed spectra", unit="spectrum"):
            try:
                pixel = value["Reflect. %"]
                pixel = pixel / 100
                wvl = value["Wvl"]
                spectrum = pixel.tolist()
                wvl_list = wvl.tolist()
                spectra_remov = SpectrumConvexHullQuotient(spectrum=spectrum, wvl=wvl_list)
                conti_rem = spectra_remov.get_continuum_removed_spectrum()
                cont_corr = pd.DataFrame({"Reflectance": conti_rem})
                cont_corr.insert(0, "Wvl", wvl)
                cont_corr["Wvl"] = wvl
                txt_path = os.path.join(_data_path, key + "_continuum_corr_spectra.txt")
                cont_corr.to_csv(txt_path, sep="\t", index=False, header=False)

                plt.figure()
                ax = plt.gca()
                cont_corr.plot(kind="line", color="g", x="Wvl", y="Reflectance", ax=ax)
                plt.xlabel(axis_labels["continuum_removed"][0], fontsize=14)
                plt.xticks(size=14)
                plt.ylabel(axis_labels["continuum_removed"][1], fontsize=14)
                plt.yticks(size=14)
                plt.title(key, fontsize=16, pad=10)
                ax.get_legend().remove()
                if show_plots:
                    plt.show()
                _save_fig(key + "_continuum_removed")
                if show_plots:
                    plt.pause(1)
                plt.close()
            except Exception as e:
                _logger.error(f"Error exporting continuum removed spectrum for {key}: {str(e)}")

        return spectra

    def run_pipeline(show_plots=True, thresholds=None, axis_labels=None):
        _logger.info("Starting NIR spectra processing")
        _cleanup(settings.OUTPUT_PATH / "data")
        _cleanup(settings.OUTPUT_PATH / "plots")
        generate_spectra(thresholds=thresholds)
        process_spectra(show_plots=show_plots, axis_labels=axis_labels)
        _logger.info("Processing completed successfully")

    return os, run_pipeline, settings, tempfile


@app.cell
def _(os, settings, tempfile):
    _tmpdir = tempfile.mkdtemp(prefix="spx_")
    INPUT_DIR = os.path.join(_tmpdir, "input")
    OUTPUT_DIR = os.path.join(_tmpdir, "output")

    os.makedirs(INPUT_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    settings.configure(_tmpdir, "input", "output")

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
    import zipfile as _zipfile
    from io import BytesIO as _BytesIO
    from pathlib import Path as _Path

    import pandas as _pd

    mo.stop(not pipeline_done)

    _results_path = output_path / "data" / "results.xlsx"
    _plots_dir = output_path / "plots"
    _data_dir = output_path / "data"

    _elements = []

    # Zip the entire output folder
    _zip_buf = _BytesIO()
    with _zipfile.ZipFile(_zip_buf, "w", _zipfile.ZIP_DEFLATED) as _zf:
        for _f in sorted(_Path(output_path).rglob("*")):
            if _f.is_file():
                _zf.write(_f, _f.relative_to(output_path))
    _zip_buf.seek(0)
    _elements.append(mo.download(data=_zip_buf.getvalue(), filename="spx_results.zip", label="Download all results (.zip)"))

    # Results table
    if _results_path.exists():
        _df = _pd.read_excel(_results_path)
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
