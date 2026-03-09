# -*- coding: UTF-8 -*-
import multiprocessing
multiprocessing.freeze_support()

import os
import sys

if sys.stdout is None:
	sys.stdout = open(os.devnull, "w")
if sys.stderr is None:
	sys.stderr = open(os.devnull, "w")

import matplotlib
matplotlib.use("Agg")

import datetime
import logging
import platform
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import ttk

from src import choices
from src.config import settings

logger = logging.getLogger(__name__)


class QueueHandler(logging.Handler):
	def __init__(self, log_queue):
		super().__init__()
		self.log_queue = log_queue

	def emit(self, record):
		self.log_queue.put(self.format(record))


class SPxApp:
	def __init__(self, root):
		self.root = root
		self.root.title("SPx — Spectral Processing")
		self.root.geometry("700x520")
		self.root.minsize(600, 450)

		self.log_queue = queue.Queue()
		self._thresholds = [[name, lo, hi] for name, (lo, hi) in choices.THRESHOLDS]
		self._setup_logging()
		self._build_ui()
		self._poll_log_queue()

	def _setup_logging(self):
		handler = QueueHandler(self.log_queue)
		handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))
		root_logger = logging.getLogger()
		root_logger.addHandler(handler)
		root_logger.setLevel(logging.INFO)

	def _build_ui(self):
		main = ttk.Frame(self.root, padding=12)
		main.pack(fill=tk.BOTH, expand=True)

		# Directory picker
		dir_frame = ttk.LabelFrame(main, text="Project Directory", padding=8)
		dir_frame.pack(fill=tk.X, pady=(0, 8))

		if getattr(sys, "frozen", False):
			default_dir = str(Path(sys._MEIPASS) / "data")
		else:
			default_dir = str(Path(__file__).resolve().parent.parent / "data")
		self.dir_var = tk.StringVar(value=default_dir)
		dir_entry = ttk.Entry(dir_frame, textvariable=self.dir_var)
		dir_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

		browse_btn = ttk.Button(dir_frame, text="Browse...", command=self._browse_directory)
		browse_btn.pack(side=tk.RIGHT)

		# Input/Output folder names
		folders_frame = ttk.Frame(main)
		folders_frame.pack(fill=tk.X, pady=(0, 8))

		ttk.Label(folders_frame, text="Input folder:").pack(side=tk.LEFT)
		self.input_var = tk.StringVar(value="samples")
		ttk.Entry(folders_frame, textvariable=self.input_var, width=14).pack(side=tk.LEFT, padx=(4, 12))

		ttk.Label(folders_frame, text="Output folder:").pack(side=tk.LEFT)
		self.output_var = tk.StringVar(value="output")
		ttk.Entry(folders_frame, textvariable=self.output_var, width=14).pack(side=tk.LEFT, padx=(4, 0))

		# Endmembers file picker
		endmembers_frame = ttk.LabelFrame(main, text="Endmembers File", padding=8)
		endmembers_frame.pack(fill=tk.X, pady=(0, 8))

		self.endmembers_var = tk.StringVar(value=str(settings.ENDMEMBERS_PATH))
		ttk.Entry(endmembers_frame, textvariable=self.endmembers_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
		ttk.Button(endmembers_frame, text="Browse...", command=self._browse_endmembers).pack(side=tk.RIGHT)

		# Edit buttons for thresholds
		edit_frame = ttk.Frame(main)
		edit_frame.pack(fill=tk.X, pady=(0, 8))

		ttk.Button(edit_frame, text="Edit Thresholds", command=self._open_thresholds_dialog).pack(side=tk.LEFT, padx=(0, 6))

		# Action buttons
		btn_frame = ttk.Frame(main)
		btn_frame.pack(fill=tk.X, pady=(0, 8))

		self.process_btn = ttk.Button(btn_frame, text="Process Spectra", command=self._run_process)
		self.process_btn.pack(side=tk.LEFT, padx=(0, 6))

		self.predict_btn = ttk.Button(btn_frame, text="Run Unmixing", command=self._run_predict)
		self.predict_btn.pack(side=tk.LEFT)

		# Progress bar
		self.progress = ttk.Progressbar(main, mode="indeterminate")
		self.progress.pack(fill=tk.X, pady=(0, 8))

		# Tabbed notebook for Log and Output Files
		self.notebook = ttk.Notebook(main)
		self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 8))

		# Tab 1: Log
		log_frame = ttk.Frame(self.notebook)
		self.notebook.add(log_frame, text="Log")

		self.log_text = scrolledtext.ScrolledText(log_frame, height=14, state=tk.DISABLED, wrap=tk.WORD)
		self.log_text.pack(fill=tk.BOTH, expand=True)

		# Tab 2: Output Files
		output_frame = ttk.Frame(self.notebook)
		self.notebook.add(output_frame, text="Output Files")
		self._build_file_explorer(output_frame)

		# Status bar
		status_frame = ttk.Frame(main)
		status_frame.pack(fill=tk.X)

		self.open_btn = ttk.Button(status_frame, text="Open Output Folder", command=self._open_output, state=tk.DISABLED)
		self.open_btn.pack(side=tk.LEFT)

		self.status_var = tk.StringVar(value="Ready")
		ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.RIGHT)

	def _build_file_explorer(self, parent):
		toolbar = ttk.Frame(parent)
		toolbar.pack(fill=tk.X, pady=(4, 2), padx=4)
		ttk.Button(toolbar, text="Refresh", command=self._refresh_file_explorer).pack(side=tk.LEFT)

		columns = ("size", "modified")
		self.file_tree = ttk.Treeview(parent, columns=columns, selectmode="browse")
		self.file_tree.heading("#0", text="Name", anchor=tk.W)
		self.file_tree.heading("size", text="Size", anchor=tk.E)
		self.file_tree.heading("modified", text="Modified", anchor=tk.W)
		self.file_tree.column("#0", width=300, minwidth=150)
		self.file_tree.column("size", width=80, minwidth=60, anchor=tk.E)
		self.file_tree.column("modified", width=140, minwidth=100)

		scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.file_tree.yview)
		self.file_tree.configure(yscrollcommand=scrollbar.set)

		self.file_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0), pady=(0, 4))
		scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=(0, 4), padx=(0, 4))

		self.file_tree.bind("<Double-1>", self._on_tree_double_click)

	def _refresh_file_explorer(self):
		self.file_tree.delete(*self.file_tree.get_children())

		try:
			output_path = Path(settings.OUTPUT_PATH)
		except Exception:
			return

		if not output_path.is_dir():
			return

		for subdir_name in ("data", "plots"):
			subdir = output_path / subdir_name
			if not subdir.is_dir():
				continue

			dir_node = self.file_tree.insert("", tk.END, text=subdir_name + "/", open=True, values=("", ""))
			for f in sorted(subdir.iterdir()):
				if f.is_file():
					stat = f.stat()
					size = self._format_size(stat.st_size)
					mtime = datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
					self.file_tree.insert(dir_node, tk.END, text=f.name, values=(size, mtime), tags=(str(f),))

	@staticmethod
	def _format_size(size_bytes):
		if size_bytes < 1024:
			return f"{size_bytes} B"
		elif size_bytes < 1024 * 1024:
			return f"{size_bytes / 1024:.1f} KB"
		else:
			return f"{size_bytes / (1024 * 1024):.1f} MB"

	def _on_tree_double_click(self, event):
		item = self.file_tree.focus()
		if not item:
			return
		tags = self.file_tree.item(item, "tags")
		if tags:
			self._open_file(tags[0])

	def _open_file(self, path):
		if platform.system() == "Darwin":
			subprocess.Popen(["open", path])
		elif platform.system() == "Windows":
			os.startfile(path)
		else:
			subprocess.Popen(["xdg-open", path])

	def _browse_directory(self):
		path = filedialog.askdirectory(title="Select Project Directory")
		if path:
			self.dir_var.set(path)

	def _configure_settings(self):
		project_dir = self.dir_var.get().strip()
		if not project_dir:
			self._log_message("ERROR: Please select a project directory.")
			return False

		try:
			settings.configure(project_dir, self.input_var.get().strip(), self.output_var.get().strip())
			return True
		except ValueError as e:
			self._log_message(f"ERROR: {e}")
			return False

	def _set_running(self, running):
		state = tk.DISABLED if running else tk.NORMAL
		self.process_btn.config(state=state)
		self.predict_btn.config(state=state)
		if running:
			self.progress.start(10)
		else:
			self.progress.stop()

	def _run_process(self):
		if not self._configure_settings():
			return

		self._set_running(True)
		self.status_var.set("Processing spectra...")

		thresholds = [(n, (lo, hi)) for n, lo, hi in self._thresholds]

		def task():
			try:
				from src.base.main import run_pipeline
				run_pipeline(show_plots=False, thresholds=thresholds)
				self.root.after(0, self._on_task_done, "Processing completed successfully.")
			except Exception as e:
				self.root.after(0, self._on_task_done, f"Processing failed: {e}")

		threading.Thread(target=task, daemon=True).start()

	def _run_predict(self):
		if not self._configure_settings():
			return

		self._set_running(True)
		self.status_var.set("Running unmixing...")

		endmembers_path = self.endmembers_var.get().strip()

		def task():
			try:
				from src.base.predict import run_prediction
				run_prediction(endmembers_path=Path(endmembers_path) if endmembers_path else None)
				self.root.after(0, self._on_task_done, "Unmixing completed successfully.")
			except Exception as e:
				self.root.after(0, self._on_task_done, f"Unmixing failed: {e}")

		threading.Thread(target=task, daemon=True).start()

	def _on_task_done(self, message):
		self._set_running(False)
		self.status_var.set(message)
		self.open_btn.config(state=tk.NORMAL)
		self._log_message(message)
		self._refresh_file_explorer()
		self.notebook.select(1)

	def _open_output(self):
		path = str(settings.OUTPUT_PATH)
		if platform.system() == "Darwin":
			subprocess.Popen(["open", path])
		elif platform.system() == "Windows":
			os.startfile(path)
		else:
			subprocess.Popen(["xdg-open", path])

	def _log_message(self, msg):
		self.log_text.config(state=tk.NORMAL)
		self.log_text.insert(tk.END, msg + "\n")
		self.log_text.see(tk.END)
		self.log_text.config(state=tk.DISABLED)

	def _poll_log_queue(self):
		while True:
			try:
				msg = self.log_queue.get_nowait()
				self._log_message(msg)
			except queue.Empty:
				break
		self.root.after(100, self._poll_log_queue)

	def _browse_endmembers(self):
		path = filedialog.askopenfilename(
			title="Select Endmembers File",
			filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
		)
		if path:
			self.endmembers_var.set(path)

	def _open_thresholds_dialog(self):
		ThresholdsDialog(self.root, self)


