"""
Clean Bulk Entry Page
Refactored to use shared styles and eliminate code duplication
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFrame, QDateEdit, QMessageBox, 
    QScrollArea, QSizePolicy, QFileDialog, QDialog
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from datetime import datetime
import csv
import pandas as pd
import os
from ...core.utils import parse_transaction
from ..components.widgets import PageHeader, EditableAccountComboBox
from ..components.card_based_entry import CardBasedTransactionEntry
from ..components.shared_styles import get_field_style, get_button_style, load_accounts_from_system, populate_account_combo
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..common import ResponsiveHelper


class BulkEntryPage(QWidget):
    """Clean bulk entry page."""
    
    entries_saved = pyqtSignal()
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.entry_cards = []
        self.next_card_number = 1
        self._setup_ui()
        self._apply_styling()
        self._add_initial_cards()
        
    def _apply_styling(self):
        """Apply modern glassmorphism styling."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the main UI."""
        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 16, 0, 16)
        page_layout.setSpacing(16)
        
        # Toolbar
        toolbar_section = self._create_toolbar()
        page_layout.addWidget(toolbar_section)
        
        # Cards container
        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch(1)
        
        # Scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea, QWidget#scrollAreaWidgetContents {
                background: transparent;
                border: none;
            }
            QWidget { background: transparent; }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0;
            }
        """)
        
        scroll_area.setWidget(self.cards_widget)
        page_layout.addWidget(scroll_area, 1)
        
    def _create_toolbar(self):
        """Create the toolbar section."""
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.06);
                border: 1px solid rgba(255, 255, 255, 0.12);
                border-radius: 12px;
                margin-bottom: 8px;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(20, 16, 20, 16)
        toolbar_layout.setSpacing(12)
        
        # Title
        title_label = QLabel("Bulk Entry")
        title_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.9);
            font-size: 18px;
            font-weight: 600;
            background: transparent;
            border: none;
        """)
        
        # Summary
        self.summary_label = QLabel("0 entries, $0.00 total")
        self.summary_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
            font-weight: 400;
            background: transparent;
            border: none;
        """)
        
        # Buttons
        add_btn = QPushButton("➕ Add Entry")
        add_btn.setStyleSheet(get_button_style())
        add_btn.clicked.connect(self._add_new_card)
        
        import_btn = QPushButton("📁 Import CSV/Excel")
        import_btn.setStyleSheet(get_button_style())
        import_btn.clicked.connect(self._import_file)
        
        save_all_btn = QPushButton("💾 Save All")
        save_all_btn.setStyleSheet(get_button_style(primary=True))
        save_all_btn.clicked.connect(self._save_all_entries)
        
        clear_all_btn = QPushButton("🗑️ Clear All")
        clear_all_btn.setStyleSheet(get_button_style(secondary=True))
        clear_all_btn.clicked.connect(self._clear_all_entries)
        
        toolbar_layout.addWidget(title_label)
        toolbar_layout.addWidget(self.summary_label)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(add_btn)
        toolbar_layout.addWidget(import_btn)
        toolbar_layout.addWidget(save_all_btn)
        toolbar_layout.addWidget(clear_all_btn)
        
        return toolbar_frame
    
    def _add_initial_cards(self):
        """Add initial empty cards."""
        for _ in range(3):
            self._add_new_card()
        QTimer.singleShot(100, self._update_summary)
            
    def _add_new_card(self):
        """Add a new entry card."""
        card = CardBasedTransactionEntry(self.system, self.next_card_number)
        card.remove_requested.connect(self._remove_card)
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Connect to validation changes
        card.desc_edit.textChanged.connect(self._check_auto_add_card)
        card.debit_combo.currentTextChanged.connect(self._check_auto_add_card)
        card.credit_combo.currentTextChanged.connect(self._check_auto_add_card)
        card.amount_edit.textChanged.connect(self._check_auto_add_card)
        
        self.cards_layout.insertWidget(len(self.entry_cards), card)
        self.entry_cards.append(card)
        self.next_card_number += 1
        
    def _check_auto_add_card(self):
        """Auto-add a new card if the last one has data."""
        if self.entry_cards:
            last_card = self.entry_cards[-1]
            if last_card._has_any_data():
                all_have_data = all(card._has_any_data() for card in self.entry_cards)
                if all_have_data:
                    self._add_new_card()
        self._update_summary()
        
    def _update_summary(self):
        """Update the summary display."""
        valid_entries = [card for card in self.entry_cards if card.is_valid()]
        total_amount = 0.0
        
        for card in valid_entries:
            try:
                amount_text = card.amount_edit.text().strip()
                if amount_text:
                    total_amount += float(amount_text)
            except ValueError:
                pass
        
        count = len(valid_entries)
        self.summary_label.setText(f"{count} entries, ${total_amount:,.2f} total")
        
    def _remove_card(self, card):
        """Remove an entry card."""
        if len(self.entry_cards) > 1:
            self.cards_layout.removeWidget(card)
            self.entry_cards.remove(card)
            card.deleteLater()
            self._renumber_cards()
            self._update_summary()
        else:
            QMessageBox.information(self, "Cannot Remove", "At least one entry card must remain.")
            
    def _renumber_cards(self):
        """Renumber all cards after removal."""
        for i, card in enumerate(self.entry_cards):
            card.card_number = i + 1
            
    def _save_all_entries(self):
        """Save all valid entries."""
        valid_entries = []
        invalid_cards = []
        
        for i, card in enumerate(self.entry_cards):
            if card.is_valid():
                valid_entries.append(card.get_entry_data())
            elif card._has_any_data():
                invalid_cards.append(i + 1)
        
        if invalid_cards:
            invalid_count = len(invalid_cards)
            card_list = ", ".join(map(str, invalid_cards[:5]))
            if len(invalid_cards) > 5:
                card_list += f", and {len(invalid_cards) - 5} more"
            
            QMessageBox.warning(
                self, 
                "Invalid Entries Detected", 
                f"Cannot save: {invalid_count} entry card(s) have invalid or missing account information.\n\n"
                f"Please check cards: {card_list}\n\n"
                "⚠ Account fields with red borders contain invalid accounts.\n"
                "⚠ Account fields with orange borders are required but empty."
            )
            return
        
        if not valid_entries:
            QMessageBox.warning(self, "No Valid Entries", "Please fill out at least one complete entry.")
            return
        
        try:
            for entry in valid_entries:
                if hasattr(self.system, 'add_journal_entry'):
                    self.system.add_journal_entry(
                        entry['date'],
                        entry['description'],
                        entry['debit_account'],
                        entry['credit_account'],
                        entry['amount']
                    )
            
            QMessageBox.information(self, "Success", f"Successfully saved {len(valid_entries)} entries!")
            self._clear_all_entries()
            self.entries_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save entries: {e}")
    
    def _clear_all_entries(self):
        """Clear all entry cards."""
        for card in self.entry_cards:
            card.clear_entry()
        self._update_summary()
    
    def _import_file(self):
        """Import entries from CSV/Excel file."""
        try:
            from ..components.enhanced_csv_import import EnhancedCSVImportDialog
            
            import_dialog = EnhancedCSVImportDialog(self.system, self)
            
            if import_dialog.exec() == QDialog.DialogCode.Accepted:
                import_data = import_dialog.get_import_data()
                summary = import_dialog.get_import_summary()
                
                if not import_data:
                    QMessageBox.warning(self, "No Data", "No valid transactions found to import.")
                    return
                
                self._clear_all_entries()
                
                while len(self.entry_cards) < len(import_data):
                    self._add_new_card()
                
                for i, entry_data in enumerate(import_data):
                    if i < len(self.entry_cards):
                        card = self.entry_cards[i]
                        card.set_entry_data(entry_data)
                
                total = summary['total_processed']
                skipped = summary['skipped_rows']
                mappings = summary['mappings_used']
                
                summary_msg = f"""
                <h3>Import Completed Successfully!</h3>
                <p><b>Transactions Imported:</b> {total}</p>
                <p><b>Rows Skipped:</b> {skipped}</p>
                <p><b>Account Mappings Applied:</b> {mappings}</p>
                """
                
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle("Import Summary")
                msg_box.setTextFormat(Qt.TextFormat.RichText)
                msg_box.setText(summary_msg)
                msg_box.setIcon(QMessageBox.Icon.Information)
                msg_box.exec()
                
                self._update_summary()
                
        except ImportError:
            self._simple_import_file()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import file: {e}")
    
    def _simple_import_file(self):
        """Simple CSV/Excel import fallback."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Transactions", "", 
            "Excel files (*.xlsx *.xls);;CSV files (*.csv);;All files (*.*)"
        )
        
        if file_path:
            try:
                if file_path.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_path)
                else:
                    df = pd.read_csv(file_path)
                
                self._clear_all_entries()
                
                while len(self.entry_cards) < len(df):
                    self._add_new_card()
                
                for i, row in df.iterrows():
                    if i < len(self.entry_cards):
                        card = self.entry_cards[i]
                        card.set_entry_data({
                            'date': str(row.get('Date', '')),
                            'description': str(row.get('Description', '')),
                            'debit_account': str(row.get('Debit Account', '')),
                            'credit_account': str(row.get('Credit Account', '')),
                            'amount': str(row.get('Amount', ''))
                        })
                
                QMessageBox.information(self, "Import Successful", f"Imported {len(df)} entries from file.")
                self._update_summary()
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import file: {e}")
    
    def refresh_accounts_from_system(self):
        """Reload accounts from the system and refresh all entry cards."""
        try:
            new_accounts = load_accounts_from_system(self.system)
            for card in self.entry_cards:
                card.refresh_accounts(new_accounts)
        except Exception as e:
            print(f"Error refreshing accounts: {e}")
