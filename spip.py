import os
import sys
import subprocess
import logging
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QComboBox,
    QWidget, QHBoxLayout, QMessageBox, QProgressBar, QHeaderView,
    QFileDialog, QTextEdit, QListWidget, QInputDialog, QTabWidget
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import requests
from bs4 import BeautifulSoup  # For parsing HTML in fetch_all_packages
import importlib
import re

# === Custom Memory Handler for Logging ===
class InMemoryLogHandler(logging.Handler):
    """Custom logging handler that stores log records in memory."""
    def __init__(self):
        super().__init__()
        self.log_records = []

    def emit(self, record):
        log_entry = self.format(record)
        self.log_records.append(log_entry)

    def get_logs(self):
        return "\n".join(self.log_records)

# === Detect Python Versions ===
def detect_python_versions():
    """Detect installed Python versions."""
    logging.info("Detecting Python installations...")
    common_paths = [
        # Add common paths where Python might be installed
        "C:/Python",
        "C:/Program Files/Python",
        "C:/Program Files (x86)/Python",
        os.path.expanduser("~") + "/AppData/Local/Programs/Python",  # For Windows users
        "/usr/bin",  # For Unix/Linux users
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
                        logging.info(f"Detected Python: {version} at {python_exec}")
                    except subprocess.CalledProcessError as e:
                        logging.warning(f"Error checking version for {python_exec}: {e}")
    return python_versions

# === Logging Setup ===
def setup_logging():
    """Set up logging with live console output and in-memory buffering."""
    root_dir = os.getcwd()
    existing_logs = [f for f in os.listdir(root_dir) if f.startswith("Log") and f.endswith(".log")]
    log_index = len(existing_logs) + 1
    current_time = datetime.now().strftime("%I-%M%p").lower().replace(":", "-")  # Changed format to avoid ':'
    log_filename = f"Log{log_index}.{current_time}.log"

    # Create in-memory log handler
    memory_handler = InMemoryLogHandler()
    memory_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    memory_handler.setFormatter(formatter)

    # Set up logging
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    # StreamHandler for console output
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)

    # Add handlers
    logger.addHandler(stream_handler)
    logger.addHandler(memory_handler)

    logging.info(f"Log initialized: {log_filename}")
    return memory_handler, log_filename

# === Package Fetching ===
def fetch_curated_packages():
    """Fetch a curated list of popular Python libraries with module-package mapping."""
    logging.info("Fetching curated list of popular packages...")
    # Dictionary mapping module names to pip package names
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
    logging.info(f"Loaded {len(curated_packages)} curated packages with module-package mapping.")
    return curated_packages

def fetch_all_packages():
    """Fetch all available packages from PyPI Simple with module-package mapping."""
    logging.info("Fetching all available packages from PyPI Simple...")
    try:
        response = requests.get("https://pypi.org/simple/")
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            packages = {}
            for a in soup.find_all('a'):
                pkg = a.text
                # Attempt to map module name to package name assuming they are the same
                # This might not always be accurate
                module_name = pkg.split('.')[0].lower()
                packages[module_name] = pkg
            logging.info(f"Retrieved {len(packages)} total packages with module-package mapping.")
            return packages
        else:
            logging.error(f"Failed to fetch PyPI Simple index: HTTP {response.status_code}")
            return {}
    except Exception as e:
        logging.error(f"Error fetching PyPI Simple index: {e}")
        return {}

