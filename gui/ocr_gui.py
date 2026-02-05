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
    QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

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

        # --- Results Text Area ---
        results_label = QLabel("Extracted Text:")
        results_label.setStyleSheet("color: #a8b4d4; font-size: 12px; margin-top: 10px;")
        layout.addWidget(results_label)
        
        self.text_area = QTextEdit()
        self.text_area.setMinimumHeight(250)
        self.text_area.setReadOnly(True)
        self.text_area.setPlaceholderText("Extracted text will appear here...\n\nYou can then copy and paste into SAP or other applications.")
        self.text_area.setStyleSheet("""
            QTextEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(30, 41, 59, 0.95), stop:1 rgba(15, 23, 42, 0.98));
                color: #e2e8f0; font-size: 13px; font-family: 'Consolas', 'Courier New', monospace;
                border: 1px solid #475569; border-radius: 12px; padding: 12px;
            }
        """)
        layout.addWidget(self.text_area)

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
        filter_str = "Supported Files (*.tif *.tiff *.png *.jpg *.jpeg *.bmp *.gif *.pdf);;All Files (*)"
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image or PDF", "", filter_str)
        if file_path:
            self.load_file(file_path)

    def load_file(self, path):
        self.current_file = path
        filename = os.path.basename(path)
        self.file_label.setText(f"📄 {filename}")
        self.file_label.setToolTip(path)
        self.status_label.setText("")
        self.text_area.clear()

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
        
        default_name = "extracted_text.txt"
        if self.current_file:
            base = os.path.splitext(os.path.basename(self.current_file))[0]
            default_name = f"{base}_extracted.txt"
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Save Text File", default_name, "Text Files (*.txt)")
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
