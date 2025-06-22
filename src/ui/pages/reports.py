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
    ResponsiveHelper, Qt, QGridLayout, QSizePolicy, QSpacerItem, QStackedWidget,
    QMessageBox
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QFont, QColor
from ...core.utils import format_currency
from ..components.scrollbar_styles import ModernScrollbarStyles
from ..components.widgets import PageHeader, DateRangeSelector
from ..components.report_views import (
    IncomeStatementView, BalanceSheetView, CashFlowStatementView, StatementOfEquityView
)
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt6.QtGui import QFont, QCursor


class ReportCard(QFrame):
    """Small report card using Windows 11 ledger card design."""
    
    cardClicked = pyqtSignal(str)  # Report name
    
    def __init__(self, title, subtitle="", value="", color="#64B5F6", parent=None):
        super().__init__(parent)
        self.title = title
        self.subtitle = subtitle
        self.value = value
        self.color = color
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the card UI using Windows 11 ledger card design."""
        self.setFixedHeight(140)  # Increased height to prevent text clipping
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                border-color: rgba(0, 0, 0, 0.3);
                margin: 4px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)  # Reduced top/bottom margins for more text space
        layout.setSpacing(6)  # Reduced spacing for better text fit
        
        # Header row with colored indicator tag (like ledger level tags)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)
        
        # Colored indicator tag (styled like ledger level tags)
        indicator = QLabel("●")
        indicator.setStyleSheet(f"""
            color: {self.color};
            font-weight: 600;
            font-size: 11px;
            background: rgba({self._hex_to_rgba(self.color)}, 0.2);
            padding: 2px 6px;
            border-radius: 4px;
            border: none;
        """)
        indicator.setFixedWidth(20)
        header_layout.addWidget(indicator)
        
        header_layout.addStretch()
        
        # Subtitle/category
        if self.subtitle:
            subtitle_label = QLabel(self.subtitle)
            subtitle_label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.6);
                font-size: 11px;
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
            font-size: 14px;
            background: transparent;
            border: none;
        """)
        title_label.setWordWrap(True)
        title_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(title_label)
        
        # Add a small stretch to push value to bottom
        layout.addStretch()
        
        # Value row
        if self.value:
            value_label = QLabel(self.value)
            value_label.setStyleSheet(f"""
                color: white;
                font-weight: 700;
                font-size: 16px;
                background: transparent;
                border: none;
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignBottom)
            layout.addWidget(value_label)
        else:
            layout.addStretch()
    
    def _hex_to_rgba(self, hex_color):
        """Convert hex color to RGB values for rgba."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"{r}, {g}, {b}"
        return "100, 181, 246"  # Default blue
        
    def mousePressEvent(self, event):
        """Handle card click."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.cardClicked.emit(self.title)
        super().mousePressEvent(event)


class KPICard(QFrame):
    """KPI card for the top section using Windows 11 styling."""
    
    def __init__(self, title, value, subtitle="", color="#4CAF50", parent=None):
        super().__init__(parent)
        self.title = title
        self.value = value
        self.subtitle = subtitle
        self.color = color
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the KPI card UI with Windows 11 styling."""
        self.setFixedHeight(140)  # Increased height to match ReportCard and prevent clipping
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                border-color: rgba(0, 0, 0, 0.3);
                margin: 4px;
            }            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)  # Reduced top/bottom margins for more text space
        layout.setSpacing(6)  # Reduced spacing for better text fit
        
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
        
        # Add stretch to space elements better
        layout.addStretch()
        
        # Value
        value_label = QLabel(self.value)
        value_label.setStyleSheet("""
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
        """Setup the expandable section with Windows 11 styling."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Clickable header frame
        self.header_frame = QFrame()
        header_style = """
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
                border-color: rgba(0, 0, 0, 0.3);
                padding: 0px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """
        self.header_frame.setStyleSheet(header_style)
        self.header_frame.setFixedHeight(60)
        self.header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        self.header_frame.mousePressEvent = self._on_header_click
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(16, 12, 16, 12)  # Match card margins
        header_layout.setSpacing(12)
        
        # Icon with background (like ledger tags)
        icon_label = QLabel(self.icon)
        icon_label.setStyleSheet("""
            font-size: 16px;
            color: #64B5F6;
            background: rgba(100, 181, 246, 0.2);
            padding: 4px 6px;
            border-radius: 4px;
            border: none;
        """)
        icon_label.setFixedWidth(32)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(icon_label)
        
        # Title and subtitle container
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            font-size: 14px;
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
        
        header_layout.addLayout(title_container)
        header_layout.addStretch()
        
        # Toggle indicator (Windows 11 style)
        self.toggle_indicator = QLabel("▶")
        self.toggle_indicator.setStyleSheet("""
            QLabel {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 4px;
                padding: 4px;
                min-width: 24px;
                min-height: 24px;
                font-size: 10px;
                color: rgba(255, 255, 255, 0.9);
            }
            QLabel:hover {
                background: rgba(255, 255, 255, 0.12);
                border-color: rgba(255, 255, 255, 0.25);
            }
        """)
        self.toggle_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        
        # Scrollable content area - starts right after date selector
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Apply modern scrollbar styling
        scroll_area_style = """
            QScrollArea {
                background: transparent;
                border: none;
            }
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        scroll_area.setStyleSheet(scroll_area_style)
        
        # Scroll content widget - includes KPI section and all other sections
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        # No left/right margins since page already has them
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
        # KPI section (now inside scroll area)
        self._create_kpi_section(scroll_layout)
        
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
          # Sample KPI data (8 cards = 2 rows of 4) - using dynamic currency formatting
        kpi_data = [
            ("Total Revenue", format_currency(128900), "Monthly: +8.2%", "#2196F3"),
            ("Net Income", format_currency(45230), "vs Last Month: +12.5%", "#4CAF50"),
            ("Cash Flow", format_currency(32150), "Operating Activities", "#FF9800"),
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
    
    def refresh_currency_display(self):
        """Refresh all currency displays when currency symbol changes."""
        try:
            # Refresh the KPI section which contains currency values
            # Re-create the main layout to update currency formatting
            self._setup_ui()
        except Exception as e:
            print(f"Error refreshing currency display in reports: {e}")
    
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
        else:            QMessageBox.information(self, "Financial Statement", 
                                  f"Generating {statement_name}...\nThis feature will be implemented soon!")
    
    def _handle_ratio_click(self, ratio_name):
        """Handle ratio card clicks."""
        try:
            # Check if system has enhanced ratio calculator
            if hasattr(self.system, 'ratio_calculator'):
                if "Liquidity" in ratio_name:
                    ratios = self.system.ratio_calculator.calculate_liquidity_ratios()
                    self._show_ratio_results("Liquidity Ratios", ratios)
                elif "Profitability" in ratio_name:
                    ratios = self.system.ratio_calculator.calculate_profitability_ratios()
                    self._show_ratio_results("Profitability Ratios", ratios)
                elif "Leverage" in ratio_name:
                    ratios = self.system.ratio_calculator.calculate_leverage_ratios()
                    self._show_ratio_results("Leverage Ratios", ratios)
                elif "Efficiency" in ratio_name:
                    ratios = self.system.ratio_calculator.calculate_efficiency_ratios()
                    self._show_ratio_results("Efficiency Ratios", ratios)
                elif "Market" in ratio_name:
                    ratios = self.system.ratio_calculator.calculate_market_ratios()
                    self._show_ratio_results("Market Ratios", ratios)
                elif "Growth" in ratio_name:
                    ratios = self.system.ratio_calculator.calculate_growth_ratios()
                    self._show_ratio_results("Growth Ratios", ratios)
                else:
                    # Calculate all ratios
                    all_ratios = self.system.ratio_calculator.calculate_all_ratios()
                    self._show_ratio_results("All Financial Ratios", all_ratios)
            else:
                QMessageBox.information(self, "Financial Ratios", 
                                      f"Calculating {ratio_name}...\nThis feature is available with enhanced system features!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to calculate ratios: {str(e)}")
    
    def _handle_analysis_click(self, analysis_name):
        """Handle analysis report card clicks."""
        try:
            # Check if system has enhanced budget manager
            if hasattr(self.system, 'budget_manager') and "Budget" in analysis_name:
                if "Budget vs Actual" in analysis_name:
                    analysis = self.system.budget_manager.generate_budget_vs_actual_report()
                    self._show_budget_analysis("Budget vs Actual Analysis", analysis)
                elif "Variance Analysis" in analysis_name:
                    analysis = self.system.budget_manager.calculate_variances()
                    self._show_variance_analysis("Variance Analysis", analysis)
                else:
                    QMessageBox.information(self, "Analysis Report", 
                                          f"Generating {analysis_name}...\nThis feature will be implemented soon!")
            elif hasattr(self.system, 'cash_flow_manager') and "Cash Flow" in analysis_name:
                # Advanced cash flow analysis
                analysis = self.system.cash_flow_manager.generate_advanced_analysis()
                self._show_cash_flow_analysis("Advanced Cash Flow Analysis", analysis)
            else:
                QMessageBox.information(self, "Analysis Report", 
                                      f"Generating {analysis_name}...\nThis feature is available with enhanced system features!")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to generate analysis: {str(e)}")
            
    def _show_ratio_results(self, title, ratios):
        """Show ratio calculation results in a formatted dialog."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        # Create table for ratios
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["Ratio", "Value", "Interpretation"])
        
        # Populate table
        if ratios and 'ratios' in ratios:
            ratio_list = ratios['ratios']
            table.setRowCount(len(ratio_list))
            
            for row, ratio in enumerate(ratio_list):
                table.setItem(row, 0, QTableWidgetItem(ratio.get('name', '')))
                table.setItem(row, 1, QTableWidgetItem(f"{ratio.get('value', 0):.2f}"))
                table.setItem(row, 2, QTableWidgetItem(ratio.get('interpretation', '')))
        else:
            # Mock data for demonstration
            mock_ratios = [
                {"name": "Current Ratio", "value": 2.5, "interpretation": "Good liquidity"},
                {"name": "Quick Ratio", "value": 1.8, "interpretation": "Strong short-term liquidity"},
                {"name": "ROE", "value": 0.15, "interpretation": "15% return on equity"},
            ]
            table.setRowCount(len(mock_ratios))
            
            for row, ratio in enumerate(mock_ratios):
                table.setItem(row, 0, QTableWidgetItem(ratio['name']))
                table.setItem(row, 1, QTableWidgetItem(f"{ratio['value']:.2f}"))
                table.setItem(row, 2, QTableWidgetItem(ratio['interpretation']))
        
        # Auto-resize columns
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.exec()
        
    def _show_budget_analysis(self, title, analysis):
        """Show budget analysis results."""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.resize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create text area for analysis
        text_area = QTextEdit()
        text_area.setReadOnly(True)
        
        if analysis and 'summary' in analysis:
            text_area.setText(analysis['summary'])
        else:
            # Mock analysis for demonstration
            mock_analysis = """
Budget vs Actual Analysis Report
================================

Revenue Analysis:
- Budgeted Revenue: $100,000
- Actual Revenue: $110,000
- Variance: +$10,000 (10% favorable)

Expense Analysis:
- Budgeted Expenses: $80,000
- Actual Expenses: $75,000
- Variance: -$5,000 (6.25% favorable)

Net Income:
- Budgeted: $20,000
- Actual: $35,000
- Variance: +$15,000 (75% favorable)

Key Insights:
✓ Revenue exceeded budget by 10%
✓ Expenses were 6.25% under budget
✓ Strong overall performance with 75% better than budgeted net income
            """
            text_area.setText(mock_analysis)
        
        layout.addWidget(text_area)
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        
        dialog.exec()
        
    def _show_variance_analysis(self, title, analysis):
        """Show variance analysis results."""
        self._show_budget_analysis(title, analysis)  # Use same format for now
        
    def _show_cash_flow_analysis(self, title, analysis):
        """Show cash flow analysis results."""
        self._show_budget_analysis(title, analysis)  # Use same format for now
