# File: gui/image_splitter_gui.py
"""
TIFF Splitter GUI Module - Enhanced version matching PDF Splitter interface
Allows splitting multi-page TIFF with custom page ranges and renaming
"""
import os
import sys
import datetime

# --- PyInstaller Path Fix ---
if getattr(sys, 'frozen', False):
    bundle_dir = sys._MEIPASS
    if bundle_dir not in sys.path:
        sys.path.insert(0, bundle_dir)

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog,
    QTableWidget, QSpinBox, QLineEdit, QDateEdit, QHeaderView, QMessageBox,
    QAbstractItemView, QGraphicsDropShadowEffect, QFrame, QComboBox
)
from PyQt5.QtCore import Qt, QDate, QEvent
from PyQt5.QtGui import QFont, QColor


# --- Reusing custom DateEdit from PDF Splitter ---
class ClickableDateEdit(QDateEdit):
    def focusInEvent(self, event):
        super().focusInEvent(event)
        self.calendarWidget().show()
    
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.calendarWidget().show()


class ImageSplitterGUI(QWidget):
    """Split multi-page TIFF files into individual images with renaming support."""
    
    # Premium Dark Theme Colors
    THEME = {
        "bg_gradient_start": "#0a0a1a",
        "bg_gradient_mid": "#0f1629", 
        "bg_gradient_end": "#1a1a2e",
        "text_primary": "#ffffff",
        "text_secondary": "#a8b4d4",
        "accent_primary": "#6366f1",
        "button_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #8b5cf6)",
        "button_hover": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #7c7fff, stop:1 #a78bfa)",
        "split_btn_gradient": "qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:0.5 #06b6d4, stop:1 #3b82f6)",
        "danger_color": "#ef4444",
        "success_color": "#10b981",
        "card_border": "rgba(100, 140, 255, 0.25)",
    }
    
    def __init__(self, go_back_callback=None):
        super().__init__()
        self.go_back_callback = go_back_callback
        self.tiff_path = ""
        self.total_pages = 0
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(14)
        layout.setContentsMargins(30, 20, 30, 20)

        # --- Drag Drop Hint (Top, visible) ---
        drag_hint = QLabel("Drag and Drop TIFF files supported | Tab to add new rows")
        drag_hint.setAlignment(Qt.AlignCenter)
        drag_hint.setStyleSheet("color: #06b6d4; font-size: 12px; font-weight: bold; padding: 8px; background: rgba(6, 182, 212, 0.1); border-radius: 6px;")
        layout.addWidget(drag_hint)

        # --- Header Row: Back Button + Centered Title ---
        header_row = QHBoxLayout()
        
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
            header_row.addWidget(btn_back)
        
        header_row.addStretch()
        
        # Title - Electric Blue Fluorescent, Centered
        title_label = QLabel("Oi360 TIFF SPLITTER")
        title_label.setFont(QFont("Georgia", 38, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: #00d4ff; 
            background: transparent;
            letter-spacing: 3px;
        """)
        # Add glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(30)
        glow.setOffset(0, 0)
        glow.setColor(QColor(0, 212, 255, 200))  # Electric blue glow
        title_label.setGraphicsEffect(glow)
        header_row.addWidget(title_label)
        
        header_row.addStretch()
        layout.addLayout(header_row)

        # --- Subtitle ---
        subtitle = QLabel("Powered by GRACE | Premium Image Management")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #94a3b8; font-style: italic; font-size: 11px;")
        layout.addWidget(subtitle)

        # --- TIFF Info Label ---
        self.info_label = QLabel("TIFF Info: Not loaded")
        self.info_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        self.info_label.setStyleSheet(f"color: {self.THEME['danger_color']}; border: 1px solid {self.THEME['danger_color']}; padding: 10px; border-radius: 10px; background: rgba(239, 68, 68, 0.1);")
        layout.addWidget(self.info_label)

        # --- File Selection Row ---
        file_row = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        self.file_label.setStyleSheet("color: #cbd5e1; font-size: 13px;")
        
        browse_btn = QPushButton("SELECT TIFF FILE")
        browse_btn.setMinimumSize(180, 50)
        browse_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #8b5cf6, stop:1 #a78bfa);
                color: white; font-weight: bold; border-radius: 12px; padding: 10px 20px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a78bfa, stop:1 #c4b5fd); }
        """)
        browse_btn.clicked.connect(self.browse_tiff)
        
        file_row.addWidget(self.file_label, 1)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        # --- Date Picker and Output Format Row ---
        options_row = QHBoxLayout()
        
        # Date Picker
        date_label = QLabel("Download Date:")
        date_label.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 12px;")
        self.date_picker = ClickableDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        self.date_picker.setMinimumSize(180, 42)
        self.date_picker.setStyleSheet("""
            QDateEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                color: white; padding: 8px 12px; border: 1px solid #475569; border-radius: 10px; font-size: 13px;
            }
            QDateEdit:focus { border: 2px solid #06b6d4; }
            QDateEdit::drop-down { border: none; width: 30px; }
        """)
        options_row.addWidget(date_label)
        options_row.addWidget(self.date_picker)
        
        options_row.addStretch()
        
        # Output Format Selector
        format_label = QLabel("Output Format:")
        format_label.setStyleSheet("color: #e2e8f0; font-weight: bold; font-size: 12px;")
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PNG", "JPEG", "TIFF"])
        self.format_combo.setMinimumSize(120, 42)
        self.format_combo.setStyleSheet("""
            QComboBox {
                background: #1e293b; color: #e2e8f0; padding: 8px 16px;
                border: 1px solid #475569; border-radius: 8px; min-width: 120px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView { background: #1e293b; color: #e2e8f0; }
        """)
        options_row.addWidget(format_label)
        options_row.addWidget(self.format_combo)
        
        layout.addLayout(options_row)

        # --- Table (Modern Glassmorphism - Matching PDF Splitter) ---
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Start Page", "End Page", "Output File Name", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setStyleSheet("""
            QTableWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 rgba(30, 41, 59, 0.9), stop:1 rgba(15, 23, 42, 0.95));
                color: white; gridline-color: #334155; border: 1px solid #475569; border-radius: 12px;
            }
            QTableWidget::item { padding: 8px; background: transparent; }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #334155, stop:1 #1e293b);
                color: #e2e8f0; font-weight: bold; padding: 12px; border: none; border-bottom: 2px solid #06b6d4;
            }
        """)
        layout.addWidget(self.table)
        
        self.add_row_widgets(0, start_val=1)

        # --- Split Button ---
        split_btn = QPushButton(">>> SPLIT AND RENAME TIFF <<<")
        split_btn.setMinimumHeight(58)
        split_btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
        split_btn.setCursor(Qt.PointingHandCursor)
        split_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self.THEME['split_btn_gradient']}; 
                color: white; font-weight: bold; border-radius: 14px;
            }}
            QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #34d399, stop:0.5 #22d3ee, stop:1 #60a5fa); }}
        """)
        split_btn.clicked.connect(self.split_tiff)
        layout.addWidget(split_btn)

        self.setLayout(layout)

    def add_row_widgets(self, row_pos, start_val=1):
        self.table.insertRow(row_pos)
        self.table.setRowHeight(row_pos, 52)
        
        # Modern input style
        input_style = """
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
            color: #e2e8f0; padding: 8px 12px; border: 1px solid #475569; border-radius: 8px; font-size: 13px;
        """
        
        start_spin = QSpinBox()
        start_spin.setRange(1, 9999)
        if start_val: start_spin.setValue(start_val)
        start_spin.setStyleSheet(input_style)
        start_spin.setMinimumHeight(38)
        
        end_spin = QSpinBox()
        end_spin.setRange(0, 9999)
        end_spin.setSpecialValueText(" ") 
        end_spin.setStyleSheet(input_style)
        end_spin.setMinimumHeight(38)
        
        name_edit = QLineEdit()
        name_edit.setPlaceholderText("e.g. Invoice001")
        name_edit.setStyleSheet("""
            QLineEdit {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
                color: #e2e8f0; padding: 8px 12px; border: 1px solid #475569; border-radius: 8px; font-size: 13px;
            }
            QLineEdit:focus { border: 2px solid #06b6d4; }
        """)
        name_edit.setMinimumHeight(38)

        # Tab logic - creates new row when Tab is pressed in Output File Name
        def handle_tab():
            end_val = end_spin.value()
            if not end_val or (self.total_pages and end_val >= self.total_pages): 
                return
            next_start = end_val + 1
            if self.total_pages and next_start > self.total_pages: 
                return
            self.add_row_widgets(self.table.rowCount(), start_val=next_start)
            self.table.setCurrentCell(self.table.rowCount() - 1, 0)
        
        # Install event filter for Tab key detection
        name_edit.installEventFilter(self)
        name_edit._tab_handler = handle_tab
        
        remove_btn = QPushButton("DELETE")
        remove_btn.setMinimumSize(80, 38)
        remove_btn.setCursor(Qt.PointingHandCursor)
        remove_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #ef4444, stop:1 #dc2626);
                color: white; font-weight: bold; border-radius: 8px; font-size: 11px;
            }
            QPushButton:hover { background: #f87171; }
        """)
        remove_btn.clicked.connect(lambda: self.remove_row(row_pos))
        
        self.table.setCellWidget(row_pos, 0, start_spin)
        self.table.setCellWidget(row_pos, 1, end_spin)
        self.table.setCellWidget(row_pos, 2, name_edit)
        self.table.setCellWidget(row_pos, 3, remove_btn)

    def eventFilter(self, obj, event):
        """Handle Tab key to create new rows."""
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            if hasattr(obj, '_tab_handler'):
                obj._tab_handler()
                return True
        return super().eventFilter(obj, event)

    def remove_row(self, row):
        if self.table.rowCount() > 1: 
            self.table.removeRow(row)

    def browse_tiff(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select TIFF File", "", "TIFF Files (*.tif *.tiff)")
        if path: 
            self.load_tiff(path)

    def load_tiff(self, path):
        try:
            from PIL import Image
            
            img = Image.open(path)
            self.total_pages = 0
            
            # Count pages in multi-page TIFF
            try:
                while True:
                    self.total_pages += 1
                    img.seek(self.total_pages)
            except EOFError:
                pass
            
            self.tiff_path = path
            self.file_label.setText(os.path.basename(path))
            self.info_label.setText(f"[OK] {os.path.basename(path)} | Pages: {self.total_pages}")
            self.info_label.setStyleSheet(f"color: {self.THEME['success_color']}; border: 1px solid {self.THEME['success_color']}; padding: 10px; border-radius: 8px;")
            
        except ImportError:
            QMessageBox.critical(self, "Error", "Pillow library not found.\nPlease install: pip install Pillow")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load TIFF: {str(e)}")

    def split_tiff(self):
        if not self.tiff_path:
            QMessageBox.warning(self, "Error", "No TIFF selected.")
            return

        # Collect ranges from table
        ranges = []
        date_str = self.date_picker.date().toString("ddMMyyyy")
        output_format = self.format_combo.currentText().lower()
        ext_map = {'png': 'png', 'jpeg': 'jpg', 'tiff': 'tif'}
        ext = ext_map.get(output_format, 'png')
        
        for row in range(self.table.rowCount()):
            s = self.table.cellWidget(row, 0).value()
            e = self.table.cellWidget(row, 1).value()
            n = self.table.cellWidget(row, 2).text().strip()
            
            if n and e > 0:
                # Remove any existing extension
                if '.' in n:
                    n = n.rsplit('.', 1)[0]
                out_name = f"{n}_{date_str}.{ext}"
                ranges.append((s, e, out_name))

        if not ranges:
            QMessageBox.warning(self, "Warning", "Please define at least one range with an output filename.")
            return

        # Ask for output folder
        output_folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if not output_folder:
            return

        try:
            from PIL import Image
            
            img = Image.open(self.tiff_path)
            files_created = 0
            
            for start_page, end_page, out_name in ranges:
                # For single-page output
                if start_page == end_page:
                    img.seek(start_page - 1)  # 0-indexed
                    output_path = os.path.join(output_folder, out_name)
                    
                    # Convert to RGB if saving as JPEG
                    if output_format == 'jpeg' and img.mode in ('RGBA', 'P', 'LA'):
                        page_img = img.copy().convert('RGB')
                    else:
                        page_img = img.copy()
                    
                    page_img.save(output_path)
                    files_created += 1
                else:
                    # For multi-page output (save as multi-page TIFF or multiple files)
                    if output_format == 'tiff':
                        # Save as multi-page TIFF
                        pages_to_save = []
                        for page_num in range(start_page - 1, end_page):
                            img.seek(page_num)
                            pages_to_save.append(img.copy())
                        
                        if pages_to_save:
                            output_path = os.path.join(output_folder, out_name)
                            pages_to_save[0].save(
                                output_path,
                                save_all=True,
                                append_images=pages_to_save[1:] if len(pages_to_save) > 1 else []
                            )
                            files_created += 1
                    else:
                        # For PNG/JPEG, create individual files with page numbers
                        base_name = out_name.rsplit('.', 1)[0]
                        for page_num in range(start_page - 1, end_page):
                            img.seek(page_num)
                            page_filename = f"{base_name}_p{page_num + 1:03d}.{ext}"
                            output_path = os.path.join(output_folder, page_filename)
                            
                            if output_format == 'jpeg' and img.mode in ('RGBA', 'P', 'LA'):
                                page_img = img.copy().convert('RGB')
                            else:
                                page_img = img.copy()
                            
                            page_img.save(output_path)
                            files_created += 1
            
            QMessageBox.information(self, "Success", f"Split Complete!\n{files_created} file(s) saved to:\n{output_folder}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Split failed: {str(e)}")

    # Drag and Drop
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls(): 
            event.accept()
    
    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(('.tif', '.tiff')):
                self.load_tiff(path)
