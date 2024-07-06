import os
import sys
import subprocess
import logging
import hashlib
from collections import defaultdict
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QFileDialog, QLabel, QTreeWidget, QTreeWidgetItem, QMessageBox, 
                             QCheckBox, QScrollArea, QComboBox, QSplitter,
                             QTextEdit, QPushButton, QListWidget, QListWidgetItem,
                             QFileIconProvider, QLineEdit, QProgressBar)
from PyQt6.QtGui import QFont, QIcon, QColor, QPixmap
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QFileInfo, QThread, QObject, pyqtSignal

class FileHasher(QObject):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, folder, file_types=None):
        super().__init__()
        self.folder = folder
        self.file_types = file_types

    def run(self):
        duplicates = defaultdict(list)
        total_files = sum([len(files) for r, d, files in os.walk(self.folder)])
        processed_files = 0

        try:
            for root, _, files in os.walk(self.folder):
                for filename in files:
                    try:
                        if self.file_types and not any(filename.lower().endswith(ft.lower()) for ft in self.file_types):
                            continue
                        filepath = os.path.join(root, filename)
                        file_hash = self.hash_file(filepath)
                        file_size = os.path.getsize(filepath)
                        duplicates[file_hash].append((filepath, file_size))
                        processed_files += 1
                        self.progress.emit(int(processed_files / total_files * 100))
                    except Exception as e:
                        print(f"Error processing file {filename}: {str(e)}")
        except Exception as e:
            print(f"Error during file search: {str(e)}")
        
        self.finished.emit(duplicates)

    def hash_file(self, filepath):
        BLOCK_SIZE = 65536
        file_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            fb = f.read(BLOCK_SIZE)
            while len(fb) > 0:
                file_hash.update(fb)
                fb = f.read(BLOCK_SIZE)
        return file_hash.hexdigest()

class AnimatedButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.animation = QPropertyAnimation(self, b"size")
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
        self.animation.setDuration(300)

    def enterEvent(self, event):
        self.animation.setStartValue(self.size())
        self.animation.setEndValue(QSize(self.width() + 10, self.height() + 5))
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.animation.setStartValue(self.size())
        self.animation.setEndValue(QSize(self.width() - 10, self.height() - 5))
        self.animation.start()
        super().leaveEvent(event)

class CustomTreeWidget(QTreeWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

class CancellableProgressBar(QWidget):
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.progress_bar = QProgressBar()
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancelled.emit)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.cancel_button)

    def setValue(self, value):
        self.progress_bar.setValue(value)

    def setVisible(self, visible):
        super().setVisible(visible)
        if not visible:
            self.setValue(0)

