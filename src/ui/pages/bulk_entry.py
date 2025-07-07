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
from ...core.utils import format_currency
from ...core.events import accounting_events
from ...core.account_matcher import EnhancedAccountMatcher
from ..components.scrollbar_styles import ModernScrollbarStyles
from ..components.widgets import PageHeader, EditableAccountComboBox
from ..components.card_based_entry import CardBasedTransactionEntry
from ..components.shared_styles import get_field_style, get_button_style, load_accounts_from_system, populate_account_combo
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.progress_dialog import CircularProgressDialog
from ..common import ResponsiveHelper


class BulkEntryPage(QWidget):
    """Clean bulk entry page."""
      # Constants for entry limits
    SOFT_LIMIT = 10000  # Show warning above this
    HARD_LIMIT = 100000  # Reject import above this
    entries_saved = pyqtSignal()
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.entry_cards = []
        self.next_card_number = 1
          # Performance optimization flags
        self._bulk_import_mode = False
        self._skip_validation_updates = False
        self._memory_conservation_mode = False
        self._validation_cache = {}        # Load accounts once for all cards
        try:
            # Use the working load_accounts_from_system function
            self.formatted_accounts = load_accounts_from_system(self.system)
            
            # Initialize account_matcher to None before refresh
            self.account_matcher = None
            
            # Enhanced AccountMatcher for intelligent import assistance with semantic understanding
            self._refresh_account_matcher()
        except Exception as e:
            print(f"❌ Error loading accounts in bulk entry: {e}")
            self.formatted_accounts = []
            self.account_matcher = None
        self._setup_ui()
        self._add_new_card()  # Start with one empty card
        
        # Connect to account change events for real-time updates
        accounting_events.accounts_changed.connect(self._refresh_accounts)
    
    def _apply_styling(self):
        """Apply modern glassmorphism styling."""
        GlassmorphismHelper.apply_main_container_effect(self)
        self.setStyleSheet(ModernStyles.get_complete_stylesheet())
        
    def _setup_ui(self):
        """Setup the main UI."""
        page_layout = QVBoxLayout(self)
        # Use 0 left/right margins when used as tab - parent JournalPage provides those
        page_layout.setContentsMargins(0, 0,  # Remove top margin for seamless flow
                                     0, ResponsiveHelper.scale_size(24, 16, 32))
        page_layout.setSpacing(16)  # Standardized spacing
        
        # Toolbar
        toolbar_section = self._create_toolbar()
        page_layout.addWidget(toolbar_section)
        
        # Cards container
        self.cards_widget = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_widget)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)
        self.cards_layout.addStretch(1)
          # Scroll area with modern scrollbar
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Apply modern scrollbar styling
        scroll_area_style = """
            QScrollArea, QWidget#scrollAreaWidgetContents {
                background: transparent;
                border: none;
            }
            QWidget { background: transparent; }
        """ + ModernScrollbarStyles.get_vertical_scrollbar_style()
        scroll_area.setStyleSheet(scroll_area_style)
        
        scroll_area.setWidget(self.cards_widget)
        page_layout.addWidget(scroll_area, 1)
        
        # Store reference for virtual scrolling optimization
        self.scroll_area = scroll_area
        
        # Setup scroll-based optimization
        self._setup_scroll_optimization()
    
    def _create_toolbar(self):
        """Create the toolbar section."""
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.3);
                border-radius: 8px;
            }
        """)
        
        toolbar_layout = QHBoxLayout(toolbar_frame)
        responsive_margin = ResponsiveHelper.scale_size(20, 16, 24)
        toolbar_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                        responsive_margin, responsive_margin)
        toolbar_layout.setSpacing(ResponsiveHelper.scale_size(12, 10, 16))
        
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
        self.summary_label = QLabel(f"0 entries, {format_currency(0)} total")
        self.summary_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.7);
            font-size: 14px;
            font-weight: 400;
            background: transparent;
            border: none;
        """)        # Buttons - all with equal sizing
        button_width = 100
        button_height = 32
        
        add_btn = QPushButton("Add Entry")
        add_btn.setStyleSheet(get_button_style())
        add_btn.setFixedSize(button_width, button_height)
        add_btn.clicked.connect(self._add_new_card)
        
        import_btn = QPushButton("Import")
        import_btn.setStyleSheet(get_button_style())
        import_btn.setFixedSize(button_width, button_height)
        import_btn.clicked.connect(self._import_file)
        
        save_all_btn = QPushButton("Save All")
        save_all_btn.setStyleSheet(get_button_style(primary=True))
        save_all_btn.setFixedSize(button_width, button_height)
        save_all_btn.clicked.connect(self._save_all_entries)
        self.save_all_btn = save_all_btn  # Store reference for validation management
        
        clear_all_btn = QPushButton("Delete All")
        clear_all_btn.setStyleSheet(get_button_style(secondary=True))
        clear_all_btn.setFixedSize(button_width, button_height)
        clear_all_btn.clicked.connect(self._delete_all_entries)
        
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
        
        # Connect validation styling updates with immediate field response
        if not self._bulk_import_mode:
            # Connect validation updates during normal operation
            card.connect_validation_updates(self._defer_validation_update)
        
        self.cards_layout.insertWidget(len(self.entry_cards), card)
        self.entry_cards.append(card)
        self.next_card_number += 1
        
        if not self._skip_validation_updates:
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
        # Skip summary updates during bulk operations for performance
        if self._bulk_import_mode:
            return
            
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
        formatted_total = format_currency(total_amount)
        self.summary_label.setText(f"{count} entries, {formatted_total} total")
        
    def _remove_card(self, card):
        """Remove an entry card."""
        if len(self.entry_cards) > 1:
            self.cards_layout.removeWidget(card)
            self.entry_cards.remove(card)
            card.deleteLater()
            self._renumber_cards()
            self._update_summary()            # Update validation and save button state after card removal
            self._update_validation_and_save_state()
        else:
            QMessageBox.information(self, "Cannot Remove", "At least one entry card must remain.")
            
    def _remove_card_efficient(self, card):
        """Efficiently remove a card with memory optimization."""
        if card in self.entry_cards:
            # Disconnect all signals first to prevent memory leaks
            try:
                card.remove_requested.disconnect()
                card.desc_edit.textChanged.disconnect()
                card.debit_combo.currentTextChanged.disconnect()
                card.credit_combo.currentTextChanged.disconnect()
                card.amount_edit.textChanged.disconnect()
            except:
                pass  # Some signals might not be connected
            
            # Remove from layout and list
            self.cards_layout.removeWidget(card)
            self.entry_cards.remove(card)
            
            # Schedule for deletion
            card.deleteLater()
            
        # Update summary only if not in bulk mode
        if not self._skip_validation_updates:
            self._update_summary()
            self._update_validation_and_save_state()
    
    def _renumber_cards(self):
        """Renumber all cards after removal."""
        for i, card in enumerate(self.entry_cards):
            card.card_number = i + 1
            
    def _save_all_entries(self):
        """Save all valid entries one by one, removing each card as it's saved."""
        valid_entries = []
        valid_cards = []  # Keep track of valid cards
        invalid_cards = []
        
        for i, card in enumerate(self.entry_cards):
            if card.is_valid():
                valid_entries.append(card.get_entry_data())
                valid_cards.append(card)  # Store the card reference
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
                "⚠ Account fields with orange borders are required but empty."            )
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
              # Enable bulk save mode for performance
            self._bulk_import_mode = True
            self._skip_validation_updates = True
              # Apply memory optimizations for large saves
            if len(valid_entries) > 2000:  # Increased threshold for memory optimization
                self._optimize_memory_usage()
            
            success_count = 0
            failed_entries = []
            cards_to_remove = []  # Track cards that need to be removed
            batch_size = 50  # Larger batch size for better performance
            ui_update_interval = 10  # Update UI every 10 entries
            
            # Disable all widgets temporarily for better performance
            for card in self.entry_cards:
                card.setEnabled(False)
            
            # Save entries with optimized batch processing
            for i, (entry_data, card) in enumerate(zip(valid_entries, valid_cards)):
                if progress.was_cancelled():
                    break
                
                try:
                    # Save the individual entry
                    self.system.add_journal_entry(entry_data)
                    
                    success_count += 1
                    cards_to_remove.append(card)
                    
                    # Update progress and UI only at intervals for better performance
                    if (i + 1) % ui_update_interval == 0 or i == len(valid_entries) - 1:
                        progress_value = int(((i + 1) / len(valid_entries)) * 100)
                        progress.set_progress(
                            progress_value,
                            f"Saved {i + 1} of {len(valid_entries)} entries..."
                        )
                        QApplication.processEvents()
                    
                except Exception as e:
                    failed_entries.append((i, str(e)))
                    # Don't include this card in removal list if saving failed
                    continue
            
            # Batch remove all successfully saved cards at once for better performance
            for card in cards_to_remove:
                self.cards_layout.removeWidget(card)
                if card in self.entry_cards:
                    self.entry_cards.remove(card)
                card.deleteLater()
            
            # Re-enable remaining widgets
            for card in self.entry_cards:
                card.setEnabled(True)
            
            progress.close()
              # Disable bulk import mode and re-enable validation
            self._bulk_import_mode = False
            self._skip_validation_updates = False
            
            # Clean up memory and optimize widgets
            self._optimize_memory_usage()
            
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
            
            if success_count > 0:
                # Emit the saved signal
                self.entries_saved.emit()
                
                # Renumber remaining cards
                self._renumber_cards()
                
                # Update the summary to reflect the new count
                self._update_summary()
                
                # Add a new empty card if no cards remain
                if not self.entry_cards:
                    self._add_new_card()
                # If we have remaining cards but they're all empty, ensure we have one empty card
                elif all(not card._has_any_data() for card in self.entry_cards):
                    # Remove all empty cards except one
                    while len(self.entry_cards) > 1:
                        card_to_remove = self.entry_cards[-1]
                        self.cards_layout.removeWidget(card_to_remove)
                        self.entry_cards.remove(card_to_remove)
                        card_to_remove.deleteLater()
                    self._renumber_cards()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save entries: {e}")
        finally:
            # Ensure cleanup happens regardless of success or failure
            self._bulk_import_mode = False
            self._skip_validation_updates = False
            self._cleanup_unused_resources()
    
    def _clear_all_entries(self):
        """Clear all entry cards."""
        for card in self.entry_cards:
            card.clear_entry()
        self._update_summary()
        
    def _delete_all_entries(self):
        """Delete all entry cards efficiently using batch processing."""
        if len(self.entry_cards) <= 1:
            # If only one card, just clear it instead of deleting
            if self.entry_cards:
                self.entry_cards[0].clear_entry()
            self._update_summary()
            return
        
        # Use optimized batch deletion for performance
        self._delete_all_cards_efficiently()
        
    def _delete_all_cards_efficiently(self):
        """Efficiently delete all cards using batch processing."""
        # Enable bulk mode to skip expensive updates during deletion
        self._bulk_import_mode = True
        self._skip_validation_updates = True
        
        try:
            # Disable widget updates for better performance
            self.setUpdatesEnabled(False)
            
            # Keep only the first card, remove all others
            cards_to_remove = self.entry_cards[1:]  # All cards except the first one
            
            # Batch disconnect all signals to prevent memory leaks
            for card in cards_to_remove:
                try:
                    card.remove_requested.disconnect()
                    card.desc_edit.textChanged.disconnect()
                    card.debit_combo.currentTextChanged.disconnect()
                    card.credit_combo.currentTextChanged.disconnect()
                    card.amount_edit.textChanged.disconnect()
                except:
                    pass  # Some signals might not be connected
                
                # Remove from layout and list
                self.cards_layout.removeWidget(card)
                card.deleteLater()
            
            # Update the entry cards list to only contain the first card
            self.entry_cards = self.entry_cards[:1]
            
            # Clear the remaining card
            if self.entry_cards:
                self.entry_cards[0].clear_entry()
                self.entry_cards[0].card_number = 1
            
        finally:
            # Re-enable updates and bulk mode
            self._bulk_import_mode = False
            self._skip_validation_updates = False
            self.setUpdatesEnabled(True)
            
            # Do a single update at the end instead of per-card updates
            self._update_summary()
            self._update_validation_and_save_state()
    
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
                  # Suggest virtual scrolling for very large imports
                if total_entries > 20000:  # Suggest for very large imports
                    response = QMessageBox.question(
                        self,
                        "Performance Optimization",
                        f"You are importing {total_entries:,} entries, which may impact performance.\n\n"
                        "For better performance with large datasets, consider:\n"
                        "• Splitting the data into smaller files (under 10,000 entries each)\n"
                        "• Using the 'Save All' button to save entries in batches\n"
                        "• Closing other applications to free memory\n\n"
                        "Do you want to continue with this import?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.Yes
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
                    return

                progress.set_progress(10, "Preparing for import...")
                QApplication.processEvents()
                  # Enable bulk import mode for performance optimization
                self._bulk_import_mode = True
                self._skip_validation_updates = True
                
                # Apply large dataset optimizations
                self._optimize_for_large_dataset(total_entries)
                self._optimize_memory_usage()
                
                # Store the initial state so we can revert if cancelled
                initial_cards = []
                for card in self.entry_cards[:]:  # Create a copy of the list
                    initial_cards.append({
                        'date': card.date_edit.date().toString('yyyy-MM-dd'),
                        'description': card.desc_edit.text(),
                        'debit_account': card.debit_combo.currentText(),
                        'credit_account': card.credit_combo.currentText(),
                        'amount': card.amount_edit.text()
                    })
                  # Clear existing cards
                self._clear_all_entries()
                
                # Import data with optimized batch processing
                batch_size = 50  # Process in batches for better performance
                for i, row in df.iterrows():
                    if progress.was_cancelled():
                        # Ensure UI updates are re-enabled immediately
                        self.setUpdatesEnabled(True)
                        self.scroll_area.setUpdatesEnabled(True)
                        self._bulk_import_mode = False
                        self._skip_validation_updates = False
                        
                        # Revert to initial state
                        self._clear_all_entries()
                        for initial_data in initial_cards:
                            self._add_new_card()
                            if len(self.entry_cards) > 0:
                                card = self.entry_cards[-1]
                                card.set_entry_data(initial_data)
                        
                        # Make sure we have at least one card if restoration failed
                        if not self.entry_cards:
                            self._add_new_card()
                        
                        progress.close()
                        self._cleanup_unused_resources()  # Ensure proper cleanup
                        return
                    
                    # Create a new card for this entry
                    self._add_new_card()
                    
                    # Get the newly created card
                    if len(self.entry_cards) > 0:
                        card = self.entry_cards[-1]
                        
                        # Use EnhancedAccountMatcher for intelligent account matching with semantic understanding
                        debit_account_raw = str(row.get('Debit Account', ''))
                        credit_account_raw = str(row.get('Credit Account', ''))
                        
                        # Match accounts using EnhancedAccountMatcher
                        debit_account_matched = self._resolve_account_for_import(debit_account_raw)
                        credit_account_matched = self._resolve_account_for_import(credit_account_raw)
                        
                        # Set the entry data with matched accounts
                        entry_data = {
                            'date': str(row.get('Date', '')),
                            'description': str(row.get('Description', '')),
                            'debit_account': debit_account_matched,
                            'credit_account': credit_account_matched,
                            'amount': str(row.get('Amount', ''))
                        }
                        card.set_entry_data(entry_data)
                        
                        # Update progress and process events only in batches
                        if (i + 1) % batch_size == 0 or (i + 1) == total_entries:
                            progress_value = 10 + (85 * (i + 1) // total_entries)
                            progress.set_progress(
                                progress_value,
                                f"Imported {i + 1} of {total_entries} entries..."
                            )
                            QApplication.processEvents()
                
                # Disable bulk import mode and re-enable validation
                self._bulk_import_mode = False
                self._skip_validation_updates = False
                
                if progress.was_cancelled():
                    # Ensure UI updates are re-enabled before reverting state
                    self.setUpdatesEnabled(True)
                    self.scroll_area.setUpdatesEnabled(True)
                    
                    # Revert to initial state
                    self._clear_all_entries()
                    for initial_data in initial_cards:
                        self._add_new_card()
                        if len(self.entry_cards) > 0:
                            card = self.entry_cards[-1]
                            card.set_entry_data(initial_data)
                    
                    # Make sure we have at least one card if restoration failed
                    if not self.entry_cards:
                        self._add_new_card()
                    
                    progress.close()
                    self._cleanup_unused_resources()  # Ensure proper cleanup
                    return
                
                # Add one final empty card if we successfully imported all entries
                self._add_new_card()
                    
                progress.set_progress(100, "Import complete!")
                QApplication.processEvents()
                QTimer.singleShot(500, progress.close)  # Close after brief delay
                  
                # Show intelligent matching report
                imported_data = []
                for _, row in df.iterrows():
                    imported_data.append({
                        'debit_account': str(row.get('Debit Account', '')),
                        'credit_account': str(row.get('Credit Account', ''))
                    })
                self._show_intelligent_matching_report(imported_data)
                
                # Re-enable widget updates and cleanup
                self.setUpdatesEnabled(True)
                self.scroll_area.setUpdatesEnabled(True)
                self._cleanup_unused_cards()
                
                # Force immediate validation update after import
                # This ensures all cards show proper styling based on their content
                QTimer.singleShot(100, self._force_validation_update_after_import)

                # Wait briefly to ensure all updates are processed
                QTimer.singleShot(200, lambda: [
                    QMessageBox.information(self, "Import Successful", f"Imported {len(df)} entries from file."),
                    self._update_summary()
                ])
                
            except Exception as e:
                # Ensure UI updates are re-enabled on error
                self.setUpdatesEnabled(True)
                self.scroll_area.setUpdatesEnabled(True)
                self._bulk_import_mode = False
                self._skip_validation_updates = False
                
                QMessageBox.critical(self, "Import Error", f"Failed to import file: {e}")
                # Clean up on error - revert to initial state if we have it
                self._clear_all_entries()
                if 'initial_cards' in locals():
                    for initial_data in initial_cards:
                        self._add_new_card()
                        if len(self.entry_cards) > 0:
                            card = self.entry_cards[-1]
                            card.set_entry_data(initial_data)
                else:
                    # Fallback: just add one empty card
                    self._add_new_card()
                
                # Ensure proper cleanup
                self._cleanup_unused_resources()
    
    def _refresh_accounts(self):
        """Internal method to refresh accounts when events are triggered."""
        try:
            # Use the same simple approach as initialization
            self.formatted_accounts = load_accounts_from_system(self.system)
            self._refresh_account_matcher()
            
            # Refresh all cards
            self.refresh_accounts_from_system()
        except Exception as e:
            print(f"❌ Error refreshing accounts in bulk entry: {e}")
            self.formatted_accounts = []
            self.account_matcher = None
    
    def _refresh_account_matcher(self):
        """Refresh the EnhancedAccountMatcher with fresh account data."""
        try:
            # Get fresh data from system to ensure we have the latest
            fresh_accounts = load_accounts_from_system(self.system, use_fresh_data=True)
            if fresh_accounts:
                if self.account_matcher:
                    # Use the refresh method if matcher already exists
                    self.account_matcher.refresh_accounts(fresh_accounts)
                else:
                    # Create new matcher if none exists
                    self.account_matcher = EnhancedAccountMatcher(fresh_accounts)
                    print(f"✅ EnhancedAccountMatcher created with {len(fresh_accounts)} accounts")
                # Update formatted_accounts to match
                self.formatted_accounts = fresh_accounts
            else:
                self.account_matcher = None
                print("⚠️ No fresh accounts available for EnhancedAccountMatcher")
        except Exception as e:
            print(f"❌ Error refreshing EnhancedAccountMatcher: {e}")
            self.account_matcher = None
    
    def refresh_accounts_from_system(self):
        """Reload accounts from the system and refresh all entry cards."""
        try:
            new_accounts = load_accounts_from_system(self.system)
            for card in self.entry_cards:
                card.refresh_accounts(new_accounts)
        except Exception as e:
            print(f"Error refreshing accounts: {e}")
    
    def refresh_currency_display(self):
        """Refresh currency formatting in the summary."""
        # Only update if not in bulk mode
        if not self._bulk_import_mode:
            self._update_summary()
    
    def refresh_data(self):
        """Refresh bulk entry data when organization context changes."""
        try:
            print("🔄 BulkEntry: Refreshing data due to organization change...")
            self._refresh_accounts()
        except Exception as e:
            print(f"Error refreshing bulk entry data: {e}")
    
    def _update_validation_and_save_state(self):
        """Update validation styling for all cards and save button state."""
        # Skip validation updates during bulk import for performance
        if self._skip_validation_updates:
            return
        # Apply validation immediately for responsive UI
        self._apply_validation_styling()
    
    def _apply_validation_styling(self):
        """Apply validation styling to all cards and update save button state."""
        # Skip during bulk operations for performance
        if self._bulk_import_mode:
            return
            
        has_incomplete_cards = False
        
        # Use lazy evaluation - stop checking once we find an incomplete card
        for card in self.entry_cards:
            if hasattr(card, 'apply_incomplete_styling') and hasattr(card, 'has_incomplete_data'):
                # Apply styling first
                card.apply_incomplete_styling()
                
                # Check if incomplete - use lazy evaluation for performance
                if not has_incomplete_cards and card.has_incomplete_data():
                    has_incomplete_cards = True
                    # For performance, we can break early if we just need to know if ANY card is incomplete
                    # But we still need to apply styling to all cards, so continue
        
        # Update save button state
        self._update_save_button_state(has_incomplete_cards)
    
    def _update_save_button_state(self, has_incomplete_cards):
        """Update the save button state based on validation."""
        if hasattr(self, 'save_all_btn'):
            # Enable save button if there are valid entries
            valid_count = sum(1 for card in self.entry_cards if card.is_valid())
            self.save_all_btn.setEnabled(valid_count > 0)
            
            # Update button text to show count
            if valid_count > 0:
                self.save_all_btn.setText(f"Save All ({valid_count})")
            else:
                self.save_all_btn.setText("Save All")
    
    def _batch_operation_wrapper(self, operation_func, *args, **kwargs):
        """Wrapper for batch operations to optimize performance."""
        # Store current state
        was_bulk_mode = self._bulk_import_mode
        was_skip_validation = self._skip_validation_updates
        
        try:
            # Enable bulk mode
            self._bulk_import_mode = True
            self._skip_validation_updates = True
            
            # Execute the operation
            result = operation_func(*args, **kwargs)
            
            return result
        finally:
            # Restore state
            self._bulk_import_mode = was_bulk_mode
            self._skip_validation_updates = was_skip_validation            # Trigger single validation update after batch operation
            if not was_skip_validation:
                QTimer.singleShot(50, self._update_validation_and_save_state)
    
    def _should_use_virtual_scrolling(self, entry_count):
        """Determine if virtual scrolling should be recommended for performance."""
        return entry_count > 20000  # Increased threshold for virtual scrolling recommendation
    
    def _optimize_for_large_dataset(self, entry_count):
        """Apply optimizations for large datasets."""
        if entry_count > 5000:  # Increased threshold for memory conservation
            # Disable animations and visual effects
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            
            # Enable memory conservation mode
            self._memory_conservation_mode = True
            
            # Suggest virtual scrolling for very large datasets
            if self._should_use_virtual_scrolling(entry_count):
                QMessageBox.information(
                    self,
                    "Performance Tip",
                    f"You're importing {entry_count:,} entries. For optimal performance with very large datasets, "
                    f"consider processing in smaller batches of {self.SOFT_LIMIT:,} entries or less."
                )
    
    def _cleanup_unused_cards(self):
        """Remove empty cards to free memory."""
        if hasattr(self, '_memory_conservation_mode') and self._memory_conservation_mode:
            cards_to_remove = []
            for i, card in enumerate(self.entry_cards):
                if (hasattr(card, 'is_empty') and card.is_empty() and 
                    i < len(self.entry_cards) - 1):  # Keep at least one card
                    cards_to_remove.append(card)
            
            for card in cards_to_remove:
                self._remove_card(card)
                
    def _optimize_memory_usage(self):
        """Optimize memory usage during bulk operations."""
        # Force garbage collection
        import gc
        gc.collect()
        
        # Clear any cached data
        if hasattr(self, '_validation_cache'):
            self._validation_cache.clear()
            
        # Minimize widget updates
        self.setUpdatesEnabled(False)
        self.scroll_area.setUpdatesEnabled(False)
    
    def _cleanup_unused_resources(self):
        """Clean up unused resources and reset optimization flags."""
        # Reset memory conservation mode
        self._memory_conservation_mode = False
        
        # Clear validation cache
        if hasattr(self, '_validation_cache'):
            self._validation_cache.clear()
        
        # Re-enable widget updates
        self.setUpdatesEnabled(True)
        self.scroll_area.setUpdatesEnabled(True)
        
        # Force garbage collection for memory cleanup
        import gc
        gc.collect()
        
        # Update validation state
        self._update_validation_and_save_state()
    
    def _validate_with_cache(self, card):
        """Validate a card with caching for better performance."""
        if not hasattr(self, '_validation_cache'):
            self._validation_cache = {}
        
        # Create a cache key based on card contents
        cache_key = (
            card.date_edit.date().toString('yyyy-MM-dd'),
            card.desc_edit.text(),
            card.debit_combo.currentText(),
            card.credit_combo.currentText(),
            card.amount_edit.text()
        )
        
        # Check cache first
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]
        
        # Perform validation and cache result
        is_valid = card.is_valid()
        self._validation_cache[cache_key] = is_valid
        
        # Limit cache size to prevent memory issues
        if len(self._validation_cache) > 1000:
            # Remove oldest entries (simple FIFO)
            keys_to_remove = list(self._validation_cache.keys())[:100]
            for key in keys_to_remove:
                del self._validation_cache[key]
        
        return is_valid
    
    def _defer_validation_update(self):
        """Defer validation updates for better performance."""
        if self._skip_validation_updates or self._bulk_import_mode:
            return
            
        # Use a timer to defer validation updates
        if not hasattr(self, '_validation_timer'):
            self._validation_timer = QTimer()
            self._validation_timer.setSingleShot(True)
            self._validation_timer.timeout.connect(self._update_validation_and_save_state)
        
        # Restart the timer to defer the update
        self._validation_timer.start(100)  # 100ms delay
    
    def _get_visible_cards(self):
        """Get only the cards that are currently visible in the scroll area."""
        if not hasattr(self, 'scroll_area') or not self.scroll_area.widget():
            return self.entry_cards
        
        # Get scroll area geometry
        scroll_rect = self.scroll_area.viewport().rect()
        scroll_top = self.scroll_area.verticalScrollBar().value()
        scroll_bottom = scroll_top + scroll_rect.height()
        
        visible_cards = []
        for card in self.entry_cards:
            if card.isVisible():
                card_pos = card.pos().y()
                card_height = card.height()
                
                # Check if card is in visible area (with some buffer)
                buffer = 50  # 50px buffer
                if (card_pos + card_height >= scroll_top - buffer and 
                    card_pos <= scroll_bottom + buffer):
                    visible_cards.append(card)
        
        return visible_cards if visible_cards else self.entry_cards
    
    def _update_validation_for_visible_cards_only(self):
        """Update validation only for visible cards to improve performance."""
        if self._skip_validation_updates or self._bulk_import_mode:
            return
        
        visible_cards = self._get_visible_cards()
        
        # Only validate visible cards
        for card in visible_cards:
            if hasattr(card, 'validate_styling'):
                card.validate_styling()
        
        # Update save button based on all cards (this is fast)
        self._update_save_button_state(False)
    
    def _setup_scroll_optimization(self):
        """Setup scroll-based optimization for large numbers of cards."""
        if hasattr(self, 'scroll_area'):
            # Connect scroll events to trigger validation updates
            scrollbar = self.scroll_area.verticalScrollBar()
            if not hasattr(self, '_scroll_timer'):
                self._scroll_timer = QTimer()
                self._scroll_timer.setSingleShot(True)
                self._scroll_timer.timeout.connect(self._update_validation_for_visible_cards_only)
            
            def on_scroll():
                if len(self.entry_cards) > 100:  # Only optimize for large numbers
                    self._scroll_timer.start(50)  # Small delay for smooth scrolling
            
            scrollbar.valueChanged.connect(on_scroll)
    
    def _delete_all_with_progress(self):
        """Delete all cards with progress feedback for very large operations."""
        card_count = len(self.entry_cards)
        
        # For small numbers, use instant deletion
        if card_count <= 50:
            self._delete_all_cards_efficiently()
            return
        
        # For large numbers, show progress
        from ..components.progress_dialog import CircularProgressDialog
        progress = CircularProgressDialog(self)
        progress.set_progress(0, f"Deleting {card_count} entries...")
        progress.show()
        QApplication.processEvents()
        
        try:
            # Enable bulk mode
            self._bulk_import_mode = True
            self._skip_validation_updates = True
            self.setUpdatesEnabled(False)
            
            # Keep only the first card, remove all others in batches
            cards_to_remove = self.entry_cards[1:]
            batch_size = 20
            
            for i in range(0, len(cards_to_remove), batch_size):
                if progress.was_cancelled():
                    break
                    
                batch = cards_to_remove[i:i + batch_size]
                
                # Process batch
                for card in batch:
                    try:
                        card.remove_requested.disconnect()
                        card.desc_edit.textChanged.disconnect()
                        card.debit_combo.currentTextChanged.disconnect()
                        card.credit_combo.currentTextChanged.disconnect()
                        card.amount_edit.textChanged.disconnect()
                    except:
                        pass
                    
                    self.cards_layout.removeWidget(card)
                    card.deleteLater()
                
                # Update progress
                progress_value = int(((i + len(batch)) / len(cards_to_remove)) * 100)
                progress.set_progress(progress_value, f"Deleted {i + len(batch)} of {len(cards_to_remove)} entries...")
                QApplication.processEvents()
            
            # Update the entry cards list
            if not progress.was_cancelled():
                self.entry_cards = self.entry_cards[:1]
                if self.entry_cards:
                    self.entry_cards[0].clear_entry()
                    self.entry_cards[0].card_number = 1
                progress.set_progress(100, "Deletion complete!")
            
        finally:
            # Cleanup
            self._bulk_import_mode = False
            self._skip_validation_updates = False
            self.setUpdatesEnabled(True)
            progress.close()
            
            self._update_summary()
            self._update_validation_and_save_state()
    
    def _on_accounts_changed(self):
        """Handle account changes by refreshing the account list in all cards."""
        try:
            # Reload accounts from the system
            all_accounts_data = self.system.get_all_accounts()
            postable_accounts_data = self.system.get_postable_accounts()
            
            # Handle different account data formats
            if postable_accounts_data and len(postable_accounts_data) > 0:
                sample_account = postable_accounts_data[0]
                if isinstance(sample_account, tuple):
                    self.formatted_accounts = [f"{acc[2]} - {acc[0]}" for acc in postable_accounts_data if len(acc) >= 3]
                    all_formatted_accounts = [f"{acc[2]} - {acc[0]}" for acc in all_accounts_data if len(acc) >= 3]
                elif isinstance(sample_account, dict):
                    self.formatted_accounts = [f"{acc.get('code', '')} - {acc.get('name', '')}" for acc in postable_accounts_data]
                    all_formatted_accounts = [f"{acc.get('code', '')} - {acc.get('name', '')}" for acc in all_accounts_data]
                else:
                    self.formatted_accounts = []
                    all_formatted_accounts = []
            else:
                self.formatted_accounts = []
                all_formatted_accounts = []
            
            # Reinitialize EnhancedAccountMatcher with ALL accounts (including non-postable)
            if all_formatted_accounts:
                self.account_matcher = EnhancedAccountMatcher(all_formatted_accounts)
                print(f"✅ EnhancedAccountMatcher reinitialized with {len(all_formatted_accounts)} accounts (including non-postable)")
            else:
                self.account_matcher = None
            
            # Update all existing cards with the new account list
            for card in self.entry_cards:
                card.debit_combo.setAccountList(self.formatted_accounts)
                card.credit_combo.setAccountList(self.formatted_accounts)
                
            print("✅ Account list and matcher refreshed in bulk entry page")
        except Exception as e:
            print(f"❌ Error refreshing accounts in bulk entry: {e}")
            self.account_matcher = None
    
    def _resolve_account_for_import(self, raw_account_name):
        """Use EnhancedAccountMatcher to resolve account name for import with semantic understanding."""
        if not raw_account_name or not raw_account_name.strip():
            return ""
        raw_account_name = str(raw_account_name).strip()
        if self.account_matcher:
            # Use enhanced matching with lower confidence threshold to catch more semantic matches
            matched, confidence = self.account_matcher.match_account(raw_account_name, confidence_threshold=0.4)
            if matched:
                # Log the smart matching for user feedback
                if confidence >= 0.7:
                    print(f"✅ Smart match: '{raw_account_name}' → '{matched}' (confidence: {confidence:.2f})")
                elif confidence >= 0.5:
                    print(f"🔍 Semantic match: '{raw_account_name}' → '{matched}' (confidence: {confidence:.2f})")
                else:
                    print(f"❓ Fuzzy match: '{raw_account_name}' → '{matched}' (confidence: {confidence:.2f})")
                return matched
            else:
                # Show suggestions if no direct match
                if hasattr(self.account_matcher, 'get_semantic_suggestions'):
                    suggestions = self.account_matcher.get_semantic_suggestions(raw_account_name, max_suggestions=3)
                    if suggestions:
                        print(f"💡 No direct match for '{raw_account_name}', suggestions:")
                        for account, score, reason in suggestions[:3]:
                            print(f"   - {account} (score: {score:.2f}, {reason})")
                else:
                    print(f"❌ No match found for '{raw_account_name}'")
        
        # Instead of returning the raw account name (which will be rejected by validation),
        # return empty string so the field is left empty for manual entry
        return ""
    
    def _show_intelligent_matching_report(self, imported_data):
        """Show a report of intelligent matching results."""
        if not self.account_matcher or not imported_data:
            return
        
        # Extract unique account names from imported data
        account_names = set()
        for entry in imported_data:
            debit_account = str(entry.get('debit_account', '')).strip()
            credit_account = str(entry.get('credit_account', '')).strip()
            if debit_account:
                account_names.add(debit_account)
            if credit_account:
                account_names.add(credit_account)
        
        if not account_names:
            return
        
        print("\n" + "="*60)
        print("🧠 INTELLIGENT ACCOUNT MATCHING REPORT")
        print("="*60)
        
        matched_count = 0
        semantic_count = 0
        
        for account_name in sorted(account_names):
            matched, confidence = self.account_matcher.match_account(account_name, confidence_threshold=0.4)
            
            if matched:
                matched_count += 1
                match_type = "Exact" if confidence >= 0.9 else "Semantic" if confidence >= 0.6 else "Fuzzy"
                if confidence >= 0.6:
                    semantic_count += 1
                
                print(f"✅ {match_type}: '{account_name}' → '{matched}' ({confidence:.2f})")
            else:
                # Show suggestions for unmatched accounts
                if hasattr(self.account_matcher, 'get_semantic_suggestions'):
                    suggestions = self.account_matcher.get_semantic_suggestions(account_name, max_suggestions=2)
                    if suggestions:
                        print(f"❓ '{account_name}' → No match, suggestions:")
                        for suggestion, score, reason in suggestions:
                            print(f"   💡 {suggestion} ({score:.2f}) - {reason}")
                    else:
                        print(f"❌ '{account_name}' → No matches or suggestions")
                else:
                    print(f"❌ '{account_name}' → No match found")
        
        print(f"\n📊 Summary:")
        print(f"   • Total unique accounts: {len(account_names)}")
        print(f"   • Successfully matched: {matched_count}")
        print(f"   • Semantic matches: {semantic_count}")
        print(f"   • Match rate: {(matched_count/len(account_names)*100):.1f}%")
        print("="*60 + "\n")
        
        # Show user-friendly summary dialog
        self._show_matching_summary_dialog(len(account_names), matched_count, semantic_count)
    
    def _show_matching_summary_dialog(self, total_accounts, matched_count, semantic_count):
        """Show a user-friendly dialog summarizing the intelligent matching results."""
        if total_accounts == 0:
            return
        
        match_rate = (matched_count / total_accounts) * 100
        semantic_rate = (semantic_count / total_accounts) * 100
        
        title = "🧠 Smart Account Matching Results"
        
        if match_rate >= 80:
            icon = QMessageBox.Icon.Information
            msg_type = "Excellent matching!"
        elif match_rate >= 60:
            icon = QMessageBox.Icon.Information  
            msg_type = "Good matching results"
        elif match_rate >= 40:
            icon = QMessageBox.Icon.Warning
            msg_type = "Partial matching"
        else:
            icon = QMessageBox.Icon.Warning
            msg_type = "Limited matching found"
        
        message = f"""{msg_type}

📊 Matching Summary:
• Total unique accounts: {total_accounts}
• Successfully matched: {matched_count} ({match_rate:.1f}%)
• Semantic matches: {semantic_count} ({semantic_rate:.1f}%)

🧠 The Enhanced Account Matcher used semantic understanding to recognize that terms like:
• "Sales" and "Revenue" mean the same thing
• "A/R" refers to "Accounts Receivable" 
• "Wages" and "Salary" are equivalent

💡 Check the console output for detailed matching information."""

        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
    
    def _force_validation_update_after_import(self):
        """Force validation update after import to ensure proper styling and reconnect signals."""
        try:
            # Make sure we're no longer in bulk mode
            self._bulk_import_mode = False
            self._skip_validation_updates = False
            
            # Reconnect validation updates for all cards created during bulk import
            for card in self.entry_cards:
                if hasattr(card, 'connect_validation_updates'):
                    # Connect both the deferred validation and immediate field change handlers
                    card.connect_validation_updates(self._defer_validation_update)
                    
                    # Also ensure the individual field change handler is connected for immediate response
                    if hasattr(card, '_on_field_changed'):
                        try:
                            # Disconnect first to avoid duplicates
                            card.desc_edit.textChanged.disconnect(card._on_field_changed)
                            card.debit_combo.currentTextChanged.disconnect(card._on_field_changed)
                            card.credit_combo.currentTextChanged.disconnect(card._on_field_changed)
                            card.amount_edit.textChanged.disconnect(card._on_field_changed)
                        except:
                            pass  # Ignore if not connected
                        
                        # Reconnect the immediate field change handler
                        card.desc_edit.textChanged.connect(card._on_field_changed)
                        card.debit_combo.currentTextChanged.connect(card._on_field_changed)
                        card.credit_combo.currentTextChanged.connect(card._on_field_changed)
                        card.amount_edit.textChanged.connect(card._on_field_changed)
            
            # Apply validation styling to all cards
            for card in self.entry_cards:
                if hasattr(card, 'apply_incomplete_styling'):
                    card.apply_incomplete_styling()
            
            # Update the save button state
            self._update_validation_and_save_state()
            
            print(f"✅ Validation signals reconnected for {len(self.entry_cards)} cards after import")
            
        except Exception as e:
            print(f"❌ Error forcing validation update after import: {e}")
