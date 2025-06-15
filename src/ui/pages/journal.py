"""
Clean, Professional Journal Page
Simple entry form + clean transaction display
No complexity, no clutter, just what accountants need.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QFrame, QDateEdit, QMessageBox, 
    QScrollArea, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QPropertyAnimation, QEasingCurve, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
from ...core.utils import parse_transaction, analyze_accounts_with_llm
from ..components.widgets import DateRangeSelector, PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..common import ResponsiveHelper


class TransactionCard(QFrame):
    """A clean card for displaying a transaction."""
    
    def __init__(self, entry_data):
        super().__init__()
        self.entry_data = entry_data
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the transaction card UI."""
        self.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin: 2px 0px;
            }
            QFrame:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.2);
            }        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(15)
          # Entry data structure: (id, date, description, debit_account, credit_account, amount, timestamp)
        # Date (position 1)
        date_label = QLabel(str(self.entry_data[1]))
        date_label.setStyleSheet("color: #90CAF9; font-weight: 500; background: transparent; border: none;")
        date_label.setFixedWidth(85)
        
        # Description (position 2)
        desc_label = QLabel(str(self.entry_data[2]))
        desc_label.setStyleSheet("color: white; font-weight: 500; background: transparent; border: none;")
        desc_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
          # Debit account (position 3 - debit_account)
        from_label = QLabel(str(self.entry_data[3]))
        from_label.setStyleSheet("color: #A5D6A7; font-size: 12px; background: transparent; border: none;")
        from_label.setFixedWidth(140)
        
        # Credit account (position 4 - credit_account) 
        to_label = QLabel(str(self.entry_data[4]))
        to_label.setStyleSheet("color: #FFAB91; font-size: 12px; background: transparent; border: none;")
        to_label.setFixedWidth(140)
        
        # Amount column - single, properly aligned (position 5)
        amount = float(self.entry_data[5])
        amount_label = QLabel(f"${amount:,.2f}")
        amount_label.setStyleSheet("color: #81C784; font-weight: 600; background: transparent; border: none;")
        amount_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        amount_label.setFixedWidth(120)
        
        layout.addWidget(date_label)
        layout.addWidget(desc_label)
        layout.addWidget(from_label)
        layout.addWidget(to_label)
        layout.addWidget(amount_label)
