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
from PyQt6.QtCore import QRectF, QTimer
import time
from collections import defaultdict
from datetime import datetime


class DashboardPage(QWidget):
    """Main dashboard page with financial overview and quick actions."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        
        # Initialize loading states
        self.chart_loading_states = {
            'chart1': False,
            'donut': False
        }
        
        # Initialize chart update timers
        self.chart1_timer = QTimer()
        self.chart1_timer.setSingleShot(True)
        self.chart1_timer.timeout.connect(self._perform_chart1_update)
        
        self.donut_timer = QTimer()
        self.donut_timer.setSingleShot(True)
        self.donut_timer.timeout.connect(self._perform_donut_chart_update)
        
        # Cache data validation result to avoid repeated calls
        self._cached_has_data = None
        self._last_data_check = 0
        
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
        self.card_current_ratio = MetricCard("Current Ratio", "0.00", "", clickable=True)
        self.card_dso = MetricCard("Days Sales Outstanding", "0", "", clickable=True)
        self.card_expenses = MetricCard("Expenses", "0.00", "", clickable=True)
        self.card_revenue = MetricCard("Revenue", "0.00", "", clickable=True)

        # --- Chart 1: Revenue vs Expenses (Line/Area Chart, pyqtgraph) ---
        # Fetch all accounts for dropdowns (no postable filter)
        accounts = self.system.get_chart_of_accounts(active_only=True)
        account_names = [acc['name'] for acc in accounts]
        # Dropdowns
        self.account1_combo = QComboBox()
        self.account1_combo.addItems(account_names)
        self.account1_combo.setStyleSheet("background: rgba(32,34,37,0.7); color: white; border-radius: 8px; padding: 6px 12px; font-size: 13px;")
        self.account2_combo = QComboBox()
        self.account2_combo.addItems(account_names)
        self.account2_combo.setStyleSheet("background: rgba(32,34,37,0.7); color: white; border-radius: 8px; padding: 6px 12px; font-size: 13px;")
        # Layout for dropdowns
        dropdown_layout = QHBoxLayout()
        dropdown_layout.setContentsMargins(0, 0, 0, 8)
        dropdown_layout.setSpacing(16)
        dropdown_layout.addStretch(1)
        dropdown_layout.addWidget(self.account1_combo)
        dropdown_layout.addSpacing(8)
        dropdown_layout.addWidget(QLabel("vs"))
        dropdown_layout.addSpacing(8)
        dropdown_layout.addWidget(self.account2_combo)
        dropdown_layout.addStretch(1)
        dropdown_widget = QWidget()
        dropdown_widget.setLayout(dropdown_layout)
        # Chart with zoom functionality
        self.chart1_plot = pg.PlotWidget(background='w')
        self.chart1_plot.setBackground(None)
        self.chart1_plot.setStyleSheet('background: transparent;')
        
        # Enable zoom and pan functionality
        self.chart1_plot.setMouseEnabled(x=True, y=True)
        self.chart1_plot.enableAutoRange(axis='x')
        self.chart1_plot.enableAutoRange(axis='y')
        
        # Add zoom controls (no grid lines)
        self.chart1_plot.showGrid(x=False, y=False)
        self.chart1_plot.getAxis('left').setPen(pg.mkPen('w', width=1))
        self.chart1_plot.getAxis('bottom').setPen(pg.mkPen('w', width=1))
        # Default month labels (will be overridden by real data)
        default_month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
        default_months = np.arange(6)
        # Combine dropdowns and chart in a vertical layout
        chart1_container = QWidget()
        chart1_vlayout = QVBoxLayout(chart1_container)
        chart1_vlayout.setContentsMargins(0, 0, 0, 0)
        chart1_vlayout.setSpacing(0)
        chart1_vlayout.addWidget(dropdown_widget)
        chart1_vlayout.addWidget(self.chart1_plot)
        chart1 = PyQtGraphChartCard(chart1_container)
        chart1.setMinimumHeight(200)
        # Define update_chart after combo boxes are created
        def _show_no_data_chart(plot_widget, message="No data available"):
            """Show no data message on chart"""
            plot_widget.clear()
            plot_widget.setLabel('left', "Value", color='white', size='10pt')
            plot_widget.setLabel('bottom', "Period", color='white', size='10pt')
            plot_widget.addLegend(offset=(10,10), labelTextColor='white', brush=pg.mkBrush(30,32,36,180))
            
            # Add text item to show no data message
            from PyQt6.QtGui import QColor
            text_item = pg.TextItem(text=message, 
                                  color=QColor(255, 255, 255, 153),  # 153 = 0.6 * 255
                                  anchor=(0.5, 0.5))
            plot_widget.addItem(text_item)
            text_item.setPos(0.5, 0.5)
        
        def _show_no_data_chart_accounts(plot_widget, account1, account2):
            """Show no data message on account comparison chart"""
            message = f"No data available for\n{account1} vs {account2}\nin selected date range"
            _show_no_data_chart(plot_widget, message)
        
        def update_chart():
            account1 = self.account1_combo.currentText()
            account2 = self.account2_combo.currentText()
            from_date, to_date = self.date_selector.get_date_range()
            from_date_str = from_date.toString("yyyy-MM-dd")
            to_date_str = to_date.toString("yyyy-MM-dd")
            
            try:
                # Check if accounts are postable or parent accounts
                accounts = self.system.get_chart_of_accounts(active_only=False)
                account1_data = next((acc for acc in accounts if acc['name'] == account1), None)
                account2_data = next((acc for acc in accounts if acc['name'] == account2), None)
                
                # Determine account types and get appropriate data
                account1_is_postable = account1_data.get('is_postable', True) if account1_data else True
                account2_is_postable = account2_data.get('is_postable', True) if account2_data else True
                
                # Get data for both accounts
                data1 = None
                data2 = None
                
                # For postable accounts, use ledger data
                if account1_is_postable:
                    ledger1 = self.system.get_ledger(account1, from_date_str, to_date_str)
                    if ledger1:
                        data1 = self._calculate_running_balance_from_ledger(ledger1, account1)
                
                if account2_is_postable:
                    ledger2 = self.system.get_ledger(account2, from_date_str, to_date_str)
                    if ledger2:
                        data2 = self._calculate_running_balance_from_ledger(ledger2, account2)
                
                # For parent accounts, use balance sheet data
                if not account1_is_postable and account1_data:
                    data1 = self._get_parent_account_balance(account1_data, to_date_str)
                
                if not account2_is_postable and account2_data:
                    data2 = self._get_parent_account_balance(account2_data, to_date_str)
                
                # If we have data for either account, plot it
                if data1 or data2:
                    # Prepare data for plotting
                    dates = []
                    values1 = []
                    values2 = []
                    
                    if data1 and isinstance(data1, dict):
                        # Ledger data - multiple dates
                        dates1 = sorted(data1.keys())
                        values1 = [data1[date] for date in dates1]
                        dates = dates1
                    elif data1 is not None:
                        # Balance sheet data - single point
                        dates = [to_date_str]
                        values1 = [data1]
                    
                    if data2 and isinstance(data2, dict):
                        # Ledger data - multiple dates
                        dates2 = sorted(data2.keys())
                        values2 = [data2[date] for date in dates2]
                        # Merge dates if needed
                        if not dates:
                            dates = dates2
                        else:
                            all_dates = sorted(set(dates + dates2))
                            # Extend values to match all dates
                            extended_values1 = []
                            extended_values2 = []
                            for date in all_dates:
                                if isinstance(data1, dict):
                                    extended_values1.append(data1.get(date, values1[-1] if values1 else 0))
                                else:
                                    extended_values1.append(data1 if data1 is not None else 0)
                                extended_values2.append(data2.get(date, values2[-1] if values2 else 0))
                            dates = all_dates
                            values1 = extended_values1
                            values2 = extended_values2
                    elif data2 is not None:
                        # Balance sheet data - single point
                        if not dates:
                            dates = [to_date_str]
                        values2 = [data2]
                    
                    if dates:
                        # Update chart with data
                        self.chart1_plot.clear()
                        self.chart1_plot.plot(range(len(dates)), values1, pen=pg.mkPen('#4caf50', width=3), name=account1, symbol='o', symbolBrush='#4caf50')
                        self.chart1_plot.plot(range(len(dates)), values2, pen=pg.mkPen('#f44336', width=3), name=account2, symbol='o', symbolBrush='#f44336')
                        self.chart1_plot.getAxis('bottom').setTicks([list(enumerate(dates))])
                        self.chart1_plot.setLabel('left', "Balance", color='white', size='10pt')
                        self.chart1_plot.setLabel('bottom', "Date", color='white', size='10pt')
                        self.chart1_plot.addLegend(offset=(10,10), labelTextColor='white', brush=pg.mkBrush(30,32,36,180))
                        
                        print(f"✅ Account comparison chart updated with data for {len(dates)} points")
                        print(f"   Account 1 ({account1}): {'Postable' if account1_is_postable else 'Parent'}, final balance: {values1[-1] if values1 else 0}")
                        print(f"   Account 2 ({account2}): {'Postable' if account2_is_postable else 'Parent'}, final balance: {values2[-1] if values2 else 0}")
                    else:
                        # No data available
                        print("⚠️ No data available for selected accounts and date range")
                        _show_no_data_chart_accounts(self.chart1_plot, account1, account2)
                else:
                    # No data available
                    print("⚠️ No data available")
                    _show_no_data_chart_accounts(self.chart1_plot, account1, account2)
                    
            except Exception as e:
                print(f"❌ Error updating account comparison chart: {e}")
                # Show no data message on error
                _show_no_data_chart_accounts(self.chart1_plot, account1, account2)
        
        self.update_chart1 = self._update_chart1_with_loading
        self.account1_combo.currentIndexChanged.connect(self._update_chart1_with_loading)
        self.account2_combo.currentIndexChanged.connect(self._update_chart1_with_loading)
        self.date_selector.dateRangeChanged.connect(self._update_chart1_with_loading)
        self._update_chart1_with_loading()

        # --- Chart 2: Gross Margin (Line Chart, pyqtgraph) ---
        # (Removed margin chart and related dropdown)
        # --- Chart 3: Revenue Growth (Line Chart, pyqtgraph) ---
        # (Removed)
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
        
        # Create donut chart with real data
        def update_donut_chart():
            try:
                from_date, to_date = self.date_selector.get_date_range()
                
                # Check if date range is valid
                if from_date is None or to_date is None:
                    print("⚠️ No date range selected for donut chart")
                    donut_labels = ["No Date Range"]
                    donut_values = [1]
                    donut_colors = ["#666666"]
                    self.donut_widget.values = donut_values
                    self.donut_widget.labels = donut_labels
                    self.donut_widget.colors = donut_colors
                    self.donut_widget.update()
                    self._hide_chart_loading('donut')
                    return
                
                from_date_str = from_date.toString("yyyy-MM-dd")
                to_date_str = to_date.toString("yyyy-MM-dd")
                
                # Check if system is available
                if not self.system:
                    print("⚠️ No accounting system available for donut chart")
                    donut_labels = ["No System"]
                    donut_values = [1]
                    donut_colors = ["#666666"]
                    self.donut_widget.values = donut_values
                    self.donut_widget.labels = donut_labels
                    self.donut_widget.colors = donut_colors
                    self.donut_widget.update()
                    self._hide_chart_loading('donut')
                    return
                
                # Get expense breakdown data for donut chart
                try:
                    print("🔄 Getting expense breakdown for donut chart...")
                    from_date_str = from_date.toString("yyyy-MM-dd")
                    to_date_str = to_date.toString("yyyy-MM-dd")
                    
                    # Get expense accounts and their balances for the date range
                    expense_accounts = []
                    accounts = self.system.get_chart_of_accounts(active_only=True)
                    
                    for account in accounts:
                        if account.get('account_type') == 'expense':
                            account_name = account['name']
                            # Get ledger entries for this expense account
                            ledger_entries = self.system.get_ledger(account_name, from_date_str, to_date_str)
                            if ledger_entries:
                                # Calculate total expense for this account
                                total_expense = 0
                                for entry in ledger_entries:
                                    value = 0
                                    if isinstance(entry, dict):
                                        v = entry.get('debit', 0)
                                    elif isinstance(entry, tuple):
                                        v = entry[1] if len(entry) > 1 else 0
                                    else:
                                        v = 0
                                    try:
                                        value = float(v)
                                    except (ValueError, TypeError):
                                        value = 0
                                    total_expense += abs(value)
                                if total_expense > 0:
                                    expense_accounts.append({
                                        'name': account_name,
                                        'amount': total_expense
                                    })
                
                except Exception as e:
                    print(f"❌ Error updating donut chart: {e}")
                    donut_labels = ["Error"]
                    donut_values = [1]
                    donut_colors = ["#666666"]
                    self.donut_widget.values = donut_values
                    self.donut_widget.labels = donut_labels
                    self.donut_widget.colors = donut_colors
                    self.donut_widget.update()
            
            except Exception as e:
                print(f"❌ Error updating donut chart: {e}")
                donut_labels = ["Error"]
                donut_values = [1]
                donut_colors = ["#666666"]
                self.donut_widget.values = donut_values
                self.donut_widget.labels = donut_labels
                self.donut_widget.colors = donut_colors
                self.donut_widget.update()
        
        print("✅ Donut chart update complete")
        self._hide_chart_loading('donut')

        # Create donut chart widget
        donut_labels = ["Loading..."]
        donut_values = [1]
        donut_colors = ["#666666"]
        self.donut_widget = DonutChartWidget(donut_values, donut_labels, donut_colors)
        chart4 = PyQtGraphChartCard(self.donut_widget)
        chart4.setMinimumHeight(320)
        chart4.setMaximumHeight(600)
        
        # Connect date range selector to donut chart updates
        self.date_selector.dateRangeChanged.connect(self._update_donut_chart_with_loading)
        
        # Initial update
        self._update_donut_chart_with_loading()

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
        grid.addWidget(self.card_current_ratio, 4, 1)
        grid.addWidget(self.card_expenses, 4, 2)
        grid.addWidget(self.card_revenue, 4, 3)
        # Removed now-empty row 5
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
        
        # Actions layout - use grid to occupy full width
        actions_layout = QGridLayout()
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
        
        settings_card = ActionCard(
            "Settings",
            "Configure application preferences and system settings",
            accent_color="#9C27B0"
        )
        settings_card.clicked = self._open_settings_tab
        
        # Add action cards to grid (4 columns)
        actions_layout.addWidget(add_entry_card, 0, 0)
        actions_layout.addWidget(view_reports_card, 0, 1)
        actions_layout.addWidget(manage_accounts_card, 0, 2)
        actions_layout.addWidget(settings_card, 0, 3)
        
        # Set equal stretch for all columns so they occupy full width
        for col in range(4):
            actions_layout.setColumnStretch(col, 1)
            
        content_layout.addLayout(actions_layout)
        
    def _setup_default_accounts(self):
        """Set up default Revenue and Expense accounts for chart comparison."""
        try:
            accounts = self.system.get_chart_of_accounts(active_only=True)
            
            # Find default accounts
            revenue_account = None
            expense_account = None
            
            for account in accounts:
                account_name = account['name'].lower()
                if 'revenue' in account_name or 'income' in account_name:
                    revenue_account = account['name']
                elif 'expense' in account_name or 'cost' in account_name:
                    expense_account = account['name']
            
            # Set defaults if found
            if revenue_account and hasattr(self, 'account1_combo'):
                self.account1_combo.setCurrentText(revenue_account)
                print(f"✅ Set default account1: {revenue_account}")
            
            if expense_account and hasattr(self, 'account2_combo'):
                self.account2_combo.setCurrentText(expense_account)
                print(f"✅ Set default account2: {expense_account}")
            
            # If no specific accounts found, use first two accounts
            if not revenue_account and not expense_account and len(accounts) >= 2:
                if hasattr(self, 'account1_combo'):
                    self.account1_combo.setCurrentIndex(0)
                if hasattr(self, 'account2_combo'):
                    self.account2_combo.setCurrentIndex(1)
                print("✅ Set first two accounts as defaults")
                
        except Exception as e:
            print(f"❌ Error setting default accounts: {e}")

    def _load_data(self):
        """Load dashboard data and set up default accounts."""
        self._update_metrics()
        self._setup_default_accounts()
    
    def _show_no_data_chart(self, plot_widget, message="No data available"):
        """Show no data message on chart"""
        plot_widget.clear()
        plot_widget.setLabel('left', "Value", color='white', size='10pt')
        plot_widget.setLabel('bottom', "Period", color='white', size='10pt')
        plot_widget.addLegend(offset=(10,10), labelTextColor='white', brush=pg.mkBrush(30,32,36,180))
        
        # Add text item to show no data message
        from PyQt6.QtGui import QColor
        text_item = pg.TextItem(text=message, 
                              color=QColor(255, 255, 255, 153),  # 153 = 0.6 * 255
                              anchor=(0.5, 0.5))
        plot_widget.addItem(text_item)
        text_item.setPos(0.5, 0.5)
    
    def _show_no_data_chart_accounts(self, plot_widget, account1, account2):
        """Show no data message on account comparison chart"""
        message = f"No data available for\n{account1} vs {account2}\nin selected date range"
        self._show_no_data_chart(plot_widget, message)
    
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
        
        # Get currency symbol
        symbol = self._get_currency_symbol()
        
        # Update card values using proper currency formatting
        self.card_cash.set_value(format_currency(cash))
        self.card_net_income.set_value(format_currency(net_income))
        self.card_liabilities.set_value(format_currency(liabilities))
        self.card_revenue.set_value(format_currency(revenue))
        self.card_expenses.set_value(format_currency(expenses))
        
        # Calculate and update ratios using the financial ratio calculator
        self._update_ratio_metrics(to_date_str)
        
        # Get accounts receivable and payable data
        receivables = self._get_accounts_receivable(to_date_str)
        payables = self._get_accounts_payable(to_date_str)
        
        # Update receivables and payables cards
        self.card_receivables.set_value(format_currency(receivables))
        self.card_payables.set_value(format_currency(payables))
        
        # Update trend indicators
        self._update_trend_indicators(cash, revenue, expenses, liabilities, net_income)
        
    def _update_ratio_metrics(self, as_of_date):
        """Update ratio metrics using the financial ratio calculator."""
        try:
            # Import the financial ratio calculator
            from src.core.financial_ratios import FinancialRatioCalculator
            from datetime import datetime
            
            # Convert string date to date object
            if isinstance(as_of_date, str):
                as_of_date = datetime.strptime(as_of_date, '%Y-%m-%d').date()
            
            # Create ratio calculator instance
            ratio_calculator = FinancialRatioCalculator(self.system.db_manager, self.system)
            
            # Calculate all ratios
            print(f"🔍 Calculating ratios for date: {as_of_date}")
            ratio_data = ratio_calculator.calculate_all_ratios(as_of_date)
            
            if 'error' in ratio_data:
                print(f"❌ Error calculating ratios: {ratio_data['error']}")
                # Set default values on error
                self.card_quick_ratio.set_value("0.00")
                self.card_debt_equity.set_value("0.00")
                self.card_current_ratio.set_value("0.00")
                self.card_gross_margin.set_value("0.00%")
                self.card_operating_margin.set_value("0.00%")
                return
            
            print(f"✅ Ratio calculation successful: {ratio_data.keys()}")
            
            # Extract ratios from the calculated data
            ratios = ratio_data.get('ratios', {})
            print(f"📊 Available ratio categories: {list(ratios.keys())}")
            
            # Update Quick Ratio
            liquidity_ratios = ratios.get('liquidity', {})
            print(f"💧 Liquidity ratios available: {list(liquidity_ratios.keys())}")
            quick_ratio_data = liquidity_ratios.get('quick_ratio', {})
            if quick_ratio_data:
                quick_ratio_value = quick_ratio_data.get('value', 0)
                self.card_quick_ratio.set_value(f"{quick_ratio_value:.2f}")
                print(f"✅ Quick ratio updated: {quick_ratio_value:.2f}")
            else:
                self.card_quick_ratio.set_value("0.00")
                print("⚠️ No quick ratio data available")
            
            # Update Current Ratio
            current_ratio_data = liquidity_ratios.get('current_ratio', {})
            if current_ratio_data:
                current_ratio_value = current_ratio_data.get('value', 0)
                self.card_current_ratio.set_value(f"{current_ratio_value:.2f}")
                print(f"✅ Current ratio updated: {current_ratio_value:.2f}")
            else:
                self.card_current_ratio.set_value("0.00")
                print("⚠️ No current ratio data available")
            
            # Update Debt-to-Equity Ratio
            leverage_ratios = ratios.get('leverage', {})
            print(f"⚖️ Leverage ratios available: {list(leverage_ratios.keys())}")
            debt_equity_data = leverage_ratios.get('debt_to_equity', {})
            if debt_equity_data:
                debt_equity_value = debt_equity_data.get('value', 0)
                self.card_debt_equity.set_value(f"{debt_equity_value:.2f}")
                print(f"✅ Debt-to-equity ratio updated: {debt_equity_value:.2f}")
            else:
                self.card_debt_equity.set_value("0.00")
                print("⚠️ No debt-to-equity ratio data available")
            
            # Update Profitability Ratios (Gross Margin and Operating Margin)
            profitability_ratios = ratios.get('profitability', {})
            print(f"💰 Profitability ratios available: {list(profitability_ratios.keys())}")
            
            # Update Gross Margin
            gross_margin_data = profitability_ratios.get('gross_profit_margin', {})
            if gross_margin_data:
                gross_margin_value = gross_margin_data.get('value', 0)
                self.card_gross_margin.set_value(f"{gross_margin_value:.1f}%")
                print(f"✅ Gross margin updated: {gross_margin_value:.1f}%")
            else:
                self.card_gross_margin.set_value("0.00%")
                print("⚠️ No gross margin data available")
            
            # Update Operating Margin (using net profit margin as proxy)
            net_margin_data = profitability_ratios.get('net_profit_margin', {})
            if net_margin_data:
                net_margin_value = net_margin_data.get('value', 0)
                self.card_operating_margin.set_value(f"{net_margin_value:.1f}%")
                print(f"✅ Operating margin updated: {net_margin_value:.1f}%")
            else:
                self.card_operating_margin.set_value("0.00%")
                print("⚠️ No operating margin data available")
            
        except Exception as e:
            print(f"❌ Error updating ratio metrics: {e}")
            # Set default values on error
            self.card_quick_ratio.set_value("0.00")
            self.card_debt_equity.set_value("0.00")
            self.card_current_ratio.set_value("0.00")
            self.card_gross_margin.set_value("0.00%")
            self.card_operating_margin.set_value("0.00%")
            
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
            
    def _calculate_running_balance_from_ledger(self, ledger_entries, account_name):
        """Calculate running balance from ledger entries."""
        running_balance = 0.0
        daily_balances = {}
        
        for entry in ledger_entries:
            date, description, debit_account, credit_account, amount = entry
            
            # Determine if this is a debit or credit to our account
            is_debit = (debit_account == account_name or 
                      (debit_account and account_name in debit_account))
            is_credit = (credit_account == account_name or 
                       (credit_account and account_name in credit_account))
            
            if is_debit:
                running_balance += amount
            elif is_credit:
                running_balance -= amount
            
            # Store balance for this date
            daily_balances[date] = running_balance
        
        return daily_balances
    
    def _get_parent_account_balance(self, account_data, as_of_date):
        """Get parent account balance using hierarchical aggregation (same as ledger cards)."""
        try:
            # Use hierarchical account balances (same method as ledger cards)
            hierarchical_balances = self.system.get_hierarchical_account_balances(None, as_of_date)
            
            # Find the account in the hierarchical balances
            account_name = account_data['name']
            balance_info = hierarchical_balances.get(account_name, {})
            
            # Return the net balance (aggregated from children)
            net_balance = balance_info.get('net_balance', 0.0)
            
            # For parent accounts, we want the absolute value for display
            return abs(net_balance)
            
        except Exception as e:
            print(f"❌ Error getting parent account balance for {account_data['name']}: {e}")
            return 0.0
    
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
            
    def _get_accounts_receivable(self, as_of_date=None):
        """Get accounts receivable using group-based balance sheet."""
        try:
            balance_sheet = self.system.generate_group_based_balance_sheet(as_of_date)
            
            # Look for current assets section which includes receivables
            for section in balance_sheet.get('asset_sections', []):
                if section.get('group') == 'current_asset':
                    # Extract receivables from current assets
                    receivable_accounts = ['receivable', 'ar', 'accounts receivable', 'trade receivable']
                    receivable_total = 0.0
                    for account in section.get('accounts', []):
                        account_name = account.get('name', '').lower()
                        if any(receivable_type in account_name for receivable_type in receivable_accounts):
                            receivable_total += abs(account.get('balance', 0))
                        # Also check children recursively
                        receivable_total += self._extract_receivables_from_account_tree(account)
                    return receivable_total
            return 0.0
        except Exception as e:
            print(f"Error getting accounts receivable: {e}")
            return 0.0
            
    def _get_accounts_payable(self, as_of_date=None):
        """Get accounts payable using group-based balance sheet."""
        try:
            balance_sheet = self.system.generate_group_based_balance_sheet(as_of_date)
            
            # Look for current liabilities section which includes payables
            for section in balance_sheet.get('liability_sections', []):
                if section.get('group') == 'current_liability':
                    # Extract payables from current liabilities
                    payable_accounts = ['payable', 'ap', 'accounts payable', 'trade payable']
                    payable_total = 0.0
                    for account in section.get('accounts', []):
                        account_name = account.get('name', '').lower()
                        if any(payable_type in account_name for payable_type in payable_accounts):
                            payable_total += abs(account.get('balance', 0))
                        # Also check children recursively
                        payable_total += self._extract_payables_from_account_tree(account)
                    return payable_total
            return 0.0
        except Exception as e:
            print(f"Error getting accounts payable: {e}")
            return 0.0
            
    def _extract_receivables_from_account_tree(self, account):
        """Extract receivables from account tree recursively."""
        receivable_total = 0.0
        receivable_accounts = ['receivable', 'ar', 'accounts receivable', 'trade receivable']
        
        # Check if this account is a receivable
        account_name = account.get('name', '').lower()
        if any(receivable_type in account_name for receivable_type in receivable_accounts):
            receivable_total += abs(account.get('balance', 0))
        
        # Check children recursively
        for child in account.get('children', []):
            receivable_total += self._extract_receivables_from_account_tree(child)
            
        return receivable_total
        
    def _extract_payables_from_account_tree(self, account):
        """Extract payables from account tree recursively."""
        payable_total = 0.0
        payable_accounts = ['payable', 'ap', 'accounts payable', 'trade payable']
        
        # Check if this account is a payable
        account_name = account.get('name', '').lower()
        if any(payable_type in account_name for payable_type in payable_accounts):
            payable_total += abs(account.get('balance', 0))
        
        # Check children recursively
        for child in account.get('children', []):
            payable_total += self._extract_payables_from_account_tree(child)
            
        return payable_total
        
    def _get_currency_symbol(self):
        """Get the currency symbol from the main window."""
        mw = self.window()
        return getattr(mw, 'currency_symbol', '$')
        
    def _on_date_range_changed(self, start_date, end_date):
        """Handle date range selection changes with smart data validation."""
        # Quick check for data before expensive operations (using cached check)
        if not self._check_has_data():
            # Show empty state immediately
            self._show_empty_state()
            return
        
        # Update metrics immediately (fast)
        self._update_metrics()
        
        # Charts will update with their own loading states via signal connections
        # No need to manually trigger chart updates here
    
    def _show_empty_state(self):
        """Show appropriate empty state when no data is available."""
        # Set all metrics to zero
        self.card_cash.set_value("0.00")
        self.card_net_income.set_value("0.00")
        self.card_revenue_growth.set_value("0.00%")
        self.card_expense_growth.set_value("0.00%")
        self.card_liabilities.set_value("0.00")
        self.card_working_capital.set_value("0.00")
        self.card_gross_margin.set_value("0.00%")
        self.card_operating_margin.set_value("0.00%")
        self.card_receivables.set_value("0.00")
        self.card_payables.set_value("0.00")
        self.card_quick_ratio.set_value("0.00")
        self.card_debt_equity.set_value("0.00")
        self.card_current_ratio.set_value("0.00")
        self.card_dso.set_value("0")
        self.card_expenses.set_value("0.00")
        self.card_revenue.set_value("0.00")
        
        # Show no data charts
        if hasattr(self, 'chart1_plot'):
            self._show_no_data_chart(self.chart1_plot, "No transactions available\nfor selected date range")
        if hasattr(self, 'donut_widget'): # Changed from chart2_plot to donut_widget
            self._show_no_data_chart(self.donut_widget, "No financial data available\nfor selected date range") # Changed from chart2_plot to donut_widget
        
        print("📊 Dashboard: Showing empty state - no data available")
        
    def _open_journal_entry_dialog(self):
        """Switch to the journal tab to add a new entry."""
        main_window = self.window()
        if main_window and hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Journal')
            
    def _open_reports_tab(self):
        """Open the reports tab."""
        main_window = self.window()
        if main_window and hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Reports')
            
    def _open_accounts_tab(self):
        """Open the accounts tab."""
        main_window = self.window()
        if main_window and hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Accounts')
            
    def _open_settings_tab(self):
        """Open the settings tab."""
        main_window = self.window()
        if main_window and hasattr(main_window, 'setCurrentIndexByName'):
            main_window.setCurrentIndexByName('Settings')
            
    def refresh_currency_display(self):
        """Refresh all currency displays when currency symbol changes."""
        try:
            # Refresh the dashboard metrics
            self._update_metrics()
        except Exception as e:
            print(f"Error refreshing currency display in dashboard: {e}")
    
    def refresh_data(self):
        """Refresh dashboard data when organization context changes."""
        try:
            print("🔄 Dashboard: Refreshing data due to organization change...")
            self._load_data()
            
            # Refresh chart dropdowns with new organization data
            self._refresh_chart_dropdowns()
            
            # Set up default accounts for new organization
            self._setup_default_accounts()
            
            # Force refresh all charts with new organization data
            if hasattr(self, 'date_selector'):
                from_date, to_date = self.date_selector.get_date_range()
                print(f"   Date range: {from_date.toString('yyyy-MM-dd')} to {to_date.toString('yyyy-MM-dd')}")
                
                # Trigger chart updates with loading states
                self._update_chart1_with_loading()
                self._update_donut_chart_with_loading()
                print("   ✅ Dashboard refreshed with new organization context")
                
        except Exception as e:
            print(f"❌ Error refreshing dashboard data: {e}")
    
    def refresh_organization_context(self, new_system):
        """Update the system reference when organization changes."""
        try:
            print(f"🔄 Dashboard: Updating system reference for new organization...")
            self.system = new_system
            self._load_data()
            
            # Refresh chart dropdowns with new organization data
            self._refresh_chart_dropdowns()
            
            # Set up default accounts for new organization
            self._setup_default_accounts()
            
            print("   ✅ Dashboard system reference updated")
        except Exception as e:
            print(f"❌ Error updating dashboard system reference: {e}")
    
    def _refresh_chart_dropdowns(self):
        """Refresh chart dropdowns with new organization data."""
        try:
            print("   🔄 Refreshing chart dropdowns...")
            
            # Refresh account dropdowns for Chart 1
            if hasattr(self, 'account1_combo') and hasattr(self, 'account2_combo'):
                # Get new accounts from the current organization
                accounts = self.system.get_chart_of_accounts(active_only=True)
                account_names = [acc['name'] for acc in accounts]
                
                # Store current selections
                current_account1 = self.account1_combo.currentText()
                current_account2 = self.account2_combo.currentText()
                
                # Clear and repopulate dropdowns
                self.account1_combo.clear()
                self.account2_combo.clear()
                self.account1_combo.addItems(account_names)
                self.account2_combo.addItems(account_names)
                
                # Try to restore previous selections if they still exist
                if current_account1 in account_names:
                    self.account1_combo.setCurrentText(current_account1)
                elif account_names:
                    self.account1_combo.setCurrentIndex(0)
                
                if current_account2 in account_names:
                    self.account2_combo.setCurrentText(current_account2)
                elif len(account_names) > 1:
                    self.account2_combo.setCurrentIndex(1)
                elif account_names:
                    self.account2_combo.setCurrentIndex(0)
                
                print(f"   ✅ Account dropdowns refreshed with {len(account_names)} accounts")
                
                # Trigger chart update with loading state
                if hasattr(self, '_update_chart1_with_loading'):
                    self._update_chart1_with_loading()
            
            print("   ✅ Chart dropdowns refreshed successfully")
            
        except Exception as e:
            print(f"   ❌ Error refreshing chart dropdowns: {e}")
        
    def _apply_styling(self):
        """Apply beautiful glassmorphism styling to the dashboard."""
        # Apply glassmorphism styling (removed Mica effect as it's handled by MainWindow)
        
        # Apply main container glassmorphism effect
        GlassmorphismHelper.apply_main_container_effect(self)
        
        # Set the complete modern stylesheet
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())

    def _show_chart_loading(self, chart_name):
        """Show loading state for a specific chart."""
        if chart_name == 'chart1' and hasattr(self, 'chart1_plot'):
            self.chart1_plot.clear()
            # Add loading text
            text_item = pg.TextItem(text="Loading account comparison...", 
                                  color=pg.mkColor('white'),
                                  anchor=(0.5, 0.5))
            self.chart1_plot.addItem(text_item)
            text_item.setPos(0.5, 0.5)
            self.chart_loading_states['chart1'] = True
            
        elif chart_name == 'donut' and hasattr(self, 'donut_widget'):
            # For donut chart, show loading state
            self.donut_widget.values = [1]
            self.donut_widget.labels = ["Loading..."]
            self.donut_widget.colors = ["#666666"]
            self.donut_widget.update()
            self.chart_loading_states['donut'] = True
    
    def _hide_chart_loading(self, chart_name):
        """Hide loading state for a specific chart."""
        self.chart_loading_states[chart_name] = False
    
    def _update_chart1_with_loading(self):
        """Update chart1 with loading state."""
        print("🔄 Starting chart1 update with loading...")
        self._show_chart_loading('chart1')
        
        # Use QTimer to delay the actual update
        self.chart1_timer.start(100)  # 100ms delay
        print("⏰ Chart1 timer started")
    
    def _perform_chart1_update(self):
        """Perform the actual chart1 update."""
        print("🎯 Performing chart1 update...")
        try:
            account1 = self.account1_combo.currentText()
            account2 = self.account2_combo.currentText()
            from_date, to_date = self.date_selector.get_date_range()
            from_date_str = from_date.toString("yyyy-MM-dd")
            to_date_str = to_date.toString("yyyy-MM-dd")
            
            print(f"📊 Chart1 accounts: {account1} vs {account2}")
            print(f"📅 Date range: {from_date_str} to {to_date_str}")
            
            # Only fetch data if accounts are selected
            if account1 == "Select Account" or account2 == "Select Account":
                print("⚠️ No accounts selected, showing no data")
                self._show_no_data_chart_accounts(self.chart1_plot, account1, account2)
                self._hide_chart_loading('chart1')
                return
            
            # Fetch data only for selected accounts
            data1 = None
            data2 = None
            
            # Get account data for account1
            if account1 and account1 != "Select Account":
                print(f"🔍 Fetching data for account1: {account1}")
                accounts = self.system.get_chart_of_accounts(active_only=False)
                account1_data = next((acc for acc in accounts if acc['name'] == account1), None)
                
                if account1_data:
                    account1_is_postable = account1_data.get('is_postable', True)
                    
                    if account1_is_postable:
                        ledger1 = self.system.get_ledger(account1, from_date_str, to_date_str)
                        if ledger1:
                            data1 = self._calculate_running_balance_from_ledger(ledger1, account1)
                            print(f"✅ Got ledger data for {account1}: {len(ledger1)} entries")
                    else:
                        data1 = self._get_parent_account_balance(account1_data, to_date_str)
                        print(f"✅ Got balance sheet data for {account1}: {data1}")
            
            # Get account data for account2
            if account2 and account2 != "Select Account":
                print(f"🔍 Fetching data for account2: {account2}")
                accounts = self.system.get_chart_of_accounts(active_only=False)
                account2_data = next((acc for acc in accounts if acc['name'] == account2), None)
                
                if account2_data:
                    account2_is_postable = account2_data.get('is_postable', True)
                    
                    if account2_is_postable:
                        ledger2 = self.system.get_ledger(account2, from_date_str, to_date_str)
                        if ledger2:
                            data2 = self._calculate_running_balance_from_ledger(ledger2, account2)
                            print(f"✅ Got ledger data for {account2}: {len(ledger2)} entries")
                    else:
                        data2 = self._get_parent_account_balance(account2_data, to_date_str)
                        print(f"✅ Got balance sheet data for {account2}: {data2}")
            
            # Update chart with data
            if data1 or data2:
                print("📈 Updating chart1 display with data")
                self._update_chart1_display(data1, data2, account1, account2)
            else:
                print("⚠️ No data available for selected accounts")
                self._show_no_data_chart_accounts(self.chart1_plot, account1, account2)
                
        except Exception as e:
            print(f"❌ Error updating account comparison chart: {e}")
            self._show_no_data_chart_accounts(self.chart1_plot, account1, account2)
        
        print("✅ Chart1 update complete")
        self._hide_chart_loading('chart1')
    
    def _update_chart1_display(self, data1, data2, account1, account2):
        """Update chart1 display with fetched data, aggregated by month."""
        def aggregate_monthly(data):
            if not isinstance(data, dict):
                return [], []
            monthly = defaultdict(float)
            for date_str, value in data.items():
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                month_key = dt.strftime("%Y-%m")
                monthly[month_key] += value
            # Sort by month
            months = sorted(monthly.keys())
            values = [monthly[m] for m in months]
            return months, values
        
        months1, values1 = aggregate_monthly(data1) if data1 else ([], [])
        months2, values2 = aggregate_monthly(data2) if data2 else ([], [])
        
        # Merge months
        all_months = sorted(set(months1) | set(months2))
        def fill_values(months, values):
            month_to_value = dict(zip(months, values))
            return [month_to_value.get(m, 0) for m in all_months]
        values1_filled = fill_values(months1, values1)
        values2_filled = fill_values(months2, values2)
        
        # Format month labels for X axis
        month_labels = [datetime.strptime(m, "%Y-%m").strftime("%b %Y") for m in all_months]
        
        if all_months:
            self.chart1_plot.clear()
            self.chart1_plot.plot(range(len(all_months)), values1_filled, pen=pg.mkPen('#4caf50', width=3), name=account1, symbol='o', symbolBrush='#4caf50')
            self.chart1_plot.plot(range(len(all_months)), values2_filled, pen=pg.mkPen('#f44336', width=3), name=account2, symbol='o', symbolBrush='#f44336')
            self.chart1_plot.getAxis('bottom').setTicks([list(enumerate(month_labels))])
            self.chart1_plot.setLabel('left', "Balance", color='white', size='10pt')
            self.chart1_plot.setLabel('bottom', "Month", color='white', size='10pt')
            self.chart1_plot.addLegend(offset=(10,10), labelTextColor='white', brush=pg.mkBrush(30,32,36,180))
            print(f"✅ Account comparison chart updated with data for {len(all_months)} months")
            print(f"   Account 1 ({account1}): final balance: {values1_filled[-1] if values1_filled else 0}")
            print(f"   Account 2 ({account2}): final balance: {values2_filled[-1] if values2_filled else 0}")
        else:
            print("⚠️ No data available for selected accounts and date range")
            self._show_no_data_chart_accounts(self.chart1_plot, account1, account2)
    
    def _update_donut_chart_with_loading(self):
        """Update donut chart with loading state."""
        print("🔄 Starting donut chart update with loading...")
        self._show_chart_loading('donut')
        
        # Use QTimer to delay the actual update
        self.donut_timer.start(100)  # 100ms delay
        print("⏰ Donut chart timer started")
    
    def _perform_donut_chart_update(self):
        """Perform the actual donut chart update."""
        print("🎯 Performing donut chart update...")
        try:
            from_date, to_date = self.date_selector.get_date_range()
            
            print(f"📅 Date range: {from_date.toString('yyyy-MM-dd')} to {to_date.toString('yyyy-MM-dd')}")
            
            # Check if date range is valid
            if from_date is None or to_date is None:
                print("⚠️ No date range selected for donut chart")
                donut_labels = ["No Date Range"]
                donut_values = [1]
                donut_colors = ["#666666"]
                self.donut_widget.values = donut_values
                self.donut_widget.labels = donut_labels
                self.donut_widget.colors = donut_colors
                self.donut_widget.update()
                self._hide_chart_loading('donut')
                return
            
            from_date_str = from_date.toString("yyyy-MM-dd")
            to_date_str = to_date.toString("yyyy-MM-dd")
            
            # Check if system is available
            if not self.system:
                print("⚠️ No accounting system available for donut chart")
                donut_labels = ["No System"]
                donut_values = [1]
                donut_colors = ["#666666"]
                self.donut_widget.values = donut_values
                self.donut_widget.labels = donut_labels
                self.donut_widget.colors = donut_colors
                self.donut_widget.update()
                self._hide_chart_loading('donut')
                return
            
            # Get expense breakdown data for donut chart
            try:
                print("🔄 Getting expense breakdown for donut chart...")
                from_date_str = from_date.toString("yyyy-MM-dd")
                to_date_str = to_date.toString("yyyy-MM-dd")
                
                # Get expense accounts and their balances for the date range
                expense_accounts = []
                accounts = self.system.get_chart_of_accounts(active_only=True)
                
                for account in accounts:
                    if account.get('account_type') == 'expense':
                        account_name = account['name']
                        # Get ledger entries for this expense account
                        ledger_entries = self.system.get_ledger(account_name, from_date_str, to_date_str)
                        if ledger_entries:
                            # Calculate total expense for this account
                            total_expense = 0
                            for entry in ledger_entries:
                                value = 0
                                if isinstance(entry, dict):
                                    v = entry.get('debit', 0)
                                elif isinstance(entry, tuple):
                                    v = entry[1] if len(entry) > 1 else 0
                                else:
                                    v = 0
                                try:
                                    value = float(v)
                                except (ValueError, TypeError):
                                    value = 0
                                total_expense += abs(value)
                            if total_expense > 0:
                                expense_accounts.append({
                                    'name': account_name,
                                    'amount': total_expense
                                })
                
                print(f"✅ Found {len(expense_accounts)} expense accounts with data")
                
                if expense_accounts:
                    # Sort by amount (highest first) and take top 8
                    expense_accounts.sort(key=lambda x: x['amount'], reverse=True)
                    top_expenses = expense_accounts[:8]
                    
                    # Prepare donut chart data
                    donut_labels = []
                    donut_values = []
                    donut_colors = []
                    
                    # Color palette for expenses
                    expense_colors = [
                        '#f44336', '#e91e63', '#9c27b0', '#673ab7',
                        '#3f51b5', '#2196f3', '#03a9f4', '#00bcd4'
                    ]
                    
                    for i, expense in enumerate(top_expenses):
                        donut_labels.append(expense['name'])
                        donut_values.append(expense['amount'])
                        donut_colors.append(expense_colors[i % len(expense_colors)])
                    
                    top_expenses_str = [f"{e['name']}: {e['amount']}" for e in top_expenses]
                    print(f"📊 Top expenses: {top_expenses_str}")
                    
                else:
                    # No expense data available
                    print("⚠️ No expense data available for selected date range")
                    donut_labels = ["No Expenses"]
                    donut_values = [1]
                    donut_colors = ["#666666"]
                
                # Update donut chart
                self.donut_widget.values = donut_values
                self.donut_widget.labels = donut_labels
                self.donut_widget.colors = donut_colors
                self.donut_widget.update()
                
                print(f"✅ Donut chart updated with {len(donut_values)} expense categories")
                
            except Exception as e:
                print(f"❌ Error updating donut chart: {e}")
                donut_labels = ["Error"]
                donut_values = [1]
                donut_colors = ["#666666"]
                self.donut_widget.values = donut_values
                self.donut_widget.labels = donut_labels
                self.donut_widget.colors = donut_colors
                self.donut_widget.update()
        
        except Exception as e:
            print(f"❌ Error updating donut chart: {e}")
            donut_labels = ["Error"]
            donut_values = [1]
            donut_colors = ["#666666"]
            self.donut_widget.values = donut_values
            self.donut_widget.labels = donut_labels
            self.donut_widget.colors = donut_colors
            self.donut_widget.update()
        
        print("✅ Donut chart update complete")
        self._hide_chart_loading('donut')

    def _check_has_data(self):
        """Check if organization has data with caching to reduce repeated calls."""
        current_time = time.time()
        
        # Only check every 10 seconds to avoid excessive calls
        if (self._cached_has_data is None or 
            current_time - self._last_data_check > 10):
            
            if hasattr(self.system, 'data_validator'):
                self._cached_has_data = self.system.data_validator.has_any_data()
                self._last_data_check = current_time
            else:
                self._cached_has_data = True  # Assume data exists if no validator
        
        return self._cached_has_data