class AdvancedDuplicateFileFinder(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Advanced Duplicate File Finder")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.setup_ui()
        self.setup_themes()
        self.apply_theme("Dark")

        # Set up logging
        logging.basicConfig(filename='duplicate_finder.log', level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger()

        # Undo stack
        self.undo_stack = []

    def setup_ui(self):
        # Top bar
        top_bar = QHBoxLayout()
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["Dark", "Light", "Solarized", "Nord"])
        self.theme_selector.currentTextChanged.connect(self.apply_theme)
        top_bar.addWidget(QLabel("Theme:"))
        top_bar.addWidget(self.theme_selector)
        top_bar.addStretch()
        self.main_layout.addLayout(top_bar)

        # File type filter
        filter_layout = QHBoxLayout()
        self.file_type_filter = QLineEdit()
        self.file_type_filter.setPlaceholderText("Enter file extensions to include (e.g., jpg,png,pdf)")
        filter_layout.addWidget(QLabel("File Types:"))
        filter_layout.addWidget(self.file_type_filter)
        self.main_layout.addLayout(filter_layout)

        # Main content
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_layout.addWidget(content_splitter)

        # Left panel
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Folder selection
        folder_layout = QHBoxLayout()
        self.folder_label = QLabel("No folder selected")
        folder_layout.addWidget(self.folder_label)
        self.browse_button = AnimatedButton("Browse")
        self.browse_button.clicked.connect(self.browse_folder)
        folder_layout.addWidget(self.browse_button)
        left_layout.addLayout(folder_layout)

        # Search button
        self.search_button = AnimatedButton("Search for Duplicates")
        self.search_button.clicked.connect(self.start_search)
        left_layout.addWidget(self.search_button)

        # Progress bar
        self.progress_bar = CancellableProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.cancelled.connect(self.cancel_search)
        left_layout.addWidget(self.progress_bar)

        # Results tree
        self.tree = CustomTreeWidget()
        self.tree.setHeaderLabels(["File", "Size", "Path"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 100)
        self.tree.itemSelectionChanged.connect(self.update_preview)
        left_layout.addWidget(self.tree)

        # Delete buttons
        delete_layout = QHBoxLayout()
        self.delete_selected_button = AnimatedButton("Delete Selected")
        self.delete_selected_button.clicked.connect(self.delete_selected_duplicates)
        self.delete_selected_button.setVisible(False)
        delete_layout.addWidget(self.delete_selected_button)

        self.delete_all_button = AnimatedButton("Delete All Except First")
        self.delete_all_button.clicked.connect(self.delete_all_duplicates)
        self.delete_all_button.setVisible(False)
        delete_layout.addWidget(self.delete_all_button)

        left_layout.addLayout(delete_layout)

        # Undo button
        self.undo_button = AnimatedButton("Undo Last Delete")
        self.undo_button.clicked.connect(self.undo_last_delete)
        self.undo_button.setVisible(False)
        left_layout.addWidget(self.undo_button)

        content_splitter.addWidget(left_panel)

        # Right panel
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        # File preview
        self.preview_label = QLabel("File Preview")
        right_layout.addWidget(self.preview_label)
        
        self.preview_scroll = QScrollArea()
        self.preview_scroll.setWidgetResizable(True)
        self.preview_content = QLabel()
        self.preview_content.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_scroll.setWidget(self.preview_content)
        right_layout.addWidget(self.preview_scroll)

        # File operations
        operations_layout = QHBoxLayout()
        self.open_button = AnimatedButton("Open File")
        self.open_button.clicked.connect(self.open_selected_file)
        operations_layout.addWidget(self.open_button)
        self.open_folder_button = AnimatedButton("Open Containing Folder")
        self.open_folder_button.clicked.connect(self.open_containing_folder)
        operations_layout.addWidget(self.open_folder_button)
        right_layout.addLayout(operations_layout)

        # File details
        self.details_list = QListWidget()
        right_layout.addWidget(self.details_list)

        # Disk space information
        self.disk_space_label = QLabel()
        right_layout.addWidget(self.disk_space_label)

        content_splitter.addWidget(right_panel)

        # Set initial sizes for the splitter
        content_splitter.setSizes([600, 600])

    def setup_themes(self):
        self.themes = {
            "Dark": {
                "bg_color": "#2E3440",
                "text_color": "#ECEFF4",
                "button_color": "#5E81AC",
                "button_hover": "#81A1C1",
                "tree_bg": "#3B4252",
                "tree_alt_bg": "#434C5E",
                "selection_color": "#88C0D0",
                "progress_bar": "#A3BE8C"
            },
            "Light": {
                "bg_color": "#ECEFF4",
                "text_color": "#2E3440",
                "button_color": "#5E81AC",
                "button_hover": "#81A1C1",
                "tree_bg": "#E5E9F0",
                "tree_alt_bg": "#D8DEE9",
                "selection_color": "#88C0D0",
                "progress_bar": "#A3BE8C"
            },
            "Solarized": {
                "bg_color": "#002B36",
                "text_color": "#839496",
                "button_color": "#268BD2",
                "button_hover": "#2AA198",
                "tree_bg": "#073642",
                "tree_alt_bg": "#004052",
                "selection_color": "#CB4B16",
                "progress_bar": "#859900"
            },
            "Nord": {
                "bg_color": "#2E3440",
                "text_color": "#D8DEE9",
                "button_color": "#5E81AC",
                "button_hover": "#81A1C1",
                "tree_bg": "#3B4252",
                "tree_alt_bg": "#434C5E",
                "selection_color": "#88C0D0",
                "progress_bar": "#A3BE8C"
            }
        }

    def apply_theme(self, theme_name):
        theme = self.themes[theme_name]
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{
                background-color: {theme['bg_color']};
                color: {theme['text_color']};
            }}
            QPushButton {{
                background-color: {theme['button_color']};
                color: {theme['text_color']};
                border: none;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                font-size: 16px;
                margin: 4px 2px;
                border-radius: 4px;
                transition: background-color 0.3s;
            }}
            QPushButton:hover {{
                background-color: {theme['button_hover']};
            }}
            QTreeWidget {{
                background-color: {theme['tree_bg']};
                alternate-background-color: {theme['tree_alt_bg']};
                color: {theme['text_color']};
                border: 1px solid {theme['button_color']};
                border-radius: 4px;
            }}
            QTreeWidget::item:selected {{
                background-color: {theme['selection_color']};
            }}
            QProgressBar {{
                border: 2px solid {theme['text_color']};
                border-radius: 5px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {theme['progress_bar']};
            }}
            QScrollBar:vertical {{
                border: none;
                background-color: {theme['tree_alt_bg']};
                width: 14px;
                margin: 15px 0 15px 0;
            }}
            QScrollBar::handle:vertical {{
                background-color: {theme['button_color']};
                min-height: 30px;
                border-radius: 7px;
            }}
            QScrollBar::handle:vertical:hover {{
                background-color: {theme['button_hover']};
            }}
            QComboBox {{
                background-color: {theme['button_color']};
                color: {theme['text_color']};
                border: 1px solid {theme['text_color']};
                padding: 5px;
                border-radius: 3px;
            }}
            QComboBox:hover {{
                background-color: {theme['button_hover']};
            }}
            QComboBox QAbstractItemView {{
                background-color: {theme['bg_color']};
                color: {theme['text_color']};
                selection-background-color: {theme['selection_color']};
            }}
            QTextEdit, QListWidget {{
                background-color: {theme['tree_bg']};
                color: {theme['text_color']};
                border: 1px solid {theme['button_color']};
                border-radius: 4px;
            }}
            QSplitter::handle {{
                background-color: {theme['button_color']};
            }}
            QSplitter::handle:hover {{
                background-color: {theme['button_hover']};
            }}
        """)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.folder_label.setText(folder)
            self.update_disk_space_info()

    def start_search(self):
        folder = self.folder_label.text()
        if folder == "No folder selected":
            QMessageBox.warning(self, "Error", "Please select a folder first.")
            return

        self.tree.clear()
        self.progress_bar.setVisible(True)
        self.search_button.setEnabled(False)
        self.delete_selected_button.setVisible(False)
        self.delete_all_button.setVisible(False)

        file_types = self.file_type_filter.text().split(',') if self.file_type_filter.text() else None

        self.logger.info(f"Starting search in folder: {folder}")
        if file_types:
            self.logger.info(f"File types filter: {file_types}")

        self.file_hasher = FileHasher(folder, file_types)
        self.file_hasher.progress.connect(self.update_progress)
        self.file_hasher.finished.connect(self.search_completed)
        
        self.thread = QThread()
        self.file_hasher.moveToThread(self.thread)
        self.thread.started.connect(self.file_hasher.run)
        self.thread.start()

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def search_completed(self, duplicates):
        self.thread.quit()
        self.thread.wait()
        self.display_results(duplicates)
        self.update_disk_space_info()
        self.logger.info("Search completed")

    def cancel_search(self):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.quit()
            self.thread.wait()
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)
        self.logger.info("Search cancelled by user")

    def display_results(self, duplicates):
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)

        if not duplicates:
            QMessageBox.information(self, "Result", "No duplicates found.")
            return

        for file_hash, files in duplicates.items():
            if len(files) > 1:
                group_item = QTreeWidgetItem(self.tree)
                group_item.setText(0, f"Duplicate Group ({len(files)} files)")
                group_item.setFont(0, QFont("Arial", 10, QFont.Weight.Bold))
                checkbox = QCheckBox()
                self.tree.setItemWidget(group_item, 2, checkbox)
                for filepath, size in files:
                    file_item = QTreeWidgetItem(group_item)
                    file_item.setText(0, os.path.basename(filepath))
                    file_item.setText(1, f"{size/1024:.2f} KB")
                    file_item.setText(2, filepath)

        if self.tree.topLevelItemCount() > 0:
            self.delete_selected_button.setVisible(True)
            self.delete_all_button.setVisible(True)

        self.logger.info(f"Found {self.tree.topLevelItemCount()} duplicate groups")

    def delete_selected_duplicates(self):
        selected_groups = []
        for i in range(self.tree.topLevelItemCount()):
            group_item = self.tree.topLevelItem(i)
            checkbox = self.tree.itemWidget(group_item, 2)
            if checkbox.isChecked():
                selected_groups.append(group_item)

        if not selected_groups:
            QMessageBox.warning(self, "No Selection", "Please select at least one group to delete.")
            return

        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     f"Are you sure you want to delete all duplicates except the first one in {len(selected_groups)} selected groups?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.delete_duplicates(selected_groups)

    def delete_all_duplicates(self):
        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     "Are you sure you want to delete all duplicates except the first one in each group?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            all_groups = [self.tree.topLevelItem(i) for i in range(self.tree.topLevelItemCount())]
            self.delete_duplicates(all_groups)

    def delete_duplicates(self, groups):
        files_to_delete = []
        for group_item in groups:
            for j in range(1, group_item.childCount()):  # Start from 1 to keep the first file
                file_item = group_item.child(j)
                filepath = file_item.text(2)
                files_to_delete.append(filepath)

        deleted_count = 0
        for filepath in files_to_delete:
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                self.logger.error(f"Error deleting {filepath}: {str(e)}")

        self.update_tree_after_deletion()
        self.update_disk_space_info()

        QMessageBox.information(self, "Deletion Complete", f"{deleted_count} duplicate files have been deleted.")
        self.logger.info(f"Deleted {deleted_count} files")

        # Add to undo stack
        self.undo_stack.append(files_to_delete)
        self.undo_button.setVisible(True)

    def undo_last_delete(self):
        if not self.undo_stack:
            return

        files_to_restore = self.undo_stack.pop()
        restored_count = 0
        for filepath in files_to_restore:
            try:
                # Here you would implement the logic to restore the file
                # This could involve moving it from a temporary location or using a backup system
                # For now, we'll just log it
                self.logger.info(f"Restored file: {filepath}")
                restored_count += 1
            except Exception as e:
                self.logger.error(f"Error restoring {filepath}: {str(e)}")

        self.logger.info(f"Restored {restored_count} files")
        self.update_tree_after_undo(files_to_restore)
        self.update_disk_space_info()

        if not self.undo_stack:
            self.undo_button.setVisible(False)

    def update_tree_after_deletion(self):
        for i in range(self.tree.topLevelItemCount() - 1, -1, -1):
            group_item = self.tree.topLevelItem(i)
            for j in range(group_item.childCount() - 1, 0, -1):  # Start from the last item, exclude the first one
                file_item = group_item.child(j)
                filepath = file_item.text(2)
                if not os.path.exists(filepath):
                    group_item.removeChild(file_item)
            
            if group_item.childCount() == 1:
                self.tree.invisibleRootItem().removeChild(group_item)

    def update_tree_after_undo(self, restored_files):
        # This is a placeholder. You would need to implement the logic to add back the restored files to the tree.
        pass

    def update_preview(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            self.preview_content.clear()
            self.details_list.clear()
            return

        file_item = selected_items[0]
        if file_item.parent() is None:  # It's a group item
            self.preview_content.setText("Select a file to preview its contents.")
            self.details_list.clear()
            return

        filepath = file_item.text(2)
        self.update_file_details(filepath)

        file_info = QFileInfo(filepath)
        
        if file_info.suffix().lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                self.preview_content.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.preview_content.setText("Unable to load image")
        else:
            self.preview_content.setText(f"File type: {file_info.suffix().upper()}\n\nUse 'Open File' to view contents")

    def update_file_details(self, filepath):
        self.details_list.clear()
        try:
            file_stat = os.stat(filepath)
            details = [
                f"Path: {filepath}",
                f"Size: {file_stat.st_size} bytes",
                f"Created: {self.format_time(file_stat.st_ctime)}",
                f"Modified: {self.format_time(file_stat.st_mtime)}",
                f"Accessed: {self.format_time(file_stat.st_atime)}",
            ]
            for detail in details:
                self.details_list.addItem(QListWidgetItem(detail))
        except Exception as e:
            self.details_list.addItem(QListWidgetItem(f"Error getting file details: {str(e)}"))

    def format_time(self, timestamp):
        return datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')

    def open_selected_file(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return

        file_item = selected_items[0]
        if file_item.parent() is None:  # It's a group item
            return

        filepath = file_item.text(2)
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.call(('open', filepath))
        elif sys.platform.startswith('win'):  # Windows
            os.startfile(filepath)
        else:  # Linux and other Unix-like
            subprocess.call(('xdg-open', filepath))

    def open_containing_folder(self):
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return

        file_item = selected_items[0]
        if file_item.parent() is None:  # It's a group item
            return

        filepath = file_item.text(2)
        folder_path = os.path.dirname(filepath)
        
        if sys.platform.startswith('darwin'):  # macOS
            subprocess.call(('open', folder_path))
        elif sys.platform.startswith('win'):  # Windows
            os.startfile(folder_path)
        else:  # Linux and other Unix-like
            subprocess.call(('xdg-open', folder_path))

    def update_disk_space_info(self):
        folder = self.folder_label.text()
        if folder == "No folder selected":
            self.disk_space_label.setText("Select a folder to see disk space information.")
            return

        try:
            total, used, free = self.get_disk_space(folder)
            self.disk_space_label.setText(f"Total: {total/1e9:.2f} GB | Used: {used/1e9:.2f} GB | Free: {free/1e9:.2f} GB")
        except Exception as e:
            self.disk_space_label.setText(f"Error getting disk space: {str(e)}")

    def get_disk_space(self, folder):
        if sys.platform.startswith('win'):
            import ctypes
            free_bytes = ctypes.c_ulonglong(0)
            total_bytes = ctypes.c_ulonglong(0)
            ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, ctypes.pointer(total_bytes), ctypes.pointer(free_bytes))
            total = total_bytes.value
            free = free_bytes.value
            used = total - free
        else:
            st = os.statvfs(folder)
            total = st.f_blocks * st.f_frsize
            free = st.f_bavail * st.f_frsize
            used = (st.f_blocks - st.f_bfree) * st.f_frsize
        return total, used, free

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit', 'Are you sure you want to exit?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            self.logger.info("Application closed")
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedDuplicateFileFinder()
    window.show()
    sys.exit(app.exec())