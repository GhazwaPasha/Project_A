"""
Modern Reports Page - Completely Rebuilt
Structure:
1. Top KPI section (non-expandable, max 2 rows)
2. Financial Statements (expandable with small cards)
3. Ratios (expandable with small cards)
4. Analysis Reports (expandable with small cards)

Built with ledger-style card design and glassmorphism UI.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QScrollArea,
    ResponsiveHelper, Qt, QGridLayout, QSizePolicy, QSpacerItem, QStackedWidget
)
from PyQt6.QtWidgets import QMessageBox
from ..components.widgets import PageHeader, DateRangeSelector
from ..components.report_views import (
    IncomeStatementView, BalanceSheetView, CashFlowStatementView, StatementOfEquityView
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QCursor


class ReportCard(QFrame):
    """Small report card based on ledger card design."""
    
    cardClicked = pyqtSignal(str)  # Report name
    
    def __init__(self, title, subtitle="", value="", color="#64B5F6", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.value = value
        self.color = color
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the card UI based on ledger card design."""
        self.setFixedHeight(110)  # Increased height to prevent text clipping
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);                border-radius: 8px;
                border-color: rgba(0, 0, 0, 0.3);
                margin: 4px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)  # Reduced margins for more space
        layout.setSpacing(4)  # Reduced spacing for better fit
        
        # Header row with colored indicator
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)
        
        # Colored indicator
        indicator = QLabel("●")
        indicator.setStyleSheet(f"""
            color: {self.color};
            font-weight: 600;
            font-size: 10px;
            background: transparent;
            border: none;
        """)
        indicator.setFixedSize(12, 12)  # Fixed size to prevent layout issues
        header_layout.addWidget(indicator)
        
        header_layout.addStretch()
        
        # Subtitle/category
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.6);
                font-size: 9px;
                font-weight: 500;
                background: transparent;
                border: none;
            """)
            subtitle_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            header_layout.addWidget(subtitle_label)
        
        layout.addLayout(header_layout)
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            color: white;
            font-weight: 600;
            font-size: 12px;
            background: transparent;
            border: none;
            line-height: 1.2;
        """)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(title_label)
        
        # Value row
        if self.value:
            value_label = QLabel(self.value)
            value_label.setStyleSheet(f"""
                color: {self.color};
                font-weight: 700;
                font-size: 13px;
                background: transparent;
                border: none;
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
            layout.addWidget(value_label)
        else:
            layout.addStretch()
        
    def mousePressEvent(self, event):
        """Handle card click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.cardClicked.emit(self.title)
        super().mousePressEvent(event)


class KPICard(QFrame):
    """KPI card for the top section - larger than report cards."""
    
    def __init__(self, title, value, subtitle="", color="#4CAF50", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the KPI card UI."""
        self.setFixedHeight(120)  # Back to original height
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                margin: 4px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)  # Back to original margins
        layout.setSpacing(8)  # Back to original spacing
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8);
            font-weight: 500;
            font-size: 12px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(title_label)
          # Value
        value_label = QLabel(self.value)
        value_label.setStyleSheet(f"""
            color: white;
            font-weight: 700;
            font-size: 18px;
            background: transparent;
            border: none;
        """)
        layout.addWidget(value_label)
        
        # Subtitle
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setStyleSheet(f"""
                color: {self.color};
                font-size: 10px;
                font-weight: 500;
                background: transparent;
                border: none;
            """)
            layout.addWidget(subtitle_label)


class ExpandableSection(QWidget):
    """Expandable section with journal-style header and content area."""
    
    def __init__(self, title, subtitle="", icon="📊", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.icon = icon
        self.is_expanded = False
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the expandable section with journal-style header."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Clickable header frame (journal style)
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 12px;
                padding: 0px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
            }
        """)
        self.header_frame.setFixedHeight(60)
        self.header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_frame.mousePressEvent = self._on_header_click
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(12)
        
        # Icon
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("""
            font-size: 18px;
            color: #64B5F6;
            background: transparent;
            border: none;
        """)
        header_layout.addWidget(icon_label)
        
        # Title and subtitle container
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: white;
            background: transparent;
            border: none;
        """)
        
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setStyleSheet("""
                font-size: 12px;
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                border: none;
            """)
            title_container.addWidget(title_label)
            title_container.addWidget(subtitle_label)
        else:
            title_container.addWidget(title_label)
        
        # Toggle indicator (subtle arrow)
        self.toggle_indicator = QLabel("▶")
        self.toggle_indicator.setStyleSheet("""
            font-size: 12px;
            color: rgba(255, 255, 255, 0.6);
            background: transparent;
            border: none;
        """)
        self.toggle_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_indicator, 0, Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.header_frame)
        
        # Content container
        self.content_container = QWidget()
        self.content_container.setStyleSheet("""
            QWidget {
                background: transparent;
                border: none;
                padding: 0px;
            }
        """)
        self.content_layout = QGridLayout(self.content_container)
        self.content_layout.setSpacing(ResponsiveHelper.scale_size(12, 10, 16))
        self.content_layout.setContentsMargins(0, 8, 0, 16)
        
        layout.addWidget(self.content_container)
        
        # Animation setup
        self.animation = QPropertyAnimation(self.content_container, b"maximumHeight")
        self.animation.setDuration(250)  # Slightly longer for smoother animation
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
          # Start collapsed
        self.content_container.setMaximumHeight(0)
        self.content_container.setVisible(False)
        
    def add_card(self, card, row, col):
        """Add a card to the section."""
        self.content_layout.addWidget(card, row, col)
        
    def _on_header_click(self, event):
        """Handle header click to toggle section."""
        self._toggle_section()
        
    def _toggle_section(self):
        """Toggle section visibility with smooth animation."""
        self.is_expanded = not self.is_expanded
        
        # Update toggle indicator
        self.toggle_indicator.setText("▼" if self.is_expanded else "▶")
        
        # Update header styling
        self._update_header_styling()
        
        # Always disconnect previous connections to prevent conflicts
        try:
            self.animation.finished.disconnect()
        except TypeError:
            pass
        
        if self.is_expanded:
            # Expanding
            self.content_container.setVisible(True)
            self.content_container.setMaximumHeight(16777215)  # Remove restriction
            target_height = self.content_container.sizeHint().height()
            self.animation.setStartValue(0)
            self.animation.setEndValue(target_height)
            # No need to connect finished signal for expansion
        else:
            # Collapsing
            current_height = self.content_container.height()
            self.animation.setStartValue(current_height)
            self.animation.setEndValue(0)
            # Hide after animation completes
            self.animation.finished.connect(lambda: self.content_container.setVisible(False))
        
        self.animation.start()
        
    def _update_header_styling(self):
        """Update header styling based on expanded state."""
        if self.is_expanded:
            self.header_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.08);
                    border: none;
                    border-top-left-radius: 12px;
                    border-top-right-radius: 12px;
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                    padding: 0px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.12);
                }
            """)
        else:
            self.header_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.08);
                    border: none;
                    border-radius: 12px;
                    padding: 0px;
                }
                QFrame:hover {
                    background: rgba(255, 255, 255, 0.12);
                }
            """)


class ReportsPage(QWidget):
    """Modern reports page with new structure."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
        self._populate_sections()
        
    def _setup_ui(self):
        """Setup the main UI structure."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create stacked widget for switching views
        self.stacked_widget = QStackedWidget()
        
        # Create overview page
        self.overview_page = self._create_overview_page()
        self.stacked_widget.addWidget(self.overview_page)
        
        # Create detailed report views
        self.income_statement_view = IncomeStatementView()
        self.income_statement_view.backToReports.connect(self._show_overview)
        self.stacked_widget.addWidget(self.income_statement_view)
        
        self.balance_sheet_view = BalanceSheetView()
        self.balance_sheet_view.backToReports.connect(self._show_overview)
        self.stacked_widget.addWidget(self.balance_sheet_view)
        
        self.cash_flow_view = CashFlowStatementView()
        self.cash_flow_view.backToReports.connect(self._show_overview)
        self.stacked_widget.addWidget(self.cash_flow_view)        
        self.equity_statement_view = StatementOfEquityView()
        self.equity_statement_view.backToReports.connect(self._show_overview)
        self.stacked_widget.addWidget(self.equity_statement_view)
        
        layout.addWidget(self.stacked_widget)
    
    def _create_overview_page(self):
        """Create the reports overview page."""
        page = QWidget()
        
        # Main page layout - no scroll area at page level
        page_layout = QVBoxLayout(page)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        page_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        page_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
        # Fixed top section (header, date selector, KPIs)
        # Page header
        header = PageHeader("Reports", "Comprehensive financial reporting and analysis")
        page_layout.addWidget(header)
        
        # Date range selector
        self.date_selector = DateRangeSelector(callback=self._on_date_range_changed)
        page_layout.addWidget(self.date_selector)
        
        # Top KPI section (non-expandable, always visible)
        self._create_kpi_section(page_layout)
        
        # Scrollable sections area - only for expandable sections
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
        """)
        
        # Scroll content widget - only for expandable sections
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        # No left/right margins since page already has them
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
        # Financial Statements section (expandable)
        self.statements_section = ExpandableSection("Financial Statements", "Core financial documents and statements", "📋")
        scroll_layout.addWidget(self.statements_section)
        
        # Ratios section (expandable)
        self.ratios_section = ExpandableSection("Financial Ratios", "Calculate and analyze key financial ratios", "📊")
        scroll_layout.addWidget(self.ratios_section)
        
        # Analysis Reports section (expandable)
        self.analysis_section = ExpandableSection("Analysis Reports", "Advanced financial analysis and insights", "📈")
        scroll_layout.addWidget(self.analysis_section)
        
        # Add stretch to push content to top
        scroll_layout.addStretch()
        
        # Set scroll widget
        scroll_area.setWidget(scroll_widget)
          # Add scroll area to main page layout
        page_layout.addWidget(scroll_area, 1)  # Give it stretch factor 1 to fill remaining space
        
        return page
        
    def _show_overview(self):
        """Show the reports overview page."""
        self.stacked_widget.setCurrentIndex(0)
        
    def _create_kpi_section(self, main_layout):
        """Create the top KPI section (non-expandable, max 2 rows)."""
        # KPI cards grid (max 2 rows) - no heading needed
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(ResponsiveHelper.scale_size(12, 10, 16))
        
        # Sample KPI data (8 cards = 2 rows of 4)
        kpi_data = [
            ("Total Revenue", "$128,900", "Monthly: +8.2%", "#2196F3"),
            ("Net Income", "$45,230", "vs Last Month: +12.5%", "#4CAF50"),
            ("Cash Flow", "$32,150", "Operating Activities", "#FF9800"),
            ("ROE", "15.8%", "vs Last Quarter: +2.1%", "#00BCD4"),            ("A/R Days", "28 days", "Industry Avg: 31", "#9C27B0"),
            ("Debt Ratio", "0.45", "Healthy Range: <0.5", "#4CAF50"),
            ("Quick Ratio", "1.8", "Liquid Assets", "#4CAF50"),
            ("Gross Margin", "69.6%", "Profit Efficiency", "#FF5722"),        ]
        
        for i, (title, value, subtitle, color) in enumerate(kpi_data):
            card = KPICard(title, value, subtitle, color)
            row = i // 4  # 4 cards per row (back to original)
            col = i % 4
            kpi_grid.addWidget(card, row, col)
        
        main_layout.addLayout(kpi_grid)
        
    def _populate_sections(self):
        """Populate the expandable sections with cards."""
        # Financial Statements
        statements_data = [
            ("Income Statement", "P&L", "Generate", "#4CAF50"),
            ("Balance Sheet", "Financial Position", "Generate", "#2196F3"),
            ("Cash Flow Statement", "Cash Analysis", "Generate", "#FF9800"),
            ("Trial Balance", "Account Verification", "Generate", "#9C27B0"),
            ("General Ledger", "Transaction Details", "View", "#00BCD4"),
            ("Statement of Equity", "Owner's Equity", "Generate", "#F44336"),
        ]
        
        for i, (title, subtitle, value, color) in enumerate(statements_data):
            card = ReportCard(title, subtitle, value, color)
            card.cardClicked.connect(self._handle_statement_click)
            row = i // 3  # 3 cards per row
            col = i % 3
            self.statements_section.add_card(card, row, col)
        
        # Financial Ratios
        ratios_data = [
            ("Liquidity Ratios", "Current, Quick, Cash", "Calculate", "#4CAF50"),
            ("Profitability Ratios", "ROE, ROA, Margins", "Calculate", "#2196F3"),
            ("Leverage Ratios", "Debt, Coverage", "Calculate", "#FF9800"),
            ("Efficiency Ratios", "Turnover, Days", "Calculate", "#9C27B0"),
            ("Market Ratios", "P/E, Book Value", "Calculate", "#00BCD4"),
            ("Growth Ratios", "Revenue, Earnings", "Calculate", "#F44336"),
        ]
        
        for i, (title, subtitle, value, color) in enumerate(ratios_data):
            card = ReportCard(title, subtitle, value, color)
            card.cardClicked.connect(self._handle_ratio_click)
            row = i // 3  # 3 cards per row
            col = i % 3
            self.ratios_section.add_card(card, row, col)
        
        # Analysis Reports
        analysis_data = [
            ("Trend Analysis", "Multi-period Trends", "Analyze", "#4CAF50"),
            ("Budget vs Actual", "Performance Analysis", "Compare", "#2196F3"),
            ("Variance Analysis", "Budget Deviations", "Analyze", "#FF9800"),
            ("Accounts Aging", "A/R & A/P Aging", "Review", "#9C27B0"),
            ("Cost Analysis", "Expense Breakdown", "Analyze", "#00BCD4"),
            ("Revenue Analysis", "Income Sources", "Analyze", "#F44336"),
            ("Seasonal Analysis", "Periodic Patterns", "Analyze", "#795548"),
            ("Competitive Analysis", "Benchmarking", "Compare", "#607D8B"),        ]
        
        for i, (title, subtitle, value, color) in enumerate(analysis_data):
            card = ReportCard(title, subtitle, value, color)
            card.cardClicked.connect(self._handle_analysis_click)
            row = i // 3  # 3 cards per row
            col = i % 3
            self.analysis_section.add_card(card, row, col)
    
    def _on_date_range_changed(self, start_date, end_date):
        """Handle date range changes."""
        # Update all data based on new date range
        pass
    
    def _handle_statement_click(self, statement_name):
        """Handle financial statement card clicks."""
        # Get current date range and convert to string format
        from_date_obj, to_date_obj = self.date_selector.get_date_range()
        from_date = from_date_obj.toString("yyyy-MM-dd") if from_date_obj else None
        to_date = to_date_obj.toString("yyyy-MM-dd") if to_date_obj else None
        
        # Navigate to existing tabs for Ledger and Trial Balance
        if statement_name == "General Ledger":
            # Navigate to Ledger tab (index 2)
            main_window = self.window()
            if hasattr(main_window, 'setCurrentIndexByName'):
                main_window.setCurrentIndexByName("Ledger")
        elif statement_name == "Trial Balance":
            # Navigate to Trial Balance tab (index 3)
            main_window = self.window()
            if hasattr(main_window, 'setCurrentIndexByName'):
                main_window.setCurrentIndexByName("Trial Balance")
        # Navigate to detailed report views for financial statements
        elif statement_name == "Income Statement":
            self.income_statement_view.show_income_statement(self.system, from_date, to_date)
            self.stacked_widget.setCurrentIndex(1)  # Income Statement view
        elif statement_name == "Balance Sheet":
            self.balance_sheet_view.show_balance_sheet(self.system, to_date)
            self.stacked_widget.setCurrentIndex(2)  # Balance Sheet view
        elif statement_name == "Cash Flow Statement":
            self.cash_flow_view.show_cash_flow_statement(self.system, from_date, to_date)
            self.stacked_widget.setCurrentIndex(3)  # Cash Flow view
        elif statement_name == "Statement of Equity":
            self.equity_statement_view.show_statement_of_equity(self.system, from_date, to_date)
            self.stacked_widget.setCurrentIndex(4)  # Equity Statement view
        else:
            QMessageBox.information(self, "Financial Statement", 
                                  f"Generating {statement_name}...\nThis feature will be implemented soon!")
    
    def _handle_ratio_click(self, ratio_name):
        """Handle ratio card clicks."""
        QMessageBox.information(self, "Financial Ratios", 
                              f"Calculating {ratio_name}...\nThis feature will be implemented soon!")
    
    def _handle_analysis_click(self, analysis_name):
        """Handle analysis report card clicks."""
        QMessageBox.information(self, "Analysis Report", 
                              f"Generating {analysis_name}...\nThis feature will be implemented soon!")
