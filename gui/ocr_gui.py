# File: gui/ocr_gui.py
"""
OCR Engine GUI Module for Oi360 Document Suite
Extracts text from images and scanned PDFs using Tesseract OCR
"""
import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
    QTextEdit, QMessageBox, QGraphicsDropShadowEffect, QComboBox, QApplication,
    QProgressBar, QFrame, QLineEdit, QScrollArea
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QTextCharFormat, QTextCursor, QPixmap, QImage

# --- PyInstaller Path Fix ---
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)


class OCRWorker(QThread):
    """Background thread for OCR processing to keep UI responsive."""
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    
    def __init__(self, file_path, language='eng'):
        super().__init__()
        self.file_path = file_path
        self.language = language
    
    def run(self):
        try:
            import pytesseract
            from PIL import Image
            
            file_ext = os.path.splitext(self.file_path)[1].lower()
            
            # Handle PDF files
            if file_ext == '.pdf':
                self.progress.emit("Converting PDF to images...")
                try:
                    from pdf2image import convert_from_path
                    pages = convert_from_path(self.file_path, dpi=300)
                    
                    all_text = []
                    for i, page in enumerate(pages):
                        self.progress.emit(f"Processing page {i+1} of {len(pages)}...")
                        text = pytesseract.image_to_string(page, lang=self.language)
                        all_text.append(f"--- Page {i+1} ---\n{text}")
                    
                    self.finished.emit("\n\n".join(all_text))
                except ImportError:
                    self.error.emit("pdf2image library not found. Please install: pip install pdf2image")
                    return
            
            # Handle image files
            else:
                self.progress.emit("Processing image...")
                
                # Open and preprocess image
                img = Image.open(self.file_path)
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P', 'LA'):
                    img = img.convert('RGB')
                
                # For multi-page TIFF files
                if file_ext in ('.tif', '.tiff'):
                    all_text = []
                    try:
                        page_num = 0
                        while True:
                            img.seek(page_num)
                            self.progress.emit(f"Processing TIFF page {page_num + 1}...")
                            
                            # Convert current frame to RGB
                            frame = img.copy()
                            if frame.mode in ('RGBA', 'P', 'LA'):
                                frame = frame.convert('RGB')
                            
                            text = pytesseract.image_to_string(frame, lang=self.language)
                            all_text.append(f"--- Page {page_num + 1} ---\n{text}")
                            page_num += 1
                    except EOFError:
                        pass  # End of pages
                    
                    if all_text:
                        self.finished.emit("\n\n".join(all_text))
                    else:
                        self.finished.emit("No text could be extracted from the image.")
                else:
                    # Single image
                    text = pytesseract.image_to_string(img, lang=self.language)
                    self.finished.emit(text if text.strip() else "No text could be extracted from the image.")
        
        except Exception as e:
            self.error.emit(str(e))


class ExternalPreviewWindow(QWidget):
    """Separate window for document preview, useful for dual-monitor setups."""
    
    def __init__(self, title="Document Preview"):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(800, 1000)
        self.setStyleSheet("background: #0a0a1a; color: white;")
        
        self.zoom_factor = 1.0
        self.base_pixmap = None
        
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #06b6d4; font-weight: bold; font-size: 14px;")
        
        self.btn_out = QPushButton("−")
        self.btn_in = QPushButton("+")
        self.btn_fit = QPushButton("FIT WIDTH")
        
        for btn in [self.btn_out, self.btn_in, self.btn_fit]:
            btn.setFixedSize(80 if btn == self.btn_fit else 40, 35)
            btn.setStyleSheet("background: #374151; color: white; border-radius: 5px; font-weight: bold;")
            btn.setCursor(Qt.PointingHandCursor)
            
        self.btn_out.clicked.connect(lambda: self.adjust_zoom(0.8))
        self.btn_in.clicked.connect(lambda: self.adjust_zoom(1.2))
        self.btn_fit.clicked.connect(self.reset_zoom)
        
        toolbar.addWidget(self.btn_out)
        toolbar.addWidget(self.btn_in)
        toolbar.addWidget(self.btn_fit)
        toolbar.addStretch()
        toolbar.addWidget(self.zoom_label)
        layout.addLayout(toolbar)
        
        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("background: #0f172a; border: 1px solid #475569;")
        
        self.label = QLabel("Loading...")
        self.label.setAlignment(Qt.AlignCenter)
        self.scroll.setWidget(self.label)
        layout.addWidget(self.scroll)

    def set_pixmap(self, pixmap, zoom):
        self.base_pixmap = pixmap
        self.zoom_factor = zoom
        self.apply_zoom()
        
    def adjust_zoom(self, factor):
        if self.base_pixmap:
            self.zoom_factor *= factor
            self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))
            self.apply_zoom()
            
    def reset_zoom(self):
        if self.base_pixmap:
            width = self.scroll.width() - 30
            if width > 0:
                self.zoom_factor = width / self.base_pixmap.width()
                if self.zoom_factor > 1.0: self.zoom_factor = 1.0
            self.apply_zoom()
            
    def apply_zoom(self):
        if self.base_pixmap:
            w = int(self.base_pixmap.width() * self.zoom_factor)
            h = int(self.base_pixmap.height() * self.zoom_factor)
            scaled = self.base_pixmap.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled)
            self.zoom_label.setText(f"{int(self.zoom_factor * 100)}%")