# === Module Checker Thread ===
class ModuleCheckerThread(QThread):
    missing_modules_signal = pyqtSignal(list)
    all_modules_installed_signal = pyqtSignal()
    progress_signal = pyqtSignal(int)  # Added signal

    def __init__(self, imports_text, module_to_package, python_exec, total_modules):
        super().__init__()
        self.imports_text = imports_text
        self.module_to_package = module_to_package
        self.python_exec = python_exec
        self.total_modules = total_modules

    def run(self):
        logging.debug("Background thread started for processing import statements.")
        module_names = self.parse_imports(self.imports_text)
        missing_modules = []
        processed = 0
        for module in module_names:
            if not self.is_module_installed(module):
                missing_modules.append(module)
            processed += 1
            progress = int((processed / self.total_modules) * 100)
            self.progress_signal.emit(progress)  # Emit progress
        if missing_modules:
            self.missing_modules_signal.emit(missing_modules)
        else:
            self.all_modules_installed_signal.emit()
        logging.debug("Background thread finished processing import statements.")

    def parse_imports(self, imports_text):
        logging.debug("Parsing import statements.")
        import_statements = imports_text.strip().split('\n')
        module_names = set()
        for line in import_statements:
            line = line.strip()
            if line.startswith('#') or not line:
                continue  # Skip comments and empty lines
            if line.startswith('import '):
                # Handle 'import x', 'import x as y', 'import x, y', 'import x as y, z as w'
                imports = line[7:].split(',')
                for mod in imports:
                    mod = mod.strip()
                    mod = mod.split(' as ')[0].strip()
                    mod = mod.split('.')[0]  # Get the top-level module
                    module_names.add(mod)
                    logging.debug(f"Found module: {mod}")
            elif line.startswith('from '):
                # Handle 'from x import y'
                match = re.match(r'from\s+(\S+)\s+import', line)
                if match:
                    mod = match.group(1)
                    mod = mod.split('.')[0]
                    module_names.add(mod)
                    logging.debug(f"Found module: {mod}")
        return module_names

    def is_module_installed(self, module_name):
        try:
            subprocess.check_output([self.python_exec, '-c', f'import {module_name}'], stderr=subprocess.STDOUT)
            logging.debug(f"Module '{module_name}' is installed in {self.python_exec}.")
            return True
        except subprocess.CalledProcessError as e:
            logging.warning(f"Module '{module_name}' is not installed in {self.python_exec}. Output: {e.output}")
            return False

