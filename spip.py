import os
import sys
import subprocess
import threading
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QWidget, QHBoxLayout, QMessageBox, QProgressBar, QHeaderView,
    QFileDialog, QTextEdit, QListWidget, QInputDialog, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
import requests
from bs4 import BeautifulSoup  # For parsing HTML in fetch_all_packages
import importlib
import re

# === CONSOLE LOADING SCREEN ===
def show_console_loading_screen():
    global spinning  # Declare 'spinning' as global at the beginning
    ascii_text = r"""
 ____                        ____ ___ ____  
/ ___| _   _ _ __   ___ _ __|  _ \_ _|  _ \ 
\___ \| | | | '_ \ / _ \ '__| |_) | || |_) |
 ___) | |_| | |_) |  __/ |  |  __/| ||  __/ 
|____/ \__,_| .__/ \___|_|  |_|  |___|_|    
            |_|                             
Loading...
"""
    print(ascii_text)
    
    spinner = ['|', '/', '-', '\\']
    spinning = True  # Start the spinner

    def spin():
        global spinning
        i = 0
        while spinning:
            sys.stdout.write(f"\rPlease wait... {spinner[i % len(spinner)]}")
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    spinner_thread = threading.Thread(target=spin)
    spinner_thread.start()

    # Return a callback that stops the spinner when called.
    def finish_loading():
        global spinning
        spinning = False
        spinner_thread.join()
        print("\rLoading complete!")
        print("Welcome to the Python Library Downloader!")
    return finish_loading

# === Detect Python Versions ===
def detect_python_versions():
    """Detect installed Python versions."""
    common_paths = [
        "C:/Python",
        "C:/Program Files/Python",
        "C:/Program Files (x86)/Python",
        os.path.expanduser("~") + "/AppData/Local/Programs/Python",
        "/usr/bin",
        "/usr/local/bin",
    ]
    python_versions = {}
    for path in common_paths:
        if os.path.exists(path):
            for folder in os.listdir(path):
                python_exec = ""
                if sys.platform == "win32":
                    python_exec = os.path.join(path, folder, "python.exe")
                else:
                    python_exec = os.path.join(path, folder, "python3")
                if os.path.exists(python_exec):
                    try:
                        version = subprocess.check_output(
                            [python_exec, "--version"], text=True, stderr=subprocess.STDOUT
                        ).strip()
                        python_versions[version] = python_exec
                    except subprocess.CalledProcessError:
                        pass
    return python_versions

