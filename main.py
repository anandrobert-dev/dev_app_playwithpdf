# File: main.py
import sys
import os

# --- ADD PROJECT ROOT TO PYTHON PATH ---
# This ensures modules like pdf_utils can be imported when running from any directory
_project_root = os.path.dirname(os.path.abspath(__file__))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QTextEdit, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QAbstractItemView, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QDragEnterEvent, QDropEvent, QTransform, QPainter

# Import the Splitter from your GUI folder
# NOTE: Ensure your folder has an empty __init__.py file inside 'gui' folder if this fails, 
# but usually it works fine in modern Python.
from gui.splitter_gui import PDFSplitterGUI
from gui.image_merger_gui import ImageMergerGUI
from gui.image_splitter_gui import ImageSplitterGUI
from gui.ocr_gui import OCRGUI
from gui.pdf_to_office_gui import PDFToOfficeGUI


# --- RESOURCE PATH HELPER FOR PYINSTALLER ---
def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Use the directory where the script is located, not cwd
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

# --- MERGER LOGIC START ---
from pypdf import PdfWriter, PdfReader
# --- FLOW LAYOUT (FOR RESPONSIVE THUMBNAILS) ---
from PyQt5.QtWidgets import QLayout, QSizePolicy
from PyQt5.QtCore import QPoint, QRect, QSize

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

# --- ROTATING LABEL WIDGET ---
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QPixmap

