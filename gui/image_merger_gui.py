# File: gui/image_merger_gui.py
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QAbstractItemView,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# --- PyInstaller Path Fix ---
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

class ImageMergerGUI(QWidget):
    """Merge multiple images into a single PDF or multi-page TIFF."""
    
    SUPPORTED_FORMATS = ('.tif', '.tiff', '.png', '.jpg', '.jpeg', '.bmp', '.gif')
    
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # --- Drag Drop Hint ---
        drag_hint = QLabel("Drag and Drop image files to add | Drag items to re-order")
        drag_hint.setAlignment(Qt.AlignCenter)
        drag_hint.setStyleSheet("color: #06b6d4; font-size: 12px; font-weight: bold; padding: 8px; background: rgba(6, 182, 212, 0.1); border-radius: 6px;")
        layout.addWidget(drag_hint)
        
        # --- Header Row ---
        header = QHBoxLayout()
        
        if self.go_back_callback:
            btn_back = QPushButton("« MAIN MENU")
            btn_back.setFixedSize(140, 42)
            btn_back.setCursor(Qt.PointingHandCursor)
            btn_back.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #374151, stop:1 #4b5563);
                    color: #e5e7eb; border-radius: 10px; font-weight: bold; font-size: 11px;
                    border: 1px solid #6b7280;
                }
                QPushButton:hover { background: #4b5563; }
            """)
            btn_back.clicked.connect(self.go_back_callback)
            header.addWidget(btn_back)
        
        header.addStretch()
        
        # Title - Electric Blue
        title = QLabel("IMAGE MERGER")
        title.setFont(QFont("Georgia", 38, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00d4ff; background: transparent; letter-spacing: 3px;")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setOffset(0, 0)
        glow.setColor(QColor(0, 212, 255, 200))
        title.setGraphicsEffect(glow)
        header.addWidget(title)
        
        header.addStretch()
        layout.addLayout(header)

        # --- Subtitle ---
        subtitle = QLabel("Merge images into PDF | Supports TIF, PNG, JPG")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px;")
        layout.addWidget(subtitle)

        # --- List Widget ---
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QAbstractItemView.InternalMove)
        self.list_widget.setMinimumHeight(250)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(30, 41, 59, 0.9), stop:1 rgba(15, 23, 42, 0.95));
                color: #e2e8f0; font-size: 14px; border: 1px solid #475569; border-radius: 12px; padding: 12px;
            }
            QListWidget::item {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                border: 1px solid #475569; border-radius: 8px; padding: 10px; margin: 4px;
            }
            QListWidget::item:selected { background: #06b6d4; border: 2px solid #22d3ee; }
            QListWidget::item:hover { background: #334155; }
        """)
        layout.addWidget(self.list_widget)

        # --- Buttons Row ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)
        
        btn_add = QPushButton("+ ADD IMAGES")
        btn_add.setMinimumSize(180, 50)
        btn_add.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a78bfa);
                color: white; font-weight: bold; border-radius: 12px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a78bfa, stop:1 #c4b5fd); }
        """)
        btn_add.clicked.connect(self.add_files_dialog)
        
        btn_clear = QPushButton("CLEAR LIST")
        btn_clear.setMinimumSize(180, 50)
        btn_clear.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626);
                color: white; font-weight: bold; border-radius: 12px;
            }
            QPushButton:hover { background: #f87171; }
        """)
        btn_clear.clicked.connect(self.list_widget.clear)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_clear)
        layout.addLayout(btn_row)

        # --- Merge Button ---
        self.btn_merge = QPushButton(">>> MERGE TO PDF <<<")
        self.btn_merge.setMinimumHeight(58)
        self.btn_merge.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.btn_merge.setCursor(Qt.PointingHandCursor)
        self.btn_merge.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:0.5 #06b6d4, stop:1 #3b82f6);
                color: white; font-weight: bold; border-radius: 14px; margin-top: 10px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:0.5 #22d3ee, stop:1 #60a5fa); }
        """)
        self.btn_merge.clicked.connect(self.perform_merge)
        layout.addWidget(self.btn_merge)

        self.setLayout(layout)

    def add_files_dialog(self):
        filter_str = "Image Files (*.tif *.tiff *.png *.jpg *.jpeg *.bmp *.gif)"
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", "", filter_str)
        if files:
            for f in files:
                self.add_file_to_list(f)

    def add_file_to_list(self, path):
        item = QListWidgetItem(os.path.basename(path))
        item.setData(Qt.UserRole, path)
        self.list_widget.addItem(item)

    def perform_merge(self):
        count = self.list_widget.count()
        if count < 2:
            QMessageBox.warning(self, "Warning", "Please add at least 2 images to merge.")
            return

        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "merged_images.pdf", "PDF Files (*.pdf)")
        if not save_path:
            return

        try:
            import img2pdf
            from PIL import Image
            
            image_paths = []
            for i in range(count):
                item = self.list_widget.item(i)
                image_paths.append(item.data(Qt.UserRole))
            
            # Convert images to RGB if needed (for RGBA/P mode images)
            converted_paths = []
            temp_files = []
            
            for img_path in image_paths:
                img = Image.open(img_path)
                if img.mode in ('RGBA', 'P', 'LA'):
                    rgb_img = img.convert('RGB')
                    temp_path = img_path + '_temp.jpg'
                    rgb_img.save(temp_path, 'JPEG')
                    converted_paths.append(temp_path)
                    temp_files.append(temp_path)
                else:
                    converted_paths.append(img_path)
            
            # Create PDF
            with open(save_path, "wb") as f:
                f.write(img2pdf.convert(converted_paths))
            
            # Cleanup temp files
            for temp in temp_files:
                if os.path.exists(temp):
                    os.remove(temp)
            
            QMessageBox.information(self, "Success", f"Images merged to PDF!\nLocation: {save_path}")
            self.list_widget.clear()
            
        except ImportError:
            QMessageBox.critical(self, "Error", "Required library 'img2pdf' or 'Pillow' not found.\nPlease install: pip install img2pdf Pillow")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Merge failed: {str(e)}")

    # Drag and Drop Support
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile().lower()
            if any(path.endswith(ext) for ext in self.SUPPORTED_FORMATS):
                self.add_file_to_list(url.toLocalFile())