class ThresholdsDialog(tk.Toplevel):
	def __init__(self, parent, app):
		super().__init__(parent)
		self.app = app
		self.title("Edit Thresholds")
		self.geometry("480x400")
		self.resizable(True, True)
		self.grab_set()

		self._data = [row[:] for row in app._thresholds]
		self._selected_idx = None

		self._build_ui()
		self._refresh_tree()

	def _build_ui(self):
		# Treeview
		tree_frame = ttk.Frame(self)
		tree_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(8, 4))

		self.tree = ttk.Treeview(tree_frame, columns=("min", "max"), selectmode="browse")
		self.tree.heading("#0", text="Name", anchor=tk.W)
		self.tree.heading("min", text="Min (nm)", anchor=tk.E)
		self.tree.heading("max", text="Max (nm)", anchor=tk.E)
		self.tree.column("#0", width=160)
		self.tree.column("min", width=90, anchor=tk.E)
		self.tree.column("max", width=90, anchor=tk.E)

		sb = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
		self.tree.configure(yscrollcommand=sb.set)
		self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
		sb.pack(side=tk.RIGHT, fill=tk.Y)
		self.tree.bind("<<TreeviewSelect>>", self._on_select)

		# Edit / Add form
		form_frame = ttk.LabelFrame(self, text="Add / Edit Row", padding=6)
		form_frame.pack(fill=tk.X, padx=8, pady=4)

		ttk.Label(form_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=(0, 4))
		self._name_var = tk.StringVar()
		ttk.Entry(form_frame, textvariable=self._name_var, width=14).grid(row=0, column=1, padx=(0, 8))

		ttk.Label(form_frame, text="Min (nm):").grid(row=0, column=2, sticky=tk.W, padx=(0, 4))
		self._min_var = tk.StringVar()
		ttk.Entry(form_frame, textvariable=self._min_var, width=8).grid(row=0, column=3, padx=(0, 8))

		ttk.Label(form_frame, text="Max (nm):").grid(row=0, column=4, sticky=tk.W, padx=(0, 4))
		self._max_var = tk.StringVar()
		ttk.Entry(form_frame, textvariable=self._max_var, width=8).grid(row=0, column=5, padx=(0, 8))

		form_btns = ttk.Frame(form_frame)
		form_btns.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=(6, 0))
		ttk.Button(form_btns, text="Add New", command=self._add_row).pack(side=tk.LEFT, padx=(0, 6))
		ttk.Button(form_btns, text="Update Selected", command=self._update_selected).pack(side=tk.LEFT)

		# Bottom buttons
		btn_frame = ttk.Frame(self)
		btn_frame.pack(fill=tk.X, padx=8, pady=(4, 8))

		ttk.Button(btn_frame, text="Remove Selected", command=self._remove_selected).pack(side=tk.LEFT)
		ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side=tk.RIGHT)
		ttk.Button(btn_frame, text="Save", command=self._save).pack(side=tk.RIGHT, padx=(0, 6))

	def _refresh_tree(self):
		self.tree.delete(*self.tree.get_children())
		for row in self._data:
			self.tree.insert("", tk.END, text=row[0], values=(row[1], row[2]))

	def _on_select(self, _event=None):
		item = self.tree.focus()
		if not item:
			return
		self._selected_idx = self.tree.index(item)
		row = self._data[self._selected_idx]
		self._name_var.set(row[0])
		self._min_var.set(row[1])
		self._max_var.set(row[2])

	def _parse_form(self):
		name = self._name_var.get().strip()
		if not name:
			messagebox.showerror("Invalid input", "Name cannot be empty.", parent=self)
			return None
		try:
			lo = float(self._min_var.get())
			hi = float(self._max_var.get())
		except ValueError:
			messagebox.showerror("Invalid input", "Min and Max must be numbers.", parent=self)
			return None
		return [name, lo, hi]

	def _add_row(self):
		row = self._parse_form()
		if row is None:
			return
		self._data.append(row)
		self._refresh_tree()
		self._name_var.set("")
		self._min_var.set("")
		self._max_var.set("")

	def _update_selected(self):
		if self._selected_idx is None:
			messagebox.showinfo("No selection", "Select a row in the list first.", parent=self)
			return
		row = self._parse_form()
		if row is None:
			return
		self._data[self._selected_idx] = row
		self._refresh_tree()

	def _remove_selected(self):
		item = self.tree.focus()
		if not item:
			return
		idx = self.tree.index(item)
		del self._data[idx]
		self._selected_idx = None
		self._refresh_tree()

	def _save(self):
		self.app._thresholds = [row[:] for row in self._data]
		self.destroy()


def run():
	root = tk.Tk()
	SPxApp(root)
	root.mainloop()


if __name__ == "__main__":
	run()
