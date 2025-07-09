
import shutil
import shutil
import os
import sys
import time
import hashlib
import logging
import filetype
import configparser
from collections import deque, Counter
from datetime import datetime, timedelta

# Get the directory of the current script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(SCRIPT_DIR, 'config.ini')

# --- Configuration ---
config = configparser.ConfigParser()
config.read(CONFIG_PATH)


DOCKING_STATION_PATH = os.path.expanduser(config['DEFAULT']['docking_station_path'])
ORGANIZED_PATH = os.path.expanduser(config['DEFAULT']['organized_path'])
STABILITY_WAIT_TIME_SECONDS = int(config['DEFAULT']['stability_wait_time_seconds'])
DUPLICATE_RETENTION_DAYS = int(config['DEFAULT']['duplicate_retention_days'])
SCAN_INTERVAL_SECONDS = int(config['DEFAULT']['scan_interval_seconds'])

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# --- Temporary File Extensions ---
TEMP_FILE_EXTENSIONS = ['.crdownload', '.part', '.tmp', '.download']
IGNORED_FILES = []

# --- Category Map ---
CATEGORY_MAP = {
    # Documents
    'pdf': 'documents', 'docx': 'documents', 'doc': 'documents', 'txt': 'documents', 'rtf': 'documents',
    'xlsx': 'documents', 'xls': 'documents', 'pptx': 'documents', 'ppt': 'documents', 'csv': 'documents',
    'epub': 'documents', 'mobi': 'documents', 'odt': 'documents', 'ods': 'documents', 'odp': 'documents',
    # Photos
    'jpg': 'photos', 'jpeg': 'photos', 'png': 'photos', 'gif': 'photos', 'webp': 'photos', 'tiff': 'photos',
    'tif': 'photos', 'bmp': 'photos', 'heic': 'photos', 'svg': 'photos', 'ai': 'photos', 'psd': 'photos',
    # Videos
    'mp4': 'videos', 'mov': 'videos', 'avi': 'videos', 'mkv': 'videos', 'wmv': 'videos', 'flv': 'videos',
    'webm': 'videos',
    # Audio
    'mp3': 'audio', 'wav': 'audio', 'aac': 'audio', 'flac': 'audio', 'ogg': 'audio', 'm4a': 'audio',
    'aiff': 'audio',
    # Archives
    'zip': 'archives', 'rar': 'archives', '7z': 'archives', 'tar': 'archives', 'gz': 'archives', 'bz2': 'archives',
    'iso': 'archives', 'dmg': 'archives',
    # 3D Models
    'stl': '3d_models', 'obj': '3d_models', 'gcode': '3d_models', '3mf': '3d_models', 'fbx': '3d_models',
    'blend': '3d_models',
    # Executables
    'exe': 'executables', 'msi': 'executables', 'app': 'executables', 'bat': 'executables', 'sh': 'executables',
    # Fonts
    'ttf': 'fonts', 'otf': 'fonts', 'woff': 'fonts', 'woff2': 'fonts',
    # Projects
    'py': 'projects', 'js': 'projects', 'html': 'projects', 'css': 'projects', 'cpp': 'projects', 'c': 'projects',
    'h': 'projects', 'java': 'projects', 'json': 'projects', 'xml': 'projects', 'yml': 'projects', 'md': 'projects',
}

# --- Core Logic ---
def get_week_folder_name(date):
    start_of_week = date - timedelta(days=(date.weekday() + 1) % 7)
    end_of_week = start_of_week + timedelta(days=6)
    return f"{start_of_week.strftime('%B %d')}-{end_of_week.strftime('%d')}"

def is_file_stable(file_path):
    """Checks if a file is stable by verifying its size over a period of time."""
    if not os.path.exists(file_path):
        return False

    try:
        initial_size = os.path.getsize(file_path)
        time.sleep(STABILITY_WAIT_TIME_SECONDS)
        current_size = os.path.getsize(file_path)
        return initial_size == current_size
    except OSError as e:
        logging.warning(f"Error accessing file {file_path}: {e}")
        return False

