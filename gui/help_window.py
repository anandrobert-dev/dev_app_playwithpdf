# Help Window Component for Oi360 Document Suite
# A detachable, non-modal window for displaying SOP documentation

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextBrowser, QPushButton, QHBoxLayout,
    QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class HelpWindow(QDialog):
    """
    A detachable help window that displays SOP documentation.
    Can be moved to a second monitor for dual-display setups.
    """
    
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"📖 {title} - Help")
        self.setMinimumSize(550, 600)
        self.setMaximumSize(700, 800)
        
        # Make it a normal window (not modal, movable, stays on top optional)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.WindowMinimizeButtonHint)
        
        # Styling
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                    stop:0 #0f172a, stop:0.5 #1e293b, stop:1 #0f172a);
            }
        """)
        
        self.setup_ui(title, content)
    
    def setup_ui(self, title, content):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel(f"📖 {title}")
        header.setFont(QFont("Georgia", 20, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            color: #22d3ee;
            background: transparent;
            padding: 10px;
        """)
        
        # Add glow effect
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(20)
        glow.setOffset(0, 0)
        glow.setColor(QColor(34, 211, 238, 150))
        header.setGraphicsEffect(glow)
        
        layout.addWidget(header)
        
        # Content Browser (supports HTML)
        self.content_browser = QTextBrowser()
        self.content_browser.setHtml(self._wrap_content(content))
        self.content_browser.setOpenExternalLinks(False)
        self.content_browser.setStyleSheet("""
            QTextBrowser {
                background: rgba(30, 41, 59, 0.9);
                color: #e2e8f0;
                border: 1px solid #475569;
                border-radius: 12px;
                padding: 15px;
                font-size: 13px;
                line-height: 1.6;
            }
            QScrollBar:vertical {
                width: 10px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #475569;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        layout.addWidget(self.content_browser)
        
        # Footer buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_close = QPushButton("✓ Got It!")
        btn_close.setFixedSize(120, 40)
        btn_close.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn_close.setCursor(Qt.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #10b981, stop:1 #059669);
                color: white;
                border-radius: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #34d399, stop:1 #10b981);
            }
        """)
        btn_close.clicked.connect(self.close)
        
        btn_layout.addWidget(btn_close)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _wrap_content(self, content):
        """Wrap content with consistent HTML styling."""
        return f"""
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #e2e8f0;
                line-height: 1.7;
            }}
            h2 {{
                color: #22d3ee;
                border-bottom: 2px solid #06b6d4;
                padding-bottom: 8px;
                margin-bottom: 15px;
            }}
            h3 {{
                color: #a78bfa;
                margin-top: 20px;
                margin-bottom: 10px;
            }}
            ul, ol {{
                margin-left: 5px;
                padding-left: 20px;
            }}
            li {{
                margin-bottom: 8px;
            }}
            b {{
                color: #fbbf24;
            }}
            span {{
                padding: 2px 6px;
                border-radius: 4px;
            }}
        </style>
        {content}
        """


def show_help(tool_key, parent=None):
    """
    Convenience function to show help for a specific tool.
    
    Args:
        tool_key: One of 'pdf_splitter', 'pdf_merger', 'pdf_to_office', 
                  'tiff_splitter', 'image_to_pdf', 'ocr_engine'
        parent: Optional parent widget
    """
    from gui.help_content import HELP_CONTENT
    
    titles = {
        'pdf_splitter': 'PDF Splitter',
        'pdf_merger': 'PDF Merger',
        'pdf_to_office': 'PDF to Office',
        'tiff_splitter': 'TIFF Splitter',
        'image_to_pdf': 'Image → PDF',
        'ocr_engine': 'OCR Engine'
    }
    
    title = titles.get(tool_key, 'Help')
    content = HELP_CONTENT.get(tool_key, '<p>Help content not available.</p>')
    
    window = HelpWindow(title, content, parent)
    window.show()
    return window
