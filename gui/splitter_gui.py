# Cleaned and fully fixed version of splitter_gui.py with indentation and refresh

import os
import datetime
from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QTableWidget,
    QSpinBox, QLineEdit, QDateEdit, QHeaderView, QMessageBox, QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate, QEvent
from PyQt5.QtGui import QPixmap
from PyPDF2 import PdfReader

class PDFSplitterGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Oi360 PDF Splitter - Powered by GRACE")
        self.setMinimumSize(950, 580)
        self.pdf_path = ""
        self.total_pages = 0
        self.setAcceptDrops(True)
        self.setup_ui()

    def setup_ui(self):
        self.setStyleSheet(""" ...styles remain unchanged... """)
        layout = QVBoxLayout()

        logo = QLabel()
        logo.setPixmap(QPixmap("oi360_logo.jpeg").scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        logo.setAlignment(Qt.AlignRight)
        layout.addWidget(logo)

        self.info_label = QLabel("PDF Info: Not loaded")
        layout.addWidget(self.info_label)

        file_row = QHBoxLayout()
        self.file_label = QLabel("No file selected")
        browse_btn = QPushButton("Select PDF")
        browse_btn.clicked.connect(self.browse_pdf)
        file_row.addWidget(self.file_label)
        file_row.addWidget(browse_btn)
        layout.addLayout(file_row)

        date_row = QHBoxLayout()
        date_label = QLabel("Download Date:")
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDate(QDate.currentDate())
        date_row.addWidget(date_label)
        date_row.addWidget(self.date_picker)
        layout.addLayout(date_row)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Start Page", "End Page", "Output File Name", ""])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        self.add_row_widgets(0, start_val=1)

        split_btn = QPushButton("🚀 Split & Rename PDFs")
        split_btn.clicked.connect(self.split_pdf)
        layout.addWidget(split_btn)

        self.setLayout(layout)

    def add_row_widgets(self, row_pos, start_val=None):
        self.table.insertRow(row_pos)
        start_spin = QSpinBox(); start_spin.setMinimum(1); start_spin.setMaximum(9999)
        if start_val: start_spin.setValue(start_val)
        end_spin = QSpinBox(); end_spin.setMinimum(1); end_spin.setMaximum(9999)
        name_edit = QLineEdit(); name_edit.setPlaceholderText("e.g. Invoice001")

        def handle_tab():
            end_val = end_spin.value()
            if not end_val or (self.total_pages and end_val >= self.total_pages): return
            next_start = end_val + 1
            if self.total_pages and next_start > self.total_pages: return
            self.add_row_widgets(self.table.rowCount(), start_val=next_start)
            self.table.setCurrentCell(self.table.rowCount() - 1, 0)

        name_edit.installEventFilter(self); name_edit._tab_handler = handle_tab
        remove_btn = QPushButton("❌"); remove_btn.setStyleSheet("background-color: #ff4d4d; color: white;"); remove_btn.clicked.connect(lambda: self.table.removeRow(row_pos))
        self.table.setCellWidget(row_pos, 0, start_spin)
        self.table.setCellWidget(row_pos, 1, end_spin)
        self.table.setCellWidget(row_pos, 2, name_edit)
        self.table.setCellWidget(row_pos, 3, remove_btn)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            if hasattr(obj, '_tab_handler'):
                obj._tab_handler()
                return True
        return super().eventFilter(obj, event)

    def browse_pdf(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if path:
            self.load_pdf(path)

    def load_pdf(self, path):
        self.pdf_path = path
        self.file_label.setText(os.path.basename(path))
        file_size = os.path.getsize(path) / (1024 * 1024)
        reader = PdfReader(path)
        self.total_pages = len(reader.pages)
        self.info_label.setText(f"📄 {os.path.basename(path)} | Pages: {self.total_pages} | Size: {file_size:.1f} MB")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls and urls[0].toLocalFile().lower().endswith(".pdf"):
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path.lower().endswith(".pdf"):
                self.load_pdf(path)
            else:
                self.show_error("Only PDF files are supported.")

    def show_message(self, msg):
        QMessageBox.information(self, "Success", msg)

    def show_error(self, msg):
        QMessageBox.critical(self, "Error", msg)

    def split_pdf(self):
        if not self.pdf_path:
            self.show_error("No PDF file selected.")
            return

        date_str = self.date_picker.date().toString("ddMMyyyy")
        used_names = set()
        ranges = []

        for row in range(self.table.rowCount()):
            start_widget = self.table.cellWidget(row, 0)
            end_widget = self.table.cellWidget(row, 1)
            name_widget = self.table.cellWidget(row, 2)

            if not (start_widget and end_widget and name_widget): continue
            start = start_widget.value(); end = end_widget.value(); name = name_widget.text().strip()
            if not name or end == 0: continue
            if not name.lower().endswith(".pdf"): name += ".pdf"
            output_name = f"{name.rsplit('.', 1)[0]}_{date_str}.pdf"
            if output_name in used_names:
                self.show_error(f"Duplicate file name: {output_name}"); return
            if start > end:
                self.show_error(f"Start page must be <= end page (Row {row + 1})"); return
            ranges.append((start, end, output_name)); used_names.add(output_name)

        try:
            output_folder = os.path.join(os.path.dirname(self.pdf_path), "split_output")
            os.makedirs(output_folder, exist_ok=True)
        except PermissionError:
            self.show_error(f"Permission denied to create output folder in: {os.path.dirname(self.pdf_path)}"); return

        try:
            from pdf_utils.splitter import split_pdf_by_ranges
        except ImportError:
            self.show_error("Split function not found."); return

        success = split_pdf_by_ranges(self.pdf_path, ranges, output_folder)

        try:
            log_file = os.path.join(output_folder, "split_log.txt")
            with open(log_file, "w") as log:
                log.write(f"Split Log for: {os.path.basename(self.pdf_path)}\n")
                log.write(f"Total Pages: {self.total_pages}\n")
                log.write(f"Split Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                for start, end, name in ranges:
                    log.write(f"Pages {start}-{end} -> {name}\n")
        except Exception as e:
            print(f"Log write failed: {e}")

        if success:
            self.show_message(f"✅ Split completed!\nSaved to: {output_folder}")
            self.table.setRowCount(0)
            self.add_row_widgets(0, start_val=1)
        else:
            self.show_error("Something went wrong during PDF splitting.")
