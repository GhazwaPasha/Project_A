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
            accounts_data = self.system.get_postable_accounts()
            # Fix: accounts_data is now tuples (name, type, code, parent_code, level, is_postable, description)
            # Index 2 = code, Index 0 = name
            if accounts_data and len(accounts_data) > 0:
                # Check if it's tuple format or dict format for compatibility
                sample_account = accounts_data[0]
                if isinstance(sample_account, tuple):
                    # New tuple format: (name, type, code, parent_code, level, is_postable, description)
                    self.formatted_accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data if len(acc) >= 3]
                elif isinstance(sample_account, dict):
                    # Old dict format for backward compatibility
                    self.formatted_accounts = [f"{acc.get('code', '')} - {acc.get('name', '')}" for acc in accounts_data]
                else:
                    # Fallback: empty list
                    self.formatted_accounts = []
                    print(f"⚠️  Unknown account data format: {type(sample_account)}")
            else:
                self.formatted_accounts = []
                print("⚠️  No accounts loaded from system")
        except Exception as e:
            print(f"❌ Error loading accounts in bulk entry: {e}")
            self.formatted_accounts = []
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
          # Connect validation styling updates with deferred validation for better performance
        if not self._bulk_import_mode:
            # Use the improved connection method for better validation feedback
            if hasattr(card, 'connect_validation_updates'):
                card.connect_validation_updates(self._defer_validation_update)
            else:
                # Fallback to individual connections
                card.desc_edit.textChanged.connect(self._defer_validation_update)
                card.debit_combo.currentTextChanged.connect(self._defer_validation_update)
                card.credit_combo.currentTextChanged.connect(self._defer_validation_update)
                card.amount_edit.textChanged.connect(self._defer_validation_update)
        
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
                        # Revert to initial state
                        self._bulk_import_mode = False
                        self._skip_validation_updates = False
                        self._clear_all_entries()
                        for initial_data in initial_cards:
                            self._add_new_card()
                            if len(self.entry_cards) > 0:
                                card = self.entry_cards[-1]
                                card.set_entry_data(initial_data)
                        progress.close()
                        return
                    
                    # Create a new card for this entry
                    self._add_new_card()
                    
                    # Get the newly created card
                    if len(self.entry_cards) > 0:
                        card = self.entry_cards[-1]
                        
                        # Set the entry data
                        entry_data = {
                            'date': str(row.get('Date', '')),
                            'description': str(row.get('Description', '')),
                            'debit_account': str(row.get('Debit Account', '')),
                            'credit_account': str(row.get('Credit Account', '')),
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
                    # Revert to initial state
                    self._clear_all_entries()
                    for initial_data in initial_cards:
                        self._add_new_card()
                        if len(self.entry_cards) > 0:
                            card = self.entry_cards[-1]
                            card.set_entry_data(initial_data)
                    progress.close()
                    return
                
                # Add one final empty card if we successfully imported all entries
                self._add_new_card()
                    
                progress.set_progress(100, "Import complete!")
                QApplication.processEvents()
                QTimer.singleShot(500, progress.close)  # Close after brief delay
                  # Trigger validation and UI updates after import
                self._update_validation_and_save_state()
                
                # Re-enable widget updates and cleanup
                self.setUpdatesEnabled(True)
                self.scroll_area.setUpdatesEnabled(True)
                self._cleanup_unused_cards()

                # Wait briefly to ensure all updates are processed
                QTimer.singleShot(100, lambda: [
                    QMessageBox.information(self, "Import Successful", f"Imported {len(df)} entries from file."),
                    self._update_summary()
                ])
                
            except Exception as e:
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
            accounts_data = self.system.get_postable_accounts()
            self.formatted_accounts = [f"{acc['code']} - {acc['name']}" for acc in accounts_data]
            
            # Update all existing cards with the new account list
            for card in self.entry_cards:
                card.debit_combo.setAccountList(self.formatted_accounts)
                card.credit_combo.setAccountList(self.formatted_accounts)
                
            print("✅ Account list refreshed in bulk entry page")
        except Exception as e:
            print(f"❌ Error refreshing accounts in bulk entry: {e}")
    
    def _refresh_accounts(self):
        """Internal method to refresh accounts when events are triggered."""
        try:
            # Update the local accounts cache
            accounts_data = self.system.get_postable_accounts()
            # Fix: accounts_data is now tuples (name, type, code, parent_code, level, is_postable, description)
            # Index 2 = code, Index 0 = name
            if accounts_data and len(accounts_data) > 0:
                # Check if it's tuple format or dict format for compatibility
                sample_account = accounts_data[0]
                if isinstance(sample_account, tuple):
                    # New tuple format: (name, type, code, parent_code, level, is_postable, description)
                    self.formatted_accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data if len(acc) >= 3]
                elif isinstance(sample_account, dict):
                    # Old dict format for backward compatibility
                    self.formatted_accounts = [f"{acc.get('code', '')} - {acc.get('name', '')}" for acc in accounts_data]
                else:
                    # Fallback: empty list
                    self.formatted_accounts = []
                    print(f"⚠️  Unknown account data format during refresh: {type(sample_account)}")
            else:
                self.formatted_accounts = []
                print("⚠️  No accounts loaded during refresh")
            
            # Refresh all cards
            self.refresh_accounts_from_system()
        except Exception as e:
            print(f"❌ Error refreshing accounts in bulk entry: {e}")
            self.formatted_accounts = []
