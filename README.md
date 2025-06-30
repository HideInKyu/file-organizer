# File Organizer

This project is a Python script that automatically organizes files from a specified directory (the "docking station") into categorized folders based on their file type. It can also be used to re-organize an existing directory of sorted files.

-----

## Quick Start

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/hideinkyu/file-organizer.git
    ```
2.  **Navigate to the project directory:**
    ```bash
    cd file-organizer
    ```
3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure the script:**
    Before running the script, you can customize the settings in the `config.ini` file.
5.  **Run the script:**
    ```bash
    python main.py
    ```
    You will be prompted to choose between two options:
    1.  Organize new files from the docking station
    2.  Re-organize existing files in the organized directory

-----

## Features

  * **Automatic file classification:** Sorts files into categories like documents, photos, videos, audio, archives, and more.
  * **Directory classification:** Analyzes the contents of directories to classify them based on the most common file type within.
  * **Duplicate handling:** Detects and handles duplicate files by renaming them.
  * **Configurable:** Easily configure paths, wait times, and other settings through a `config.ini` file.
  * **Interactive or automated:** Choose to organize new files or re-organize existing ones.
  * **Stable file detection:** Waits for files to be fully downloaded or copied before organizing them.

-----

## How It Works

The script operates by scanning a designated "docking station" directory for new files or an "organized" directory for existing files to re-organize. Here's a deeper look at its core functionalities:

### Configuration

  * The script begins by reading the `config.ini` file to load paths for the docking station and the organized files directory, as well as settings for file stability checks, duplicate retention, and scan intervals.

### File Stability

  * To avoid moving files that are still being written (e.g., in-progress downloads), the script uses an `is_file_stable` function. This function checks the file size, waits for a configurable period (`stability_wait_time_seconds`), and then checks the size again. A file is considered stable if its size has not changed.

### Classification

  * **Files:** Individual files are classified based on their extension. A `CATEGORY_MAP` dictionary maps a wide range of file extensions to their respective categories (e.g., 'pdf' to 'documents', 'jpg' to 'photos').
  * **Directories:** For directories, the script performs a deeper analysis. It walks through the directory, guesses the file type of each file, and determines the most common file extension. This most common extension is then used to classify the entire directory.

### Duplicate Handling

  * If a file with the same name already exists in the target directory, the script's `get_unique_filename` function is called. This function appends a number to the filename (e.g., `file(1).txt`) to ensure that the original file is not overwritten. The new file is then moved to a 'duplicates' folder within the organized directory.

### Main Logic

  * The script presents two main choices to the user: organize new files or re-organize existing ones.
      * **Organize New Files:** If the user chooses to organize new files, the script scans the docking station, classifies each item, and then moves it to the appropriate category folder within the organized directory.
      * **Re-organize Existing Files:** If the user opts to re-organize, the script scans the existing category folders in the organized directory. If a file or directory's classification has changed, it is moved to the correct new category folder.
  * Both processes run in a loop, periodically scanning for new files or changes, until the user stops the script.