class RotatingLabel(QLabel):
    """A QLabel that rotates its pixmap continuously."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.angle = 0
        self.original_pixmap = None
        self.rotation_speed = 1  # degrees per tick
        self.clockwise = False  # False = anticlockwise
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.rotate_step)
    
    def setPixmap(self, pixmap):
        self.original_pixmap = pixmap
        super().setPixmap(pixmap)
    
    def start_rotation(self, speed=1, clockwise=False):
        """Start continuous rotation."""
        self.rotation_speed = speed
        self.clockwise = clockwise
        self.timer.start(30)  # ~33 fps
    
    def stop_rotation(self):
        self.timer.stop()
    
    def rotate_step(self):
        if self.original_pixmap is None:
            return
        
        # Update angle (anticlockwise = negative direction)
        if self.clockwise:
            self.angle = (self.angle + self.rotation_speed) % 360
        else:
            self.angle = (self.angle - self.rotation_speed) % 360
        
        # Apply rotation transform
        transform = QTransform()
        transform.translate(self.original_pixmap.width() / 2, self.original_pixmap.height() / 2)
        transform.rotate(self.angle)
        transform.translate(-self.original_pixmap.width() / 2, -self.original_pixmap.height() / 2)
        
        rotated = self.original_pixmap.transformed(transform, Qt.SmoothTransformation)
        super().setPixmap(rotated)

        rotated = self.original_pixmap.transformed(transform, Qt.SmoothTransformation)
        super().setPixmap(rotated)

# --- PAGE ITEM WIDGET ---
from PyQt5.QtWidgets import QCheckBox, QToolButton
from PyQt5.QtGui import QPixmap, QImage

class PageItem(QWidget):
    """Represent an individual PDF page with thumbnail, selection and rotation."""
    def __init__(self, pixmap, original_file, page_index, zoom=1.0):
        super().__init__()
        self.original_file = original_file
        self.page_index = page_index # 0-indexed
        self.rotation = 0
        self.zoom = zoom
        
        self.setStyleSheet("""
            QWidget { background: rgba(30, 41, 59, 0.8); border: 1px solid #475569; border-radius: 8px; }
            QWidget:hover { border: 1px solid #06b6d4; background: rgba(30, 41, 59, 1); }
        """)
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(5)
        
        # Header: Checkbox + Page Label
        header = QHBoxLayout()
        self.checkbox = QCheckBox()
        self.checkbox.setChecked(True)
        self.checkbox.setStyleSheet("QCheckBox::indicator { width: 18px; height: 18px; }")
        header.addWidget(self.checkbox)
        
        self.label = QLabel(f"Page {page_index + 1}")
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

        self.set_thumbnail(pixmap)
        self.update_zoom(zoom)

    def set_thumbnail(self, pixmap):
        self.base_pixmap = pixmap
        self.update_display()

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

class MergerGUI(QWidget):
    def __init__(self, go_back_callback):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.setAcceptDrops(True)
        self.pages = [] # List of PageItem objects
        self.page_zoom = 1.0
        self._page_data_cache = [] # Hold references to prevent slanting (Stride issue)
        self.setup_ui()

    def setup_ui(self):
        # --- Main Scroll Area Wrapper for full page scrolling ---
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 10px; background: transparent; }
            QScrollBar::handle:vertical { background: #334155; border-radius: 5px; min-height: 30px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        # Container widget for scroll area
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        
        layout = QVBoxLayout(scroll_content)
        layout.setSpacing(14)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # --- Drag Drop Hint ---
        drag_hint = QLabel("Drag and Drop PDFs to add | Tick pages to keep | Click ↻ to rotate")
        drag_hint.setAlignment(Qt.AlignCenter)
        drag_hint.setStyleSheet("color: #06b6d4; font-size: 12px; font-weight: bold; padding: 8px; background: rgba(6, 182, 212, 0.1); border-radius: 6px;")
        layout.addWidget(drag_hint)
        
        # --- Header ---
        header = QHBoxLayout()
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
        
        title = QLabel("Oi360 PDF MERGER")
        title.setFont(QFont("Georgia", 38, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00d4ff; background: transparent; letter-spacing: 3px;")
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setOffset(0, 0)
        glow.setColor(QColor(0, 212, 255, 200))
        title.setGraphicsEffect(glow)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        # --- Subtitle ---
        subtitle = QLabel("Powered by GRACE | Visual Page Management")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px;")
        layout.addWidget(subtitle)

        # --- TOOLBAR: Select All / Deselect All / Clear ---
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
        
        btn_add = QPushButton("+ ADD DOCUMENTS")
        btn_add.setMinimumSize(180, 50)
        btn_add.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_add.setCursor(Qt.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a78bfa); color: white; border-radius: 12px; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a78bfa, stop:1 #c4b5fd); }
        """)
        btn_add.clicked.connect(self.add_files_dialog)
        
        btn_clear = QPushButton("CLEAR ALL")
        btn_clear.setMinimumSize(180, 50)
        btn_clear.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626); color: white; border-radius: 12px; }
            QPushButton:hover { background: #f87171; }
        """)
        btn_clear.clicked.connect(self.clear_all_pages)

        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_clear)
        layout.addLayout(btn_row)

        self.btn_merge = QPushButton(">>> GENERATE FINAL PDF (SELECTED PAGES) <<<")
        self.btn_merge.setMinimumHeight(58)
        self.btn_merge.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.btn_merge.setCursor(Qt.PointingHandCursor)
        self.btn_merge.setStyleSheet("""
            QPushButton { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:0.5 #06b6d4, stop:1 #3b82f6); color: white; border-radius: 14px; margin-top: 10px; }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:0.5 #22d3ee, stop:1 #60a5fa); }
        """)
        self.btn_merge.clicked.connect(self.perform_merge)
        layout.addWidget(self.btn_merge)

        # Set scroll content and main layout
        main_scroll.setWidget(scroll_content)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(main_scroll)

    def add_files_dialog(self):
        downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_path): downloads_path = ""
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDFs", downloads_path, "PDF Files (*.pdf)")
        if files:
            for f in files:
                self.add_file_to_grid(f)

    def add_file_to_grid(self, path):
        try:
            from pdf2image import convert_from_path
            # High quality but small enough for grid
            images = convert_from_path(path, dpi=72)
            
            for i, img in enumerate(images):
                if img.mode != "RGB":
                    img = img.convert("RGB")
                
                width, height = img.size
                bytes_per_line = 3 * width
                # Hold reference to raw data to prevent slanting (Stride/GC issue)
                raw_data = img.tobytes("raw", "RGB")
                self._page_data_cache.append(raw_data)
                
                qimage = QImage(raw_data, width, height, bytes_per_line, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimage)
                
                page_item = PageItem(pixmap, path, i, zoom=self.page_zoom)
                self.pages.append(page_item)
                self.flow_layout.addWidget(page_item)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load PDF: {str(e)}")

    def adjust_page_zoom(self, factor):
        self.page_zoom *= factor
        self.page_zoom = max(0.4, min(self.page_zoom, 2.5))
        self.zoom_label.setText(f"{int(self.page_zoom * 100)}%")
        for p in self.pages:
            p.update_zoom(self.page_zoom)
        # Update layout to reflect size changes
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
        # Clear flow layout
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
        default_save_path = os.path.join(downloads_path, "Merged_Document.pdf")
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Combined PDF", default_save_path, "PDF Files (*.pdf)")
        if not save_path: return

        try:
            writer = PdfWriter()
            # Cache readers for performance if multiple pages from same file
            readers = {}
            
            for p in selected_pages:
                if p.original_file not in readers:
                    readers[p.original_file] = PdfReader(p.original_file)
                
                reader = readers[p.original_file]
                page_obj = reader.pages[p.page_index]
                
                if p.rotation != 0:
                    page_obj.rotate(p.rotation)
                
                writer.add_page(page_obj)
            
            with open(save_path, "wb") as f:
                writer.write(f)
            
            QMessageBox.information(self, "Success", f"PDF Generated successfully with {len(selected_pages)} pages!")
            self.clear_all_pages()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Merge failed: {str(e)}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls(): event.accept()
    
    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            if url.toLocalFile().lower().endswith('.pdf'):
                self.add_file_to_grid(url.toLocalFile())
# --- MERGER LOGIC END ---

class WelcomeScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.setup_ui()

    def setup_ui(self):
        # --- Main Scroll Area Wrapper for full page scrolling ---
        main_scroll = QScrollArea()
        main_scroll.setWidgetResizable(True)
        main_scroll.setFrameShape(QScrollArea.NoFrame)
        main_scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 10px; background: transparent; }
            QScrollBar::handle:vertical { background: #334155; border-radius: 5px; min-height: 30px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)
        
        # Container widget for scroll area
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        
        main_layout = QVBoxLayout(scroll_content)
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(20)
        
        # --- Title (Centered, Golden with Glow) ---
        title = QLabel("Oi360 Document SUITE")
        title.setFont(QFont("Georgia", 48, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #ffd700; 
            background: transparent;
            letter-spacing: 4px;
        """)
        # Add golden glow effect
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setOffset(0, 0)
        glow.setColor(QColor(255, 215, 0, 220))  # Pure Golden glow
        title.setGraphicsEffect(glow)
        main_layout.addWidget(title)
        
        # --- Welcome Text (Centered) ---
        desc = QLabel("Welcome to your premium document management dashboard.\nSelect a tool below to begin.")
        desc.setFont(QFont("Segoe UI", 14))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #a8b4d4; margin-bottom: 10px;")
        main_layout.addWidget(desc)
        
        # --- Disclaimer Banner (Elegant & Professional) ---
        disclaimer = QLabel("🎁 FREE FOR INTERNAL USE  •  Enhancing Productivity, Empowering Teams")
        disclaimer.setFont(QFont("Segoe UI", 10))
        disclaimer.setAlignment(Qt.AlignCenter)
        disclaimer.setStyleSheet("""
            color: #22d3ee;
            background: rgba(6, 182, 212, 0.08);
            border: 1px solid rgba(6, 182, 212, 0.3);
            border-radius: 8px;
            padding: 8px 20px;
            margin: 5px 100px 15px 100px;
        """)
        main_layout.addWidget(disclaimer)
        
        # --- Content Area: Left Buttons | Logo | Right Buttons ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(30)
        
        # Import help window
        from gui.help_window import show_help
        
        # Store help windows to keep them alive
        self.help_windows = []
        
        def open_help(tool_key):
            window = show_help(tool_key, self)
            self.help_windows.append(window)
        
        # Helper function to create button rows with help button
        def create_button_row(main_btn, help_key):
            row = QHBoxLayout()
            row.setSpacing(8)
            row.addWidget(main_btn)
            
            help_btn = QPushButton("📖")
            help_btn.setFixedSize(45, 45)
            help_btn.setCursor(Qt.PointingHandCursor)
            help_btn.setToolTip("View Help / SOP")
            help_btn.setStyleSheet("""
                QPushButton {
                    background: rgba(100, 116, 139, 0.6);
                    color: white;
                    border-radius: 10px;
                    font-size: 18px;
                }
                QPushButton:hover {
                    background: rgba(34, 211, 238, 0.8);
                }
            """)
            help_btn.clicked.connect(lambda: open_help(help_key))
            row.addWidget(help_btn)
            return row
        
        # --- LEFT PANEL: PDF Tools (3 buttons) ---
        left_panel = QVBoxLayout()
        left_panel.setSpacing(20)
        left_panel.setAlignment(Qt.AlignCenter)

        btn_split = QPushButton("PDF SPLITTER")
        btn_split.setFixedSize(220, 60)
        btn_split.setCursor(Qt.PointingHandCursor)
        btn_split.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_split.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6); color: white; border-radius: 15px;")
        btn_split.clicked.connect(lambda: self.switch_callback(1))

        btn_merge = QPushButton("PDF MERGER")
        btn_merge.setFixedSize(220, 60)
        btn_merge.setCursor(Qt.PointingHandCursor)
        btn_merge.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_merge.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); color: white; border-radius: 15px;")
        btn_merge.clicked.connect(lambda: self.switch_callback(2))

        btn_pdf_office = QPushButton("PDF to OFFICE")
        btn_pdf_office.setFixedSize(220, 60)
        btn_pdf_office.setCursor(Qt.PointingHandCursor)
        btn_pdf_office.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_pdf_office.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c3aed, stop:1 #a855f7); color: white; border-radius: 15px;")
        btn_pdf_office.clicked.connect(lambda: self.switch_callback(6))

        left_panel.addLayout(create_button_row(btn_split, 'pdf_splitter'))
        left_panel.addLayout(create_button_row(btn_merge, 'pdf_merger'))
        left_panel.addLayout(create_button_row(btn_pdf_office, 'pdf_to_office'))
        
        content_layout.addLayout(left_panel, 30)
        
        # --- CENTER PANEL: Logo (Centered) ---
        center_panel = QVBoxLayout()
        center_panel.setAlignment(Qt.AlignCenter)
        
        from PyQt5.QtGui import QPixmap
        logo_path = resource_path("oi360_logo.png")
        
        logo_label = QLabel()
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(360, 320, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("Logo Not Found")
            logo_label.setStyleSheet("color: #666; font-size: 14px;")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")

        center_panel.addWidget(logo_label)
        content_layout.addLayout(center_panel, 40)
        
        # --- RIGHT PANEL: Other Tools (3 buttons) ---
        right_panel = QVBoxLayout()
        right_panel.setSpacing(20)
        right_panel.setAlignment(Qt.AlignCenter)

        btn_img_split = QPushButton("TIFF SPLITTER")
        btn_img_split.setFixedSize(220, 60)
        btn_img_split.setCursor(Qt.PointingHandCursor)
        btn_img_split.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_img_split.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #0891b2); color: white; border-radius: 15px;")
        btn_img_split.clicked.connect(lambda: self.switch_callback(3))

        btn_img_merge = QPushButton("IMAGE → PDF")
        btn_img_merge.setFixedSize(220, 60)
        btn_img_merge.setCursor(Qt.PointingHandCursor)
        btn_img_merge.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_img_merge.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ec4899, stop:1 #db2777); color: white; border-radius: 15px;")
        btn_img_merge.clicked.connect(lambda: self.switch_callback(4))

        btn_ocr = QPushButton("OCR ENGINE")
        btn_ocr.setFixedSize(220, 60)
        btn_ocr.setCursor(Qt.PointingHandCursor)
        btn_ocr.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_ocr.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6B00, stop:1 #FF9500); color: white; border-radius: 15px;")
        btn_ocr.clicked.connect(lambda: self.switch_callback(5))

        right_panel.addLayout(create_button_row(btn_img_split, 'tiff_splitter'))
        right_panel.addLayout(create_button_row(btn_img_merge, 'image_to_pdf'))
        right_panel.addLayout(create_button_row(btn_ocr, 'ocr_engine'))
        
        content_layout.addLayout(right_panel, 30)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()
        
        # Copyright footer
        copyright_label = QLabel("© 2026 Koinonia Technologies. All rights reserved.\nProprietary Software | Independent Development")
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet("color: #64748b; font-size: 11px; padding: 10px;")
        main_layout.addWidget(copyright_label)
        
        # Set scroll content and main layout
        main_scroll.setWidget(scroll_content)
        
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(main_scroll)

class MainApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oi360 Document Suite - Powered by GRACE")
        self.resize(1100, 750)
        
        # Global Stylesheet
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0a0a1a, stop:0.5 #0f1629, stop:1 #1a1a2e); }
            QWidget { font-family: 'Segoe UI', sans-serif; }
        """)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Pages
        self.page_welcome = WelcomeScreen(self.switch_to_page)
        self.page_splitter = PDFSplitterGUI(go_back_callback=self.go_home)
        self.page_merger = MergerGUI(go_back_callback=self.go_home)
        self.page_img_splitter = ImageSplitterGUI(go_back_callback=self.go_home)
        self.page_img_merger = ImageMergerGUI(go_back_callback=self.go_home)
        self.page_ocr = OCRGUI(go_back_callback=self.go_home)
        self.page_pdf_office = PDFToOfficeGUI(go_back_callback=self.go_home)

        self.stack.addWidget(self.page_welcome)      # Index 0
        self.stack.addWidget(self.page_splitter)     # Index 1
        self.stack.addWidget(self.page_merger)       # Index 2
        self.stack.addWidget(self.page_img_splitter) # Index 3
        self.stack.addWidget(self.page_img_merger)   # Index 4
        self.stack.addWidget(self.page_ocr)          # Index 5
        self.stack.addWidget(self.page_pdf_office)   # Index 6

    def switch_to_page(self, index):
        self.stack.setCurrentIndex(index)

    def go_home(self):
        self.stack.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())