class OCRGUI(QWidget):
    """OCR Engine GUI for text extraction from images and PDFs."""
    
    SUPPORTED_FORMATS = ('.tif', '.tiff', '.png', '.jpg', '.jpeg', '.bmp', '.gif', '.pdf')
    
    # Available Tesseract languages (common ones)
    LANGUAGES = {
        'English': 'eng',
        'German': 'deu',
        'French': 'fra',
        'Spanish': 'spa',
        'Italian': 'ita',
        'Portuguese': 'por',
        'Dutch': 'nld',
        'Russian': 'rus',
        'Chinese (Simplified)': 'chi_sim',
        'Japanese': 'jpn',
        'Korean': 'kor',
        'Arabic': 'ara',
        'Hindi': 'hin',
    }
    
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.setAcceptDrops(True)
        self.current_file = None
        self.ocr_worker = None
        self.zoom_factor = 1.0
        self.base_pixmap = None
        self.preview_image = None
        self._preview_data = None
        self.external_window = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 20, 30, 20)
        
        # --- Drag Drop Hint ---
        drag_hint = QLabel("Drag and Drop image or PDF files to extract text")
        drag_hint.setAlignment(Qt.AlignCenter)
        drag_hint.setStyleSheet("""
            color: #06b6d4; font-size: 12px; font-weight: bold; padding: 8px; 
            background: rgba(6, 182, 212, 0.1); border-radius: 6px;
        """)
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
        
        # Title - Electric Blue to match other modules
        title = QLabel("OCR ENGINE")
        title.setFont(QFont("Georgia", 38, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #00d4ff; background: transparent; letter-spacing: 3px;")
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setOffset(0, 0)
        glow.setColor(QColor(0, 212, 255, 200))  # Electric blue glow
        title.setGraphicsEffect(glow)
        header.addWidget(title)
        
        header.addStretch()
        layout.addLayout(header)

        # --- Subtitle ---
        subtitle = QLabel("Extract text from Images & PDFs | Powered by Tesseract OCR")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px;")
        layout.addWidget(subtitle)

        # --- File Selection Row ---
        file_row = QHBoxLayout()
        file_row.setSpacing(10)
        
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("""
            color: #e2e8f0; font-size: 13px; padding: 10px; 
            background: rgba(30, 41, 59, 0.9); border-radius: 8px;
            border: 1px solid #475569;
        """)
        self.file_label.setMinimumHeight(45)
        file_row.addWidget(self.file_label, stretch=1)
        
        btn_browse = QPushButton("📁 BROWSE")
        btn_browse.setFixedSize(120, 45)
        btn_browse.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn_browse.setCursor(Qt.PointingHandCursor)
        btn_browse.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a78bfa);
                color: white; font-weight: bold; border-radius: 10px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a78bfa, stop:1 #c4b5fd); }
        """)
        btn_browse.clicked.connect(self.browse_file)
        file_row.addWidget(btn_browse)
        
        layout.addLayout(file_row)

        # --- PREVIEW AREA (NEW) ---
        preview_group = QVBoxLayout()
        preview_group.setSpacing(5)
        
        preview_header = QHBoxLayout()
        preview_label = QLabel("DOCUMENT PREVIEW:")
        preview_label.setStyleSheet("color: #a8b4d4; font-size: 11px; font-weight: bold;")
        preview_header.addWidget(preview_label)
        
        preview_header.addStretch()
        
        # Zoom Controls
        self.zoom_label = QLabel("100%")
        self.zoom_label.setStyleSheet("color: #06b6d4; font-size: 11px; font-weight: bold; margin-right: 10px;")
        preview_header.addWidget(self.zoom_label)
        
        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_fit = QPushButton("RESET")
        self.btn_detach = QPushButton("🌐 DETACH")
        
        for btn in [self.btn_zoom_out, self.btn_zoom_in, self.btn_zoom_fit, self.btn_detach]:
            btn.setFixedSize(80 if btn in [self.btn_zoom_fit, self.btn_detach] else 35, 28)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    background: #374151; color: white; border-radius: 4px; font-weight: bold; font-size: 11px;
                }
                QPushButton:hover { background: #4b5563; }
                QPushButton:disabled { color: #555; }
            """)
        
        self.btn_detach.setStyleSheet(self.btn_detach.styleSheet().replace("#374151", "#6366f1"))
        
        self.btn_zoom_out.clicked.connect(lambda: self.adjust_zoom(0.8))
        self.btn_zoom_in.clicked.connect(lambda: self.adjust_zoom(1.2))
        self.btn_zoom_fit.clicked.connect(self.reset_zoom)
        self.btn_detach.clicked.connect(self.detach_preview)
        
        preview_header.addWidget(self.btn_zoom_out)
        preview_header.addWidget(self.btn_zoom_in)
        preview_header.addWidget(self.btn_zoom_fit)
        preview_header.addWidget(self.btn_detach)
        
        preview_group.addLayout(preview_header)
        
        self.scroll_area = QScrollArea()
        self.scroll_area.setMinimumHeight(220)
        self.scroll_area.setMaximumHeight(350)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: #0f172a; border: 1px solid #475569; border-radius: 8px;
            }
        """)
        
        self.preview_label = QLabel("No Image Loaded")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("color: #475569; background: transparent;")
        self.scroll_area.setWidget(self.preview_label)
        
        preview_group.addWidget(self.scroll_area)
        layout.addLayout(preview_group)
        
        # --- Language & Extract Row ---
        options_row = QHBoxLayout()
        options_row.setSpacing(15)
        
        lang_label = QLabel("Language:")
        lang_label.setStyleSheet("color: #a8b4d4; font-size: 12px;")
        options_row.addWidget(lang_label)
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(self.LANGUAGES.keys())
        self.lang_combo.setCurrentText("English")
        self.lang_combo.setFixedSize(160, 40)
        self.lang_combo.setStyleSheet("""
            QComboBox {
                background: #1e293b; color: #e2e8f0; border: 1px solid #475569;
                border-radius: 8px; padding: 8px; font-size: 12px;
            }
            QComboBox::drop-down { border: none; width: 30px; }
            QComboBox::down-arrow { image: none; border-left: 5px solid transparent; 
                border-right: 5px solid transparent; border-top: 6px solid #e2e8f0; }
            QComboBox QAbstractItemView { background: #1e293b; color: #e2e8f0; 
                selection-background-color: #06b6d4; }
        """)
        options_row.addWidget(self.lang_combo)
        
        options_row.addStretch()
        
        # Extract Button
        self.btn_extract = QPushButton("🔍 EXTRACT TEXT")
        self.btn_extract.setFixedSize(180, 50)
        self.btn_extract.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.btn_extract.setCursor(Qt.PointingHandCursor)
        self.btn_extract.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #3b82f6);
                color: white; font-weight: bold; border-radius: 12px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #22d3ee, stop:1 #60a5fa); }
            QPushButton:disabled { background: #4b5563; color: #9ca3af; }
        """)
        self.btn_extract.clicked.connect(self.extract_text)
        options_row.addWidget(self.btn_extract)
        
        layout.addLayout(options_row)
        
        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #475569; border-radius: 6px; background: #1e293b; height: 20px;
            }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #3b82f6); }
        """)
        layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #06b6d4; font-size: 11px;")
        layout.addWidget(self.status_label)

        # --- Search & Results Row (Horizontal) ---
        results_layout = QHBoxLayout()
        results_layout.setSpacing(15)
        
        # Left: Results Text Area
        self.text_area = QTextEdit()
        self.text_area.setMinimumHeight(350)
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText("Extracted text will appear here...\n\nYou can then copy and paste into SAP or other applications.")
        self.text_area.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(30, 41, 59, 0.95), stop:1 rgba(15, 23, 42, 0.98));
                color: #e2e8f0; font-size: 13px; font-family: 'Consolas', 'Courier New', monospace;
                border: 1px solid #475569; border-radius: 12px; padding: 12px;
            }
        """)
        results_layout.addWidget(self.text_area, stretch=7)

        # Right: Search Panel
        search_panel = QFrame()
        search_panel.setFixedWidth(260)
        search_panel.setStyleSheet("""
            QFrame {
                background: rgba(30, 41, 59, 0.5);
                border: 1px solid #475569;
                border-radius: 12px;
            }
            QLabel { background: transparent; border: none; }
        """)
        search_vbox = QVBoxLayout(search_panel)
        search_vbox.setContentsMargins(15, 15, 15, 15)
        search_vbox.setSpacing(10)

        search_title = QLabel("SEARCH TOOL")
        search_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        search_title.setStyleSheet("color: #06b6d4; border-bottom: 1px solid #475569; padding-bottom: 5px;")
        search_vbox.addWidget(search_title)

        # Consolidated Search
        search_vbox.addWidget(QLabel("Search Items (Single or List):"))
        self.search_input = QTextEdit()
        self.search_input.setPlaceholderText("Enter one or more terms...\n(one per line for multiple)")
        self.search_input.setMaximumHeight(180)
        self.search_input.setStyleSheet("""
            QTextEdit {
                background: #0f172a; color: white; border: 1px solid #6366f1;
                border-radius: 8px; padding: 10px; font-size: 12px;
            }
        """)
        search_vbox.addWidget(self.search_input)

        self.btn_find = QPushButton("🔍 FIND ALL MATCHES")
        self.btn_find.setMinimumHeight(45)
        self.btn_find.setStyleSheet("""
            QPushButton {
                background: #6366f1; color: white; font-weight: bold; border-radius: 8px;
            }
            QPushButton:hover { background: #818cf8; }
        """)
        self.btn_find.clicked.connect(self.perform_search)
        search_vbox.addWidget(self.btn_find)

        self.btn_clear_search = QPushButton("CLEAR HIGHLIGHTS")
        self.btn_clear_search.setStyleSheet("""
            QPushButton {
                background: #374151; color: #9ca3af; font-size: 11px; border-radius: 6px; padding: 5px;
            }
            QPushButton:hover { background: #4b5563; color: white; }
        """)
        self.btn_clear_search.clicked.connect(self.clear_search_highlights)
        search_vbox.addWidget(self.btn_clear_search)

        self.search_status = QLabel("")
        self.search_status.setWordWrap(True)
        self.search_status.setStyleSheet("color: #22d3ee; font-size: 11px; font-style: italic;")
        search_vbox.addWidget(self.search_status)
        
        search_vbox.addStretch()
        
        results_layout.addWidget(search_panel, stretch=3)
        layout.addLayout(results_layout)

        # --- Action Buttons Row ---
        btn_row = QHBoxLayout()
        btn_row.setSpacing(15)
        
        btn_copy = QPushButton("📋 COPY TO CLIPBOARD")
        btn_copy.setMinimumSize(200, 50)
        btn_copy.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_copy.setCursor(Qt.PointingHandCursor)
        btn_copy.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #059669);
                color: white; font-weight: bold; border-radius: 12px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:1 #10b981); }
        """)
        btn_copy.clicked.connect(self.copy_to_clipboard)
        
        btn_export = QPushButton("💾 EXPORT TO TXT")
        btn_export.setMinimumSize(180, 50)
        btn_export.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_export.setCursor(Qt.PointingHandCursor)
        btn_export.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #3b82f6, stop:1 #2563eb);
                color: white; font-weight: bold; border-radius: 12px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #60a5fa, stop:1 #3b82f6); }
        """)
        btn_export.clicked.connect(self.export_to_txt)
        
        btn_clear = QPushButton("🗑️ CLEAR")
        btn_clear.setMinimumSize(120, 50)
        btn_clear.setFont(QFont("Segoe UI", 12, QFont.Bold))
        btn_clear.setCursor(Qt.PointingHandCursor)
        btn_clear.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626);
                color: white; font-weight: bold; border-radius: 12px;
            }
            QPushButton:hover { background: #f87171; }
        """)
        btn_clear.clicked.connect(self.clear_all)

        btn_row.addWidget(btn_copy)
        btn_row.addWidget(btn_export)
        btn_row.addWidget(btn_clear)
        layout.addLayout(btn_row)

        self.setLayout(layout)

    def browse_file(self):
        # Default to Downloads folder
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_folder):
            downloads_folder = os.path.expanduser("~")
            
        filter_str = "Supported Files (*.tif *.tiff *.png *.jpg *.jpeg *.bmp *.gif *.pdf);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image or PDF", downloads_folder, filter_str)
        if file_path:
            self.load_file(file_path)

    def load_file(self, path):
        self.current_file = path
        filename = os.path.basename(path)
        self.file_label.setText(f"📄 {filename}")
        self.file_label.setToolTip(path)
        self.status_label.setText("")
        self.text_area.clear()
        self.update_preview(path)

    def update_preview(self, path):
        """Generate and display a preview of the loaded file."""
        self.preview_label.setText("Loading preview...")
        QApplication.processEvents()
        
        try:
            from PIL import Image
            file_ext = os.path.splitext(path)[1].lower()
            
            if file_ext == '.pdf':
                try:
                    from pdf2image import convert_from_path
                    # Just convert the first page for preview
                    pages = convert_from_path(path, first_page=1, last_page=1, dpi=100)
                    if pages:
                        self.preview_image = pages[0]
                except Exception as e:
                    self.preview_label.setText(f"PDF Preview Failed: {str(e)}")
                    return
            else:
                try:
                    self.preview_image = Image.open(path)
                except Exception as e:
                    self.preview_label.setText(f"Image Preview Failed: {str(e)}")
                    return
            
            if self.preview_image:
                # Convert PIL Image to QPixmap
                if self.preview_image.mode != "RGB":
                    self.preview_image = self.preview_image.convert("RGB")
                
                width, height = self.preview_image.size
                bytes_per_line = 3 * width
                # CRITICAL: QImage does not copy the data; we must hold a reference
                self._preview_data = self.preview_image.tobytes("raw", "RGB")
                
                qimage = QImage(self._preview_data, width, height, bytes_per_line, QImage.Format_RGB888)
                self.base_pixmap = QPixmap.fromImage(qimage)
                self.reset_zoom()
                
                # Sync with external window if open
                if self.external_window and self.external_window.isVisible():
                    self.external_window.set_pixmap(self.base_pixmap, self.zoom_factor)
        
        except Exception as e:
            self.preview_label.setText(f"Error: {str(e)}")

    def adjust_zoom(self, factor):
        if self.base_pixmap:
            self.zoom_factor *= factor
            # Limit zoom
            self.zoom_factor = max(0.1, min(self.zoom_factor, 5.0))
            self.apply_zoom()

    def reset_zoom(self):
        if self.base_pixmap:
            # Calculate factor to fit width (roughly)
            area_width = self.scroll_area.width() - 30
            if area_width > 0:
                self.zoom_factor = area_width / self.base_pixmap.width()
                # Don't exceed 100% on reset unless it's very small
                if self.zoom_factor > 1.0: self.zoom_factor = 1.0
            else:
                self.zoom_factor = 1.0
            self.apply_zoom()

    def apply_zoom(self):
        if self.base_pixmap:
            new_width = int(self.base_pixmap.width() * self.zoom_factor)
            new_height = int(self.base_pixmap.height() * self.zoom_factor)
            scaled = self.base_pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.preview_label.setPixmap(scaled)
            self.zoom_label.setText(f"{int(self.zoom_factor * 100)}%")
            
            # Sync with external window if open
            if self.external_window and self.external_window.isVisible():
                self.external_window.set_pixmap(self.base_pixmap, self.zoom_factor)

    def detach_preview(self):
        """Open the preview in a separate window."""
        if not self.base_pixmap:
            QMessageBox.warning(self, "Warning", "Please load a document first.")
            return
            
        if not self.external_window:
            self.external_window = ExternalPreviewWindow(f"Preview - {os.path.basename(self.current_file) if self.current_file else ''}")
            
        self.external_window.set_pixmap(self.base_pixmap, self.zoom_factor)
        self.external_window.show()
        self.external_window.raise_()

    def extract_text(self):
        if not self.current_file:
            QMessageBox.warning(self, "Warning", "Please select a file first.")
            return
        
        if not os.path.exists(self.current_file):
            QMessageBox.warning(self, "Warning", "Selected file no longer exists.")
            return
        
        # Get selected language
        lang_name = self.lang_combo.currentText()
        lang_code = self.LANGUAGES.get(lang_name, 'eng')
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.btn_extract.setEnabled(False)
        self.status_label.setText("Starting OCR...")
        self.text_area.clear()
        
        # Run OCR in background thread
        self.ocr_worker = OCRWorker(self.current_file, lang_code)
        self.ocr_worker.finished.connect(self.on_ocr_finished)
        self.ocr_worker.error.connect(self.on_ocr_error)
        self.ocr_worker.progress.connect(self.on_ocr_progress)
        self.ocr_worker.start()

    def on_ocr_finished(self, text):
        self.progress_bar.setVisible(False)
        self.btn_extract.setEnabled(True)
        self.status_label.setText("✅ Extraction complete!")
        self.text_area.setText(text)

    def on_ocr_error(self, error_msg):
        self.progress_bar.setVisible(False)
        self.btn_extract.setEnabled(True)
        self.status_label.setText("❌ Error occurred")
        
        # Friendly suggestion for missing language data
        if "traineddata" in str(error_msg).lower():
            missing_lang = "the selected language"
            if "hin" in str(error_msg).lower(): missing_lang = "Hindi"
            
            help_msg = (
                f"It looks like the <b>{missing_lang}</b> language data is missing for Tesseract.<br><br>"
                f"Please run this command in your terminal to install it:<br>"
                f"<code>sudo apt-get install tesseract-ocr-hin</code><br><br>"
                f"Then restart the app and try again."
            )
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Language Data Missing")
            msg.setText(help_msg)
            msg.setTextFormat(Qt.RichText)
            msg.exec_()
        else:
            QMessageBox.critical(self, "OCR Error", f"Failed to extract text:\n{error_msg}")

    def on_ocr_progress(self, message):
        self.status_label.setText(message)

    def copy_to_clipboard(self):
        text = self.text_area.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Warning", "No text to copy.")
            return
        
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        QMessageBox.information(self, "Success", "Text copied to clipboard!\nYou can now paste it into SAP.")

    def export_to_txt(self):
        text = self.text_area.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Warning", "No text to export.")
            return
        
        downloads_folder = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(downloads_folder):
            downloads_folder = os.path.expanduser("~")
            
        default_name = "extracted_text.txt"
        if self.current_file:
            base = os.path.splitext(os.path.basename(self.current_file))[0]
            default_name = f"{base}_extracted.txt"
        
        initial_path = os.path.join(downloads_folder, default_name)
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Text File", initial_path, "Text Files (*.txt)")
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                QMessageBox.information(self, "Success", f"Text exported to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to save file:\n{str(e)}")

    def clear_all(self):
        self.current_file = None
        self.file_label.setText("No file selected")
        self.text_area.clear()
        self.status_label.setText("")
        self.clear_search_highlights()

    def perform_search(self):
        """Search for matches and highlight them in the text area."""
        self.clear_search_highlights()
        
        # Get search terms from the multi-line edit
        raw_text = self.search_input.toPlainText().strip()
        if not raw_text:
            self.search_status.setText("Enter search terms first.")
            return
            
        search_terms = [line.strip() for line in raw_text.split('\n') if line.strip()]
            
        if not search_terms:
            self.search_status.setText("Enter valid search terms.")
            return

        # Unique terms
        search_terms = list(set(search_terms))
        
        text = self.text_area.toPlainText()
        if not text:
            self.search_status.setText("No text to search.")
            return

        extra_selections = []
        total_matches = 0
        
        # Color palette for highlights
        colors = [
            QColor(255, 255, 0, 100),   # Yellow
            QColor(0, 255, 255, 100),   # Cyan
            QColor(255, 0, 255, 100),   # Magenta
            QColor(0, 255, 0, 100),     # Lime
            QColor(255, 165, 0, 100),   # Orange
        ]
        
        for i, term in enumerate(search_terms):
            color = colors[i % len(colors)]
            
            cursor = self.text_area.document().find(term)
            term_matches = 0
            
            while not cursor.isNull():
                selection = QTextEdit.ExtraSelection()
                selection.format.setBackground(color)
                # selection.format.setForeground(Qt.black)
                selection.cursor = cursor
                extra_selections.append(selection)
                
                term_matches += 1
                total_matches += 1
                # Move to next match
                cursor = self.text_area.document().find(term, cursor)
                
        self.text_area.setExtraSelections(extra_selections)
        
        if total_matches > 0:
            self.search_status.setText(f"Found {total_matches} matches for {len(search_terms)} items.")
        else:
            self.search_status.setText("No matches found.")

    def clear_search_highlights(self):
        """Reset search inputs and clear highlights."""
        # self.single_search_input.clear()
        # self.multi_search_input.clear()
        self.text_area.setExtraSelections([])
        self.search_status.setText("")

    # Drag and Drop Support
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
    
    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if any(path.lower().endswith(ext) for ext in self.SUPPORTED_FORMATS):
                self.load_file(path)
                break  # Only load the first valid file
