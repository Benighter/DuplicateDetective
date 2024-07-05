import os
import hashlib
from collections import defaultdict
from PyQt6.QtWidgets import QPushButton, QTreeWidget, QProgressBar, QHBoxLayout, QWidget
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QSize

class FileHasher(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(dict)

    def __init__(self, root_dir):
        super().__init__()
        self.root_dir = root_dir
        self.cancelled = False

    def run(self):
        duplicates = defaultdict(list)
        total_files = sum([len(files) for r, d, files in os.walk(self.root_dir)])
        processed_files = 0

        for root, _, files in os.walk(self.root_dir):
            for filename in files:
                if self.cancelled:
                    return
                filepath = os.path.join(root, filename)
                try:
                    file_hash = self.hash_file(filepath)
                    file_size = os.path.getsize(filepath)
                    duplicates[file_hash].append((filepath, file_size))
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
                processed_files += 1
                self.progress.emit(int(processed_files / total_files * 100))

        self.finished.emit(duplicates)

    def hash_file(self, filepath):
        BLOCK_SIZE = 65536
        file_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            fb = f.read(BLOCK_SIZE)
            while len(fb) > 0:
                if self.cancelled:
                    return None
                file_hash.update(fb)
                fb = f.read(BLOCK_SIZE)
        return file_hash.hexdigest()

    def cancel(self):
        self.cancelled = True

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

class DeletionWorker(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(int)

    def __init__(self, files_to_delete):
        super().__init__()
        self.files_to_delete = files_to_delete
        self.cancelled = False

    def run(self):
        deleted_count = 0
        total_files = len(self.files_to_delete)
        for i, filepath in enumerate(self.files_to_delete):
            if self.cancelled:
                break
            try:
                os.remove(filepath)
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {filepath}: {e}")
            self.progress.emit(int((i + 1) / total_files * 100))
        self.finished.emit(deleted_count)

    def cancel(self):
        self.cancelled = True

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