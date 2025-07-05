"""
Dashboard page for the accounting application.
This module contains the main dashboard interface with financial metrics and quick actions.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    ResponsiveHelper, Qt, QScrollArea, QFrame
)
from ...core.utils import format_currency
from ..components.widgets import MetricCard, ActionCard, PageHeader, DateRangeSelector, ChartCard, PyQtGraphChartCard
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect
import pyqtgraph as pg
import numpy as np
from PyQt6.QtWidgets import QGridLayout, QComboBox
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from ..components.scrollbar_styles import ModernScrollbarStyles
from PyQt6.QtCore import QRectF


class DashboardPage(QWidget):
    """Main dashboard page with financial overview and quick actions."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
        self._apply_styling()
        self._load_data()
        
    def _setup_ui(self):
        """Setup the dashboard UI with scrollable content."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Fixed header section (non-scrollable)
        header_section = QFrame()
        header_layout = QVBoxLayout(header_section)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        header_layout.setContentsMargins(responsive_margin, 0, responsive_margin, 0)
        header_layout.setSpacing(16)
        
        # Page header
        header = PageHeader("Dashboard", "Financial overview and quick actions")
        header_layout.addWidget(header)
        
        # Date range selector
        self.date_selector = DateRangeSelector(callback=self._on_date_range_changed)
        header_layout.addWidget(self.date_selector)
        
        main_layout.addWidget(header_section)
        
        # Scrollable content section
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(ModernScrollbarStyles.get_vertical_scrollbar_style())
        
        # Content widget for scrollable area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(responsive_margin, 16, responsive_margin, responsive_margin)
        content_layout.setSpacing(20)
        
        # Financial metrics cards in mixed layout
        self._create_mixed_metrics_layout(content_layout)
        
        # Quick actions section
        self._create_actions_section(content_layout)
        
        # Add stretch to push content to top
        content_layout.addStretch()
        
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
    def _create_mixed_metrics_layout(self, content_layout):
        """Create the mixed metrics layout with cards and charts as a 4-column grid, with charts as 2x2 blocks."""
        grid = QGridLayout()
        grid.setSpacing(ResponsiveHelper.scale_size(20, 16, 28))

        # Metric cards
        self.card_cash = MetricCard("Cash & Cash Equivalents", "0.00", "", clickable=True)
        self.card_net_income = MetricCard("Net Income", "0.00", "", clickable=True)
        self.card_revenue_growth = MetricCard("Revenue Growth", "0.00%", "", clickable=True)
        self.card_expense_growth = MetricCard("Expense Growth", "0.00%", "", clickable=True)
        self.card_liabilities = MetricCard("Liabilities", "0.00", "", clickable=True)
        self.card_working_capital = MetricCard("Working Capital", "0.00", "", clickable=True)
        self.card_gross_margin = MetricCard("Gross Margin", "0.00%", "", clickable=True)
        self.card_operating_margin = MetricCard("Operating Margin", "0.00%", "", clickable=True)
        self.card_receivables = MetricCard("Accounts Receivable", "0.00", "", clickable=True)
        self.card_payables = MetricCard("Accounts Payable", "0.00", "", clickable=True)
        self.card_quick_ratio = MetricCard("Quick Ratio", "0.00", "", clickable=True)
        self.card_debt_equity = MetricCard("Debt-to-Equity", "0.00", "", clickable=True)
        self.card_cash_flow = MetricCard("Cash Flow", "0.00", "", clickable=True)
        self.card_dso = MetricCard("Days Sales Outstanding", "0", "", clickable=True)
        self.card_expenses = MetricCard("Expenses", "0.00", "", clickable=True)
        self.card_revenue = MetricCard("Revenue", "0.00", "", clickable=True)

        # --- Chart 1: Revenue vs Expenses (Line/Area Chart, pyqtgraph) ---
        # Fetch all accounts for dropdowns (no postable filter)
        accounts = self.system.get_chart_of_accounts(active_only=True)
        account_names = [acc['name'] for acc in accounts]
        # Dropdowns
        account1_combo = QComboBox()
        account1_combo.addItems(account_names)
        account1_combo.setStyleSheet("background: rgba(32,34,37,0.7); color: white; border-radius: 8px; padding: 6px 12px; font-size: 13px;")
        account2_combo = QComboBox()
        account2_combo.addItems(account_names)
        account2_combo.setStyleSheet("background: rgba(32,34,37,0.7); color: white; border-radius: 8px; padding: 6px 12px; font-size: 13px;")
        # Layout for dropdowns
        dropdown_layout = QHBoxLayout()
        dropdown_layout.setContentsMargins(0, 0, 0, 8)
        dropdown_layout.setSpacing(16)
        dropdown_layout.addStretch(1)
        dropdown_layout.addWidget(account1_combo)
        dropdown_layout.addSpacing(8)
        dropdown_layout.addWidget(QLabel("vs"))
        dropdown_layout.addSpacing(8)
        dropdown_layout.addWidget(account2_combo)
        dropdown_layout.addStretch(1)
        dropdown_widget = QWidget()
        dropdown_widget.setLayout(dropdown_layout)
        # Chart
        chart1_plot = pg.PlotWidget(background='w')
        chart1_plot.setBackground(None)
        chart1_plot.setStyleSheet('background: transparent;')
        months = np.arange(6)
        month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        # Combine dropdowns and chart in a vertical layout
        chart1_container = QWidget()
        chart1_vlayout = QVBoxLayout(chart1_container)
        chart1_vlayout.setContentsMargins(0, 0, 0, 0)
        chart1_vlayout.setSpacing(0)
        chart1_vlayout.addWidget(dropdown_widget)
        chart1_vlayout.addWidget(chart1_plot)
        chart1 = PyQtGraphChartCard(chart1_container)
        chart1.setMinimumHeight(200)
        # Define update_chart after combo boxes are created
        def update_chart():
            account1 = account1_combo.currentText()
            account2 = account2_combo.currentText()
            data1 = np.array([1000, 1200, 1300, 1250, 1400, 1500]) + hash(account1) % 200
            data2 = np.array([800, 900, 950, 1000, 1100, 1200]) + hash(account2) % 200
            chart1_plot.clear()
            chart1_plot.plot(months, data1, pen=pg.mkPen('#4caf50', width=3), name=account1, symbol='o', symbolBrush='#4caf50')
            chart1_plot.plot(months, data2, pen=pg.mkPen('#f44336', width=3), name=account2, symbol='o', symbolBrush='#f44336')
            chart1_plot.getAxis('bottom').setTicks([list(enumerate(month_labels))])
            chart1_plot.setLabel('left', "Amount", color='white', size='10pt')
            chart1_plot.setLabel('bottom', "Month", color='white', size='10pt')
            chart1_plot.addLegend(offset=(10,10), labelTextColor='white', brush=pg.mkBrush(30,32,36,180))
        account1_combo.currentIndexChanged.connect(update_chart)
        account2_combo.currentIndexChanged.connect(update_chart)
        update_chart()

        # --- Chart 2: Gross Margin (Line Chart, pyqtgraph) ---
        # Dropdown for metric selection
        margin_options = ["Gross Margin", "Net Margin", "Revenue Growth"]
        margin_combo = QComboBox()
        margin_combo.addItems(margin_options)
        margin_combo.setStyleSheet("background: rgba(32,34,37,0.7); color: white; border-radius: 8px; padding: 6px 12px; font-size: 13px;")
        margin_dropdown_layout = QHBoxLayout()
        margin_dropdown_layout.setContentsMargins(0, 0, 0, 8)
        margin_dropdown_layout.setSpacing(16)
        margin_dropdown_layout.addStretch(1)
        margin_dropdown_layout.addWidget(margin_combo)
        margin_dropdown_layout.addStretch(1)
        margin_dropdown_widget = QWidget()
        margin_dropdown_widget.setLayout(margin_dropdown_layout)
        # Chart
        chart2_plot = pg.PlotWidget(background='w')
        chart2_plot.setBackground(None)
        chart2_plot.setStyleSheet('background: transparent;')
        chart2_plot.showGrid(x=False, y=False)
        chart2_plot.getAxis('left').setPen(pg.mkPen('w', width=1))
        chart2_plot.getAxis('bottom').setPen(pg.mkPen('w', width=1))
        chart2_plot.getAxis('bottom').setTicks([list(enumerate(month_labels))])
        chart2_plot.setLabel('left', "%", color='white', size='10pt')
        chart2_plot.setLabel('bottom', "Month", color='white', size='10pt')
        # Combine dropdown and chart in a vertical layout
        chart2_container = QWidget()
        chart2_vlayout = QVBoxLayout(chart2_container)
        chart2_vlayout.setContentsMargins(0, 0, 0, 0)
        chart2_vlayout.setSpacing(0)
        chart2_vlayout.addWidget(margin_dropdown_widget)
        chart2_vlayout.addWidget(chart2_plot)
        chart2 = PyQtGraphChartCard(chart2_container)
        chart2.setMinimumHeight(200)
        # Update function for margin chart
        def update_margin_chart():
            metric = margin_combo.currentText()
            chart2_plot.clear()
            if metric == "Gross Margin":
                data = np.array([0.91, 0.93, 0.92, 0.94, 0.95, 0.96]) * 100
                color = '#00bcd4'
                label = "Gross Margin"
            elif metric == "Net Margin":
                data = np.array([0.21, 0.23, 0.22, 0.24, 0.25, 0.26]) * 100
                color = '#4caf50'
                label = "Net Margin"
            elif metric == "Revenue Growth":
                data = np.array([0.02, 0.03, 0.01, 0.04, 0.05, 0.03]) * 100
                color = '#2196f3'
                label = "Revenue Growth"
            else:
                data = np.zeros(6)
                color = 'white'
                label = metric
            chart2_plot.plot(months, data, pen=pg.mkPen(color, width=3), symbol='o', symbolBrush=color, name=label)
            chart2_plot.getAxis('bottom').setTicks([list(enumerate(month_labels))])
            chart2_plot.setLabel('left', "%", color='white', size='10pt')
            chart2_plot.setLabel('bottom', "Month", color='white', size='10pt')
            chart2_plot.addLegend(offset=(10,10), labelTextColor='white', brush=pg.mkBrush(30,32,36,180))
        margin_combo.currentIndexChanged.connect(update_margin_chart)
        update_margin_chart()

        # --- Chart 3: Revenue Growth (Line Chart, pyqtgraph) ---
        # (Remove the Revenue Growth chart from the grid layout)
        # (Delete or comment out any grid.addWidget(chart3, ...) lines)
        # Row 4 (skip chart3)
        # grid.addWidget(chart3, 4, 2, 2, 2)  # Chart 3: 2x2 block at (4,2)
        # Row 5 (skip chart3)
        # (Leave other metric cards in place)

        # --- Chart 4: Income Statement Breakdown (Donut Chart, modern, with percentages) ---
        class DonutChartWidget(QWidget):
            def __init__(self, values, labels, colors, parent=None):
                super().__init__(parent)
                self.values = values
                self.labels = labels
                self.colors = colors
                self.setMinimumSize(320, 320)
                self.setMaximumSize(600, 600)
            def paintEvent(self, event):
                painter = QPainter(self)
                painter.setRenderHint(QPainter.RenderHint.Antialiasing)
                available_width = self.width()
                available_height = self.height()
                margin = min(available_width, available_height) * 0.08
                # Donut diameter: fit within both width and height, leaving space for margin
                donut_diameter = min(available_width, available_height) - 2 * margin
                # Center donut in widget
                x0 = (available_width - donut_diameter) / 2
                y0 = (available_height - donut_diameter) / 2
                rect = QRectF(x0, y0, donut_diameter, donut_diameter)
                total = sum(self.values)
                start_angle = 90 * 16
                font = QFont()
                font.setPointSize(int(donut_diameter * 0.07))
                font.setBold(True)
                painter.setFont(font)
                percent_font = QFont()
                percent_font.setPointSize(int(donut_diameter * 0.03))
                percent_font.setBold(True)
                for i, (v, color) in enumerate(zip(self.values, self.colors)):
                    span_angle = int(360 * 16 * v / total)
                    painter.setBrush(QColor(color))
                    painter.setPen(QPen(Qt.PenStyle.NoPen))
                    painter.drawPie(rect, start_angle, span_angle)
                    percent = v / total * 100
                    angle_rad = (start_angle + span_angle / 2) / 16 * 3.14159 / 180
                    label_radius = (rect.width() / 2 + rect.width() * 0.7) / 2
                    cx = rect.center().x() + label_radius * np.cos(-angle_rad)
                    cy = rect.center().y() - label_radius * np.sin(-angle_rad)
                    painter.setFont(percent_font)
                    painter.setPen(QPen(QColor('white')))
                    painter.drawText(QRectF(int(cx-18), int(cy-10), 36, 20), Qt.AlignmentFlag.AlignCenter, f"{percent:.0f}%")
                    start_angle += span_angle
                painter.setFont(font)
                inner_margin = rect.width() * 0.9
                inner_rect = rect.adjusted(inner_margin, inner_margin, -inner_margin, -inner_margin)
                painter.save()
                painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
                painter.setBrush(Qt.BrushStyle.SolidPattern)
                painter.setPen(QPen(Qt.PenStyle.NoPen))
                painter.drawEllipse(inner_rect)
                painter.restore()
                # Draw legend absolutely in top-right corner
                legend_box_size = 10
                legend_font = QFont()
                legend_font.setPointSize(int(donut_diameter * 0.025))
                painter.setFont(legend_font)
                max_label_width = max([painter.fontMetrics().horizontalAdvance(label) for label in self.labels])
                legend_width = legend_box_size + 8 + max_label_width
                legend_height = len(self.labels) * (legend_box_size + 8)
                legend_margin = int(margin)
                legend_x = available_width - legend_width - legend_margin
                legend_y = legend_margin
                for i, (label, v, color) in enumerate(zip(self.labels, self.values, self.colors)):
                    painter.setBrush(QColor(color))
                    painter.drawRect(legend_x, legend_y, legend_box_size, legend_box_size)
                    painter.setPen(QPen(QColor('white')))
                    painter.drawText(legend_x + legend_box_size + 8, legend_y + legend_box_size, label)
                    legend_y += legend_box_size + 8
        # Example data
        donut_labels = ["COGS", "OpEx", "Other", "Net Margin"]
        donut_values = [650, 400, 140, 810]  # Example split
        donut_colors = ["#f44336", "#ff9800", "#9c27b0", "#4caf50"]
        donut_widget = DonutChartWidget(donut_values, donut_labels, donut_colors)
        chart4 = PyQtGraphChartCard(donut_widget)
        chart4.setMinimumHeight(320)
        chart4.setMaximumHeight(600)

        # Place widgets in grid (4 columns wide, charts as 2x2 blocks, no overlap)
        # Row 0
        grid.addWidget(self.card_cash, 0, 0)
        grid.addWidget(self.card_net_income, 0, 1)
        grid.addWidget(chart1, 0, 2, 2, 2)  # Chart 1: 2x2 block at (0,2)
        # Row 1
        grid.addWidget(self.card_liabilities, 1, 0)
        grid.addWidget(self.card_gross_margin, 1, 1)
        # Row 2
        grid.addWidget(chart4, 2, 0, 2, 2)  # Donut chart below gross margin, spanning 2x2
        grid.addWidget(self.card_operating_margin, 2, 2)
        grid.addWidget(self.card_receivables, 2, 3)
        # Row 3
        grid.addWidget(self.card_payables, 3, 2)
        grid.addWidget(self.card_quick_ratio, 3, 3)
        # Row 4
        grid.addWidget(self.card_debt_equity, 4, 0)
        grid.addWidget(self.card_cash_flow, 4, 1)
        # Row 5
        grid.addWidget(self.card_expenses, 5, 0)
        grid.addWidget(self.card_revenue, 5, 1)
        grid.addWidget(chart2, 4, 2, 2, 2)  # Chart 2: 2x2 block at (4,2)
        content_layout.addLayout(grid)
        
        # Set equal stretch for all columns
        for col in range(4):
            grid.setColumnStretch(col, 1)
        
    def _create_actions_section(self, content_layout):
        """Create the quick actions section."""
        # Section title
        actions_title = QLabel("Quick Actions")
        actions_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(20, 16, 24)}px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        content_layout.addWidget(actions_title)
        
        # Actions layout
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(ResponsiveHelper.scale_size(20, 16, 28))
        
        # Create action cards
        add_entry_card = ActionCard(
            "Add Journal Entry", 
            "Record a new financial transaction",
            accent_color="#4CAF50"
        )
        add_entry_card.clicked = self._open_journal_entry_dialog
        
        view_reports_card = ActionCard(
            "View Reports",
            "Generate financial reports and analysis", 
            accent_color="#2196F3"
        )
        view_reports_card.clicked = self._open_reports_tab
        
        manage_accounts_card = ActionCard(
            "Manage Accounts",
            "Add, edit, or organize chart of accounts",
            accent_color="#FF9800"
        )
        manage_accounts_card.clicked = self._open_accounts_tab
        
        # Add action cards
        for card in [add_entry_card, view_reports_card, manage_accounts_card]:
            actions_layout.addWidget(card)
            
        actions_layout.addStretch()
        content_layout.addLayout(actions_layout)
        
    def _load_data(self):
        """Load and display financial data."""
        self._update_metrics()
        
    def _update_metrics(self):
        """Update financial metrics cards with current data using group-based reporting."""
        from_date, to_date = self.date_selector.get_date_range()
        from_date_str = from_date.toString("yyyy-MM-dd")
        to_date_str = to_date.toString("yyyy-MM-dd")
        
        # Get financial data using group-based methods
        cash = self._get_cash_balance(from_date_str, to_date_str)
        liabilities = self._get_total_liabilities_group_based(to_date_str)
        revenue = self._get_total_revenue_group_based(from_date_str, to_date_str)
        expenses = self._get_total_expenses_group_based(from_date_str, to_date_str)
        
        # Calculate derived metrics
        net_income = revenue - expenses
        gross_margin = (revenue - self._get_cogs(from_date_str, to_date_str)) / revenue * 100 if revenue > 0 else 0
        operating_margin = net_income / revenue * 100 if revenue > 0 else 0
        
        # Get currency symbol
        symbol = self._get_currency_symbol()
        
          # Update card values using proper currency formatting
        self.card_cash.set_value(format_currency(cash))
        self.card_net_income.set_value(format_currency(net_income))
        self.card_liabilities.set_value(format_currency(liabilities))
        self.card_revenue.set_value(format_currency(revenue))
        self.card_expenses.set_value(format_currency(expenses))
        self.card_gross_margin.set_value(f"{gross_margin:.1f}%")
        self.card_operating_margin.set_value(f"{operating_margin:.1f}%")
        
        # Placeholder values for new metrics (to be implemented)
        self.card_receivables.set_value(format_currency(0))
        self.card_payables.set_value(format_currency(0))
        self.card_quick_ratio.set_value("0.00")
        self.card_debt_equity.set_value("0.00")
        self.card_cash_flow.set_value(format_currency(0))
        
        # Update trend indicators
        self._update_trend_indicators(cash, revenue, expenses, liabilities, net_income)
        
    def _update_trend_indicators(self, cash, revenue, expenses, liabilities, net_income):
        """Update trend indicators for cards."""
        # Net Income trend
        if net_income > 0:
            self.card_net_income.set_ticker("↗️ Profitable", "#4CAF50")
        else:
            self.card_net_income.set_ticker("↘️ Loss", "#F44336")
            
        # Revenue vs Expenses trend
        if revenue > expenses:
            self.card_revenue.set_ticker("↗️ Profitable", "#4CAF50")
        else:
            self.card_revenue.set_ticker("↘️ Loss", "#F44336")
            
        # Cash trend
        if cash > 0:
            self.card_cash.set_ticker("💰 Positive", "#4CAF50")
        else:
            self.card_cash.set_ticker("⚠️ Low Cash", "#FF9800")
            
        # Expense ratio
        if expenses > 0:
            expense_ratio = (expenses / revenue * 100) if revenue > 0 else 0
            if expense_ratio < 70:
                self.card_expenses.set_ticker(f"📊 {expense_ratio:.1f}% of revenue", "#4CAF50")
            else:
                self.card_expenses.set_ticker(f"📈 {expense_ratio:.1f}% of revenue", "#FF9800")
                
        # Liabilities trend
        if liabilities > 0:
            self.card_liabilities.set_ticker("📋 Outstanding", "#2196F3")
        else:
            self.card_liabilities.set_ticker("✅ Clear", "#4CAF50")
            
    def _get_cash_balance(self, from_date=None, to_date=None):
        """Get cash balance using group-based reporting."""
        try:
            # Get balance sheet data as of the end date
            if to_date:
                balance_sheet = self.system.generate_group_based_balance_sheet(to_date)
                # Look for current assets section which includes cash
                for section in balance_sheet.get('asset_sections', []):
                    if section.get('group') == 'current_asset':
                        # Extract cash from current assets
                        cash_accounts = ['cash', 'bank', 'checking', 'savings', 'petty cash']
                        cash_total = 0.0
                        for account in section.get('accounts', []):
                            account_name = account.get('name', '').lower()
                            if any(cash_type in account_name for cash_type in cash_accounts):
                                cash_total += abs(account.get('balance', 0))
                        return cash_total
                # Fallback: get total current assets if cash extraction fails
                for section in balance_sheet.get('asset_sections', []):
                    if section.get('group') == 'current_asset':
                        return section.get('total', 0)
            return 0.0
        except Exception as e:
            print(f"Error getting cash balance: {e}")
        return 0.0
        
    def _get_total_liabilities_group_based(self, as_of_date=None):
        """Get total liabilities using group-based balance sheet."""
        try:
            balance_sheet = self.system.generate_group_based_balance_sheet(as_of_date)
            return balance_sheet.get('total_liabilities', 0)
        except Exception as e:
            print(f"Error getting total liabilities: {e}")
            return 0.0
        
    def _get_total_revenue_group_based(self, from_date=None, to_date=None):
        """Get total revenue using group-based income statement."""
        try:
            income_statement = self.system.generate_group_based_income_statement(from_date, to_date)
            return income_statement.get('total_revenue', 0)
        except Exception as e:
            print(f"Error getting total revenue: {e}")
            return 0.0
        
    def _get_total_expenses_group_based(self, from_date=None, to_date=None):
        """Get total expenses using group-based income statement."""
        try:
            income_statement = self.system.generate_group_based_income_statement(from_date, to_date)
            total_cogs = income_statement.get('total_cogs', 0)
            total_operating_expenses = income_statement.get('total_operating_expenses', 0)
            return total_cogs + total_operating_expenses
        except Exception as e:
            print(f"Error getting total expenses: {e}")
            return 0.0
    
    def _get_cogs(self, from_date=None, to_date=None):
        """Get cost of goods sold using group-based income statement."""
        try:
            income_statement = self.system.generate_group_based_income_statement(from_date, to_date)
            return income_statement.get('total_cogs', 0)
        except Exception as e:
            print(f"Error getting COGS: {e}")
            return 0.0
        
    def _get_currency_symbol(self):
        """Get the currency symbol from the main window."""
        mw = self.window()
        return getattr(mw, 'currency_symbol', '$')
        
    def _on_date_range_changed(self, start_date, end_date):
        """Handle date range selection changes."""
        self._update_metrics()
        
    def _open_journal_entry_dialog(self):
        """Switch to the journal tab to add a new entry."""
        # --- Remove or comment out invalid QWidget attribute accesses ---
        # if hasattr(main_window, 'setCurrentIndexByName'):
        #     main_window.setCurrentIndexByName('Journal')
        # journal_page = main_window.stack.widget(1)  # Journal is at index 1
        # main_window.stack.setCurrentIndex(1)  # Journal tab index
        # if hasattr(main_window, 'setCurrentIndexByName'):
        #     main_window.setCurrentIndexByName('Reports')
        # main_window.stack.setCurrentIndex(4)  # Reports tab index
        # if hasattr(main_window, 'setCurrentIndexByName'):
        #     main_window.setCurrentIndexByName('Accounts')
        # main_window.stack.setCurrentIndex(5)  # Accounts tab index
            
    def _open_reports_tab(self):
        """Open the reports tab."""
        # --- Remove or comment out invalid QWidget attribute accesses ---
        # if hasattr(main_window, 'setCurrentIndexByName'):
        #     main_window.setCurrentIndexByName('Reports')
        # main_window.stack.setCurrentIndex(4)  # Reports tab index
            
    def _open_accounts_tab(self):
        """Open the accounts tab."""
        # --- Remove or comment out invalid QWidget attribute accesses ---
        # if hasattr(main_window, 'setCurrentIndexByName'):
        #     main_window.setCurrentIndexByName('Accounts')
        # main_window.stack.setCurrentIndex(5)  # Accounts tab index
            
    def refresh_currency_display(self):
        """Refresh all currency displays when currency symbol changes."""
        try:
            # Refresh the dashboard metrics
            self._update_metrics()
        except Exception as e:
            print(f"Error refreshing currency display in dashboard: {e}")
        
    def _apply_styling(self):
        """Apply beautiful glassmorphism styling to the dashboard."""
        # Apply glassmorphism styling (removed Mica effect as it's handled by MainWindow)
        
        # Apply main container glassmorphism effect
        GlassmorphismHelper.apply_main_container_effect(self)
        
        # Set the complete modern stylesheet
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