class JournalPage(QWidget):
    """Clean, professional journal page."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.is_form_expanded = False  # Form starts collapsed
        self._setup_ui()
        self._apply_styling()
        self._load_transactions()
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling to the journal page."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the main UI."""
        # Main layout with responsive margins
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(32, 24, 48))
        
        # Page header
        header = PageHeader("Journal Entries", "Record and view your accounting transactions")
        main_layout.addWidget(header)
        
        # Entry form (collapsible)
        self._create_collapsible_entry_form(main_layout)
          # Transactions list
        self._create_transactions_list(main_layout)
        
    def _create_collapsible_entry_form(self, main_layout):
        """Create the collapsible entry form."""
        # Container for the entire form section
        self.form_container = QFrame()
        self.form_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
            }
        """)
        
        container_layout = QVBoxLayout(self.form_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Clickable header with expand/collapse functionality
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
        
        # Make the header frame clickable
        self.header_frame.mousePressEvent = self._on_header_click
        self.header_frame.setCursor(Qt.CursorShape.PointingHandCursor)
        
        header_layout = QHBoxLayout(self.header_frame)
        header_layout.setContentsMargins(20, 16, 20, 16)
        header_layout.setSpacing(12)
        
        # Form title and subtitle
        title_container = QVBoxLayout()
        title_container.setSpacing(2)
        
        form_title = QLabel("New Transaction")
        form_title.setStyleSheet("""
            font-size: 16px;
            font-weight: 600;
            color: white;
            background: transparent;
            border: none;
        """)
        
        form_subtitle = QLabel("Add a new journal entry")
        form_subtitle.setStyleSheet("""
            font-size: 12px;
            color: rgba(255, 255, 255, 0.7);
            background: transparent;
            border: none;
        """)
        
        title_container.addWidget(form_title)
        title_container.addWidget(form_subtitle)
        
        # Toggle indicator (subtle arrow) - starts collapsed
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
        
        container_layout.addWidget(self.header_frame)
          # Collapsible content area
        self.form_content = QFrame()
        self.form_content.setStyleSheet("""
            QFrame {
                background: transparent;
                border: none;
                padding: 12px;
            }
        """)
        
        self._create_form_fields()
        container_layout.addWidget(self.form_content)
          # Set initial state (collapsed)
        self.form_content.setVisible(self.is_form_expanded)
        
        main_layout.addWidget(self.form_container)
        
    def _create_form_fields(self):
        """Create the actual form fields."""
        form_layout = QVBoxLayout(self.form_content)
        form_layout.setSpacing(12)  # Reduced spacing
        form_layout.setContentsMargins(16, 16, 16, 16)  # Reduced margins
        
        # Form fields in a grid
        fields_layout = QHBoxLayout()
        fields_layout.setSpacing(10)  # Reduced spacing between columns
        
        # Date field
        date_container = QVBoxLayout()
        date_container.setSpacing(2)  # Minimal spacing
        date_label = QLabel("Date")
        date_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8); 
            font-size: 11px; 
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setStyleSheet(self._get_input_style())
        
        date_container.addWidget(date_label)
        date_container.addWidget(self.date_edit)
        
        # Simple Description field
        desc_container = QVBoxLayout()
        desc_container.setSpacing(2)  # Minimal spacing
        
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8); 
            font-size: 11px; 
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        
        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("Transaction description")
        self.desc_edit.setStyleSheet(self._get_input_style())
        
        desc_container.addWidget(desc_label)
        desc_container.addWidget(self.desc_edit)
        
        # Debit account
        from_container = QVBoxLayout()
        from_container.setSpacing(2)  # Minimal spacing
        from_label = QLabel("Debit Account")
        from_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8); 
            font-size: 11px; 
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        
        self.from_combo = QComboBox()
        self.from_combo.setEditable(True)
        self.from_combo.setStyleSheet(self._get_combo_style())
        self._populate_accounts(self.from_combo)
        
        from_container.addWidget(from_label)
        from_container.addWidget(self.from_combo)
        
        # Credit account
        to_container = QVBoxLayout()
        to_container.setSpacing(2)  # Minimal spacing
        to_label = QLabel("Credit Account")
        to_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8); 
            font-size: 11px; 
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        
        self.to_combo = QComboBox()
        self.to_combo.setEditable(True)
        self.to_combo.setStyleSheet(self._get_combo_style())
        self._populate_accounts(self.to_combo)
        
        to_container.addWidget(to_label)
        to_container.addWidget(self.to_combo)
        
        # Amount field
        amount_container = QVBoxLayout()
        amount_container.setSpacing(2)  # Minimal spacing
        amount_label = QLabel("Amount")
        amount_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.8); 
            font-size: 11px; 
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setStyleSheet(self._get_input_style())
        
        amount_container.addWidget(amount_label)
        amount_container.addWidget(self.amount_edit)
        # Add all field containers to the layout
        fields_layout.addLayout(date_container)
        fields_layout.addLayout(desc_container)
        fields_layout.addLayout(from_container)
        fields_layout.addLayout(to_container)
        fields_layout.addLayout(amount_container)
        
        form_layout.addLayout(fields_layout)
        
        # Action buttons
        self._create_action_buttons(form_layout)
        
    def _create_action_buttons(self, form_layout):
        """Create action buttons and AI controls for the form."""        # AI input row - compact and above the buttons
        ai_input_layout = QHBoxLayout()
        ai_input_layout.setSpacing(8)
        ai_input_layout.setContentsMargins(0, 4, 0, 0)        # Natural language input field - full width to match description field above
        self.nl_input = QLineEdit()
        self.nl_input.setPlaceholderText("Describe your Entry in Words")
        self.nl_input.setStyleSheet(self._get_input_style())
        # Enable Enter key to trigger AI parsing
        self.nl_input.returnPressed.connect(self._parse_with_ai)
        
        # Add robotic icon at the end of the input field
        ai_icon = QLabel("🤖")
        ai_icon.setStyleSheet("""
            color: rgba(255, 255, 255, 0.6);
            font-size: 16px;
            background: transparent;
            border: none;
            padding: 0px 8px;
        """)
        ai_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Container for input field and icon
        ai_input_container = QHBoxLayout()
        ai_input_container.setSpacing(0)
        ai_input_container.setContentsMargins(0, 0, 0, 0)
        ai_input_container.addWidget(self.nl_input)
        ai_input_container.addWidget(ai_icon)
        
        # Success checkmark (initially hidden) - appears next to robot
        self.success_checkmark = QLabel("✅")
        self.success_checkmark.setStyleSheet("""
            color: rgba(129, 199, 132, 1.0);
            font-size: 16px;
            background: transparent;
            border: none;
            padding: 0px 4px;
        """)
        self.success_checkmark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.success_checkmark.hide()
        
        ai_input_container.addWidget(self.success_checkmark)
        
        # Parsing progress indicator - positioned separately to avoid width changes
        self.parsing_indicator = QLabel("")
        self.parsing_indicator.setStyleSheet("""
            color: rgba(129, 199, 132, 0.8);
            font-size: 10px;
            font-weight: 500;
            background: transparent;
            border: none;
        """)
        self.parsing_indicator.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        
        ai_input_layout.addLayout(ai_input_container)
        ai_input_layout.addWidget(self.parsing_indicator)
        ai_input_layout.addStretch()  # Push everything to the left
        
        form_layout.addLayout(ai_input_layout)
        
        # Combined action buttons row with AI controls inline
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 6, 0, 0)
        button_layout.setSpacing(8)
        
        # AI Parse button - compact
        self.parse_btn = QPushButton("🪄 Fill")
        self.parse_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(76, 175, 80, 0.8),
                    stop:1 rgba(129, 199, 132, 0.8));
                border: 1px solid rgba(76, 175, 80, 0.3);
                border-radius: 5px;
                padding: 6px 12px;
                color: white;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(76, 175, 80, 1.0),
                    stop:1 rgba(129, 199, 132, 1.0));
            }
            QPushButton:disabled {
                background: rgba(128, 128, 128, 0.3);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.parse_btn.clicked.connect(self._parse_with_ai)
        self.parse_btn.setFixedWidth(65)
        
        # Clear button - positioned next to Add Entry
        clear_btn = QPushButton("Clear")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: 500;
                font-size: 11px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
        """)
        clear_btn.clicked.connect(self._clear_form)
        clear_btn.setFixedWidth(55)
        
        # Add entry button - primary action
        add_btn = QPushButton("Add Entry")
        add_btn.setStyleSheet("""
            QPushButton {
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 6px 16px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background: #45a049;
            }
            QPushButton:pressed {
                background: #3d8b40;
            }
        """)
        add_btn.clicked.connect(self._add_entry)
        add_btn.setFixedWidth(85)
        
        # Layout the buttons: AI Fill on left, Clear and Add Entry on right
        button_layout.addWidget(self.parse_btn)
        button_layout.addStretch()
        button_layout.addWidget(clear_btn)
        button_layout.addWidget(add_btn)
        
        form_layout.addLayout(button_layout)
        
    def _create_transactions_list(self, main_layout):
        """Create the transactions list."""
        # Header
        list_header = QLabel("Transactions")
        list_header.setStyleSheet("""
            font-size: 20px;
            font-weight: 600;
            color: white;
            margin-bottom: 16px;
            background: transparent;
            border: none;
        """)
        main_layout.addWidget(list_header)
          # Date filter
        self._create_date_filter(main_layout)
        
        # Column headers for better alignment
        self._create_column_headers(main_layout)
        
        # Scrollable area for transactions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.4);
            }
        """)
        
        # Container for transaction cards
        self.transactions_container = QWidget()
        self.transactions_layout = QVBoxLayout(self.transactions_container)
        self.transactions_layout.setSpacing(8)
        self.transactions_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll_area.setWidget(self.transactions_container)
        main_layout.addWidget(scroll_area)
        
    def _create_date_filter(self, main_layout):
        """Create the date filter widget."""
        self.date_selector = DateRangeSelector(callback=self._on_date_range_changed)
        main_layout.addWidget(self.date_selector)
        
    def _on_date_range_changed(self):
        """Handle date range changes."""
        self._load_transactions()
        
    def _create_column_headers(self, main_layout):
        """Create column headers for the transactions table."""
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: none;
                border-radius: 6px;
                margin: 8px 0px;
            }
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(16, 8, 16, 8)
        header_layout.setSpacing(15)
        
        # Date header
        date_header = QLabel("Date")
        date_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        date_header.setFixedWidth(85)
        
        # Description header
        desc_header = QLabel("Description")
        desc_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        desc_header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
          # Debit header
        from_header = QLabel("Debit")
        from_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        from_header.setFixedWidth(140)
        
        # Credit header
        to_header = QLabel("Credit")
        to_header.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-weight: 600; font-size: 12px; background: transparent; border: none;")
        to_header.setFixedWidth(140)
        
        # Amount header - single column to match transaction display
        amount_header = QLabel("Amount")
        amount_header.setStyleSheet("color: #81C784; font-weight: 600; font-size: 12px; background: transparent; border: none;")
        amount_header.setAlignment(Qt.AlignmentFlag.AlignRight)
        amount_header.setFixedWidth(120)
        
        header_layout.addWidget(date_header)
        header_layout.addWidget(desc_header)
        header_layout.addWidget(from_header)
        header_layout.addWidget(to_header)
        header_layout.addWidget(amount_header)
        
        main_layout.addWidget(header_frame)
        
    def _on_header_click(self, event):
        """Handle header click to toggle form."""
        self._toggle_form()
        
    def _toggle_form(self):
        """Toggle the form visibility."""
        self.is_form_expanded = not self.is_form_expanded
        self.form_content.setVisible(self.is_form_expanded)
        self.toggle_indicator.setText("▼" if self.is_form_expanded else "▶")
        self._update_header_styling()
        
    def _update_header_styling(self):
        """Update header styling based on expanded state."""
        if self.is_form_expanded:
            self.header_frame.setStyleSheet("""
                QFrame {
                    background: rgba(255, 255, 255, 0.08);
                    border: none;
                    border-top-left-radius: 12px;
                    border-top-right-radius: 12px;
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
        
    def _get_input_style(self):
        """Get styling for input fields."""
        return """
            QLineEdit, QDateEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus, QDateEdit:focus {
                background: rgba(255, 255, 255, 0.15);
                border-color: #4CAF50;
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
            }
        """
        
    def _get_combo_style(self):
        """Get styling for combo boxes."""
        return """
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
                min-width: 150px;
            }
            QComboBox:focus {
                background: rgba(255, 255, 255, 0.15);
                border-color: #4CAF50;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-style: solid;
                border-width: 4px 4px 0 4px;
                border-color: white transparent transparent transparent;
            }            QComboBox QAbstractItemView {
                background: #2b2b2b;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                selection-background-color: #4CAF50;
            }
        """
        
    def _populate_accounts(self, combo):
        """Populate account combo boxes."""
        try:
            accounts = self.system.get_all_accounts()
            combo.clear()
            for account in accounts:
                combo.addItem(f"{account[2]} - {account[0]}", account[0])
        except Exception as e:
            print(f"Error loading accounts: {e}")
            
    def _populate_smart_accounts(self, combo, suggested_accounts):
        """Populate combo box with smart account suggestions first, then all accounts."""
        try:
            combo.clear()
            # Add suggested accounts first (prioritized but no visual indicator)
            for account_name in suggested_accounts:
                # Find the account details
                for name, acc_type, code, parent_code, level, is_postable, description in self.system.get_all_accounts():
                    if name.lower().strip() == account_name.lower().strip():
                        combo.addItem(f"{code} - {name}", name)
                        break
            
            # Add all other accounts
            all_accounts = self.system.get_all_accounts()
            for name, acc_type, code, parent_code, level, is_postable, description in all_accounts:
                # Skip if already added as suggestion
                if name not in suggested_accounts:
                    combo.addItem(f"{code} - {name}", name)                    
        except Exception as e:
            print(f"Error loading smart accounts: {e}")
            # Fallback to regular population
            self._populate_accounts(combo)
    
    def _clear_form(self):
        """Clear the form fields."""
        self.date_edit.setDate(QDate.currentDate())
        self.nl_input.clear()
        self.desc_edit.clear()
        self.from_combo.setCurrentIndex(-1)
        self.to_combo.setCurrentIndex(-1)
        self.amount_edit.clear()
        self._clear_parsing_indicators()  # Clear all parsing indicators
        # Refresh to show all accounts again
        self._refresh_all_accounts()
        
    def _refresh_all_accounts(self):
        """Refresh combo boxes to show all accounts."""
        self._populate_accounts(self.from_combo)
        self._populate_accounts(self.to_combo)
    
    def _parse_with_ai(self):
        """Parse natural language input with AI and fill form fields."""
        nl_text = self.nl_input.text().strip()
        
        if not nl_text:
            QMessageBox.warning(self, "AI Parse", "Please enter a transaction description first.")
            return        # Disable button and show progress
        self.parse_btn.setText("Parsing...")
        self.parse_btn.setEnabled(False)
        self.parsing_indicator.setText("Analyzing transaction...")
        self.success_checkmark.hide()
        
        try:
            # Get available accounts for context
            available_accounts = []
            accounts = self.system.get_all_accounts()
            for account in accounts:
                available_accounts.append(account[0])  # account name
            
            self.parsing_indicator.setText("Processing with AI...")
            
            # Use AI to parse the transaction (includes accounting logic enforcement)
            parsed_data = parse_transaction(nl_text, available_accounts, self.system)
            
            self.parsing_indicator.setText("Matching accounts...")
            
            # Get smart account suggestions based on the input
            suggested_accounts = analyze_accounts_with_llm(self.system, nl_text)
            
            # Update combo boxes with relevant accounts for better UX
            if suggested_accounts:
                self._populate_smart_accounts(self.from_combo, suggested_accounts)
                self._populate_smart_accounts(self.to_combo, suggested_accounts)
            
            if parsed_data:
                # Fill the form fields with AI-parsed data
                
                # Set description
                if 'description' in parsed_data:
                    self.desc_edit.setText(parsed_data['description'])
                
                # Set amount
                if 'amount' in parsed_data:
                    self.amount_edit.setText(str(parsed_data['amount']))
                
                # Set accounts (debit = from, credit = to in double-entry)
                if 'debit_account' in parsed_data:
                    from_account = parsed_data['debit_account']
                    # Find and set the account in combo
                    for i in range(self.from_combo.count()):
                        combo_text = self.from_combo.itemText(i)
                        combo_data = self.from_combo.itemData(i)
                        if (from_account.lower() in combo_text.lower() or 
                            from_account.lower() == combo_data.lower()):
                            self.from_combo.setCurrentIndex(i)
                            break
                
                if 'credit_account' in parsed_data:
                    to_account = parsed_data['credit_account']
                    # Find and set the account in combo
                    for i in range(self.to_combo.count()):
                        combo_text = self.to_combo.itemText(i)
                        combo_data = self.to_combo.itemData(i)
                        if (to_account.lower() in combo_text.lower() or 
                            to_account.lower() == combo_data.lower()):
                            self.to_combo.setCurrentIndex(i)
                            break                
                # Transaction parsed successfully - show checkmark next to robot
                self.parsing_indicator.setText("")
                self.success_checkmark.show()
                
            else:
                self.parsing_indicator.setText("❌ Could not parse transaction")
                self.success_checkmark.hide()
                QMessageBox.warning(self, "AI Parse Error",                    "❌ Could not parse the transaction.\n\n"
                    "💡 **Suggestions:**\n"
                    "• Try rephrasing with more details\n"
                    "• Include amount, accounts, and action\n"                    "• Example: 'paid office rent $500 by bank transfer'\n\n"
                    "You can still fill the form manually.")
                
        except Exception as e:
            self.parsing_indicator.setText("❌ Parsing failed")
            self.success_checkmark.hide()
            error_msg = str(e)
            if "API" in error_msg.upper():
                QMessageBox.critical(self, "AI Service Error", 
                    f"🚫 AI Service Unavailable\n\n"
                    f"The AI parsing service is currently unavailable.\n"
                    f"Please check your internet connection and API configuration.\n\n"
                    f"Error: {error_msg}\n\n"
                    f"You can still fill the form manually.")
            else:
                QMessageBox.critical(self, "AI Parse Error", 
                    f"❌ An error occurred while parsing:\n\n{error_msg}\n\n"
                    f"💡 **What you can do:**\n"
                    f"• Check your transaction description\n"
                    f"• Try a simpler format\n"
                    f"• Fill the form manually\n\n"                    f"The error has been logged for review.")
        
        finally:
            # Re-enable button and clear progress after 2 seconds
            self.parse_btn.setText("🪄 Fill")
            self.parse_btn.setEnabled(True)
            # Clear progress text after a delay, but keep checkmark visible            QTimer.singleShot(2000, lambda: self.parsing_indicator.setText(""))
    
    def _clear_parsing_indicators(self):
        """Clear all parsing indicators."""
        self.parsing_indicator.setText("")
        self.success_checkmark.hide()
        
    def _add_entry(self):
        """Add a new journal entry."""
        try:
            # Get form data
            date = self.date_edit.date().toString("yyyy-MM-dd")
            description = self.desc_edit.text().strip()
            from_account = self.from_combo.currentData()
            to_account = self.to_combo.currentData()
            amount = self.amount_edit.text().strip()
            
            # Validate
            if not all([description, from_account, to_account, amount]):
                QMessageBox.warning(self, "Error", "Please fill in all fields.")
                return
                
            try:
                amount = float(amount)
                if amount <= 0:
                    raise ValueError()
            except ValueError:
                QMessageBox.warning(self, "Error", "Please enter a valid positive amount.")
                return
                
            if from_account == to_account:
                QMessageBox.warning(self, "Error", "Debit and Credit accounts must be different.")
                return
                
            # Add the entry
            entry_id = self.system.add_journal_entry(date, description, from_account, to_account, amount)
            if entry_id:
                QMessageBox.information(self, "Success", "Journal entry added successfully!")
                self._clear_form()
                self._load_transactions()
            else:
                QMessageBox.warning(self, "Error", "Failed to add journal entry.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            
    def _load_transactions(self):
        """Load and display transactions based on date filter."""
        try:
            # Clear existing cards
            for i in reversed(range(self.transactions_layout.count())):
                widget = self.transactions_layout.itemAt(i).widget()
                if widget:
                    widget.setParent(None)
                    
            # Get date range from filter
            from_date, to_date = self.date_selector.get_date_range()
            from_date_str = from_date.toString("yyyy-MM-dd") if from_date else None
            to_date_str = to_date.toString("yyyy-MM-dd") if to_date else None
            
            # Get filtered transactions
            try:
                if from_date_str and to_date_str:
                    # Get transactions within date range
                    entries = self.system.get_journal_entries_by_date_range(from_date_str, to_date_str)
                else:
                    # Get all recent transactions
                    entries = self.system.get_recent_journal_entries(50)  # Get last 50 entries
            except Exception as e:
                print(f"Error getting entries from system: {e}")
                entries = []
            
            if not entries:
                no_data = QLabel("No transactions found.")
                no_data.setStyleSheet("""
                    color: rgba(255, 255, 255, 0.6);
                    font-size: 14px;
                    text-align: center;
                    padding: 40px;
                    background: transparent;
                    border: none;
                """)
                no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.transactions_layout.addWidget(no_data)
            else:
                for entry in entries:
                    try:
                        card = TransactionCard(entry)
                        self.transactions_layout.addWidget(card)
                    except Exception as e:
                        print(f"Error creating card for entry {entry}: {e}")
                        # Skip this entry and continue
                        continue
                    
            # Add stretch at the end
            self.transactions_layout.addStretch()
            
        except Exception as e:
            print(f"Error loading transactions: {e}")
            error_label = QLabel(f"Error loading transactions: {str(e)}")
            error_label.setStyleSheet("""
                color: #f44336;
                font-size: 14px;
                background: transparent;
                border: none;
            """)
            self.transactions_layout.addWidget(error_label)