# === Main GUI Application ===
class LibraryDownloader(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("Initializing the GUI...")
        self.setWindowTitle("Python Library Downloader")
        self.setGeometry(100, 100, 900, 700)

        # Main layout with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # First tab: Library Downloader
        self.tab1 = QWidget()
        self.tabs.addTab(self.tab1, "Library Downloader")
        self.init_tab1()

        # Second tab: Module Checker
        self.tab2 = QWidget()
        self.tabs.addTab(self.tab2, "Module Checker")
        self.init_tab2()

        # Initialize in-memory log handler
        self.memory_handler, self.log_filename = setup_logging()

    def init_tab1(self):
        """Initialize the Library Downloader tab."""
        # Layouts
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
        self.python_dropdown.addItem("Select Installation")  # Initial label for the dropdown
        self.python_dropdown.setEnabled(False)  # Disabled until installations are checked
        self.python_dropdown.currentIndexChanged.connect(self.on_python_selection_change)

        # Check Python Installations Button
        self.check_installs_button = QPushButton("Check Python Installations")
        self.check_installs_button.clicked.connect(self.check_python_installations)

        # View Installed Libraries Button
        self.view_installed_button = QPushButton("View Installed Libraries")
        self.view_installed_button.setEnabled(False)  # Disabled until installations are checked
        self.view_installed_button.clicked.connect(self.view_installed_libraries)

        # Add widgets to python layout
        python_layout.addWidget(self.check_installs_button)
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

        # Add widgets to install layout
        install_layout.addWidget(self.install_button)
        install_layout.addWidget(self.progress_bar)

        # Add widgets to main layout
        main_layout.addLayout(search_layout)
        main_layout.addWidget(self.filter_dropdown)
        main_layout.addLayout(python_layout)
        main_layout.addWidget(self.library_table)
        main_layout.addLayout(install_layout)

        self.tab1.setLayout(main_layout)

        # Load packages
        self.curated_packages = fetch_curated_packages()
        self.all_packages = fetch_all_packages()

        # Initialize module_to_package before populating packages
        self.module_to_package = self.curated_packages.copy()
        for mod, pkg in self.all_packages.items():
            if mod not in self.module_to_package:
                self.module_to_package[mod] = pkg

        self.current_package_list = []
        self.current_display_list = []  # List currently being displayed
        self.search_active = False
        self.load_limit = 1000  # Number of packages to load per chunk
        self.current_index = 0
        self.populate_initial_packages()

    def init_tab2(self):
        """Initialize the Module Checker tab."""
        layout = QVBoxLayout()

        # Layout for Python selection
        python_selection_layout = QHBoxLayout()
        python_label = QLabel("Select Python Installation:")
        self.module_checker_python_dropdown = QComboBox()
        self.module_checker_python_dropdown.setEnabled(False)  # Disabled until Python installations are checked
        python_selection_layout.addWidget(python_label)
        python_selection_layout.addWidget(self.module_checker_python_dropdown)
        layout.addLayout(python_selection_layout)

        # Instructions Label
        instructions = QLabel("Paste your import statements below and click 'Check Modules'.")
        layout.addWidget(instructions)

        # Text Area for Import Statements
        self.imports_text_edit = QTextEdit()
        self.imports_text_edit.setPlaceholderText("Enter import statements here...")
        layout.addWidget(self.imports_text_edit)

        # Check Modules Button
        self.check_modules_button = QPushButton("Check Modules")
        self.check_modules_button.clicked.connect(self.process_imports)
        layout.addWidget(self.check_modules_button)

        # Progress Bar for Module Checker
        self.module_checker_progress_bar = QProgressBar()
        self.module_checker_progress_bar.setValue(0)
        self.module_checker_progress_bar.setVisible(False)
        layout.addWidget(self.module_checker_progress_bar)

        # List Widget to Display Missing Modules
        self.missing_modules_list = QListWidget()
        layout.addWidget(self.missing_modules_list)

        self.tab2.setLayout(layout)

        # Populate the module_checker_python_dropdown if python_versions exist
        if hasattr(self, 'python_versions') and self.python_versions:
            self.populate_module_checker_python_dropdown()
        else:
            self.module_checker_python_dropdown.setEnabled(False)
            QMessageBox.information(
                self, "Python Installations Needed",
                "Please check Python installations in the 'Library Downloader' tab first."
            )

    def populate_module_checker_python_dropdown(self):
        """Populate the Module Checker Python dropdown with detected Python installations."""
        self.module_checker_python_dropdown.setEnabled(True)
        self.module_checker_python_dropdown.clear()
        self.module_checker_python_dropdown.addItem("Select Installation")
        for version, exec_path in self.python_versions.items():
            self.module_checker_python_dropdown.addItem(f"{version} - {exec_path}", exec_path)
        # Add special options if necessary
        self.module_checker_python_dropdown.addItem("Install to All Python Installations", "all")
        self.module_checker_python_dropdown.addItem("Install to Custom Directory", "custom")
        logging.info("Module Checker Python dropdown populated.")

    # === Module Checker Methods ===
    def process_imports(self):
        """Process the import statements to find missing modules."""
        imports_text = self.imports_text_edit.toPlainText()
        if not imports_text.strip():
            QMessageBox.warning(self, "Error", "Please enter import statements.")
            return

        # Get the selected Python executable
        selected_index = self.module_checker_python_dropdown.currentIndex()
        selected_data = self.module_checker_python_dropdown.currentData()
        selected_text = self.module_checker_python_dropdown.currentText()

        if selected_index == 0:
            QMessageBox.warning(self, "Error", "Please select a Python installation from the dropdown.")
            return

        if selected_data == "all":
            # Handle "Install to All Python Installations" if necessary
            # For module checker, likely need to select a single Python executable
            QMessageBox.warning(self, "Error", "Please select a specific Python installation to check modules.")
            return

        elif selected_data == "custom":
            # Handle "Install to Custom Directory" if necessary
            # For module checker, checking a custom directory might require different handling
            # Possibly not supported, or could be handled by checking the packages installed in that directory
            # For simplicity, instruct the user to select a specific Python executable
            QMessageBox.warning(self, "Error", "Please select a specific Python installation to check modules.")
            return

        else:
            python_exec = selected_data
            logging.info(f"Module Checker selected Python executable: {python_exec}")

        # Store the selected python_exec for use in handle_missing_modules
        self.selected_module_checker_python_exec = python_exec

        # Disable the button to prevent multiple clicks
        self.check_modules_button.setEnabled(False)
        self.missing_modules_list.clear()

        # Reset and show progress bar
        self.module_checker_progress_bar.setValue(0)
        self.module_checker_progress_bar.setVisible(True)

        # Start the module checker thread
        self.module_checker_thread = ModuleCheckerThread(
            imports_text,
            self.module_to_package,
            python_exec,
            self.count_total_modules(imports_text)
        )
        self.module_checker_thread.missing_modules_signal.connect(self.handle_missing_modules)
        self.module_checker_thread.all_modules_installed_signal.connect(self.handle_all_modules_installed)
        self.module_checker_thread.progress_signal.connect(self.update_module_checker_progress)  # Connect signal
        self.module_checker_thread.start()

    def count_total_modules(self, imports_text):
        """Count the total number of modules to check for progress bar."""
        import_statements = imports_text.strip().split('\n')
        module_names = set()
        for line in import_statements:
            line = line.strip()
            if line.startswith('#') or not line:
                continue  # Skip comments and empty lines
            if line.startswith('import '):
                imports = line[7:].split(',')
                for mod in imports:
                    mod = mod.strip()
                    mod = mod.split(' as ')[0].strip()
                    mod = mod.split('.')[0]  # Get the top-level module
                    module_names.add(mod)
            elif line.startswith('from '):
                match = re.match(r'from\s+(\S+)\s+import', line)
                if match:
                    mod = match.group(1)
                    mod = mod.split('.')[0]
                    module_names.add(mod)
        return len(module_names)

    def handle_missing_modules(self, missing_modules):
        """Handle the list of missing modules identified by the Module Checker."""
        logging.info(f"Missing modules: {missing_modules}")
        for module in missing_modules:
            # Determine the pip package name from the mapping
            pip_package = self.module_to_package.get(module.lower(), module)
            # Attempt to find the correct pip package name
            if pip_package != module:
                logging.debug(f"Using mapped pip package '{pip_package}' for module '{module}'.")
            else:
                logging.debug(f"No mapping found for module '{module}', using module name as package name.")

            # Proceed to install using the determined pip package name
            reply = QMessageBox.question(
                self, "Install Module",
                f"The module '{module}' is not installed in the selected Python installation.\nWould you like to install the package '{pip_package}'?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            if reply == QMessageBox.Yes:
                self.install_module(pip_package, module, self.selected_module_checker_python_exec)
            else:
                logging.info(f"User chose not to install module '{module}'.")

            # Add the module to the list widget with current status
            status = "Installed" if self.is_module_installed(module, self.selected_module_checker_python_exec) else "Not Installed"
            self.missing_modules_list.addItem(f"{module} - {status}")
        self.check_modules_button.setEnabled(True)
        self.module_checker_progress_bar.setVisible(False)

    def handle_all_modules_installed(self):
        """Handle the scenario where all modules are already installed."""
        QMessageBox.information(self, "All Modules Installed", "All modules are already installed.")
        self.check_modules_button.setEnabled(True)
        self.module_checker_progress_bar.setVisible(False)

    def install_module(self, package_name, module_name, python_exec):
        """Install the specified pip package corresponding to the module using the selected Python executable."""
        try:
            logging.info(f"Attempting to install package '{package_name}' for module '{module_name}' using {python_exec}.")
            subprocess.check_call([python_exec, '-m', 'pip', 'install', package_name])
            QMessageBox.information(self, "Success", f"Module '{module_name}' (package '{package_name}') installed successfully.")
            logging.info(f"Module '{module_name}' (package '{package_name}') installed successfully.")
        except subprocess.CalledProcessError as e:
            QMessageBox.critical(self, "Error", f"Failed to install module '{module_name}' (package '{package_name}').")
            logging.error(f"Failed to install module '{module_name}'. CalledProcessError: {e}")

    def is_module_installed(self, module_name, python_exec):
        """Check if a module is installed in the specified Python executable."""
        try:
            subprocess.check_output([python_exec, '-c', f'import {module_name}'], stderr=subprocess.STDOUT)
            logging.debug(f"Module '{module_name}' is installed in {python_exec}.")
            return True
        except subprocess.CalledProcessError as e:
            logging.warning(f"Module '{module_name}' is not installed in {python_exec}. Output: {e.output}")
            return False

    def update_module_checker_progress(self, progress):
        """Update the progress bar for the module checker."""
        self.module_checker_progress_bar.setValue(progress)

    # === Library Downloader Methods ===
    def populate_initial_packages(self):
        """Populate the table with initial set of packages based on filter."""
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
        """Load the next chunk of packages into the table."""
        if self.current_index >= len(self.current_package_list):
            return  # No more packages to load

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
        logging.info(f"Loaded packages up to index {self.current_index}.")

    def on_scroll(self, value):
        """Handle the scroll event to implement infinite scrolling."""
        scrollbar = self.library_table.verticalScrollBar()
        if value == scrollbar.maximum() and not self.search_active:
            logging.info("Reached the bottom of the table. Loading more packages...")
            self.load_more_packages()

    def apply_filter(self):
        """Apply the selected filter to the package list."""
        self.search_active = False
        self.search_input.clear()
        self.populate_initial_packages()

    def search_library(self):
        """Search for a specific library."""
        query = self.search_input.text().strip().lower()
        if not query:
            QMessageBox.warning(self, "Error", "Please enter a search query.")
            logging.warning("No search query entered.")
            return

        filter_choice = self.filter_dropdown.currentText()
        if filter_choice == "Popular Libraries":
            search_list = self.curated_packages.keys()
        else:
            search_list = self.all_packages.keys()

        # Filter packages based on the search query
        results = [pkg_module for pkg_module in search_list if query in pkg_module.lower()]

        if not results:
            QMessageBox.information(self, "No Results", f"No libraries found matching '{query}'.")
            logging.info(f"No libraries found matching '{query}'.")
            self.library_table.setRowCount(0)
            self.current_display_list = []
            self.current_package_list = []
            self.search_active = True
            return

        # Update the display list and reset indices
        self.current_package_list = results
        self.current_display_list = []
        self.current_index = 0
        self.library_table.setRowCount(0)
        self.load_more_packages()
        self.search_active = True
        logging.info(f"Search performed for '{query}'. {len(results)} libraries found.")

    def check_python_installations(self):
        """Check all Python installations and populate the dropdowns."""
        logging.info("Checking Python installations...")
        self.python_versions = detect_python_versions()
        if not self.python_versions:
            QMessageBox.warning(self, "Error", "No Python installations found.")
            logging.warning("No Python installations detected.")
            self.python_dropdown.clear()
            self.python_dropdown.addItem("No Python installations detected.")
            self.python_dropdown.setEnabled(False)
            self.view_installed_button.setEnabled(False)
            # Also disable module checker python_dropdown
            if hasattr(self, 'module_checker_python_dropdown'):
                self.module_checker_python_dropdown.clear()
                self.module_checker_python_dropdown.setEnabled(False)
            return

        # Clear and populate the library downloader's dropdown
        self.python_dropdown.setEnabled(True)
        self.python_dropdown.clear()
        self.python_dropdown.addItem("Select Installation")
        for version, exec_path in self.python_versions.items():
            self.python_dropdown.addItem(f"{version} - {exec_path}", exec_path)

        # Add special options
        self.python_dropdown.addItem("Install to All Python Installations", "all")
        self.python_dropdown.addItem("Install to Custom Directory", "custom")

        # Populate module checker python_dropdown
        if hasattr(self, 'module_checker_python_dropdown'):
            self.populate_module_checker_python_dropdown()

        self.view_installed_button.setEnabled(True)
        QMessageBox.information(self, "Python Installations", "Python installations have been detected and listed.")
        logging.info("Python installations have been populated in the dropdown.")

    def on_python_selection_change(self):
        """Handle Python dropdown selection changes, specifically for custom directory option."""
        selected_option = self.python_dropdown.currentText()

        if selected_option == "Install to Custom Directory":
            # Automatically open file dialog for selecting a custom directory
            custom_dir = QFileDialog.getExistingDirectory(self, "Select Installation Directory", "")
            if custom_dir:
                self.python_dropdown.setItemText(self.python_dropdown.currentIndex(), f"Custom Directory: {custom_dir}")
                self.python_dropdown.setCurrentText(f"Custom Directory: {custom_dir}")
                logging.info(f"Custom directory selected: {custom_dir}")
            else:
                # If no directory is selected, reset dropdown to initial value
                self.python_dropdown.setCurrentIndex(0)
                logging.warning("No custom directory selected, reverted to 'Select Installation'.")

    def install_selected_library(self):
        """Install the selected library to the chosen Python installation(s) or directory."""
        selected_items = self.library_table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Please select a library to install.")
            logging.warning("No library selected for installation.")
            return

        selected_library = selected_items[0].text()
        logging.info(f"Preparing to install library: {selected_library}")

        # Get the selected Python installation
        selected_python = self.python_dropdown.currentData()
        selected_option = self.python_dropdown.currentText()

        if not selected_python or selected_python == "Select Installation":
            QMessageBox.warning(self, "Error", "Please select a valid Python installation from the dropdown.")
            logging.warning("Invalid Python installation selected.")
            return

        # Determine installation targets
        install_targets = []
        if selected_option == "Install to All Python Installations":
            if not self.python_versions:
                QMessageBox.warning(self, "Error", "No Python installations found.")
                logging.warning("No Python installations detected.")
                return
            install_targets = list(self.python_versions.values())
            logging.info("Selected to install to all Python installations.")
        elif selected_option.startswith("Custom Directory:"):
            # Extract the custom directory path from the dropdown text
            custom_dir = selected_option.split("Custom Directory: ")[1]
            install_targets = [f"custom:{custom_dir}"]
            logging.info(f"Selected to install to custom directory: {custom_dir}")
        else:
            # Single Python installation
            install_targets = [selected_python]
            logging.info(f"Selected to install to Python executable: {selected_python}")

        # Disable UI elements during installation
        self.install_button.setEnabled(False)
        self.check_installs_button.setEnabled(False)
        self.view_installed_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(install_targets))
        self.progress_bar.setValue(0)

        # Perform installation
        errors = []
        for idx, target in enumerate(install_targets, start=1):
            if target.startswith("custom:"):
                # Install to custom directory using --target
                custom_path = target.split("custom:")[1]
                cmd = [sys.executable, "-m", "pip", "install", selected_library, "--target", custom_path]
                logging.info(f"Installing {selected_library} to custom directory: {custom_path}")
            else:
                # Install to specific Python executable
                cmd = [target, "-m", "pip", "install", selected_library]
                logging.info(f"Installing {selected_library} to Python executable: {target}")

            try:
                subprocess.run(cmd, check=True)
                logging.info(f"Successfully installed {selected_library} to {target}.")
            except subprocess.CalledProcessError as e:
                logging.error(f"Failed to install {selected_library} to {target}: {e}")
                errors.append(f"Failed to install to {target}: {e}")

            # Update progress bar
            self.progress_bar.setValue(idx)
            QApplication.processEvents()  # Keep UI responsive

        # Re-enable UI elements after installation
        self.install_button.setEnabled(True)
        self.check_installs_button.setEnabled(True)
        self.view_installed_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        if errors:
            QMessageBox.critical(self, "Installation Errors", "\n".join(errors))
            logging.error("Some installations failed.")
        else:
            QMessageBox.information(self, "Success", f"Successfully installed {selected_library}.")
            logging.info(f"All installations of {selected_library} succeeded.")

    def view_installed_libraries(self):
        """View installed libraries for the selected Python installation."""
        selected_python = self.python_dropdown.currentData()
        selected_option = self.python_dropdown.currentText()

        if not selected_python or selected_python == "Select Installation":
            QMessageBox.warning(self, "Error", "Please select a valid Python installation from the dropdown.")
            logging.warning("Invalid Python installation selected for viewing libraries.")
            return

        if selected_option.startswith("Custom Directory:") or selected_option == "Install to All Python Installations":
            QMessageBox.warning(self, "Error", "Please select a single Python installation to view its libraries.")
            logging.warning("Invalid selection for viewing libraries.")
            return

        # Get installed libraries
        logging.info(f"Retrieving installed libraries for Python executable: {selected_python}")
        try:
            result = subprocess.check_output([selected_python, "-m", "pip", "list"], text=True)
            logging.info(f"Installed libraries for {selected_option}:\n{result}")
            # Display in a new window
            self.show_installed_libraries_window(selected_option, result)
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to list libraries for {selected_option}: {e}")
            QMessageBox.critical(self, "Error", f"Failed to retrieve installed libraries for {selected_option}.")

    def show_installed_libraries_window(self, python_version, library_list):
        """Display the installed libraries in a new window."""
        window = QWidget()
        window.setWindowTitle(f"Installed Libraries - {python_version}")
        layout = QVBoxLayout()

        text_edit = QTextEdit()
        text_edit.setReadOnly(True)
        text_edit.setText(library_list)

        layout.addWidget(text_edit)
        window.setLayout(layout)
        window.resize(600, 400)
        window.show()
        # Keep a reference to prevent garbage collection
        self.installed_libs_window = window

    # === Additional Methods ===
    def closeEvent(self, event):
        """Handle the window close event to prompt for log saving."""
        reply = QMessageBox.question(
            self, 'Exit',
            "Are you sure you want to exit?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Ask if the user wants to save the log
            save_reply = QMessageBox.question(
                self, 'Save Log',
                "Would you like to save the session log?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )

            if save_reply == QMessageBox.Yes:
                # Prompt for file location
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Log", os.path.expanduser("~"),
                    "Log Files (*.log);;All Files (*)", options=options
                )
                if file_path:
                    try:
                        with open(file_path, 'w') as log_file:
                            log_file.write(self.memory_handler.get_logs())
                        QMessageBox.information(self, "Success", f"Log saved to {file_path}")
                        logging.info(f"Log saved to {file_path}")
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to save log: {e}")
                        logging.error(f"Failed to save log: {e}")
            # Proceed with closing
            event.accept()
        else:
            event.ignore()

# === Run the Application ===
if __name__ == "__main__":
    # Initialize logging
    memory_handler, log_filename = setup_logging()

    logging.info("Starting the application...")
    app = QApplication(sys.argv)
    main_window = LibraryDownloader()
    main_window.show()
    sys.exit(app.exec())
