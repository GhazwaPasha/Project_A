"""
Skeleton Loader Component
Provides loading states that match the final layout for smooth transitions
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
                            QGridLayout, QTableWidget, QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QPainter, QColor, QLinearGradient
from ..common import ResponsiveHelper


class SkeletonCard(QFrame):
    """Skeleton card that mimics MetricCard layout"""
    
    def __init__(self, title="", subtitle="", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self._setup_ui()
        self._start_animation()
    
    def _setup_ui(self):
        """Setup skeleton card UI"""
        layout = QVBoxLayout(self)
        margins = ResponsiveHelper.scale_size(16, 12, 20)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(ResponsiveHelper.scale_size(8, 6, 12))
        
        # Header skeleton
        header_layout = QHBoxLayout()
        header_layout.setSpacing(ResponsiveHelper.scale_size(8, 6, 12))
        
        # Title skeleton
        self.title_skeleton = SkeletonText(120, 16)
        header_layout.addWidget(self.title_skeleton)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Value skeleton (larger)
        self.value_skeleton = SkeletonText(80, 24)
        layout.addWidget(self.value_skeleton)
        
        # Subtitle skeleton
        if self.subtitle:
            self.subtitle_skeleton = SkeletonText(100, 12)
            layout.addWidget(self.subtitle_skeleton)
        
        layout.addStretch()
        
        # Apply styling
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
    
    def _start_animation(self):
        """Start shimmer animation"""
        self.title_skeleton.start_animation()
        self.value_skeleton.start_animation()
        if hasattr(self, 'subtitle_skeleton'):
            self.subtitle_skeleton.start_animation()


class SkeletonText(QFrame):
    """Skeleton text element with shimmer animation"""
    
    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup skeleton text UI"""
        # Use fixed size for now to avoid linter issues
        self.setFixedSize(self.width, self.height)
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
            }}
        """)
    
    def start_animation(self):
        """Start shimmer animation"""
        self.animation = QPropertyAnimation(self, b"styleSheet")
        self.animation.setDuration(1500)
        self.animation.setLoopCount(-1)  # Infinite loop
        
        # Create shimmer effect
        self.animation.setStartValue(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.1),
                    stop:0.5 rgba(255, 255, 255, 0.2),
                    stop:1 rgba(255, 255, 255, 0.1));
                border-radius: 4px;
            }}
        """)
        
        self.animation.setEndValue(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(255, 255, 255, 0.1),
                    stop:0.5 rgba(255, 255, 255, 0.2),
                    stop:1 rgba(255, 255, 255, 0.1));
                border-radius: 4px;
            }}
        """)
        
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.animation.start()


class SkeletonTable(QTableWidget):
    """Skeleton table that mimics data table layout"""
    
    def __init__(self, rows=5, columns=4, parent=None):
        super().__init__(parent)
        self.rows = rows
        self.columns = columns
        self._setup_ui()
        self._start_animation()
    
    def _setup_ui(self):
        """Setup skeleton table UI"""
        self.setRowCount(self.rows)
        self.setColumnCount(self.columns)
        
        # Set header labels
        headers = [f"Column {i+1}" for i in range(self.columns)]
        self.setHorizontalHeaderLabels(headers)
        
        # Configure table
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for i in range(1, self.columns):
            header.setSectionResizeMode(i, QHeaderView.ResizeMode.ResizeToContents)
        
        # Add skeleton cells
        for row in range(self.rows):
            for col in range(self.columns):
                skeleton_cell = SkeletonText(80, 20)
                self.setCellWidget(row, col, skeleton_cell)
        
        # Apply styling
        self.setStyleSheet("""
            QTableWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                gridline-color: rgba(255, 255, 255, 0.1);
            }
            QHeaderView::section {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                padding: 8px;
                border: none;
                font-weight: 600;
            }
        """)
    
    def _start_animation(self):
        """Start animation for all skeleton cells"""
        for row in range(self.rows):
            for col in range(self.columns):
                cell_widget = self.cellWidget(row, col)
                if isinstance(cell_widget, SkeletonText):
                    cell_widget.start_animation()


class SkeletonLoader:
    """Main skeleton loader class for managing loading states"""
    
    @staticmethod
    def create_dashboard_skeleton(parent=None):
        """Create skeleton layout for dashboard"""
        skeleton_widget = QWidget(parent)
        layout = QVBoxLayout(skeleton_widget)
        layout.setSpacing(ResponsiveHelper.scale_size(20, 16, 24))
        
        # Create skeleton cards in a grid
        grid = QGridLayout()
        grid.setSpacing(ResponsiveHelper.scale_size(20, 16, 28))
        
        # Add skeleton cards
        for row in range(4):
            for col in range(4):
                skeleton_card = SkeletonCard(f"Metric {row*4 + col + 1}", "Loading...")
                grid.addWidget(skeleton_card, row, col)
        
        layout.addLayout(grid)
        return skeleton_widget
    
    @staticmethod
    def create_table_skeleton(rows=10, columns=6, parent=None):
        """Create skeleton table"""
        return SkeletonTable(rows, columns, parent)
    
    @staticmethod
    def create_form_skeleton(fields=5, parent=None):
        """Create skeleton form"""
        skeleton_widget = QWidget(parent)
        layout = QVBoxLayout(skeleton_widget)
        layout.setSpacing(ResponsiveHelper.scale_size(16, 12, 20))
        
        for i in range(fields):
            field_layout = QHBoxLayout()
            
            # Label skeleton
            label_skeleton = SkeletonText(100, 20)
            field_layout.addWidget(label_skeleton)
            
            # Input skeleton
            input_skeleton = SkeletonText(200, 30)
            field_layout.addWidget(input_skeleton)
            
            field_layout.addStretch()
            layout.addLayout(field_layout)
        
        layout.addStretch()
        return skeleton_widget 