# DuplicateDetective

## Overview

DuplicateDetective is an advanced, user-friendly desktop application designed to help you efficiently manage duplicate files on your computer. Built with Python and PyQt6, this powerful tool offers a seamless experience for identifying, previewing, and managing duplicate files, helping you reclaim valuable disk space and organize your digital content.

## Features

- **Intuitive Graphical User Interface**: Clean, modern, and easy-to-navigate design.
- **Multi-threaded File Scanning**: Fast and efficient duplicate file detection, even for large directories.
- **Customizable File Type Filtering**: Focus your search on specific file types.
- **Interactive File Preview**: Quickly view contents of image files and details of other file types.
- **Smart Duplicate Management**: Options to delete selected duplicates or all duplicates except the first occurrence.
- **Undo Functionality**: Safeguard against accidental deletions with the ability to undo recent delete operations.
- **Real-time Progress Tracking**: Visual feedback for search and deletion operations.
- **Disk Space Visualization**: Clear overview of your disk usage.
- **Multiple Theme Options**: Customize the app's appearance with various color schemes.
- **Detailed Logging**: Keep track of all operations for future reference.
- **Cross-platform Compatibility**: Works on Windows, macOS, and Linux.

## Installation

### Prerequisites

- Python 3.6 or higher
- PyQt6

### Steps

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/DuplicateDetective.git
   ```
2. Navigate to the project directory:
   ```
   cd DuplicateDetective
   ```
3. Install the required dependencies:
   ```
   pip install PyQt6
   ```
4. Run the application:
   ```
   python main.py
   ```

## Usage

1. Launch DuplicateDetective.
2. Click "Browse" to select a folder for duplicate file search.
3. (Optional) Enter file extensions in the "File Types" field to filter your search.
4. Click "Search for Duplicates" to initiate the scan.
5. Review the results in the tree view:
   - Duplicate files are grouped together.
   - Select groups or individual files for deletion.
6. Use the preview pane to view file contents and details.
7. Click "Delete Selected" or "Delete All Except First" to remove duplicate files.
8. Use the "Undo Last Delete" option if needed.

## Customization

DuplicateDetective offers multiple themes to suit your preference:
- Dark (default)
- Light
- Solarized
- Nord

To change the theme, use the dropdown menu in the top-left corner of the application.

## Contributing

Contributions to DuplicateDetective are welcome! Please feel free to submit pull requests, create issues for bugs, or suggest new features.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` file for more information.

## Acknowledgements

- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - The GUI framework used
- [Python](https://www.python.org/) - The programming language used


Project Link: https://github.com/Benighter/DuplicateDetective
