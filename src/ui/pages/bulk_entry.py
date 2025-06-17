"""
Clean Bulk Entry Page
Refactored to use shared styles and eliminate code duplication
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QLineEdit, QFrame, QDateEdit, QMessageBox, 
    QScrollArea, QSizePolicy, QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
import pandas as pd
from ..components.widgets import PageHeader, EditableAccountComboBox
from ..components.card_based_entry import CardBasedTransactionEntry
from ..components.shared_styles import get_field_style, get_button_style, load_accounts_from_system, populate_account_combo
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.progress_dialog import CircularProgressDialog
from ..common import ResponsiveHelper


class BulkEntryPage(QWidget):
    """Clean bulk entry page."""
    
    # Constants for entry limits
    SOFT_LIMIT = 1000  # Show warning above this
    HARD_LIMIT = 5000  # Reject import above this
    entries_saved = pyqtSignal()
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.entry_cards = []
        self.next_card_number = 1
        
        # Load accounts once for all cards
        accounts_data = self.system.get_postable_accounts()
        self.formatted_accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data]
        
        self._setup_ui()
        self._add_new_card()  # Start with one empty card

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
        self.save_all_btn = save_all_btn  # Store reference for validation management
        
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
        # Trigger initial validation to set proper save button state
        QTimer.singleShot(200, self._update_validation_and_save_state)
            
    def _add_new_card(self):
        """Add a new entry card."""
        card = CardBasedTransactionEntry(self.system, self.next_card_number)
        card.remove_requested.connect(self._remove_card)
        card.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        
        # Use shared account list
        card.debit_combo.setAccountList(self.formatted_accounts)
        card.credit_combo.setAccountList(self.formatted_accounts)
        
        # Connect to validation changes
        card.desc_edit.textChanged.connect(self._check_auto_add_card)
        card.debit_combo.currentTextChanged.connect(self._check_auto_add_card)
        card.credit_combo.currentTextChanged.connect(self._check_auto_add_card)
        card.amount_edit.textChanged.connect(self._check_auto_add_card)
        
        # Connect validation styling updates for real-time feedback
        card.desc_edit.textChanged.connect(self._update_validation_and_save_state)
        card.debit_combo.currentTextChanged.connect(self._update_validation_and_save_state)
        card.credit_combo.currentTextChanged.connect(self._update_validation_and_save_state)
        card.amount_edit.textChanged.connect(self._update_validation_and_save_state)
        
        self.cards_layout.insertWidget(len(self.entry_cards), card)
        self.entry_cards.append(card)
        self.next_card_number += 1
        self._update_validation_and_save_state()
        
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
            # Update validation and save button state after card removal
            self._update_validation_and_save_state()
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
            # Create and show progress dialog
            progress = CircularProgressDialog(self)
            progress.set_progress(0, "Preparing to save entries...")
            progress.show()
            QApplication.processEvents()
            
            def progress_callback(current, total, entry):
                if progress.was_cancelled():
                    return False
                
                progress_value = int((current / total) * 100)
                progress.set_progress(
                    progress_value,
                    f"Saving entries... ({current}/{total})"
                )
                QApplication.processEvents()
                return True
            
            # Save entries one by one with progress
            success_count, failed_entries = self.system.add_journal_entries_with_progress(
                valid_entries,
                progress_callback
            )
            
            # Handle results
            if progress.was_cancelled():
                plural = "entry" if success_count == 1 else "entries"
                QMessageBox.information(
                    self,
                    "Save Cancelled",
                    f"Save operation cancelled. {success_count} {plural} were saved successfully before cancellation."
                )
            elif failed_entries:
                failed_msg = "\n".join(f"Entry {i+1}: {err}" for i, err in failed_entries[:5])
                if len(failed_entries) > 5:
                    failed_msg += f"\n... and {len(failed_entries) - 5} more errors"
                
                QMessageBox.warning(
                    self, 
                    "Partial Save Completed",
                    f"Saved {success_count} entries successfully, but {len(failed_entries)} entries failed:\n\n{failed_msg}"
                )
            else:
                plural = "entry" if success_count == 1 else "entries"
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully saved {success_count} {plural}!"
                )
            
            progress.close()
            
            if success_count > 0:
                self._clear_all_entries()
                self.entries_saved.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save entries: {e}")
    
    def _clear_all_entries(self):
        """Clear all entry cards."""
        for card in self.entry_cards:            card.clear_entry()
        self._update_summary()
        
    def _import_file(self):
        """Import entries from CSV/Excel file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Transactions", "", 
            "Excel files (*.xlsx *.xls);;CSV files (*.csv);;All files (*.*)"
        )
        
        if file_path:
            try:
                # Read the file
                if file_path.endswith(('.xlsx', '.xls')):
                    df = pd.read_excel(file_path)
                else:
                    df = pd.read_csv(file_path)
                
                total_entries = len(df)
                
                # Check hard limit first
                if total_entries > self.HARD_LIMIT:
                    QMessageBox.critical(
                        self,
                        "Import Error",
                        f"Cannot import: File contains {total_entries:,} entries, which exceeds the maximum limit of {self.HARD_LIMIT:,} entries.\n\n"
                        f"Please split your data into smaller files of {self.HARD_LIMIT:,} entries or fewer."
                    )
                    return
                
                # Warn on soft limit
                if total_entries > self.SOFT_LIMIT:
                    response = QMessageBox.warning(
                        self,
                        "Large Import Warning",
                        f"You are about to import {total_entries:,} entries, which is more than the recommended maximum of {self.SOFT_LIMIT:,} entries.\n\n"
                        "Importing a large number of entries may cause the application to become slow or unresponsive.\n\n"
                        "Do you want to continue?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if response == QMessageBox.No:
                        return
                
                # Create and show progress dialog
                progress = CircularProgressDialog(self)
                progress.set_progress(0, "Reading file...")
                progress.show()
                QApplication.processEvents()  # Ensure dialog shows immediately
                
                if progress.was_cancelled():
                    progress.close()
                    self._clear_all_entries()
                    return

                progress.set_progress(10, "Preparing entry cards...")
                QApplication.processEvents()
                
                # Store the initial state so we can revert if cancelled
                initial_card_count = len(self.entry_cards)
                self._clear_all_entries()
                
                # Create required cards
                total_entries = len(df)
                while len(self.entry_cards) < total_entries:
                    if progress.was_cancelled():
                        # Revert to initial state
                        self._clear_all_entries()
                        for _ in range(initial_card_count):
                            self._add_new_card()
                        progress.close()
                        return
                        
                    self._add_new_card()
                    progress.set_progress(
                        10 + (20 * len(self.entry_cards) // total_entries),
                        f"Creating entry cards... ({len(self.entry_cards)}/{total_entries})"
                    )
                    QApplication.processEvents()
                
                # Import data and ensure validation/updates are triggered
                for i, row in df.iterrows():
                    if progress.was_cancelled():
                        # Revert to initial state
                        self._clear_all_entries()
                        for _ in range(initial_card_count):
                            self._add_new_card()
                        progress.close()
                        return
                        
                    if i < len(self.entry_cards):
                        card = self.entry_cards[i]
                        card.set_entry_data({
                            'date': str(row.get('Date', '')),
                            'description': str(row.get('Description', '')),
                            'debit_account': str(row.get('Debit Account', '')),
                            'credit_account': str(row.get('Credit Account', '')),
                            'amount': str(row.get('Amount', ''))
                        })
                        # Force UI updates for account fields
                        card.debit_combo.repaint()
                        card.credit_combo.repaint()
                        
                        # Update progress
                        progress_value = 30 + (70 * (i + 1) // total_entries)
                        progress.set_progress(
                            progress_value,
                            f"Processing entries... ({i + 1}/{total_entries})"
                        )
                        QApplication.processEvents()
                
                if progress.was_cancelled():
                    # Revert to initial state
                    self._clear_all_entries()
                    for _ in range(initial_card_count):
                        self._add_new_card()
                    progress.close()
                    return
                    
                progress.set_progress(100, "Import complete!")
                QApplication.processEvents()
                QTimer.singleShot(500, progress.close)  # Close after brief delay
                
                # Trigger validation and UI updates after import
                self._update_validation_and_save_state()

                # Wait briefly to ensure all updates are processed
                QTimer.singleShot(100, lambda: [
                    QMessageBox.information(self, "Import Successful", f"Imported {len(df)} entries from file."),
                    self._update_summary()
                ])
                
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import file: {e}")
                # Clean up on error
                self._clear_all_entries()
                for _ in range(initial_card_count):
                    self._add_new_card()
    
    def refresh_accounts_from_system(self):
        """Reload accounts from the system and refresh all entry cards."""
        try:
            new_accounts = load_accounts_from_system(self.system)
            for card in self.entry_cards:
                card.refresh_accounts(new_accounts)
        except Exception as e:
            print(f"Error refreshing accounts: {e}")
    
    def _update_validation_and_save_state(self):
        """Update validation styling for all cards and save button state."""
        # Apply validation immediately for responsive UI
        self._apply_validation_styling()
    
    def _apply_validation_styling(self):
        """Apply validation styling to all cards and update save button state."""
        has_incomplete_cards = False
        
        for card in self.entry_cards:
            if hasattr(card, 'apply_incomplete_styling') and hasattr(card, 'has_incomplete_data'):
                # Apply styling first
                card.apply_incomplete_styling()
                
                # Check if incomplete
                if card.has_incomplete_data():
                    has_incomplete_cards = True
        
        # Update save button state
        self._update_save_button_state(has_incomplete_cards)
    
    def _update_save_button_state(self, has_incomplete_cards):
        """Enable/disable save button based on validation state."""
        if hasattr(self, 'save_all_btn'):
            should_enable = not has_incomplete_cards
            current_enabled = self.save_all_btn.isEnabled()
            
            # Only update if state actually changed to avoid unnecessary style updates
            if should_enable != current_enabled:
                self.save_all_btn.setEnabled(should_enable)
                
                # Visual feedback for disabled state
                if has_incomplete_cards:
                    self.save_all_btn.setStyleSheet("""
                        QPushButton {
                            background: rgba(108, 117, 125, 0.3);
                            color: rgba(255, 255, 255, 0.5);
                            border: 1px solid rgba(108, 117, 125, 0.5);
                            border-radius: 8px;
                            padding: 8px 16px;
                            font-weight: 500;
                        }
                    """)
                else:
                    # Restore primary button styling when enabled
                    self.save_all_btn.setStyleSheet(get_button_style(primary=True))