# === Package Fetching ===
def fetch_curated_packages():
    """Fetch a curated list of popular packages with module-package mapping."""
    curated_packages = {
        # Data Science & Machine Learning
        "numpy": "numpy",
        "pandas": "pandas",
        "matplotlib": "matplotlib",
        "scipy": "scipy",
        "sklearn": "scikit-learn",
        "tensorflow": "tensorflow",
        "keras": "keras",
        "torch": "torch",
        "xgboost": "xgboost",
        "lightgbm": "lightgbm",
        "statsmodels": "statsmodels",
        "seaborn": "seaborn",

        # Web Development
        "flask": "flask",
        "django": "django",
        "fastapi": "fastapi",
        "requests": "requests",
        "bs4": "beautifulsoup4",
        "aiohttp": "aiohttp",
        "urllib3": "urllib3",
        "tornado": "tornado",
        "bottle": "bottle",
        "werkzeug": "werkzeug",

        # Database Interaction
        "sqlalchemy": "sqlalchemy",
        "pymysql": "pymysql",
        "psycopg2": "psycopg2",
        "redis": "redis",
        "pymongo": "pymongo",

        # Visualization
        "plotly": "plotly",
        "dash": "dash",
        "bokeh": "bokeh",
        "pil": "pillow",

        # OpenAI and Related Packages
        "openai": "openai",
        "transformers": "transformers",
        "datasets": "datasets",
        "sentencepiece": "sentencepiece",

        # Utilities and Other Common Tools
        "pytest": "pytest",
        "black": "black",
        "flake8": "flake8",
        "mypy": "mypy",
        "virtualenv": "virtualenv",
        "pipenv": "pipenv",
        "pytest_cov": "pytest-cov",
        "tox": "tox",
        "invoke": "invoke",
        "pre_commit": "pre-commit",

        # Computer Vision
        "cv2": "opencv-python",
        "imageio": "imageio",
        "mediapipe": "mediapipe",
        "dlib": "dlib",

        # GUI Development
        "pyqt5": "pyqt5",
        "tkinter": "tkinter",
        "kivy": "kivy",

        # NLP and Text Processing
        "spacy": "spacy",
        "nltk": "nltk",
        "gensim": "gensim",
        "textblob": "textblob",

        # Cloud Services
        "boto3": "boto3",
        "google_cloud_storage": "google-cloud-storage",
        "azure_storage_blob": "azure-storage-blob",

        # Asynchronous Programming
        "asyncio": "asyncio",
        "trio": "trio",

        # File Handling and Compression
        "yaml": "pyyaml",
        "h5py": "h5py",
        "zlib": "zlib",
        "gzip": "gzip",

        # Security and Encryption
        "cryptography": "cryptography",
        "paramiko": "paramiko",

        # Development and Scripting Tools
        "click": "click",
        "argparse": "argparse",
        "typer": "typer",

        # HTTP Clients and REST APIs
        "httpx": "httpx",
        "requests_html": "requests-html",

        # Job Scheduling
        "apscheduler": "apscheduler",
        "schedule": "schedule",

        # Data Serialization
        "jsonschema": "jsonschema",
        "msgpack": "msgpack",
        "protobuf": "protobuf",

        # Audio Processing
        "pydub": "pydub",
        "librosa": "librosa",

        # Shell Automation
        "shutil": "shutil",
        "pathlib": "pathlib",

        # Configuration Management
        "dotenv": "python-dotenv",

        # Messaging and APIs
        "twilio": "twilio",
        "slack_sdk": "slack_sdk",

        # Others
        "pydantic": "pydantic",
        "tabulate": "tabulate",
        "rich": "rich",
        "colorama": "colorama",
        "pynput": "pynput"
    }
    return curated_packages

def fetch_all_packages():
    """Fetch all available packages from PyPI Simple with module-package mapping."""
    try:
        response = requests.get("https://pypi.org/simple/")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            packages = {}
            for a in soup.find_all('a'):
                pkg = a.text
                module_name = pkg.split('.')[0].lower()
                packages[module_name] = pkg
            return packages
        else:
            return {}
    except Exception:
        return {}

