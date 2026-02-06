from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QPainter, QPen, QBrush, QColor

class SelectablePreviewLabel(QLabel):
    """Custom QLabel that supports drawing selection rectangles for region-based processing."""
    
    selection_changed = pyqtSignal(object)  # Emits (x, y, w, h) in original image coords or None
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.selection_mode = False
        self.selection_start = None
        self.selection_end = None
        self.zoom_factor = 1.0
        self.setMouseTracking(True)
        self.setScaledContents(False)
        
    def setPixmap(self, pixmap):
        """Override to track pixmap and adjust size."""
        super().setPixmap(pixmap)
        if pixmap:
            self.setMinimumSize(pixmap.size())
            self.setMaximumSize(pixmap.size())
        
    def set_selection_mode(self, enabled):
        """Enable or disable selection mode."""
        self.selection_mode = enabled
        if enabled:
            self.setCursor(Qt.CrossCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
            self.clear_selection()
        
    def clear_selection(self):
        """Clear the current selection."""
        self.selection_start = None
        self.selection_end = None
        self.selection_changed.emit(None)
        self.update()
        
    def get_selection_rect(self):
        """Get selection rectangle in original image coordinates."""
        if not self.selection_start or not self.selection_end:
            return None
            
        # Get selection in widget coordinates
        x1 = min(self.selection_start.x(), self.selection_end.x())
        y1 = min(self.selection_start.y(), self.selection_end.y())
        x2 = max(self.selection_start.x(), self.selection_end.x())
        y2 = max(self.selection_start.y(), self.selection_end.y())
        
        # Ensure it's within pixmap bounds
        if self.pixmap():
            x1 = max(0, min(x1, self.pixmap().width()))
            y1 = max(0, min(y1, self.pixmap().height()))
            x2 = max(0, min(x2, self.pixmap().width()))
            y2 = max(0, min(y2, self.pixmap().height()))
        
        if x1 == x2 or y1 == y2:
            return None

        # Convert to original image coordinates
        if self.zoom_factor > 0:
            x1 = int(x1 / self.zoom_factor)
            y1 = int(y1 / self.zoom_factor)
            x2 = int(x2 / self.zoom_factor)
            y2 = int(y2 / self.zoom_factor)
            
        return (x1, y1, x2 - x1, y2 - y1)
        
    def mousePressEvent(self, event):
        if self.selection_mode and event.button() == Qt.LeftButton:
            self.selection_start = event.pos()
            self.selection_end = event.pos()
            self.update()
        super().mousePressEvent(event)
        
    def mouseMoveEvent(self, event):
        if self.selection_mode and self.selection_start and event.buttons() & Qt.LeftButton:
            self.selection_end = event.pos()
            self.update()
        super().mouseMoveEvent(event)
        
    def mouseReleaseEvent(self, event):
        if self.selection_mode and event.button() == Qt.LeftButton and self.selection_start:
            self.selection_end = event.pos()
            rect = self.get_selection_rect()
            if rect and rect[2] > 5 and rect[3] > 5:  # Minimum selection size
                self.selection_changed.emit(rect)
            else:
                self.clear_selection()
            self.update()
        super().mouseReleaseEvent(event)
        
    def paintEvent(self, event):
        super().paintEvent(event)
        
        if self.selection_start and self.selection_end:
            painter = QPainter(self)
            
            # Draw selection rectangle
            x1 = min(self.selection_start.x(), self.selection_end.x())
            y1 = min(self.selection_start.y(), self.selection_end.y())
            x2 = max(self.selection_start.x(), self.selection_end.x())
            y2 = max(self.selection_start.y(), self.selection_end.y())
            
            # Semi-transparent cyan fill
            painter.setBrush(QBrush(QColor(6, 182, 212, 50)))
            painter.setPen(QPen(QColor(6, 182, 212), 2, Qt.DashLine))
            painter.drawRect(x1, y1, x2 - x1, y2 - y1)
            
            painter.end()
