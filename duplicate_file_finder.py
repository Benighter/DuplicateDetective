import os
import sys
import subprocess
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QFileDialog, QLabel, QTreeWidgetItem, QMessageBox, 
                             QCheckBox, QScrollArea, QComboBox, QSplitter,
                             QTextEdit, QPushButton, QListWidget, QListWidgetItem,
                             QFileIconProvider)
from PyQt6.QtGui import QFont, QIcon, QColor, QPixmap
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QSize, QFileInfo
from helpers import FileHasher, AnimatedButton, CustomTreeWidget, DeletionWorker, CancellableProgressBar

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

        # Deletion progress bar
        self.deletion_progress_bar = CancellableProgressBar()
        self.deletion_progress_bar.setVisible(False)
        self.deletion_progress_bar.cancelled.connect(self.cancel_deletion)
        left_layout.addWidget(self.deletion_progress_bar)

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

        self.hasher = FileHasher(folder)
        self.hasher.progress.connect(self.update_progress)
        self.hasher.finished.connect(self.display_results)
        self.hasher.start()

    def cancel_search(self):
        if hasattr(self, 'hasher'):
            self.hasher.cancel()
        self.search_cancelled()

    def search_cancelled(self):
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)
        QMessageBox.information(self, "Search Cancelled", "The search operation was cancelled.")

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def display_results(self, duplicates):
        self.progress_bar.setVisible(False)
        self.search_button.setEnabled(True)

        if not duplicates:
            QMessageBox.information(self, "Search Cancelled", "The search operation was cancelled.")
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
        else:
            QMessageBox.information(self, "Result", "No duplicates found.")

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

        self.deletion_worker = DeletionWorker(files_to_delete)
        self.deletion_worker.progress.connect(self.update_deletion_progress)
        self.deletion_worker.finished.connect(self.deletion_completed)

        self.deletion_progress_bar.setVisible(True)
        self.delete_selected_button.setEnabled(False)
        self.delete_all_button.setEnabled(False)

        self.deletion_worker.start()

    def cancel_deletion(self):
        if hasattr(self, 'deletion_worker'):
            self.deletion_worker.cancel()
        self.deletion_cancelled()

    def deletion_cancelled(self):
        self.deletion_progress_bar.setVisible(False)
        self.delete_selected_button.setEnabled(True)
        self.delete_all_button.setEnabled(True)
        QMessageBox.information(self, "Deletion Cancelled", "The deletion operation was cancelled.")

    def update_deletion_progress(self, value):
        self.deletion_progress_bar.setValue(value)

    def deletion_completed(self, deleted_count):
        self.deletion_progress_bar.setVisible(False)
        self.delete_selected_button.setEnabled(True)
        self.delete_all_button.setEnabled(True)

        QMessageBox.information(self, "Deletion Complete", f"{deleted_count} duplicate files have been deleted.")

        # Update the tree view
        self.update_tree_after_deletion()

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
        icon_provider = QFileIconProvider()
        icon = icon_provider.icon(file_info)
        
        if file_info.suffix().lower() in ['jpg', 'jpeg', 'png', 'gif', 'bmp']:
            pixmap = QPixmap(filepath)
            if not pixmap.isNull():
                self.preview_content.setPixmap(pixmap.scaled(300, 300, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                self.preview_content.setText("Unable to load image")
        else:
            self.preview_content.setText(f"File type: {file_info.suffix().upper()}\n\nUse 'Open File' to view contents")
        
        self.preview_content.setStyleSheet(f"background-color: {self.themes[self.theme_selector.currentText()]['bg_color']};")

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

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Exit', 'Are you sure you want to exit?',
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            event.accept()
        else:
            event.ignore()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdvancedDuplicateFileFinder()
    window.show()
    sys.exit(app.exec())