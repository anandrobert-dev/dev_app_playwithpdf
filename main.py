# File: main.py
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, 
    QStackedWidget, QTextEdit, QListWidget, QListWidgetItem, QFileDialog, QMessageBox,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFont, QIcon, QColor, QDragEnterEvent, QDropEvent

# Import the Splitter from your GUI folder
# NOTE: Ensure your folder has an empty __init__.py file inside 'gui' folder if this fails, 
# but usually it works fine in modern Python.
from gui.splitter_gui import PDFSplitterGUI
from gui.image_merger_gui import ImageMergerGUI
from gui.image_splitter_gui import ImageSplitterGUI
from gui.ocr_gui import OCRGUI


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
from pypdf import PdfWriter

class MergerGUI(QWidget):
    def __init__(self, go_back_callback):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.setAcceptDrops(True)
        self.files_to_merge = [] # List of tuples (filename, fullpath)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # --- Drag Drop Hint (Top, visible) ---
        drag_hint = QLabel("Drag and Drop PDF files to add | Drag items to re-order")
        drag_hint.setAlignment(Qt.AlignCenter)
        drag_hint.setStyleSheet("color: #06b6d4; font-size: 12px; font-weight: bold; padding: 8px; background: rgba(6, 182, 212, 0.1); border-radius: 6px;")
        layout.addWidget(drag_hint)
        
        # --- Header Row: Back Button + Centered Title ---
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
        
        # Title - Electric Blue Fluorescent, Centered (matching Splitter)
        title = QLabel("Oi360 PDF MERGER")
        title.setFont(QFont("Georgia", 38, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #00d4ff; 
            background: transparent;
            letter-spacing: 3px;
        """)
        # Add glow effect
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setOffset(0, 0)
        glow.setColor(QColor(0, 212, 255, 200))  # Electric blue glow
        title.setGraphicsEffect(glow)
        header.addWidget(title)
        
        header.addStretch()
        layout.addLayout(header)

        # --- Subtitle ---
        subtitle = QLabel("Powered by GRACE | Premium PDF Management")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px;")
        layout.addWidget(subtitle)

        # --- List Widget (Modern Glassmorphism) ---
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
        
        btn_add = QPushButton("+ ADD FILES")
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

        # --- Merge Button (Same style as Split button) ---
        self.btn_merge = QPushButton(">>> MERGE SELECTED FILES <<<")
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
        files, _ = QFileDialog.getOpenFileNames(self, "Select PDFs", "", "PDF Files (*.pdf)")
        if files:
            for f in files:
                self.add_file_to_list(f)

    def add_file_to_list(self, path):
        item = QListWidgetItem(os.path.basename(path))
        item.setData(Qt.UserRole, path) # Store full path in hidden data
        self.list_widget.addItem(item)

    def perform_merge(self):
        count = self.list_widget.count()
        if count < 2:
            QMessageBox.warning(self, "Warning", "Please add at least 2 PDF files to merge.")
            return

        # Ask where to save
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Merged PDF", "Merged_Invoice.pdf", "PDF Files (*.pdf)")
        if not save_path: return

        try:
            merger = PdfWriter()
            for i in range(count):
                item = self.list_widget.item(i)
                full_path = item.data(Qt.UserRole)
                merger.append(full_path)
            
            merger.write(save_path)
            merger.close()
            
            QMessageBox.information(self, "Success", f"Files Merged Successfully!\nLocation: {save_path}")
            self.list_widget.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Merge failed: {str(e)}")

    # Drag and Drop Support
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls(): event.accept()
    
    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            if url.toLocalFile().lower().endswith('.pdf'):
                self.add_file_to_list(url.toLocalFile())
# --- MERGER LOGIC END ---

class WelcomeScreen(QWidget):
    def __init__(self, switch_callback):
        super().__init__()
        self.switch_callback = switch_callback
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(20)
        
        # --- Title (Centered, Fluorescent Orange) ---
        title = QLabel("Oi360 Document SUITE")
        title.setFont(QFont("Georgia", 48, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            color: #FF6B00; 
            background: transparent;
            letter-spacing: 4px;
        """)
        # Add glow effect
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(25)
        glow.setOffset(0, 0)
        glow.setColor(QColor(255, 107, 0, 200))  # Fluorescent Orange glow
        title.setGraphicsEffect(glow)
        main_layout.addWidget(title)
        
        # --- Welcome Text (Centered) ---
        desc = QLabel("Welcome to your premium document management dashboard.\nSelect a tool below to begin.")
        desc.setFont(QFont("Segoe UI", 14))
        desc.setAlignment(Qt.AlignCenter)
        desc.setStyleSheet("color: #a8b4d4; margin-bottom: 20px;")
        main_layout.addWidget(desc)
        
        # --- Content Area: Logo + Buttons ---
        content_layout = QHBoxLayout()
        content_layout.setSpacing(40)
        
        # --- LEFT PANEL: Logo (Big, Centered) ---
        left_panel = QVBoxLayout()
        left_panel.setAlignment(Qt.AlignCenter)
        
        from PyQt5.QtGui import QPixmap
        # Use resource_path for PyInstaller compatibility
        logo_path = resource_path("oi360_logo.png")
        
        logo_label = QLabel()
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path).scaled(420, 380, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("Logo Not Found")
            logo_label.setStyleSheet("color: #666; font-size: 14px;")
        logo_label.setAlignment(Qt.AlignCenter)
        logo_label.setStyleSheet("background: transparent;")

        left_panel.addWidget(logo_label)
        content_layout.addLayout(left_panel, 55)
        
        # Right: Buttons (moved more to the right)
        right_panel = QVBoxLayout()
        right_panel.setSpacing(25)
        right_panel.setAlignment(Qt.AlignCenter | Qt.AlignRight)

        btn_split = QPushButton("PDF SPLITTER")
        btn_split.setFixedSize(280, 70)
        btn_split.setCursor(Qt.PointingHandCursor)
        btn_split.setFont(QFont("Segoe UI", 14, QFont.Bold))
        btn_split.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6); color: white; border-radius: 15px;")
        btn_split.clicked.connect(lambda: self.switch_callback(1))

        btn_merge = QPushButton("PDF MERGER")
        btn_merge.setFixedSize(280, 70)
        btn_merge.setCursor(Qt.PointingHandCursor)
        btn_merge.setFont(QFont("Segoe UI", 14, QFont.Bold))
        btn_merge.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669); color: white; border-radius: 15px;")
        btn_merge.clicked.connect(lambda: self.switch_callback(2))

        right_panel.addWidget(btn_split)
        right_panel.addWidget(btn_merge)

        # --- Image Module Buttons ---
        btn_img_split = QPushButton("TIFF SPLITTER")
        btn_img_split.setFixedSize(280, 70)
        btn_img_split.setCursor(Qt.PointingHandCursor)
        btn_img_split.setFont(QFont("Segoe UI", 14, QFont.Bold))
        btn_img_split.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #0891b2); color: white; border-radius: 15px;")
        btn_img_split.clicked.connect(lambda: self.switch_callback(3))

        btn_img_merge = QPushButton("IMAGE → PDF")
        btn_img_merge.setFixedSize(280, 70)
        btn_img_merge.setCursor(Qt.PointingHandCursor)
        btn_img_merge.setFont(QFont("Segoe UI", 14, QFont.Bold))
        btn_img_merge.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ec4899, stop:1 #db2777); color: white; border-radius: 15px;")
        btn_img_merge.clicked.connect(lambda: self.switch_callback(4))

        # --- OCR Engine Button ---
        btn_ocr = QPushButton("OCR ENGINE")
        btn_ocr.setFixedSize(280, 70)
        btn_ocr.setCursor(Qt.PointingHandCursor)
        btn_ocr.setFont(QFont("Segoe UI", 14, QFont.Bold))
        btn_ocr.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #FF6B00, stop:1 #FF9500); color: white; border-radius: 15px;")
        btn_ocr.clicked.connect(lambda: self.switch_callback(5))

        right_panel.addWidget(btn_img_split)
        right_panel.addWidget(btn_img_merge)
        right_panel.addWidget(btn_ocr)
        
        content_layout.addLayout(right_panel, 45)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()
        self.setLayout(main_layout)

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

        self.stack.addWidget(self.page_welcome)      # Index 0
        self.stack.addWidget(self.page_splitter)     # Index 1
        self.stack.addWidget(self.page_merger)       # Index 2
        self.stack.addWidget(self.page_img_splitter) # Index 3
        self.stack.addWidget(self.page_img_merger)   # Index 4
        self.stack.addWidget(self.page_ocr)          # Index 5

    def switch_to_page(self, index):
        self.stack.setCurrentIndex(index)

    def go_home(self):
        self.stack.setCurrentIndex(0)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainApp()
    window.show()
    sys.exit(app.exec_())