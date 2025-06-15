"""
Dedicated Bulk Entry Page
A full-screen interface for bulk journal entry operations
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QComboBox, QFrame, QDateEdit, QMessageBox, 
    QScrollArea, QSpacerItem, QSizePolicy, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QFileDialog, QDialog, QProgressDialog, QGridLayout,
    QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor
from datetime import datetime
import csv
import pandas as pd
import os
from ...core.utils import parse_transaction
from ..components.widgets import PageHeader, NonScrollableComboBox
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..common import ResponsiveHelper


class BulkEntryTable(QTableWidget):
    """A spreadsheet-style table for bulk journal entries."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.row_count = 10  # Start with more rows in dedicated page
        self._setup_table()
        self._populate_empty_rows()
        
    def _setup_table(self):
        """Setup the table structure and styling."""
        # Set up columns
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Date", "Description", "Debit Account", "Credit Account", "Amount"])
        
        # Table settings
        self.setRowCount(self.row_count)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setGridStyle(Qt.PenStyle.SolidLine)
        
        # Remove height constraints - let it grow naturally in dedicated page
        self.setMinimumWidth(900)  # More space in dedicated page
        
        # Set row height for comfortable editing
        self.verticalHeader().setDefaultSectionSize(55)
        
        # Disable table's own scrollbars since we use a scroll area container
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Column widths - more generous in dedicated page
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Date
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Description
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)  # Debit
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Credit
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Amount
        
        self.setColumnWidth(0, 120)  # Date
        self.setColumnWidth(2, 200)  # Debit Account
        self.setColumnWidth(3, 200)  # Credit Account
        self.setColumnWidth(4, 150)  # Amount
        
        # Styling
        self.setStyleSheet("""
            QTableWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                gridline-color: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 14px;
            }
            QTableWidget::item {
                padding: 12px;
                border: none;
                background: transparent;
            }
            QTableWidget::item:selected {
                background: rgba(0, 120, 215, 0.3);
            }
            QTableWidget::item:hover {
                background: rgba(255, 255, 255, 0.08);
            }
            QHeaderView::section {
                background: rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.9);
                padding: 12px;
                border: none;
                border-bottom: 2px solid rgba(255, 255, 255, 0.2);
                font-weight: 600;
                font-size: 13px;
            }
        """)
        
    def _populate_empty_rows(self):
        """Populate the table with empty rows and appropriate widgets."""
        from PyQt6.QtCore import QDate
        
        for row in range(self.row_count):
            # Date column - QDateEdit
            date_edit = QDateEdit()
            date_edit.setDate(QDate.currentDate())
            date_edit.setCalendarPopup(True)
            date_edit.setMinimumHeight(35)
            date_edit.setStyleSheet(self._get_cell_widget_style())
            self.setCellWidget(row, 0, date_edit)
            
            # Description column - QLineEdit
            desc_edit = QLineEdit()
            desc_edit.setPlaceholderText("Transaction description...")
            desc_edit.setMinimumHeight(35)
            desc_edit.setStyleSheet(self._get_cell_widget_style())
            self.setCellWidget(row, 1, desc_edit)
              # Debit Account column - NonScrollableComboBox
            debit_combo = NonScrollableComboBox()
            debit_combo.setEditable(True)
            debit_combo.setPlaceholderText("Select debit account...")
            debit_combo.setMinimumHeight(35)
            debit_combo.setStyleSheet(self._get_combo_cell_style())
            self._populate_account_combo(debit_combo)
            self.setCellWidget(row, 2, debit_combo)
              # Credit Account column - NonScrollableComboBox
            credit_combo = NonScrollableComboBox()
            credit_combo.setEditable(True)
            credit_combo.setPlaceholderText("Select credit account...")
            credit_combo.setMinimumHeight(35)
            credit_combo.setStyleSheet(self._get_combo_cell_style())
            self._populate_account_combo(credit_combo)
            self.setCellWidget(row, 3, credit_combo)
            
            # Amount column - QLineEdit
            amount_edit = QLineEdit()
            amount_edit.setPlaceholderText("0.00")
            amount_edit.setMinimumHeight(35)
            amount_edit.setStyleSheet(self._get_cell_widget_style())
            amount_edit.textChanged.connect(self._validate_amounts)
            self.setCellWidget(row, 4, amount_edit)
    
    def _populate_account_combo(self, combo):
        """Populate account combo box with available accounts."""
        try:
            accounts = self.system.get_postable_accounts()
            combo.clear()
            combo.addItem("", "")  # Empty option
            for account in accounts:
                combo.addItem(account[0], account[0])  # account name
        except Exception as e:
            print(f"Error populating accounts: {e}")
    
    def _get_cell_widget_style(self):
        """Get styling for cell widgets."""
        return """
            QLineEdit, QDateEdit {
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                padding: 10px 12px;
                color: white;
                font-size: 14px;
                min-height: 25px;
            }
            QLineEdit:focus, QDateEdit:focus {
                border-color: rgba(0, 120, 215, 0.6);
                background: rgba(255, 255, 255, 0.05);
            }
            QDateEdit::drop-down {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
                width: 20px;
            }
        """
    
    def _get_combo_cell_style(self):
        """Get styling for combo box cells."""
        return """
            QComboBox {
                background: transparent;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                padding: 10px 12px;
                color: white;
                font-size: 14px;
                min-height: 25px;
            }
            QComboBox:focus {
                border-color: rgba(0, 120, 215, 0.6);
                background: rgba(255, 255, 255, 0.05);
            }
            QComboBox::drop-down {
                border: none;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
            }
            QComboBox QAbstractItemView {
                background: rgba(32, 32, 32, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                color: white;
                selection-background-color: rgba(0, 120, 215, 0.3);
            }
        """
    
    def _validate_amounts(self):
        """Validate amount entries in real-time."""
        # Implementation for real-time validation
        pass
    
    def add_row(self):
        """Add a new empty row to the table."""
        current_rows = self.rowCount()
        self.setRowCount(current_rows + 1)
        self.row_count = current_rows + 1
        
        # Populate the new row
        row = current_rows
        from PyQt6.QtCore import QDate
        
        # Add widgets to the new row
        date_edit = QDateEdit()
        date_edit.setDate(QDate.currentDate())
        date_edit.setCalendarPopup(True)
        date_edit.setMinimumHeight(35)
        date_edit.setStyleSheet(self._get_cell_widget_style())
        self.setCellWidget(row, 0, date_edit)
        
        desc_edit = QLineEdit()
        desc_edit.setPlaceholderText("Transaction description...")
        desc_edit.setMinimumHeight(35)
        desc_edit.setStyleSheet(self._get_cell_widget_style())
        self.setCellWidget(row, 1, desc_edit)
        
        debit_combo = NonScrollableComboBox()
        debit_combo.setEditable(True)
        debit_combo.setPlaceholderText("Select debit account...")
        debit_combo.setMinimumHeight(35)
        debit_combo.setStyleSheet(self._get_combo_cell_style())
        self._populate_account_combo(debit_combo)
        self.setCellWidget(row, 2, debit_combo)
        
        credit_combo = NonScrollableComboBox()
        credit_combo.setEditable(True)
        credit_combo.setPlaceholderText("Select credit account...")
        credit_combo.setMinimumHeight(35)
        credit_combo.setStyleSheet(self._get_combo_cell_style())
        self._populate_account_combo(credit_combo)
        self.setCellWidget(row, 3, credit_combo)
        
        amount_edit = QLineEdit()
        amount_edit.setPlaceholderText("0.00")
        amount_edit.setMinimumHeight(35)
        amount_edit.setStyleSheet(self._get_cell_widget_style())
        amount_edit.textChanged.connect(self._validate_amounts)
        self.setCellWidget(row, 4, amount_edit)
        
        # Scroll to the new row
        self.setCurrentCell(row, 1)  # Focus on description field
    
    def remove_selected_row(self):
        """Remove the currently selected row."""
        current_row = self.currentRow()
        if current_row >= 0 and self.rowCount() > 1:
            self.removeRow(current_row)
            self.row_count = self.rowCount()
    
    def clear_all_entries(self):
        """Clear all entries in the table."""
        from PyQt6.QtCore import QDate
        for row in range(self.rowCount()):
            # Clear each widget
            date_widget = self.cellWidget(row, 0)
            desc_widget = self.cellWidget(row, 1)
            debit_widget = self.cellWidget(row, 2)
            credit_widget = self.cellWidget(row, 3)
            amount_widget = self.cellWidget(row, 4)
            
            if date_widget:
                date_widget.setDate(QDate.currentDate())
            if desc_widget:
                desc_widget.clear()
            if debit_widget:
                debit_widget.setCurrentIndex(0)
            if credit_widget:
                credit_widget.setCurrentIndex(0)
            if amount_widget:
                amount_widget.clear()
        
        # Focus on first row
        self.setCurrentCell(0, 1)
    
    def get_entries_data(self):
        """Extract all entries from the table."""
        entries = []
        for row in range(self.rowCount()):
            # Get data from each widget
            date_widget = self.cellWidget(row, 0)
            desc_widget = self.cellWidget(row, 1)
            debit_widget = self.cellWidget(row, 2)
            credit_widget = self.cellWidget(row, 3)
            amount_widget = self.cellWidget(row, 4)
            
            if (date_widget and desc_widget and debit_widget and 
                credit_widget and amount_widget):
                
                # Check if row has data
                desc_text = desc_widget.text().strip()
                debit_text = debit_widget.currentText().strip()
                credit_text = credit_widget.currentText().strip()
                amount_text = amount_widget.text().strip()
                
                if desc_text and debit_text and credit_text and amount_text:
                    try:
                        entry = {
                            'date': date_widget.date().toString("yyyy-MM-dd"),
                            'description': desc_text,
                            'debit_account': debit_text,
                            'credit_account': credit_text,
                            'amount': float(amount_text)
                        }
                        entries.append(entry)
                    except ValueError:
                        # Skip invalid amount entries
                        continue
        
        return entries


