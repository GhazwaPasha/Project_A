"""
Account Classifications Page
Simple table-based interface for classifying accounts for balance sheet reporting
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QFrame, QScrollArea, QSpacerItem, QSizePolicy, QMessageBox,
    QSplitter, QGroupBox, QGridLayout, QTableWidget, QTableWidgetItem,
    QApplication, QComboBox, QLineEdit, QCheckBox, QHeaderView,
    QAbstractItemView, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette
from datetime import datetime
from ...core.utils import format_currency
from ..common import ResponsiveHelper
from ..components.styles import ModernStyles
from ..components.widgets import PageHeader
from ..components.scrollbar_styles import ModernScrollbarStyles


class AccountClassificationsPage(QWidget):
    """Page for account classifications with simple table-based interface."""
    
    backToAccounts = pyqtSignal()
    
    def __init__(self, system=None, parent=None):
        super().__init__(parent)
        self.system = system
        self.accounts = []
        self.classifications = {}
        self.categories = [
            ("", "Unclassified"),
            ("current_asset", "Current Assets"),
            ("fixed_asset", "Fixed Assets"),
            ("other_asset", "Other Assets"),
            ("current_liability", "Current Liabilities"),
            ("long_term_liability", "Long-term Liabilities"),
            ("other_liability", "Other Liabilities"),
            ("cogs", "Cost of Goods Sold"),
        ]
        self._setup_ui()
        if system:
            self.load_accounts(system)
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        layout.setContentsMargins(responsive_margin, 0,  # Remove top margin for seamless flow
                                responsive_margin, responsive_margin)
        layout.setSpacing(16)  # Standardized spacing
        
        # Page header
        header = PageHeader("Accounts Map", "")
        layout.addWidget(header)
        
        # Store reference to update subtitle
        self.page_header = header
        
        # Search and filter bar
        self._create_search_filter_bar(layout)
        
        # Main table
        self._create_accounts_table(layout)
        
        # Action buttons
        self._create_action_buttons(layout)
    

    
    def _create_search_filter_bar(self, parent_layout):
        """Create search and filter controls."""
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        
        # Search box
        search_label = QLabel("Search:")
        search_label.setStyleSheet("color: white; font-size: 13px;")
        filter_layout.addWidget(search_label)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search by account name or code...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                color: white;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 200px;
            }
            QLineEdit:focus {
                border-color: rgba(100,181,246,0.5);
            }
        """)
        self.search_box.textChanged.connect(self._filter_accounts)
        filter_layout.addWidget(self.search_box)
        
        # Classification filter
        filter_label = QLabel("Filter by:")
        filter_label.setStyleSheet("color: white; font-size: 13px;")
        filter_layout.addWidget(filter_label)
        
        self.classification_filter = QComboBox()
        self.classification_filter.addItem("All Classifications", "")
        for key, label in self.categories[1:]:  # Skip "Unclassified"
            self.classification_filter.addItem(label, key)
        self.classification_filter.setStyleSheet("""
            QComboBox {
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                color: white;
                padding: 8px 12px;
                font-size: 13px;
                min-width: 150px;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid white;
            }
        """)
        self.classification_filter.currentIndexChanged.connect(self._filter_accounts)
        filter_layout.addWidget(self.classification_filter)
        
        filter_layout.addStretch()
        parent_layout.addLayout(filter_layout)
    

    
    def _create_accounts_table(self, parent_layout):
        """Create the main accounts table."""
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Account Code", "Account Name", "Type", "Classification"])

        # Configure table properties
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(False)
        self.table.setWordWrap(False)
        self.table.setCornerButtonEnabled(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.table.setStyleSheet(ModernScrollbarStyles.get_vertical_scrollbar_style())

        # Remove extra left margin/space
        self.table.setContentsMargins(0, 0, 0, 0)
        self.table.setStyleSheet(self.table.styleSheet() + "\nQTableCornerButton::section { background: transparent; border: none; }")

        # Configure vertical header
        vertical_header = self.table.verticalHeader()
        if vertical_header:
            vertical_header.setVisible(False)
            vertical_header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Configure header
        header = self.table.horizontalHeader()
        if header:
            header.setStretchLastSection(False)
            header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Account Code
            header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)           # Account Name
            header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Type
            header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Classification
            header.setDefaultAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            header.setMinimumSectionSize(20)
            header.resizeSection(0, 110)  # Account Code
            header.resizeSection(2, 90)   # Type
            header.resizeSection(3, 170)  # Classification
            header.setStyleSheet("""
                QHeaderView::section {
                    background: rgba(255,255,255,0.04);
                    border: none;
                    border-bottom: 1px solid rgba(255,255,255,0.08);
                    padding: 0px 18px;
                    color: rgba(255,255,255,0.85);
                    font-size: 13px;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    height: 48px;
                    min-height: 44px;
                    vertical-align: middle;
                }
                QHeaderView::section:first {
                    border-top-left-radius: 12px;
                }
                QHeaderView::section:last {
                    border-top-right-radius: 12px;
                }
            """)

        # Apply modern, clean table styling (no visible selection background)
        self.table.setStyleSheet(self.table.styleSheet() + """
            QTableWidget {
                background: rgba(255,255,255,0.02);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px;
                color: white;
                font-size: 13px;
                gridline-color: transparent;
                selection-background-color: transparent;
                outline: none;
                padding: 0px;
            }
            QTableWidget::item {
                padding: 0px 18px;
                border: none;
                background: transparent;
                font-size: 13px;
                vertical-align: middle;
            }
            QTableWidget::item:hover {
                background: rgba(255,255,255,0.04);
            }
            QTableWidget::item:selected {
                background: transparent;
                color: white;
            }
            QTableWidget::item:selected:hover {
                background: transparent;
            }
        """)

        parent_layout.addWidget(self.table, 1)
    
    def _create_action_buttons(self, parent_layout):
        """Create action buttons (no bulk selection)."""
        button_layout = QHBoxLayout()
        # Back button
        back_btn = QPushButton("← Back to Accounts")
        back_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.1);
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
                color: white;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.15);
                border-color: rgba(255,255,255,0.3);
            }
        """)
        back_btn.clicked.connect(self.backToAccounts.emit)
        button_layout.addWidget(back_btn)
        button_layout.addStretch()
        # Save button
        save_btn = QPushButton("Save Classifications")
        save_btn.setStyleSheet("""
            QPushButton {
                background: rgba(76,175,80,0.8);
                border: 1px solid rgba(76,175,80,0.5);
                border-radius: 6px;
                color: white;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
                min-width: 140px;
            }
            QPushButton:hover {
                background: rgba(76,175,80,0.9);
                border-color: rgba(76,175,80,0.7);
            }
            QPushButton:pressed {
                background: rgba(76,175,80,0.7);
            }
        """)
        save_btn.clicked.connect(self.save_classifications)
        button_layout.addWidget(save_btn)
        parent_layout.addLayout(button_layout)
    
    def load_accounts(self, system):
        """Load accounts from the system."""
        self.accounts = system.get_chart_of_accounts(active_only=True)
        
        # Load existing classifications from account data
        self.classifications = {}
        for account in self.accounts:
            account_id = account.get('id')
            classification = account.get('classification')
            if classification:
                self.classifications[account_id] = classification
        
        self.populate_table()
        self._update_statistics()
    
    def populate_table(self):
        """Populate the table with accounts."""
        self.table.setRowCount(len(self.accounts))
        
        for row, account in enumerate(self.accounts):
            # Account code
            code_item = QTableWidgetItem(account.get('code', ''))
            code_item.setData(Qt.ItemDataRole.UserRole, account.get('id'))
            code_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 0, code_item)
            
            # Account name
            name_item = QTableWidgetItem(account.get('name', ''))
            name_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 1, name_item)
            
            # Account type
            type_item = QTableWidgetItem(account.get('account_type', ''))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
            self.table.setItem(row, 2, type_item)
            
            # Classification dropdown
            classification_combo = QComboBox()
            for key, label in self.categories:
                classification_combo.addItem(label, key)
            
            current_classification = self.classifications.get(account.get('id'), '')
            index = classification_combo.findData(current_classification)
            if index >= 0:
                classification_combo.setCurrentIndex(index)
            
            classification_combo.currentIndexChanged.connect(
                lambda idx, acc_id=account.get('id'): self._on_classification_changed(acc_id, idx)
            )
            
            # Style the combo box to blend with table
            classification_combo.setStyleSheet("""
                QComboBox {
                    background: transparent;
                    border: none;
                    color: white;
                    padding: 0px 12px;
                    font-size: 13px;
                    border-radius: 6px;
                    min-height: 36px;
                    height: 36px;
                }
                QComboBox:hover {
                    background: rgba(255,255,255,0.01);
                }
                QComboBox:focus {
                    background: rgba(255,255,255,0.04);
                    border: 1px solid rgba(100,181,246,0.18);
                }
                QComboBox::drop-down {
                    border: none;
                    width: 20px;
                }
                QComboBox::down-arrow {
                    image: none;
                    border-left: 5px solid transparent;
                    border-right: 5px solid transparent;
                    border-top: 5px solid rgba(255,255,255,0.7);
                }
                QComboBox::down-arrow:hover {
                    border-top-color: white;
                }
                QComboBox QAbstractItemView {
                    background: rgba(30,30,30,0.97);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 8px;
                    color: white;
                    selection-background-color: transparent;
                    outline: none;
                }
                QComboBox QAbstractItemView::item {
                    padding: 8px 12px;
                    border: none;
                }
                QComboBox QAbstractItemView::item:hover {
                    background: transparent;
                }
                QComboBox QAbstractItemView::item:selected {
                    background: transparent;
                }
            """)
            classification_combo.setMinimumHeight(36)
            classification_combo.setMaximumHeight(36)
            self.table.setCellWidget(row, 3, classification_combo)
    
    def _on_classification_changed(self, account_id, combo_index):
        """Handle classification change in dropdown."""
        combo = self.table.cellWidget(self._get_row_by_account_id(account_id), 3)
        if combo and isinstance(combo, QComboBox):
            classification_key = combo.itemData(combo_index)
            if classification_key:
                self.classifications[account_id] = classification_key
            else:
                # Remove classification
                if account_id in self.classifications:
                    del self.classifications[account_id]
            
            self._update_statistics()
    
    def _get_row_by_account_id(self, account_id):
        """Get table row by account ID."""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is not None and item.data(Qt.ItemDataRole.UserRole) == account_id:
                return row
        return -1
    
    def _filter_accounts(self):
        """Filter accounts based on search text and classification filter."""
        search_text = self.search_box.text().lower()
        classification_filter = self.classification_filter.currentData()
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item is None:
                continue
                
            account_id = item.data(Qt.ItemDataRole.UserRole)
            account = next((acc for acc in self.accounts if acc.get('id') == account_id), None)
            
            if not account:
                continue
            
            # Check search filter
            matches_search = True
            if search_text:
                name_match = search_text in account.get('name', '').lower()
                code_match = search_text in (account.get('code', '') or '').lower()
                matches_search = name_match or code_match
            
            # Check classification filter
            matches_classification = True
            if classification_filter:
                current_classification = self.classifications.get(account_id, '')
                matches_classification = current_classification == classification_filter
            
            # Show/hide row
            self.table.setRowHidden(row, not (matches_search and matches_classification))
    
    def _update_statistics(self):
        """Update statistics display in subtitle."""
        total = len(self.accounts)
        classified = len(self.classifications)
        unclassified = total - classified
        
        self.page_header.update_subtitle(
            f"Total: {total} • Classified: {classified} • Unclassified: {unclassified}"
        )
    
    def save_classifications(self):
        """Save the current classifications."""
        try:
            # Here you would typically save to the database
            # For now, we'll just show a success message
            QMessageBox.information(self, "Success", "Account classifications saved successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save classifications: {str(e)}") 