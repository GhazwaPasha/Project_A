"""
Clean, Professional Journal Page with Tab System
Refactored to eliminate code duplication and vestigial components
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFrame, QDateEdit, QMessageBox, 
    QScrollArea, QSizePolicy, QTabWidget
)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from ...core.accounting_system import AccountingSystem
from ..components.widgets import PageHeader, EditableAccountComboBox
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..common import ResponsiveHelper
from .bulk_entry import BulkEntryPage


class TransactionCard(QFrame):
    """Read-only transaction display card."""
    
    def __init__(self, entry_data):
        super().__init__()
        self.entry_data = entry_data
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the transaction card UI."""
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                margin: 2px 0px;
                min-height: 45px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)  # Match header padding
        layout.setSpacing(12)  # Match header spacing
        
        # Common styles
        base_style = """
            color: rgba(255, 255, 255, 0.9);
            font-weight: 500;
            font-size: 14px;
            background: transparent;
            border: none;
            padding: 0px;
            margin: 0px;
        """
        
        # Date column
        date_value = self.entry_data.get('date', 'N/A')
        date_label = QLabel(str(date_value))
        date_label.setFixedWidth(80)
        date_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        date_label.setStyleSheet(base_style)
        
        # Description column
        desc_value = self.entry_data.get('description', 'No description')
        desc_label = QLabel(str(desc_value))
        desc_label.setFixedWidth(200)
        desc_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        desc_label.setStyleSheet(base_style)
        desc_label.setWordWrap(True)
        
        # Debit account column
        debit_account = self.entry_data.get('debit_account', 'N/A')
        debit_label = QLabel(str(debit_account))
        debit_label.setFixedWidth(200)
        debit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        debit_label.setStyleSheet(base_style)
        debit_label.setWordWrap(True)
        
        # Credit account column
        credit_account = self.entry_data.get('credit_account', 'N/A')
        credit_label = QLabel(str(credit_account))
        credit_label.setFixedWidth(200)
        credit_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        credit_label.setStyleSheet(base_style)
        credit_label.setWordWrap(True)
        
        # Amount column
        amount = self.entry_data.get('amount', 0)
        if isinstance(amount, (int, float)):
            amount_str = f"${amount:,.2f}"
        else:
            try:
                amount_str = f"${float(amount):,.2f}"
            except (ValueError, TypeError):
                amount_str = f"${amount}"
        
        amount_label = QLabel(amount_str)
        amount_label.setFixedWidth(100)
        amount_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        amount_label.setStyleSheet(base_style)
        
        # Add all columns to layout
        layout.addWidget(date_label)
        layout.addWidget(desc_label)
        layout.addWidget(debit_label)
        layout.addWidget(credit_label)
        layout.addWidget(amount_label)
        
        # Set fixed height for consistent row height
        self.setFixedHeight(45)


class JournalPage(QWidget):
    """Tabbed journal page with single entry and bulk entry tabs."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
        self._apply_styling()
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(self._get_tab_style() + ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the tabbed interface."""
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))  # Match other pages
        
        # Page header with small margin
        header = PageHeader("Journal Entry", "Record and manage your financial transactions")
        main_layout.addWidget(header)
        
        # Small spacer to align with other pages
        main_layout.addSpacing(ResponsiveHelper.scale_size(20, 16, 24))
        
        # Tab widget - aligned with other pages' quick filters
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(self._get_tab_style())
        
        # Single entry tab
        self.single_entry_tab = SingleEntryTab(self.system)
        self.tab_widget.addTab(self.single_entry_tab, "Single Entry")
        
        # Bulk entry tab
        self.bulk_entry_tab = BulkEntryPage(self.system)
        self.tab_widget.addTab(self.bulk_entry_tab, "Bulk Entry")
          # Set default tab
        self.tab_widget.setCurrentIndex(0)
        main_layout.addWidget(self.tab_widget, 1)  # Use default stretch factor for natural spacing
    
    def _get_tab_style(self):
        """Get the styling for the tab widget."""
        return """
            QTabWidget::pane {
                border: none;
                background: transparent;
                margin-top: 2px;
            }
            
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
                font-weight: 500;
                font-size: 12px;
                margin-right: 8px;
                min-width: 80px;
            }
            
            QTabBar::tab:hover {
                background: rgba(255, 255, 255, 0.2);
                border-color: rgba(255, 255, 255, 0.3);
            }
            
            QTabBar::tab:selected {
                background: rgba(100, 181, 246, 0.3);
                border-color: #64B5F6;
                color: #64B5F6;
            }
            
            QTabBar::tab:first {
                margin-left: 0;
            }
        """