class BulkEntryPage(QWidget):
    """Dedicated page for bulk journal entries."""
    
    # Signal emitted when entries are saved
    entries_saved = pyqtSignal()
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self._setup_ui()
        self._apply_styling()
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the main UI."""
        # Main layout for the page
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.setSpacing(0)
        
        # Create scroll area for the main content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical, QScrollBar:horizontal {
                background: rgba(255, 255, 255, 0.1);
                width: 10px;
                height: 10px;
                border-radius: 5px;
                margin: 0;
            }
            QScrollBar::handle:vertical, QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 5px;
                min-height: 20px;
                min-width: 20px;
            }
            QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                height: 0px;
                width: 0px;
            }
        """)
        
        # Content widget
        content_widget = QWidget()
        main_layout = QVBoxLayout(content_widget)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(24, 18, 32))
        
        # Page header
        header = PageHeader("Bulk Journal Entries", "Add multiple transactions efficiently")
        main_layout.addWidget(header)
        
        # Create toolbar
        self._create_toolbar(main_layout)
        
        # Create table container
        self._create_table_container(main_layout)
        
        # Create validation panel
        self._create_validation_panel(main_layout)
        
        # Create action buttons
        self._create_action_buttons(main_layout)
        
        scroll_area.setWidget(content_widget)
        page_layout.addWidget(scroll_area)
    
    def _create_toolbar(self, layout):
        """Create the toolbar with table operations."""
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)
        toolbar_layout.setSpacing(12)
        
        # Add row button
        add_row_btn = QPushButton("➕ Add Row")
        add_row_btn.setStyleSheet(self._get_toolbar_button_style())
        add_row_btn.clicked.connect(self._add_row)
        
        # Remove row button
        remove_row_btn = QPushButton("➖ Remove Row")
        remove_row_btn.setStyleSheet(self._get_toolbar_button_style())
        remove_row_btn.clicked.connect(self._remove_row)
          # Add 10 rows button
        add_10_rows_btn = QPushButton("📄 Add 10 Rows")
        add_10_rows_btn.setStyleSheet(self._get_toolbar_button_style())
        add_10_rows_btn.clicked.connect(self._add_10_rows)
        
        # Import CSV button
        import_csv_btn = QPushButton("📂 Import CSV/Excel")
        import_csv_btn.setStyleSheet(self._get_toolbar_button_style("#3498db"))
        import_csv_btn.clicked.connect(self._open_import_wizard)
        
        # Clear all button
        clear_btn = QPushButton("🗑️ Clear All")
        clear_btn.setStyleSheet(self._get_toolbar_button_style())
        clear_btn.clicked.connect(self._clear_all)
        
        toolbar_layout.addWidget(add_row_btn)
        toolbar_layout.addWidget(remove_row_btn)
        toolbar_layout.addWidget(add_10_rows_btn)
        toolbar_layout.addWidget(import_csv_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(clear_btn)
        
        layout.addWidget(toolbar_frame)
    
    def _create_table_container(self, layout):
        """Create the table container."""
        # Create the bulk entry table
        self.bulk_table = BulkEntryTable(self.system)
        
        # Table container with scroll
        table_container = QFrame()
        table_container.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 8px;
            }
        """)
        
        container_layout = QVBoxLayout(table_container)
        container_layout.setContentsMargins(16, 16, 16, 16)
        
        # Table scroll area
        table_scroll = QScrollArea()
        table_scroll.setWidgetResizable(True)
        table_scroll.setMinimumHeight(400)
        table_scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
        """)
        
        table_scroll.setWidget(self.bulk_table)
        container_layout.addWidget(table_scroll)
        
        layout.addWidget(table_container)
    
    def _create_validation_panel(self, layout):
        """Create validation panel for real-time feedback."""
        self.validation_panel = QFrame()
        self.validation_panel.setStyleSheet("""
            QFrame {
                background: rgba(255, 193, 7, 0.1);
                border: 1px solid rgba(255, 193, 7, 0.3);
                border-radius: 8px;
            }
        """)
        self.validation_panel.setVisible(False)  # Hidden by default
        
        validation_layout = QHBoxLayout(self.validation_panel)
        validation_layout.setContentsMargins(16, 12, 16, 12)
        
        self.validation_label = QLabel("⚠️ Validation messages will appear here")
        self.validation_label.setStyleSheet("""
            color: rgba(255, 193, 7, 0.9);
            font-size: 14px;
            font-weight: 500;
        """)
        
        validation_layout.addWidget(self.validation_label)
        validation_layout.addStretch()
        
        layout.addWidget(self.validation_panel)
    
    def _create_action_buttons(self, layout):
        """Create action buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        # Save all button
        save_btn = QPushButton("💾 Save All Entries")
        save_btn.setStyleSheet(self._get_action_button_style("primary"))
        save_btn.clicked.connect(self._save_entries)        # Cancel/Close button  
        close_btn = QPushButton("❌ Close")
        close_btn.setStyleSheet(self._get_action_button_style("secondary"))
        close_btn.clicked.connect(self.close)
        
        button_layout.addStretch()
        button_layout.addWidget(save_btn)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _get_toolbar_button_style(self, color=None):
        """Get styling for toolbar buttons."""
        if color:
            # Convert hex color to rgba for background
            if color == "#3498db":
                bg_color = "rgba(52, 152, 219, 0.8)"
                hover_color = "rgba(52, 152, 219, 0.9)"
                pressed_color = "rgba(52, 152, 219, 0.7)"
            else:
                bg_color = "rgba(255, 255, 255, 0.1)"
                hover_color = "rgba(255, 255, 255, 0.15)"
                pressed_color = "rgba(255, 255, 255, 0.08)"
        else:
            bg_color = "rgba(255, 255, 255, 0.1)"
            hover_color = "rgba(255, 255, 255, 0.15)"
            pressed_color = "rgba(255, 255, 255, 0.08)"
            
        return f"""
            QPushButton {{
                background: {bg_color};
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: 13px;
                font-weight: 500;
                padding: 8px 16px;
                min-width: 100px;
            }}
            QPushButton:hover {{
                background: {hover_color};
                border-color: rgba(255, 255, 255, 0.3);
            }}
            QPushButton:pressed {{
                background: {pressed_color};
            }}
        """
    
    def _get_action_button_style(self, button_type="primary"):
        """Get styling for action buttons."""
        if button_type == "primary":
            return """
                QPushButton {
                    background: rgba(0, 120, 215, 0.8);
                    border: 1px solid rgba(0, 120, 215, 0.8);
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: 600;
                    padding: 12px 24px;
                    min-width: 150px;
                }
                QPushButton:hover {
                    background: rgba(0, 120, 215, 0.9);
                }
                QPushButton:pressed {
                    background: rgba(0, 120, 215, 0.7);
                }
            """
        else:
            return """
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 8px;
                    color: white;
                    font-size: 14px;
                    font-weight: 500;
                    padding: 12px 24px;
                    min-width: 120px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.15);
                }
                QPushButton:pressed {
                    background: rgba(255, 255, 255, 0.08);
                }
            """
    
    def _add_row(self):
        """Add a single row."""
        self.bulk_table.add_row()
    
    def _remove_row(self):
        """Remove selected row."""
        self.bulk_table.remove_selected_row()
    
    def _add_10_rows(self):
        """Add 10 rows at once."""
        for _ in range(10):
            self.bulk_table.add_row()
    
    def _clear_all(self):
        """Clear all entries after confirmation."""
        reply = QMessageBox.question(
            self,
            "Clear All Entries",
            "Are you sure you want to clear all entries? This action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.bulk_table.clear_all_entries()
    
    def _save_entries(self):
        """Save all entries to the system."""
        entries = self.bulk_table.get_entries_data()
        
        if not entries:
            QMessageBox.warning(self, "No Entries", "Please add some entries before saving.")
            return
        
        # Validate entries
        validation_errors = []
        for i, entry in enumerate(entries, 1):
            if entry['debit_account'] == entry['credit_account']:
                validation_errors.append(f"Row {i}: Debit and credit accounts cannot be the same")
            if entry['amount'] <= 0:
                validation_errors.append(f"Row {i}: Amount must be greater than zero")
        
        if validation_errors:
            error_msg = "Validation errors found:\n\n" + "\n".join(validation_errors)
            QMessageBox.warning(self, "Validation Errors", error_msg)
            return
        
        # Save entries
        try:
            saved_count = 0
            for entry in entries:
                # Save each entry to the system
                self.system.add_journal_entry(
                    entry['date'],
                    entry['description'],
                    entry['debit_account'],
                    entry['credit_account'],
                    entry['amount']
                )
                saved_count += 1
            
            QMessageBox.information(
                self,
                "Success",
                f"Successfully saved {saved_count} journal entries!"
            )
            
            # Emit signal to refresh parent
            self.entries_saved.emit()
            
            # Clear the table
            self.bulk_table.clear_all_entries()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save entries: {str(e)}")
    
    def _open_import_wizard(self):
        """Open the CSV/Excel import wizard."""
        wizard = ImportWizardDialog(self.system, self)
        if wizard.exec() == QDialog.DialogCode.Accepted:
            imported_data = wizard.get_imported_data()
            if imported_data:
                self._populate_table_with_imported_data(imported_data)
    
    def _populate_table_with_imported_data(self, data):
        """Populate the table with imported CSV/Excel data."""
        # Clear existing data first
        reply = QMessageBox.question(
            self,
            "Import Data",
            f"This will import {len(data)} entries. Clear existing entries first?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Yes
        )
        
        if reply == QMessageBox.StandardButton.Cancel:
            return
        elif reply == QMessageBox.StandardButton.Yes:
            self.bulk_table.clear_all_entries()
        
        # Add enough rows for the imported data
        current_rows = self.bulk_table.rowCount()
        needed_rows = len(data)
        
        if needed_rows > current_rows:
            for _ in range(needed_rows - current_rows):
                self.bulk_table.add_row()
        
        # Populate the data
        for i, entry in enumerate(data):
            if i < self.bulk_table.rowCount():
                # Set date
                date_widget = self.bulk_table.cellWidget(i, 0)
                if date_widget and 'date' in entry:
                    try:
                        from PyQt6.QtCore import QDate
                        date_obj = QDate.fromString(entry['date'], "yyyy-MM-dd")
                        if date_obj.isValid():
                            date_widget.setDate(date_obj)
                    except:
                        pass
                
                # Set description
                desc_widget = self.bulk_table.cellWidget(i, 1)
                if desc_widget and 'description' in entry:
                    desc_widget.setText(entry['description'])
                
                # Set debit account
                debit_widget = self.bulk_table.cellWidget(i, 2)
                if debit_widget and 'debit_account' in entry:
                    debit_widget.setCurrentText(entry['debit_account'])
                
                # Set credit account
                credit_widget = self.bulk_table.cellWidget(i, 3)
                if credit_widget and 'credit_account' in entry:
                    credit_widget.setCurrentText(entry['credit_account'])
                
                # Set amount
                amount_widget = self.bulk_table.cellWidget(i, 4)
                if amount_widget and 'amount' in entry:
                    amount_widget.setText(str(entry['amount']))
        
        QMessageBox.information(self, "Import Complete", f"Successfully imported {len(data)} entries!")

class ImportWizardDialog(QDialog):
    """Dialog for importing CSV/Excel files with column mapping."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.imported_data = []
        self.raw_data = []
        self.column_mapping = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the wizard UI."""
        self.setWindowTitle("Import CSV/Excel File")
        self.setModal(True)
        self.resize(800, 600)
        
        # Apply styling
        self.setStyleSheet("""
            QDialog {
                background: rgba(32, 32, 32, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 12px;
            }
            QLabel {
                color: white;
                font-size: 14px;
            }
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 8px;
                color: white;
                min-height: 20px;
            }
            QTableWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                gridline-color: rgba(255, 255, 255, 0.1);
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Import Journal Entries from CSV/Excel")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # File selection
        file_layout = QHBoxLayout()
        file_label = QLabel("File:")
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        
        browse_btn = QPushButton("Browse...")
        browse_btn.setStyleSheet(self._get_button_style())
        browse_btn.clicked.connect(self._browse_file)
        
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_label, 1)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)
        
        # Column mapping section
        mapping_label = QLabel("Column Mapping:")
        mapping_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(mapping_label)
        
        self.mapping_frame = QFrame()
        self.mapping_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 10px;
            }
        """)
        self.mapping_layout = QGridLayout(self.mapping_frame)
        layout.addWidget(self.mapping_frame)
        
        # Preview section
        preview_label = QLabel("Preview:")
        preview_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(preview_label)
        
        self.preview_table = QTableWidget()
        self.preview_table.setMaximumHeight(200)
        layout.addWidget(self.preview_table)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(self._get_button_style("secondary"))
        cancel_btn.clicked.connect(self.reject)
        
        self.import_btn = QPushButton("Import")
        self.import_btn.setStyleSheet(self._get_button_style("primary"))
        self.import_btn.clicked.connect(self._import_data)
        self.import_btn.setEnabled(False)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(self.import_btn)
        layout.addLayout(button_layout)
        
    def _get_button_style(self, button_type="normal"):
        """Get button styling."""
        if button_type == "primary":
            return """
                QPushButton {
                    background: rgba(0, 120, 215, 0.8);
                    border: 1px solid rgba(0, 120, 215, 0.8);
                    border-radius: 6px;
                    color: white;
                    font-weight: 600;
                    padding: 10px 20px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: rgba(0, 120, 215, 0.9);
                }
                QPushButton:disabled {
                    background: rgba(255, 255, 255, 0.1);
                    color: rgba(255, 255, 255, 0.5);
                }
            """
        elif button_type == "secondary":
            return """
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: white;
                    padding: 10px 20px;
                    min-width: 80px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.15);
                }
            """
        else:
            return """
                QPushButton {
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: white;
                    padding: 8px 16px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.15);
                }
            """
    
    def _browse_file(self):
        """Browse for CSV/Excel file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV/Excel File",
            "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self.file_path_label.setText(os.path.basename(file_path))
            self._load_file(file_path)
    
    def _load_file(self, file_path):
        """Load and parse the selected file."""
        try:
            if file_path.lower().endswith('.csv'):
                # Load CSV
                df = pd.read_csv(file_path)
            else:
                # Load Excel
                df = pd.read_excel(file_path)
            
            # Convert to list of dictionaries
            self.raw_data = df.to_dict('records')
            
            # Setup column mapping
            self._setup_column_mapping(df.columns.tolist())
            
            # Update preview
            self._update_preview()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
    
    def _setup_column_mapping(self, columns):
        """Setup column mapping interface."""
        # Clear existing mapping
        for i in reversed(range(self.mapping_layout.count())): 
            self.mapping_layout.itemAt(i).widget().setParent(None)
        
        # Required fields
        required_fields = ["Date", "Description", "Debit Account", "Credit Account", "Amount"]
        
        for i, field in enumerate(required_fields):
            label = QLabel(f"{field}:")
            combo = QComboBox()
            combo.addItem("-- Select Column --", "")
            
            # Add file columns
            for col in columns:
                combo.addItem(col, col)
            
            # Auto-map if possible
            auto_mapped = self._auto_map_column(field, columns)
            if auto_mapped:
                combo.setCurrentText(auto_mapped)
            
            combo.currentTextChanged.connect(self._on_mapping_changed)
            
            self.mapping_layout.addWidget(label, i, 0)
            self.mapping_layout.addWidget(combo, i, 1)
    
    def _auto_map_column(self, field, columns):
        """Automatically map columns based on common names."""
        field_lower = field.lower()
        
        # Common mappings
        mappings = {
            "date": ["date", "transaction_date", "entry_date", "txn_date"],
            "description": ["description", "desc", "memo", "details", "narrative"],
            "debit account": ["debit", "debit_account", "dr_account", "debit account"],
            "credit account": ["credit", "credit_account", "cr_account", "credit account"],
            "amount": ["amount", "value", "sum", "total", "debit_amount", "credit_amount"]
        }
        
        if field_lower in mappings:
            for col in columns:
                if col.lower() in mappings[field_lower]:
                    return col
        
        return None
    
    def _on_mapping_changed(self):
        """Handle mapping change."""
        self._update_preview()
    
    def _update_preview(self):
        """Update the preview table."""
        if not self.raw_data:
            return
        
        # Get current mapping
        mapping = self._get_current_mapping()
        
        # Show first 5 rows in preview
        preview_data = self.raw_data[:5]
        
        if not mapping or not any(mapping.values()):
            self.preview_table.setRowCount(0)
            self.preview_table.setColumnCount(0)
            self.import_btn.setEnabled(False)
            return
        
        # Setup preview table
        headers = ["Date", "Description", "Debit Account", "Credit Account", "Amount"]
        self.preview_table.setColumnCount(len(headers))
        self.preview_table.setHorizontalHeaderLabels(headers)
        self.preview_table.setRowCount(len(preview_data))
        
        # Populate preview
        for row, data_row in enumerate(preview_data):
            for col, header in enumerate(headers):
                field_key = header.lower()
                if field_key in mapping and mapping[field_key]:
                    value = str(data_row.get(mapping[field_key], ""))
                    item = QTableWidgetItem(value)
                    self.preview_table.setItem(row, col, item)
        
        # Check if all required fields are mapped
        all_mapped = all(mapping.values())
        self.import_btn.setEnabled(all_mapped)
    
    def _get_current_mapping(self):
        """Get current column mapping."""
        mapping = {}
        field_names = ["date", "description", "debit account", "credit account", "amount"]
        
        for i, field in enumerate(field_names):
            combo = self.mapping_layout.itemAtPosition(i, 1).widget()
            if combo and combo.currentData():
                mapping[field] = combo.currentData()
        
        return mapping
    
    def _import_data(self):
        """Import the data with current mapping."""
        mapping = self._get_current_mapping()
        
        if not mapping or not all(mapping.values()):
            QMessageBox.warning(self, "Warning", "Please map all required columns.")
            return
        
        try:
            self.imported_data = []
            
            for row in self.raw_data:
                try:
                    # Parse date
                    date_str = str(row.get(mapping["date"], "")).strip()
                    if not date_str:
                        continue
                    
                    # Try to parse date in various formats
                    date_obj = self._parse_date(date_str)
                    if not date_obj:
                        continue
                    
                    # Parse amount
                    amount_str = str(row.get(mapping["amount"], "")).strip()
                    if not amount_str:
                        continue
                    
                    # Clean amount (remove currency symbols, commas, etc.)
                    import re
                    amount_clean = re.sub(r'[^\d.-]', '', amount_str)
                    amount = float(amount_clean)
                    
                    if amount <= 0:
                        continue
                    
                    entry = {
                        'date': date_obj,
                        'description': str(row.get(mapping["description"], "")).strip(),
                        'debit_account': str(row.get(mapping["debit account"], "")).strip(),
                        'credit_account': str(row.get(mapping["credit account"], "")).strip(),
                        'amount': amount
                    }
                    
                    # Validate entry
                    if (entry['description'] and entry['debit_account'] and 
                        entry['credit_account'] and entry['debit_account'] != entry['credit_account']):
                        self.imported_data.append(entry)
                        
                except (ValueError, AttributeError):
                    continue
            
            if self.imported_data:
                QMessageBox.information(
                    self, 
                    "Import Ready", 
                    f"Ready to import {len(self.imported_data)} valid entries out of {len(self.raw_data)} total rows."
                )
                self.accept()
            else:
                QMessageBox.warning(self, "No Data", "No valid entries found to import.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process data: {str(e)}")
    
    def _parse_date(self, date_str):
        """Parse date string in various formats."""
        from datetime import datetime
        
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%Y/%m/%d",
            "%m-%d-%Y",
            "%d-%m-%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%d %B %Y",
            "%d %b %Y"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
        
        return None
    
    def get_imported_data(self):
        """Get the imported data."""
        return self.imported_data
