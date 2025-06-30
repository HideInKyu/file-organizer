Hyper-Efficient File Organizer
This script automates the organization of your files by moving them from a designated "docking station" (like your Downloads folder) into a structured, categorized directory. It can organize new files as they arrive or re-organize an existing directory structure.

Quick Start: Setup and Run

1. Install Dependencies
   First, you need to install the required Python library. Open your terminal or command prompt and run the following command:

pip install -r requirements.txt

2. Configure Your Paths
   Before running, you must configure your desired folders. Open the config.ini file in a text editor and change the paths to your liking:

[DEFAULT]
docking_station_path = ~/Downloads
organized_path = ~/Downloads/Organized
stability_wait_time_seconds = 500
duplicate_retention_days = 21
scan_interval_seconds = 60

docking_station_path: This is the folder the script will watch for new files (e.g., your default downloads folder).

organized_path: This is where your neatly sorted files and folders will be moved to.

3. Run the Script
   To start the organizer, navigate to the script's directory in your terminal and run the main.py file:

python main.py

You will then be prompted to choose an action:

Enter 1 to start monitoring the docking station for new files. The script will scan for new items at a regular interval.

Enter 2 to perform a one-time re-organization of the files already inside your organized_path.

To stop the script at any time, press Ctrl+C in the terminal.

How It Works
The File Organizer is designed to be a "set it and forget it" utility that brings order to your digital clutter. It operates based on a few key principles.

The Docking Station Concept
The script treats your specified docking_station_path as a temporary holding area for all incoming files and folders. When you run the script in "organize new files" mode, it continuously scans this folder for items to process.

File Stability Check
To avoid moving files that are still being downloaded or written, the script performs a stability check. It waits for a file's size to remain unchanged for a specific period (defined by stability_wait_time_seconds in the config) before considering it ready for organization. Temporary download files (like .crdownload or .part) are automatically ignored.

Intelligent Classification
The script uses a multi-layered approach to classify your files and folders accurately:

For Individual Files: Classification is primarily based on the file's extension. A comprehensive internal map sorts files into categories like documents, photos, videos, archives, and more.

For Directories: To classify a folder, the script analyzes its contents to find the most common file type within it. The folder is then moved to the category corresponding to that dominant file type.

Fallback Category: If a file type is unknown, it will be placed in a default other directory, ensuring no file is left behind.

Duplicate Handling
If the script finds an item in the docking station with the same name as an item that already exists in the target category, it handles it intelligently. Instead of overwriting, it renames the new file by appending a number (e.g., report.pdf becomes report(1).pdf) and places it in a dedicated duplicates folder for your review. This ensures no data is accidentally lost.

Re-organization Mode
If you've manually moved files around or want to apply new sorting logic to your existing organized structure, the "re-organize" mode is for you. It scans all the subdirectories within your organized_path and checks if each file is in its correct category. If any files are misplaced, it will move them to their proper home, restoring order to your archive.
