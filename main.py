import sys
from PyQt6.QtWidgets import QApplication
from duplicate_file_finder import AdvancedDuplicateFileFinder

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedDuplicateFileFinder()
    window.show()
    sys.exit(app.exec())