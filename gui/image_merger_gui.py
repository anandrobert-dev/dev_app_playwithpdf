# File: gui/image_merger_gui.py
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
    QListWidget, QListWidgetItem, QMessageBox, QAbstractItemView,
    QGraphicsDropShadowEffect, QLayout, QSizePolicy, QScrollArea, QCheckBox, QToolButton
)
from PyQt5.QtCore import Qt, QPoint, QRect, QSize
from PyQt5.QtGui import QFont, QColor, QPixmap, QImage, QTransform

# --- FLOW LAYOUT (FOR RESPONSIVE THUMBNAILS) ---
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing()
            spaceY = self.spacing()
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()

# --- IMAGE PAGE ITEM WIDGET ---
class ImagePageItem(QWidget):
    """Represent an individual image/page with thumbnail, selection and rotation."""
    def __init__(self, pixmap, original_file, page_index=0, zoom=1.0):
        super().__init__()
        self.original_file = original_file
        self.page_index = page_index
        self.rotation = 0
        self.zoom = zoom
        self.base_pixmap = pixmap
        
        self.setStyleSheet("""
            QWidget { background: rgba(30, 41, 59, 0.8); border: 1px solid #475569; border-radius: 8px; }
            QWidget:hover { border: 1px solid #06b6d4; background: rgba(30, 41, 59, 1); }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(5)
        
        # Header: Checkbox + Label
        header = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")
        header.addWidget(self.checkbox)
        
        name = os.path.basename(original_file)
        if page_index > 0:
            name += f" (P{page_index + 1})"
        self.label = QLabel(name)
        self.label.setStyleSheet("color: #a8b4d4; font-size: 10px; font-weight: bold; border: none; background: transparent;")
        header.addWidget(self.label, stretch=1)
        
        self.layout.addLayout(header)
        
        # Thumbnail
        self.thumb_label = QLabel()
        self.thumb_label.setAlignment(Qt.AlignCenter)
        self.thumb_label.setStyleSheet("border: none; background: #0f172a;")
        self.layout.addWidget(self.thumb_label)
        
        # Footer: Rotate Button
        self.footer = QHBoxLayout()
        self.btn_rotate = QToolButton()
        self.btn_rotate.setText("↻")
        self.btn_rotate.setToolTip("Rotate 90°")
        self.btn_rotate.setStyleSheet("""
            QToolButton { background: #334155; color: white; border: none; border-radius: 4px; padding: 2px; }
            QToolButton:hover { background: #475569; }
        """)
        self.btn_rotate.clicked.connect(self.rotate_page)
        self.footer.addStretch()
        self.footer.addWidget(self.btn_rotate)
        self.layout.addLayout(self.footer)

        self.update_zoom(zoom)

    def update_zoom(self, zoom):
        self.zoom = zoom
        w = int(160 * zoom)
        h = int(220 * zoom)
        self.setFixedSize(w, h)
        
        thumb_w = int(140 * zoom)
        thumb_h = int(150 * zoom)
        self.thumb_label.setFixedSize(thumb_w, thumb_h)
        
        font_size = max(6, int(10 * zoom))
        self.label.setStyleSheet(f"color: #a8b4d4; font-size: {font_size}px; font-weight: bold; border: none; background: transparent;")
        
        self.update_display()

    def update_display(self):
        if self.base_pixmap:
            thumb_w = self.thumb_label.width()
            thumb_h = self.thumb_label.height()
            
            transform = QTransform().rotate(self.rotation)
            rotated = self.base_pixmap.transformed(transform, Qt.SmoothTransformation)
            scaled = rotated.scaled(thumb_w, thumb_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.thumb_label.setPixmap(scaled)

    def rotate_page(self):
        self.rotation = (self.rotation + 90) % 360
        self.update_display()

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
        self.pages = [] # List of ImagePageItem objects
        self.page_zoom = 1.0
        self._page_data_cache = [] # Hold references to raw data
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # --- Drag Drop Hint ---
        drag_hint = QLabel("Drag and Drop image files to add | Tick items to keep | Click ↻ to rotate")
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
        subtitle = QLabel("Merge images into PDF | Visual Page Management")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px;")
        layout.addWidget(subtitle)

        # --- TOOLBAR: Select All / Deselect All / Zoom ---
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        
        btn_sel_all = QPushButton("SELECT ALL")
        btn_desel_all = QPushButton("DESELECT ALL")
        
        for btn in [btn_sel_all, btn_desel_all]:
            btn.setFixedSize(130, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background: #1e293b; color: #94a3b8; border: 1px solid #475569; border-radius: 6px; font-size: 10px; font-weight: bold; }
                QPushButton:hover { background: #334155; color: white; }
            """)
        
        btn_sel_all.clicked.connect(lambda: self.toggle_all_selection(True))
        btn_desel_all.clicked.connect(lambda: self.toggle_all_selection(False))
        
        toolbar.addWidget(btn_sel_all)
        toolbar.addWidget(btn_desel_all)
        toolbar.addStretch()
        
        # --- ZOOM CONTROLS ---
        zoom_box = QHBoxLayout()
        zoom_box.setSpacing(5)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #06b6d4; font-weight: bold; font-size: 13px; margin-right: 5px;")
        
        btn_zoom_out = QPushButton("−")
        btn_zoom_in = QPushButton("+")
        btn_zoom_reset = QPushButton("RESET")
        
        for btn in [btn_zoom_out, btn_zoom_in, btn_zoom_reset]:
            btn.setFixedSize(60 if btn == btn_zoom_reset else 32, 32)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton { background: #374151; color: white; border-radius: 6px; font-weight: bold; }
                QPushButton:hover { background: #4b5563; }
            """)
            
        btn_zoom_out.clicked.connect(lambda: self.adjust_page_zoom(0.8))
        btn_zoom_in.clicked.connect(lambda: self.adjust_page_zoom(1.2))
        btn_zoom_reset.clicked.connect(self.reset_page_zoom)
        
        zoom_box.addWidget(btn_zoom_out)
        zoom_box.addWidget(btn_zoom_in)
        zoom_box.addWidget(btn_zoom_reset)
        zoom_box.addWidget(self.zoom_label)
        
        toolbar.addLayout(zoom_box)
        layout.addLayout(toolbar)

        # --- Grid Area (Scrollable) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(350)
        self.scroll_area.setStyleSheet("""
            QScrollArea { background: #0f172a; border: 1px solid #475569; border-radius: 12px; }
            QScrollBar:vertical { width: 10px; background: transparent; }
            QScrollBar::handle:vertical { background: #334155; border-radius: 5px; }
        """)
        
        self.grid_widget = QWidget()
        self.grid_widget.setStyleSheet("background: transparent; border: none;")
        self.flow_layout = FlowLayout(self.grid_widget, margin=15, spacing=15)
        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)

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
        btn_clear.clicked.connect(self.clear_all_pages)

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
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_path): downloads_path = ""
        filter_str = "Image Files (*.tif *.tiff *.png *.jpg *.jpeg *.bmp *.gif)"
        files, _ = QFileDialog.getOpenFileNames(self, "Select Images", downloads_path, filter_str)
        if files:
            for f in files:
                self.add_file_to_grid(f)

    def add_file_to_grid(self, path):
        try:
            from PIL import Image
            img = Image.open(path)
            
            # Handle multi-page TIFF
            pages = []
            try:
                while True:
                    pages.append(img.copy())
                    img.seek(img.tell() + 1)
            except EOFError:
                pass
            
            for i, page_img in enumerate(pages):
                if page_img.mode != "RGB":
                    page_img = page_img.convert("RGB")
                
                width, height = page_img.size
                # Convert PIL image to QImage
                raw_data = page_img.tobytes("raw", "RGB")
                self._page_data_cache.append(raw_data)
                
                qimage = QImage(raw_data, width, height, 3 * width, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)
                
                page_item = ImagePageItem(pixmap, path, i, zoom=self.page_zoom)
                self.pages.append(page_item)
                self.flow_layout.addWidget(page_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load image: {str(e)}")

    def adjust_page_zoom(self, factor):
        self.page_zoom *= factor
        self.page_zoom = max(0.4, min(self.page_zoom, 2.5))
        self.zoom_label.setText(f"{int(self.page_zoom * 100)}%")
        for p in self.pages:
            p.update_zoom(self.page_zoom)
        self.flow_layout.update()

    def reset_page_zoom(self):
        self.page_zoom = 1.0
        self.zoom_label.setText("100%")
        for p in self.pages:
            p.update_zoom(1.0)
        self.flow_layout.update()

    def toggle_all_selection(self, status):
        for p in self.pages:
            p.checkbox.setChecked(status)

    def clear_all_pages(self):
        self.pages = []
        self._page_data_cache = []
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def perform_merge(self):
        selected_pages = [p for p in self.pages if p.checkbox.isChecked()]
        if not selected_pages:
            QMessageBox.warning(self, "Warning", "Please select at least one page to merge.")
            return

        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        default_save_path = os.path.join(downloads_path, "merged_images.pdf")
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", default_save_path, "PDF Files (*.pdf)")
        if not save_path:
            return

        try:
            import img2pdf
            from PIL import Image
            import io
            
            processed_images = [] # Bytes of images to merge
            
            for p in selected_pages:
                img = Image.open(p.original_file)
                # If multi-page TIFF, seek to correct page
                if p.page_index > 0:
                    img.seek(p.page_index)
                
                # Apply rotation
                if p.rotation != 0:
                    img = img.rotate(-p.rotation, expand=True) # Pillow rotates CCW, UI rotates CW
                
                # Convert to RGB (required for JPEG/PDF)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Save to buffer
                img_byte_arr = io.BytesIO()
                img.save(img_byte_arr, format='JPEG')
                processed_images.append(img_byte_arr.getvalue())
            
            # Create PDF
            with open(save_path, "wb") as f:
                f.write(img2pdf.convert(processed_images))
            
            QMessageBox.information(self, "Success", f"Images merged to PDF successfully!\nLocation: {save_path}")
            self.clear_all_pages()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Merge failed: {str(e)}")

    # Drag and Drop Support
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if any(path.lower().endswith(ext) for ext in self.SUPPORTED_FORMATS):
                self.add_file_to_grid(path)