# === Module Checker Thread ===
class ModuleCheckerThread(QThread):
    missing_modules_signal = pyqtSignal(list)
    all_modules_installed_signal = pyqtSignal()
    progress_signal = pyqtSignal(int)

    def __init__(self, imports_text, module_to_package, python_exec, total_modules):
        super().__init__()
        self.imports_text = imports_text
        self.module_to_package = module_to_package
        self.python_exec = python_exec
        self.total_modules = total_modules

    def run(self):
        module_names = self.parse_imports(self.imports_text)
        missing_modules = []
        processed = 0
        for module in module_names:
            if not self.is_module_installed(module):
                missing_modules.append(module)
            processed += 1
            progress = int((processed / self.total_modules) * 100)
            self.progress_signal.emit(progress)
        if missing_modules:
            self.missing_modules_signal.emit(missing_modules)
        else:
            self.all_modules_installed_signal.emit()

    def parse_imports(self, imports_text):
        import_statements = imports_text.strip().split('\n')
        module_names = set()
        for line in import_statements:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if line.startswith('import '):
                imports = line[7:].split(',')
                for mod in imports:
                    mod = mod.strip().split(' as ')[0].split('.')[0]
                    module_names.add(mod)
            elif line.startswith('from '):
                match = re.match(r'from\s+(\S+)\s+import', line)
                if match:
                    mod = match.group(1).split('.')[0]
                    module_names.add(mod)
        return module_names

    def is_module_installed(self, module_name):
        try:
            subprocess.check_output([self.python_exec, '-c', f'import {module_name}'], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False

# === Main GUI Application ===
class LibraryDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Library Downloader")
        self.setGeometry(100, 100, 900, 700)

        # Main layout with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab 1: Library Downloader
        self.tab1 = QWidget()
        self.tabs.addTab(self.tab1, "Library Downloader")
        self.init_tab1()

        # Tab 2: Module Checker
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2, "Module Checker")
        self.init_tab2()
      #  self.check_python_installations()

        # (Animation tab removed; now we print in console instead.)

    def init_tab1(self):
        main_layout = QVBoxLayout()
        search_layout = QHBoxLayout()
        install_layout = QHBoxLayout()
        python_layout = QHBoxLayout()

        # Search Section
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search for a library...")
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_library)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)

        # Filter Dropdown
        self.filter_dropdown = QComboBox()
        self.filter_dropdown.addItems(["Popular Libraries", "All Libraries"])
        self.filter_dropdown.currentTextChanged.connect(self.apply_filter)

        # Python Installation Selection Dropdown
        self.python_dropdown = QComboBox()
        self.python_dropdown.addItem("Select Installation")
        self.python_dropdown.setEnabled(False)
        self.python_dropdown.currentIndexChanged.connect(self.on_python_selection_change)

        # Check Python Installations Button
      #  self.check_installs_button = QPushButton("Check Python Installations")
      #  self.check_installs_button.clicked.connect(self.check_python_installations)

        # View Installed Libraries Button
        self.view_installed_button = QPushButton("View Installed Libraries")
        self.view_installed_button.setEnabled(False)
        self.view_installed_button.clicked.connect(self.view_installed_libraries)

     #   python_layout.addWidget(self.check_installs_button)
        python_layout.addWidget(self.python_dropdown)
        python_layout.addWidget(self.view_installed_button)

        # Table for Listing Libraries
        self.library_table = QTableWidget()
        self.library_table.setColumnCount(2)
        self.library_table.setHorizontalHeaderLabels(["Library Name", "Install Command"])
        self.library_table.setColumnWidth(0, 500)
        self.library_table.setColumnWidth(1, 300)
        self.library_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.library_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.library_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.library_table.verticalScrollBar().valueChanged.connect(self.on_scroll)

        # Install Button
        self.install_button = QPushButton("Install Selected")
        self.install_button.clicked.connect(self.install_selected_library)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        install_layout.addWidget(self.install_button)
        install_layout.addWidget(self.progress_bar)

        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.filter_dropdown)
        main_layout.addLayout(python_layout)
        main_layout.addWidget(self.library_table)
        main_layout.addLayout(install_layout)
        self.tab1.setLayout(main_layout)

        # Load packages
        self.curated_packages = fetch_curated_packages()
        self.all_packages = fetch_all_packages()
        self.module_to_package = self.curated_packages.copy()
        for mod, pkg in self.all_packages.items():
            if mod not in self.module_to_package:
                self.module_to_package[mod] = pkg

        self.current_package_list = []
        self.current_display_list = []
        self.search_active = False
        self.load_limit = 1000
        self.current_index = 0
        self.populate_initial_packages()

    def init_tab2(self):
        layout = QVBoxLayout()
        python_selection_layout = QHBoxLayout()
        python_label = QLabel("Select Python Installation:")
        self.module_checker_python_dropdown = QComboBox()
        self.module_checker_python_dropdown.setEnabled(False)
        python_selection_layout.addWidget(python_label)
        python_selection_layout.addWidget(self.module_checker_python_dropdown)
        layout.addLayout(python_selection_layout)

        instructions = QLabel("Paste your import statements below and click 'Check Modules'.")
        layout.addWidget(instructions)

        self.imports_text_edit = QTextEdit()
        self.imports_text_edit.setPlaceholderText("Enter import statements here...")
        layout.addWidget(self.imports_text_edit)

        self.check_modules_button = QPushButton("Check Modules")
        self.check_modules_button.clicked.connect(self.process_imports)
        layout.addWidget(self.check_modules_button)

        self.module_checker_progress_bar = QProgressBar()
        self.module_checker_progress_bar.setValue(0)
        self.module_checker_progress_bar.setVisible(False)
        layout.addWidget(self.module_checker_progress_bar)

        self.missing_modules_list = QListWidget()
        layout.addWidget(self.missing_modules_list)
        self.tab2.setLayout(layout)

       # self.populate_module_checker_python_dropdown()

    def populate_module_checker_python_dropdown(self):
        self.module_checker_python_dropdown.setEnabled(True)
        self.module_checker_python_dropdown.clear()
        self.module_checker_python_dropdown.addItem("Select Installation")
        for version, exec_path in self.python_versions.items():
            self.module_checker_python_dropdown.addItem(f"{version} - {exec_path}", exec_path)
        self.module_checker_python_dropdown.addItem("Install to All Python Installations", "all")
        self.module_checker_python_dropdown.addItem("Install to Custom Directory", "custom")

    # === Module Checker Methods ===
    def process_imports(self):
        imports_text = self.imports_text_edit.toPlainText()
        if not imports_text.strip():
            QMessageBox.warning(self, "Error", "Please enter import statements.")
            return

        selected_index = self.module_checker_python_dropdown.currentIndex()
        selected_data = self.module_checker_python_dropdown.currentData()

        if selected_index == 0:
            QMessageBox.warning(self, "Error", "Please select a Python installation from the dropdown.")
            return

        if selected_data in ("all", "custom"):
            QMessageBox.warning(self, "Error", "Please select a specific Python installation to check modules.")
            return
        else:
            python_exec = selected_data

        self.selected_module_checker_python_exec = python_exec
        self.check_modules_button.setEnabled(False)
        self.missing_modules_list.clear()
        self.module_checker_progress_bar.setValue(0)
        self.module_checker_progress_bar.setVisible(True)

        self.module_checker_thread = ModuleCheckerThread(
            imports_text,
            self.module_to_package,
            python_exec,
            self.count_total_modules(imports_text)
        )
        self.module_checker_thread.missing_modules_signal.connect(self.handle_missing_modules)
        self.module_checker_thread.all_modules_installed_signal.connect(self.handle_all_modules_installed)
        self.module_checker_thread.progress_signal.connect(self.update_module_checker_progress)
        self.module_checker_thread.start()

    def count_total_modules(self, imports_text):
        import_statements = imports_text.strip().split('\n')
        module_names = set()
        for line in import_statements:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            if line.startswith('import '):
                imports = line[7:].split(',')
                for mod in imports:
                    mod = mod.strip().split(' as ')[0].split('.')[0]
                    module_names.add(mod)
            elif line.startswith('from '):
                match = re.match(r'from\s+(\S+)\s+import', line)
                if match:
                    mod = match.group(1).split('.')[0]
                    module_names.add(mod)
        return len(module_names)

    def handle_missing_modules(self, missing_modules):
        for module in missing_modules:
            pip_package = self.module_to_package.get(module.lower(), module)
            reply = QMessageBox.question(
                self, "Install Module",
                f"The module '{module}' is not installed in the selected Python installation.\nWould you like to install the package '{pip_package}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.install_module(pip_package, module, self.selected_module_checker_python_exec)
            status = "Installed" if self.is_module_installed(module, self.selected_module_checker_python_exec) else "Not Installed"
            self.missing_modules_list.addItem(f"{module} - {status}")
        self.check_modules_button.setEnabled(True)
        self.module_checker_progress_bar.setVisible(False)

    def handle_all_modules_installed(self):
        QMessageBox.information(self, "All Modules Installed", "All modules are already installed.")
        self.check_modules_button.setEnabled(True)
        self.module_checker_progress_bar.setVisible(False)

    def install_module(self, package_name, module_name, python_exec):
        try:
            subprocess.check_call([python_exec, '-m', 'pip', 'install', package_name])
            QMessageBox.information(self, "Success", f"Module '{module_name}' (package '{package_name}') installed successfully.")
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", f"Failed to install module '{module_name}' (package '{package_name}').")

    def is_module_installed(self, module_name, python_exec):
        try:
            subprocess.check_output([python_exec, '-c', f'import {module_name}'], stderr=subprocess.STDOUT)
            return True
        except subprocess.CalledProcessError:
            return False

    def update_module_checker_progress(self, progress):
        self.module_checker_progress_bar.setValue(progress)

    # === Library Downloader Methods ===
    def populate_initial_packages(self):
        filter_choice = self.filter_dropdown.currentText()
        if filter_choice == "Popular Libraries":
            self.current_package_list = list(self.curated_packages.keys())
        else:
            self.current_package_list = list(self.all_packages.keys())
        self.current_display_list = []
        self.current_index = 0
        self.library_table.setRowCount(0)
        self.load_more_packages()

    def load_more_packages(self):
        if self.current_index >= len(self.current_package_list):
            return
        next_index = min(self.current_index + self.load_limit, len(self.current_package_list))
        packages_to_load = self.current_package_list[self.current_index:next_index]
        self.current_display_list.extend(packages_to_load)
        for pkg_module in packages_to_load:
            pip_package = self.module_to_package.get(pkg_module.lower(), pkg_module)
            row_position = self.library_table.rowCount()
            self.library_table.insertRow(row_position)
            self.library_table.setItem(row_position, 0, QTableWidgetItem(pip_package))
            self.library_table.setItem(row_position, 1, QTableWidgetItem(f"pip install {pip_package}"))
        self.current_index = next_index

    def on_scroll(self, value):
        scrollbar = self.library_table.verticalScrollBar()
        if value == scrollbar.maximum() and not self.search_active:
            self.load_more_packages()

    def apply_filter(self):
        self.search_active = False
        self.search_input.clear()
        self.populate_initial_packages()

    def search_library(self):
        query = self.search_input.text().strip().lower()
        if not query:
            QMessageBox.warning(self, "Error", "Please enter a search query.")
            return
        filter_choice = self.filter_dropdown.currentText()
        if filter_choice == "Popular Libraries":
            search_list = self.curated_packages.keys()
        else:
            search_list = self.all_packages.keys()
        results = [pkg_module for pkg_module in search_list if query in pkg_module.lower()]
        if not results:
            QMessageBox.information(self, "No Results", f"No libraries found matching '{query}'.")
            self.library_table.setRowCount(0)
            self.current_display_list = []
            self.current_package_list = []
            self.search_active = True
            return
        self.current_package_list = results
        self.current_display_list = []
        self.current_index = 0
        self.library_table.setRowCount(0)
        self.load_more_packages()
        self.search_active = True

    def check_python_installations(self):
        self.python_versions = detect_python_versions()
        if not self.python_versions:
            QMessageBox.warning(self, "Error", "No Python installations found.")
            self.python_dropdown.clear()
            self.python_dropdown.addItem("No Python installations detected.")
            self.python_dropdown.setEnabled(False)
            self.view_installed_button.setEnabled(False)
            if hasattr(self, 'module_checker_python_dropdown'):
                self.module_checker_python_dropdown.clear()
                self.module_checker_python_dropdown.setEnabled(False)
            return
        self.python_dropdown.setEnabled(True)
        self.python_dropdown.clear()
        self.python_dropdown.addItem("Select Installation")
        for version, exec_path in self.python_versions.items():
            self.python_dropdown.addItem(f"{version} - {exec_path}", exec_path)
        self.python_dropdown.addItem("Install to All Python Installations", "all")
        self.python_dropdown.addItem("Install to Custom Directory", "custom")
        if hasattr(self, 'module_checker_python_dropdown'):
            self.populate_module_checker_python_dropdown()
        self.view_installed_button.setEnabled(True)
        if hasattr(self, 'finish_loading'):
            self.finish_loading()
      #  QMessageBox.information(self, "Python Installations", "Python installations have been detected and listed.")

    def on_python_selection_change(self):
        selected_option = self.python_dropdown.currentText()
        if selected_option == "Install to Custom Directory":
            custom_dir = QFileDialog.getExistingDirectory(self, "Select Installation Directory", "")
            if custom_dir:
                self.python_dropdown.setItemText(self.python_dropdown.currentIndex(), f"Custom Directory: {custom_dir}")
                self.python_dropdown.setCurrentText(f"Custom Directory: {custom_dir}")
            else:
                self.python_dropdown.setCurrentIndex(0)

    def install_selected_library(self):
        selected_items = self.library_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a library to install.")
            return
        selected_library = selected_items[0].text()
        selected_python = self.python_dropdown.currentData()
        selected_option = self.python_dropdown.currentText()
        if not selected_python or selected_python == "Select Installation":
            QMessageBox.warning(self, "Error", "Please select a valid Python installation from the dropdown.")
            return
        install_targets = []
        if selected_option == "Install to All Python Installations":
            if not self.python_versions:
                QMessageBox.warning(self, "Error", "No Python installations found.")
                return
            install_targets = list(self.python_versions.values())
        elif selected_option.startswith("Custom Directory:"):
            custom_dir = selected_option.split("Custom Directory: ")[1]
            install_targets = [f"custom:{custom_dir}"]
        else:
            install_targets = [selected_python]

        self.install_button.setEnabled(False)
        self.check_installs_button.setEnabled(False)
        self.view_installed_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(install_targets))
        self.progress_bar.setValue(0)
        errors = []
        for idx, target in enumerate(install_targets, start=1):
            if target.startswith("custom:"):
                custom_path = target.split("custom:")[1]
                cmd = [sys.executable, "-m", "pip", "install", selected_library, "--target", custom_path]
            else:
                cmd = [target, "-m", "pip", "install", selected_library]
            try:
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                errors.append(f"Failed to install to {target}: {e}")
            self.progress_bar.setValue(idx)
            QApplication.processEvents()
        self.install_button.setEnabled(True)
        self.check_installs_button.setEnabled(True)
        self.view_installed_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        if errors:
            QMessageBox.critical(self, "Installation Errors", "\n".join(errors))
        else:
            QMessageBox.information(self, "Success", f"Successfully installed {selected_library}.")

    def view_installed_libraries(self):
        selected_python = self.python_dropdown.currentData()
        selected_option = self.python_dropdown.currentText()
        if not selected_python or selected_python == "Select Installation":
            QMessageBox.warning(self, "Error", "Please select a valid Python installation from the dropdown.")
            return
        if selected_option.startswith("Custom Directory:") or selected_option == "Install to All Python Installations":
            QMessageBox.warning(self, "Error", "Please select a single Python installation to view its libraries.")
            return
        try:
            result = subprocess.check_output([selected_python, "-m", "pip", "list", "--format=freeze"], text=True)
            self.show_installed_libraries_window(selected_option, result, selected_python)
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", f"Failed to retrieve installed libraries for {selected_option}.")

    def show_installed_libraries_window(self, python_version, library_list, python_exec):
        window = QWidget()
        window.setWindowTitle(f"Installed Libraries - {python_version}")
        layout = QVBoxLayout()

        # Create a list widget to show installed packages
        self.installed_list_widget = QListWidget()
        packages = library_list.strip().split('\n')
        for pkg_line in packages:
            self.installed_list_widget.addItem(pkg_line)
        layout.addWidget(self.installed_list_widget)

        # Uninstall Button
        uninstall_button = QPushButton("Uninstall Selected Package")
        uninstall_button.clicked.connect(lambda: self.uninstall_selected_package(python_exec))
        layout.addWidget(uninstall_button)

        window.setLayout(layout)
        window.resize(600, 400)
        window.show()
        self.installed_libs_window = window  # Keep a reference

    def uninstall_selected_package(self, python_exec):
        selected_items = self.installed_list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a package to uninstall.")
            return
        package_line = selected_items[0].text()
        package_name = package_line.split("==")[0]
        reply = QMessageBox.question(
            self, "Confirm Uninstall",
            f"Are you sure you want to uninstall '{package_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                subprocess.check_call([python_exec, "-m", "pip", "uninstall", package_name, "-y"])
                QMessageBox.information(self, "Success", f"'{package_name}' uninstalled successfully.")
                # Refresh the list widget
                self.refresh_installed_libraries(python_exec)
            except subprocess.CalledProcessError:
                QMessageBox.critical(self, "Error", f"Failed to uninstall '{package_name}'.")

    def refresh_installed_libraries(self, python_exec):
        try:
            result = subprocess.check_output([python_exec, "-m", "pip", "list", "--format=freeze"], text=True)
            self.installed_list_widget.clear()
            packages = result.strip().split('\n')
            for pkg_line in packages:
                self.installed_list_widget.addItem(pkg_line)
        except subprocess.CalledProcessError:
            QMessageBox.critical(self, "Error", "Failed to refresh installed libraries list.")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self, 'Exit',
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            event.accept()
        else:
            event.ignore()

# === Run the Application ===
if __name__ == "__main__":
    finish_loading = show_console_loading_screen()  # Start the spinner
    
    app = QApplication(sys.argv)
    main_window = LibraryDownloader()
    main_window.finish_loading = finish_loading  # Inject the callback
    
    # Now, manually call check_python_installations() after finish_loading is set.
    main_window.check_python_installations()
    
    # Delay showing the PyQt5 window by 1 second (1000 ms)
    QTimer.singleShot(1000, main_window.show)
    
    sys.exit(app.exec())