class SingleEntryTab(QWidget):
    """Clean single entry tab with form and transaction history."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.accounts = []
        self._load_accounts()
        self._setup_ui()
        self._load_transactions()
        
    def _load_accounts(self):
        """Load accounts from the system."""
        try:
            if hasattr(self.system, 'get_all_accounts'):
                accounts_data = self.system.get_all_accounts()
                self.accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data if acc[5]]
            else:
                # No fallback accounts - system must have proper chart of accounts
                self.accounts = []
                print("Warning: System does not have get_all_accounts method")
        except Exception as e:
            print(f"Error loading accounts: {e}")
            # No fallback accounts - system must have proper chart of accounts
            self.accounts = []
        
    def _setup_ui(self):
        """Setup the single entry tab UI with fixed top section and scrollable transactions."""
        tab_layout = QVBoxLayout(self)
        tab_layout.setContentsMargins(0, 0, 0, 0)
        tab_layout.setSpacing(0)
        
        # Main container (no scroll area - fixed content)
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(0, ResponsiveHelper.scale_size(24, 16, 32),
                                     0, ResponsiveHelper.scale_size(24, 16, 32))
        main_layout.setSpacing(ResponsiveHelper.scale_size(24, 16, 32))
        
        # Entry form (fixed at top)
        self.entry_form = self._create_entry_form()
        main_layout.addWidget(self.entry_form)
        
        # Transaction History Header (fixed)
        header_label = QLabel("Transaction History")
        header_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            background: transparent;
            border: none;
        """)
        main_layout.addWidget(header_label)
        
        # Create headers frame with proper height and styling
        self.headers_frame = QFrame()
        self.headers_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                margin-bottom: 8px;
                min-height: 45px;
            }
            QLabel {
                font-weight: bold;
            }
        """)
        
        # Setup headers layout with proper spacing
        headers_layout = QHBoxLayout(self.headers_frame)
        headers_layout.setContentsMargins(16, 0, 16, 0)  # Remove vertical padding from layout
        headers_layout.setSpacing(12)
        
        # Define and create headers with proper widths
        headers = [
            ("DATE", 80, "rgba(255, 255, 255, 0.8)"),
            ("DESCRIPTION", 200, "rgba(255, 255, 255, 0.8)"),
            ("DEBIT ACCOUNT", 200, "rgba(255, 255, 255, 0.8)"),
            ("CREDIT ACCOUNT", 200, "rgba(255, 255, 255, 0.8)"),
            ("AMOUNT", 100, "rgba(255, 255, 255, 0.8)")
        ]
        
        for text, width, color in headers:
            header = QLabel(text)
            header.setFixedWidth(width)
            header.setFixedHeight(45)
            header.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            header.setStyleSheet(f"""
                color: {color};
                font-weight: 700;
                font-size: 12px;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                letter-spacing: 0.5px;
            """)
            headers_layout.addWidget(header)
        
        main_layout.addWidget(self.headers_frame)
        
        # Add the fixed content to main layout
        tab_layout.addWidget(main_container)        # Scrollable transactions area
        self.transactions_scroll = QScrollArea()
        self.transactions_scroll.setWidgetResizable(True)
        self.transactions_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.transactions_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.transactions_scroll.setStyleSheet("""
            QScrollArea, QWidget#scrollAreaWidgetContents {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
            QWidget { background: transparent; }
        """)
        
        # Transactions container widget (scrollable content)
        self.transactions_widget = QWidget()
        self.transactions_layout = QVBoxLayout(self.transactions_widget)
        self.transactions_layout.setContentsMargins(0, 0, 0, ResponsiveHelper.scale_size(24, 16, 32))
        self.transactions_layout.setSpacing(8)        
        self.transactions_scroll.setWidget(self.transactions_widget)
        tab_layout.addWidget(self.transactions_scroll, 1)  # This takes remaining space

    def _create_entry_form(self):
        """Create expandable entry form."""
        from PyQt6.QtCore import QPropertyAnimation, QEasingCurve
        from PyQt6.QtWidgets import QGridLayout
        from ..components.shared_styles import get_field_style, get_button_style, get_label_style
        
        # Main container
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
            }
        """)
        container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header with toggle
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.12);
                border: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
            }
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 12, 18, 12)
        header_layout.setSpacing(8)
        
        title = QLabel("New Transaction")
        title.setStyleSheet("color: white; font-size: 15px; font-weight: 600; background: transparent;")
        
        toggle_btn = QLabel()
        toggle_btn.setStyleSheet("""
            QLabel {
                border: none;
                background: transparent;
                font-size: 18px;
                color: rgba(255, 255, 255, 0.9);
            }
        """)
        toggle_btn.setText("▶")
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(toggle_btn)

        # Collapsible content
        content = QFrame()
        content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(18, 8, 18, 18)
        content_layout.setSpacing(12)

        # Form fields grid
        grid = QGridLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(4)
        
        # Labels
        labels = ["DATE", "DESCRIPTION", "DEBIT ACCOUNT", "CREDIT ACCOUNT", "AMOUNT"]
        for i, text in enumerate(labels):
            label = QLabel(text)
            label.setStyleSheet("""
                color: rgba(255, 255, 255, 0.8);
                font-size: 11px;
                font-weight: 600;
                background: transparent;
                border: none;
                padding: 0px;
                margin: 0px;
                letter-spacing: 0.5px;
            """)
            label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            grid.addWidget(label, 0, i)
        
        # Input fields
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setFixedHeight(32)
        self.date_edit.setFixedWidth(130)
        self.date_edit.setStyleSheet("""
            QDateEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 4px 12px;
                color: white;
                font-size: 12px;
                min-height: 32px;
            }
            QDateEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QDateEdit:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
            QDateEdit::drop-down {
                border: none;
                width: 20px;
            }
            QDateEdit::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid rgba(255, 255, 255, 0.7);
                margin-right: 6px;
            }
            QCalendarWidget {
                background-color: rgb(32, 32, 32);
                color: white;
            }
            QCalendarWidget QToolButton {
                color: white;
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 4px;
            }
            QCalendarWidget QToolButton:hover {
                background: rgba(255, 255, 255, 0.1);
            }
            QCalendarWidget QMenu {
                background-color: rgb(32, 32, 32);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QCalendarWidget QSpinBox {
                color: white;
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 2px;
            }
            QCalendarWidget QAbstractItemView:enabled {
                color: white;
                background: rgb(32, 32, 32);
                selection-background-color: rgba(100, 181, 246, 0.3);
                selection-color: white;
            }
            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background: rgb(32, 32, 32);
            }
        """)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Enter description...")
        self.desc_edit.setMinimumWidth(180)
        self.desc_edit.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 4px 12px;
                color: white;
                font-size: 12px;
                min-height: 32px;
            }
            QLineEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        
        account_combo_style = """
            QComboBox {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 4px 12px;
                color: white;
                font-size: 12px;
                min-height: 32px;
                min-width: 160px;
            }
            QComboBox:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QComboBox:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 4px solid transparent;
                border-right: 4px solid transparent;
                border-top: 4px solid rgba(255, 255, 255, 0.7);
                margin-right: 6px;
            }
            QComboBox::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
            QComboBox QAbstractItemView {
                background: rgba(40, 40, 40, 0.95);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                color: white;
                selection-background-color: rgba(100, 181, 246, 0.2);
                selection-color: white;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item {
                padding: 8px 12px;
                border: none;
                border-radius: 4px;
                margin: 2px;
            }
            QComboBox QAbstractItemView::item:hover {
                background: rgba(100, 181, 246, 0.1);
            }
            QComboBox QAbstractItemView::item:selected {
                background: rgba(100, 181, 246, 0.2);
            }
        """

        self.debit_combo = EditableAccountComboBox()
        self.debit_combo.setMinimumWidth(160)
        self.debit_combo.setMaximumWidth(240)
        self.debit_combo.setStyleSheet(account_combo_style)
        self._populate_account_combo(self.debit_combo)
        
        self.credit_combo = EditableAccountComboBox()
        self.credit_combo.setMinimumWidth(160)
        self.credit_combo.setMaximumWidth(240)
        self.credit_combo.setStyleSheet(account_combo_style)
        self._populate_account_combo(self.credit_combo)
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.amount_edit.setFixedWidth(130)
        self.amount_edit.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 4px 12px;
                color: white;
                font-size: 12px;
                min-height: 32px;
            }
            QLineEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        
        fields = [self.date_edit, self.desc_edit, self.debit_combo, self.credit_combo, self.amount_edit]
        for i, field in enumerate(fields):
            grid.addWidget(field, 1, i)
        
        # AI input field and buttons
        self.nl_input = QLineEdit()
        self.nl_input.setPlaceholderText("Describe your transaction in plain English...")
        self.nl_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                padding: 4px 12px;
                color: white;
                font-size: 12px;
                min-height: 32px;
            }
            QLineEdit:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QLineEdit:focus {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.5);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        grid.addWidget(self.nl_input, 2, 0, 1, 2)  # row 2, span columns 0-1 (Date + Description)

        button_base_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
                color: white;
                padding: 4px 16px;
                font-size: 12px;
                font-weight: 500;
                min-height: 32px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(100, 181, 246, 0.3);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.15);
            }
        """

        primary_button_style = button_base_style + """
            QPushButton {
                background: rgba(100, 181, 246, 0.2);
                border: 1px solid rgba(100, 181, 246, 0.5);
                color: #90CAF9;
            }
            QPushButton:hover {
                background: rgba(100, 181, 246, 0.3);
                border: 1px solid rgba(100, 181, 246, 0.7);
            }
            QPushButton:pressed {
                background: rgba(100, 181, 246, 0.4);
            }
        """

        # Interpret button
        parse_btn = QPushButton("Interpret")
        parse_btn.setStyleSheet(button_base_style)
        parse_btn.clicked.connect(self._parse_transaction)
        grid.addWidget(parse_btn, 2, 2)  # row 2, column 2 (Debit)
        
        # Save button (primary)
        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(primary_button_style)
        save_btn.clicked.connect(self._save_entry)
        grid.addWidget(save_btn, 2, 3)  # row 2, column 3 (Credit)
        
        # Clear button
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet(button_base_style)
        clear_btn.clicked.connect(self._clear_form)
        grid.addWidget(clear_btn, 2, 4)  # row 2, column 4 (Amount)

        content_layout.addLayout(grid)

        # Setup animation
        content.setVisible(False)
        layout.addWidget(content)

        animation = QPropertyAnimation(content, b"maximumHeight")
        animation.setDuration(250)
        animation.setEasingCurve(QEasingCurve.Type.InOutCubic)

        def toggle():
            # Check current visibility to determine state
            expanded = content.isVisible()
            toggle_btn.setText("▶" if expanded else "▼")
            
            animation.stop()
            try:
                animation.finished.disconnect()
            except TypeError:
                pass
            
            if not expanded:  # Currently collapsed, so expand
                content.setVisible(True)
                content.setMaximumHeight(16777215)
                content_height = content.sizeHint().height()
                animation.setStartValue(0)
                animation.setEndValue(content_height)
                animation.start()
            else:  # Currently expanded, so collapse
                current_height = content.height()
                animation.setStartValue(current_height)
                animation.setEndValue(0)
                animation.finished.connect(lambda: content.setVisible(False))
                animation.start()

        def header_toggle():
            toggle()
        
        # Only connect header click to toggle function (not the triangle icon)
        header.mousePressEvent = lambda event: header_toggle()

        layout.insertWidget(0, header)
        return container
    
    def _populate_account_combo(self, combo):
        """Populate account combo box."""
        combo.setAccountList(self.accounts)
        combo.setPlaceholderText("Select or type account...")
        combo.clear_selection()
    
    def _parse_transaction(self):
        """Parse natural language transaction."""
        nl_text = self.nl_input.text().strip()
        if not nl_text:
            QMessageBox.warning(self, "Missing Input", "Please enter a description to parse.")
            return
        try:
            from ...core.utils import parse_transaction
            parsed = parse_transaction(nl_text, valid_accounts=self.accounts, system=self.system)
            self.date_edit.setDate(QDate.fromString(parsed['date'], 'yyyy-MM-dd'))
            self.desc_edit.setText(parsed['description'])
            self.debit_combo.setCurrentText(parsed['debit_account'])
            self.credit_combo.setCurrentText(parsed['credit_account'])
            self.amount_edit.setText(str(parsed['amount']))
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Could not parse entry: {e}")

    def _save_entry(self):
        """Save the journal entry."""
        try:
            date = self.date_edit.date().toString("yyyy-MM-dd")
            description = self.desc_edit.text().strip()
            debit_account = self.debit_combo.currentText().strip()
            credit_account = self.credit_combo.currentText().strip()
            amount = self.amount_edit.text().strip()
            
            # Validation
            if not all([description, debit_account, credit_account, amount]):
                QMessageBox.warning(self, "Validation Error", "Please fill in all fields.")
                return
                
            if debit_account == credit_account:
                QMessageBox.warning(self, "Validation Error", "Debit and Credit accounts cannot be the same.")
                return
                
            try:
                float(amount)
            except ValueError:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid amount.")
                return
            
            # Save to system
            if hasattr(self.system, 'add_journal_entry'):
                entry_id = self.system.add_journal_entry(date, description, debit_account, credit_account, amount)
            
            QMessageBox.information(self, "Success", "Transaction saved successfully!")
            self._clear_form()
            
            # Refresh transactions with improved timing
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._load_transactions)  # Small delay to ensure DB operations complete
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save transaction: {e}")
    
    def _clear_form(self):
        """Clear all form fields."""
        self.desc_edit.clear()
        self.debit_combo.clear_selection()
        self.credit_combo.clear_selection()
        self.amount_edit.clear()
        self.date_edit.setDate(QDate.currentDate())
        self.nl_input.clear()
        
    def _create_transactions_section(self):
        """This method is no longer used - transactions are now directly in main layout."""
        pass
    def _load_transactions(self):
        """Load and display recent transactions."""
        # Clear existing transactions
        for i in reversed(range(self.transactions_layout.count())):
            item = self.transactions_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget:
                    self.transactions_layout.removeWidget(widget)
                    widget.deleteLater()
                else:
                    # It's a spacer item
                    self.transactions_layout.removeItem(item)
        
        try:
            if hasattr(self.system, 'get_recent_journal_entries'):
                transactions = self.system.get_recent_journal_entries(limit=10)
                
                if transactions:
                    for transaction in transactions:
                        card = TransactionCard(transaction)
                        card.show()  # Ensure card is visible
                        self.transactions_layout.addWidget(card)
                else:
                    empty_label = QLabel("No transactions yet. Add your first transaction above!")
                    empty_label.setStyleSheet("""
                        color: rgba(255, 255, 255, 0.6);
                        font-size: 14px;
                        font-style: italic;
                        text-align: center;
                        padding: 40px;
                    """)
                    empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.transactions_layout.addWidget(empty_label)
            
            # Add spacer to push content to top
            from PyQt6.QtWidgets import QSpacerItem
            spacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            self.transactions_layout.addItem(spacer)
            
            # Force comprehensive layout update
            self.transactions_widget.updateGeometry()
            self.transactions_layout.update()
            
            # Also update the parent widgets
            if self.transactions_widget.parent():
                self.transactions_widget.parent().updateGeometry()
                self.transactions_widget.parent().update()
            
            # Force a repaint of the entire widget
            self.transactions_widget.repaint()
            
            # Ensure scroll area shows the top (newest entries)
            if hasattr(self, 'transactions_scroll'):
                self.transactions_scroll.verticalScrollBar().setValue(0)
                self.transactions_scroll.ensureVisible(0, 0)
            
        except Exception as e:
            print(f"Error loading transactions: {e}")
            error_label = QLabel("Error loading transactions. Please try again.")
            error_label.setStyleSheet("""
                color: rgba(255, 100, 100, 0.8);
                font-size: 14px;
                text-align: center;
                padding: 40px;
            """)
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.transactions_layout.addWidget(error_label)