def get_file_hash(file_path):
    """Calculates the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def classify_directory(directory_path):
    """Classifies a directory based on the most common file type inside it."""
    extensions = []
    for _, _, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(directory_path, file)
            try:
                kind = filetype.guess(file_path)
                if kind:
                    extensions.append(kind.extension.lower())
                else:
                    ext = os.path.splitext(file)[1][1:].lower()
                    if ext:
                        extensions.append(ext)
            except FileNotFoundError:
                logging.warning(f"File not found (possibly not downloaded from cloud): {file_path}. Skipping.")
                continue
            except OSError as e:
                logging.warning(f"Error accessing file {file_path}: {e}. Skipping.")
                continue
    
    if not extensions:
        return 'other'

    most_common_ext = Counter(extensions).most_common(1)[0][0]
    return CATEGORY_MAP.get(most_common_ext, 'other')

def get_unique_filename(directory, filename):
    """Generates a unique filename by appending (n) if a file with the same name exists."""
    base, ext = os.path.splitext(filename)
    counter = 0
    new_filename = filename
    while os.path.exists(os.path.join(directory, new_filename)):
        counter += 1
        new_filename = f"{base}({counter}){ext}"
    return new_filename

def move_item(source_path, category):
    """Moves a file or directory to the appropriate category folder."""
    today = datetime.now()
    week_folder = get_week_folder_name(today)
    target_dir = os.path.join(ORGANIZED_PATH, category, week_folder)

    # Check if the source is a file and get its extension
    if os.path.isfile(source_path):
        ext = os.path.splitext(source_path)[1][1:].lower()
        if ext:
            target_dir = os.path.join(target_dir, ext)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir, exist_ok=True)

    target_path = os.path.join(target_dir, os.path.basename(source_path))

    is_duplicate = False
    if os.path.exists(target_path):
        original_filename = os.path.basename(source_path)
        unique_filename = get_unique_filename(target_dir, original_filename)
        target_path = os.path.join(target_dir, unique_filename)
        logging.info(f"Duplicate file detected. Renaming {original_filename} to {unique_filename}")
        is_duplicate = True

    if is_duplicate:
        final_category = 'duplicates'
        target_dir = os.path.join(ORGANIZED_PATH, final_category)
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)
        target_path = os.path.join(target_dir, os.path.basename(target_path)) # Re-evaluate target_path with new directory

    shutil.move(source_path, target_path)
    logging.info(f"Moved {source_path} to {target_path}")


def reorganize_existing_files():
    """Scans the organized directory and re-organizes files if necessary."""
    logging.info("Starting to re-organize existing files.")
    items_to_reorganize = {}

    for category in os.listdir(ORGANIZED_PATH):
        category_path = os.path.join(ORGANIZED_PATH, category)
        if not os.path.isdir(category_path):
            continue

        for item_name in os.listdir(category_path):
            item_path = os.path.join(category_path, item_name)

            # Skip ignored files
            if item_name in IGNORED_FILES:
                logging.info(f"Skipping ignored file during re-organization: {item_name}")
                continue
            
            if os.path.isdir(item_path):
                new_category = classify_directory(item_path)
                if new_category != category:
                    items_to_reorganize[item_path] = new_category
            else:
                ext = os.path.splitext(item_name)[1][1:].lower()
                new_category = CATEGORY_MAP.get(ext, 'other')
                if new_category != category:
                    items_to_reorganize[item_path] = new_category
    
    if not items_to_reorganize:
        logging.info("No items to re-organize.")
        return

    print("--- Re-organization Plan ---")
    for item, new_category in items_to_reorganize.items():
        print(f"Move '{item}' -> '{new_category}' category")
    print("----------------------------")

    logging.info("Re-organization approved automatically.")
    for item, new_category in items_to_reorganize.items():
        move_item(item, new_category)
    logging.info("Re-organization complete.")

def organize_new_files():
    # --- Scan and Classify ---
    items_to_organize = {}
    abs_organized_path = os.path.abspath(ORGANIZED_PATH)

    for item_name in os.listdir(DOCKING_STATION_PATH):
        if item_name.startswith('.'):
            continue
        item_path = os.path.join(DOCKING_STATION_PATH, item_name)
        
        # Skip the organized folder itself
        if os.path.abspath(item_path) == abs_organized_path:
            continue

        # Skip ignored files
        if item_name in IGNORED_FILES:
            logging.info(f"Skipping ignored file: {item_name}")
            continue

        # Skip temporary download files
        if any(item_name.endswith(ext) for ext in TEMP_FILE_EXTENSIONS):
            logging.info(f"Skipping temporary file: {item_name}")
            continue

        # Check for file stability
        if not os.path.isdir(item_path) and not is_file_stable(item_path):
            logging.info(f"File not stable yet, skipping: {item_name}")
            continue

        if os.path.isdir(item_path):
            category = classify_directory(item_path)
            items_to_organize[item_path] = category
            logging.info(f"Added directory '{item_name}' to organization queue (category: {category}).")
        else:
            ext = os.path.splitext(item_name)[1][1:].lower()
            category = CATEGORY_MAP.get(ext, 'other')
            items_to_organize[item_path] = category
            logging.info(f"Added file '{item_name}' to organization queue (category: {category}).")

    # --- Display Plan and Get Confirmation ---
    if not items_to_organize:
        logging.info("No items to organize.")
        return

    print("--- Organization Plan ---")
    for item, category in items_to_organize.items():
        print(f"Move '{item}' -> '{category}' category")
    print("-------------------------")

    logging.info("Organization approved automatically.")
    for item, category in items_to_organize.items():
        move_item(item, category)
    logging.info("Organization complete.")


if __name__ == "__main__":
    # --- Ensure directories exist ---
    if not os.path.exists(DOCKING_STATION_PATH):
        os.makedirs(DOCKING_STATION_PATH)
        logging.info(f"Created docking station at: {DOCKING_STATION_PATH}")
    if not os.path.exists(ORGANIZED_PATH):
        os.makedirs(ORGANIZED_PATH)
        logging.info(f"Created organized directory at: {ORGANIZED_PATH}")

    # --- User Choice ---
    print("What would you like to do?")
    print("1. Organize new files from the docking station")
    print("2. Re-organize existing files in the organized directory")
    choice = input("Enter your choice (1 or 2): ")

    try:
        if choice == '1':
            while True:
                organize_new_files()
                time.sleep(SCAN_INTERVAL_SECONDS)
        elif choice == '2':
            while True:
                reorganize_existing_files()
                time.sleep(SCAN_INTERVAL_SECONDS)
        else:
            logging.info("Invalid choice. Exiting.")
            sys.exit()
    except KeyboardInterrupt:
        logging.info("Program interrupted by user (Ctrl+C). Exiting.")
        sys.exit(0)


