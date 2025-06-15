"""
Enhanced CSV Import Dialog with intelligent account matching.
"""

import pandas as pd
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox, QTextEdit,
    QSplitter, QGroupBox, QProgressBar, QComboBox, QCheckBox, QSpinBox,
    QTabWidget, QWidget, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor

from ..core.account_matcher import AccountMatcher


class AccountMappingThread(QThread):
    """Background thread for account matching to avoid UI freezing."""
    
    progress_updated = pyqtSignal(int, str)
    matching_completed = pyqtSignal(dict)
    
    def __init__(self, imported_data, chart_of_accounts):
        super().__init__()
        self.imported_data = imported_data
        self.chart_of_accounts = chart_of_accounts
        
    def run(self):
        """Run the account matching process."""
        try:
            self.progress_updated.emit(10, "Initializing account matcher...")
            matcher = AccountMatcher(self.chart_of_accounts)
            
            self.progress_updated.emit(30, "Extracting account names from data...")
            # Extract unique account names from imported data
            debit_accounts = self.imported_data['Debit Account'].dropna().astype(str).tolist()
            credit_accounts = self.imported_data['Credit Account'].dropna().astype(str).tolist()
            all_accounts = list(set(debit_accounts + credit_accounts))
            
            self.progress_updated.emit(50, "Matching accounts to chart of accounts...")
            # Create mapping report
            report = matcher.create_mapping_report(all_accounts)
            
            self.progress_updated.emit(80, "Processing mapping results...")
            # Add matcher instance to report for later use
            report['matcher'] = matcher
            
            self.progress_updated.emit(100, "Account matching completed!")
            self.matching_completed.emit(report)
            
        except Exception as e:
            self.progress_updated.emit(100, f"Error: {str(e)}")


class EnhancedCSVImportDialog(QDialog):
    """Enhanced CSV import dialog with intelligent account matching."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.imported_data = None
        self.mapping_report = None
        self.account_matcher = None
        self.final_mappings = {}  # User-confirmed mappings
        
        self.setWindowTitle("Enhanced CSV/Excel Import")
        self.setModal(True)
        self.resize(1200, 800)
        
        # Load chart of accounts
        self._load_chart_of_accounts()
        
        self._setup_ui()
        self._apply_styling()
    
    def _load_chart_of_accounts(self):
        """Load the chart of accounts from the system."""
        try:
            if hasattr(self.system, 'get_all_accounts'):
                accounts_data = self.system.get_all_accounts()
                # accounts_data is a list of tuples: (name, type, code, parent_code, level, is_postable, description)
                self.chart_of_accounts = [f"{acc[2]} - {acc[0]}" for acc in accounts_data if acc[5]]  # Only postable accounts
            else:
                # Fallback for basic system
                self.chart_of_accounts = [
                    "1001 - Cash",
                    "1002 - Bank Account", 
                    "1100 - Accounts Receivable",
                    "2001 - Accounts Payable",
                    "3001 - Owner's Equity",
                    "4001 - Sales Revenue",
                    "5001 - Cost of Goods Sold",
                    "6001 - Operating Expenses"
                ]
        except Exception as e:
            print(f"Error loading accounts: {e}")
            self.chart_of_accounts = ["1001 - Cash", "1002 - Bank Account"]  # Minimal fallback
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        # Title
        title_label = QLabel("Enhanced CSV/Excel Import with Intelligent Account Matching")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding: 10px;
                background: #ecf0f1;
                border-radius: 8px;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
        # Create tab widget for different stages
        self.tab_widget = QTabWidget()
        
        # Step 1: File Selection
        self.file_tab = self._create_file_selection_tab()
        self.tab_widget.addTab(self.file_tab, "1. Select File")
        
        # Step 2: Account Matching
        self.matching_tab = self._create_account_matching_tab()
        self.tab_widget.addTab(self.matching_tab, "2. Account Matching")
        
        # Step 3: Data Preview
        self.preview_tab = self._create_data_preview_tab()
        self.tab_widget.addTab(self.preview_tab, "3. Preview & Import")
        
        # Initially disable later tabs
        self.tab_widget.setTabEnabled(1, False)
        self.tab_widget.setTabEnabled(2, False)
        
        layout.addWidget(self.tab_widget)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready to import CSV/Excel file")
        self.status_label.setStyleSheet("color: #7f8c8d; padding: 5px;")
        layout.addWidget(self.status_label)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.back_btn = QPushButton("← Back")
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.setEnabled(False)
        
        self.next_btn = QPushButton("Next →")
        self.next_btn.clicked.connect(self._go_next)
        self.next_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        self.import_btn = QPushButton("Import Transactions")
        self.import_btn.clicked.connect(self._import_transactions)
        self.import_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.back_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.cancel_btn)
        buttons_layout.addWidget(self.next_btn)
        buttons_layout.addWidget(self.import_btn)
        
        layout.addLayout(buttons_layout)
    
    def _create_file_selection_tab(self):
        """Create the file selection tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        
        # Instructions
        instructions = QLabel("""
        <h3>Step 1: Select CSV or Excel File</h3>
        <p>Choose a CSV or Excel file containing transaction data. The file should have columns for:</p>
        <ul>
            <li><b>Date</b> - Transaction date</li>
            <li><b>Description</b> - Transaction description</li>
            <li><b>Debit Account</b> - Account to debit</li>
            <li><b>Credit Account</b> - Account to credit</li>
            <li><b>Amount</b> - Transaction amount</li>
        </ul>
        <p><i>Account names will be intelligently matched to your chart of accounts.</i></p>
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # File selection
        file_group = QGroupBox("File Selection")
        file_layout = QVBoxLayout(file_group)
        
        file_select_layout = QHBoxLayout()
        self.file_path_label = QLabel("No file selected")
        self.file_path_label.setStyleSheet("padding: 8px; background: #f8f9fa; border: 1px solid #dee2e6; border-radius: 4px;")
        
        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._browse_file)
        
        file_select_layout.addWidget(self.file_path_label, 1)
        file_select_layout.addWidget(self.browse_btn)
        file_layout.addLayout(file_select_layout)
        
        # Preview of file data
        self.file_preview = QTableWidget()
        self.file_preview.setMaximumHeight(200)
        file_layout.addWidget(QLabel("File Preview (first 5 rows):"))
        file_layout.addWidget(self.file_preview)
        
        layout.addWidget(file_group)
        layout.addStretch()
        
        return tab
    
    def _create_account_matching_tab(self):
        """Create the account matching tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel("""
        <h3>Step 2: Review Account Matching</h3>
        <p>The system has automatically matched imported account names to your chart of accounts. 
        Review and adjust the mappings as needed.</p>
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Splitter for matching results and details
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Matching results table
        matching_group = QGroupBox("Account Mappings")
        matching_layout = QVBoxLayout(matching_group)
        
        self.mapping_table = QTableWidget()
        self.mapping_table.setColumnCount(4)
        self.mapping_table.setHorizontalHeaderLabels([
            "Imported Account", "Matched Account", "Confidence", "Action"
        ])
        self.mapping_table.horizontalHeader().setStretchLastSection(True)
        
        matching_layout.addWidget(self.mapping_table)
        splitter.addWidget(matching_group)
        
        # Right side: Statistics and details
        details_group = QGroupBox("Matching Statistics")
        details_layout = QVBoxLayout(details_group)
        
        self.stats_text = QTextEdit()
        self.stats_text.setMaximumHeight(200)
        self.stats_text.setReadOnly(True)
        details_layout.addWidget(self.stats_text)
        
        # Chart of accounts reference
        chart_label = QLabel("Chart of Accounts Reference:")
        details_layout.addWidget(chart_label)
        
        self.chart_list = QTableWidget()
        self.chart_list.setColumnCount(1)
        self.chart_list.setHorizontalHeaderLabels(["Available Accounts"])
        self.chart_list.horizontalHeader().setStretchLastSection(True)
        details_layout.addWidget(self.chart_list)
        
        splitter.addWidget(details_group)
        splitter.setSizes([700, 500])
        
        layout.addWidget(splitter)
        
        return tab
    
    def _create_data_preview_tab(self):
        """Create the data preview tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel("""
        <h3>Step 3: Preview and Import</h3>
        <p>Review the final transaction data with mapped accounts before importing.</p>
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels([
            "Date", "Description", "Debit Account", "Credit Account", "Amount"
        ])
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        
        layout.addWidget(self.preview_table)
        
        # Import options
        options_group = QGroupBox("Import Options")
        options_layout = QHBoxLayout(options_group)
        
        self.validate_amounts = QCheckBox("Validate amount formats")
        self.validate_amounts.setChecked(True)
        
        self.skip_invalid = QCheckBox("Skip invalid rows")
        self.skip_invalid.setChecked(True)
        
        options_layout.addWidget(self.validate_amounts)
        options_layout.addWidget(self.skip_invalid)
        options_layout.addStretch()
        
        layout.addWidget(options_group)
        
        return tab
    
    def _apply_styling(self):
        """Apply styling to the dialog."""
        self.setStyleSheet("""
            QDialog {
                background-color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background: #f0f0f0;
                border: 1px solid #c0c0c0;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 8px;
                margin-top: 1ex;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
            QTableWidget {
                gridline-color: #ddd;
                background-color: #fafafa;
                alternate-background-color: #f0f0f0;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
    
    def _browse_file(self):
        """Browse for CSV/Excel file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV/Excel File", "",
            "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        
        if file_path:
            self._load_file(file_path)
    
    def _load_file(self, file_path):
        """Load and preview the selected file."""
        try:
            self.status_label.setText(f"Loading file: {file_path}")
            
            # Read the file
            if file_path.lower().endswith('.csv'):
                self.imported_data = pd.read_csv(file_path)
            else:
                self.imported_data = pd.read_excel(file_path)
            
            # Update file path label
            self.file_path_label.setText(file_path)
            
            # Preview first 5 rows
            self._update_file_preview()
            
            # Enable next button
            self.next_btn.setEnabled(True)
            self.status_label.setText(f"File loaded successfully. {len(self.imported_data)} rows found.")
            
        except Exception as e:
            QMessageBox.critical(self, "File Load Error", f"Failed to load file: {str(e)}")
            self.status_label.setText("Error loading file")
    
    def _update_file_preview(self):
        """Update the file preview table."""
        if self.imported_data is None:
            return
        
        preview_data = self.imported_data.head(5)
        
        self.file_preview.setRowCount(len(preview_data))
        self.file_preview.setColumnCount(len(preview_data.columns))
        self.file_preview.setHorizontalHeaderLabels(preview_data.columns.tolist())
        
        for i, row in preview_data.iterrows():
            for j, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                self.file_preview.setItem(i, j, item)
        
        self.file_preview.resizeColumnsToContents()
    
    def _go_back(self):
        """Go to previous tab."""
        current_index = self.tab_widget.currentIndex()
        if current_index > 0:
            self.tab_widget.setCurrentIndex(current_index - 1)
            self._update_button_states()
    
    def _go_next(self):
        """Go to next tab."""
        current_index = self.tab_widget.currentIndex()
        
        if current_index == 0:  # File selection -> Account matching
            self._start_account_matching()
        elif current_index == 1:  # Account matching -> Preview
            self._prepare_data_preview()
        
        if current_index < self.tab_widget.count() - 1:
            self.tab_widget.setCurrentIndex(current_index + 1)
            self._update_button_states()
    
    def _update_button_states(self):
        """Update button states based on current tab."""
        current_index = self.tab_widget.currentIndex()
        
        self.back_btn.setEnabled(current_index > 0)
        self.next_btn.setEnabled(current_index < self.tab_widget.count() - 1)
        self.import_btn.setEnabled(current_index == self.tab_widget.count() - 1)
    
    def _start_account_matching(self):
        """Start the account matching process."""
        if self.imported_data is None:
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting account matching...")
        
        # Start matching in background thread
        self.matching_thread = AccountMappingThread(self.imported_data, self.chart_of_accounts)
        self.matching_thread.progress_updated.connect(self._update_progress)
        self.matching_thread.matching_completed.connect(self._on_matching_completed)
        self.matching_thread.start()
    
    def _update_progress(self, value, message):
        """Update progress bar and status."""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def _on_matching_completed(self, report):
        """Handle completion of account matching."""
        self.mapping_report = report
        self.account_matcher = report['matcher']
        
        self.progress_bar.setVisible(False)
        self.status_label.setText("Account matching completed")
        
        # Enable the account matching tab
        self.tab_widget.setTabEnabled(1, True)
        
        # Update the UI with matching results
        self._update_matching_ui()
    
    def _update_matching_ui(self):
        """Update the account matching UI with results."""
        if not self.mapping_report:
            return
        
        # Update statistics
        stats = self.mapping_report['statistics']
        stats_text = f"""
        <h4>Matching Statistics</h4>
        <p><b>Total Accounts:</b> {stats['total_accounts']}</p>
        <p><b>Successfully Mapped:</b> {stats['mapped_accounts']}</p>
        <p><b>Unmapped:</b> {stats['unmapped_accounts']}</p>
        <br>
        <p><b>Confidence Levels:</b></p>
        <p>High (>80%): {stats['high_confidence']}</p>
        <p>Medium (60-80%): {stats['medium_confidence']}</p>
        <p>Low (<60%): {stats['low_confidence']}</p>
        """
        self.stats_text.setHtml(stats_text)
        
        # Update chart of accounts list
        self.chart_list.setRowCount(len(self.chart_of_accounts))
        for i, account in enumerate(self.chart_of_accounts):
            item = QTableWidgetItem(account)
            self.chart_list.setItem(i, 0, item)
        
        # Update mapping table
        mappings = self.mapping_report['mappings']
        unmapped = self.mapping_report['unmapped']
        
        all_entries = list(mappings.items()) + [(acc, None) for acc in unmapped]
        self.mapping_table.setRowCount(len(all_entries))
        
        for row, (imported_account, mapping_info) in enumerate(all_entries):
            # Imported account name
            self.mapping_table.setItem(row, 0, QTableWidgetItem(imported_account))
            
            if mapping_info:
                # Matched account
                matched = mapping_info['matched_account']
                confidence = mapping_info['confidence']
                
                self.mapping_table.setItem(row, 1, QTableWidgetItem(matched))
                
                # Confidence with color coding
                confidence_item = QTableWidgetItem(f"{confidence:.1%}")
                if confidence > 0.8:
                    confidence_item.setBackground(QColor("#d4edda"))  # Green
                elif confidence >= 0.6:
                    confidence_item.setBackground(QColor("#fff3cd"))  # Yellow
                else:
                    confidence_item.setBackground(QColor("#f8d7da"))  # Red
                self.mapping_table.setItem(row, 2, confidence_item)
                
                # Action combo box for manual override
                action_combo = QComboBox()
                action_combo.addItem("Use Match")
                action_combo.addItem("Manual Select")
                action_combo.addItems(self.chart_of_accounts)
                action_combo.currentTextChanged.connect(
                    lambda text, acc=imported_account: self._handle_mapping_change(acc, text)
                )
                self.mapping_table.setCellWidget(row, 3, action_combo)
                
                # Store the default mapping
                self.final_mappings[imported_account] = matched
            else:
                # Unmapped account
                self.mapping_table.setItem(row, 1, QTableWidgetItem("No match found"))
                
                no_match_item = QTableWidgetItem("0.0%")
                no_match_item.setBackground(QColor("#f8d7da"))  # Red
                self.mapping_table.setItem(row, 2, no_match_item)
                
                # Manual selection required
                action_combo = QComboBox()
                action_combo.addItem("Select Account...")
                action_combo.addItems(self.chart_of_accounts)
                action_combo.currentTextChanged.connect(
                    lambda text, acc=imported_account: self._handle_mapping_change(acc, text)
                )
                self.mapping_table.setCellWidget(row, 3, action_combo)
        
        self.mapping_table.resizeColumnsToContents()
    
    def _handle_mapping_change(self, imported_account, selected_text):
        """Handle manual mapping changes."""
        if selected_text in self.chart_of_accounts:
            self.final_mappings[imported_account] = selected_text
        elif selected_text == "Manual Select":
            # Could implement a more detailed selection dialog here
            pass
    
    def _prepare_data_preview(self):
        """Prepare the data preview with final mappings."""
        if self.imported_data is None or not hasattr(self, 'final_mappings'):
            return
        
        # Apply mappings to the data
        preview_data = self.imported_data.copy()
        
        # Map debit accounts
        preview_data['Debit Account'] = preview_data['Debit Account'].map(
            lambda x: self.final_mappings.get(str(x), str(x))
        )
        
        # Map credit accounts  
        preview_data['Credit Account'] = preview_data['Credit Account'].map(
            lambda x: self.final_mappings.get(str(x), str(x))
        )
        
        # Update preview table
        self.preview_table.setRowCount(len(preview_data))
        
        for i, row in preview_data.iterrows():
            self.preview_table.setItem(i, 0, QTableWidgetItem(str(row.get('Date', ''))))
            self.preview_table.setItem(i, 1, QTableWidgetItem(str(row.get('Description', ''))))
            self.preview_table.setItem(i, 2, QTableWidgetItem(str(row.get('Debit Account', ''))))
            self.preview_table.setItem(i, 3, QTableWidgetItem(str(row.get('Credit Account', ''))))
            self.preview_table.setItem(i, 4, QTableWidgetItem(str(row.get('Amount', ''))))
        
        self.preview_table.resizeColumnsToContents()
        
        # Enable the preview tab
        self.tab_widget.setTabEnabled(2, True)
        
        self.status_label.setText(f"Preview ready. {len(preview_data)} transactions to import.")
    
    def _import_transactions(self):
        """Import the transactions with mapped accounts."""
        if self.imported_data is None:
            return
        
        try:
            # Apply final mappings and create import data
            import_data = []
            skipped_rows = 0
            
            for i, row in self.imported_data.iterrows():
                # Map accounts
                debit_account = self.final_mappings.get(str(row.get('Debit Account', '')), str(row.get('Debit Account', '')))
                credit_account = self.final_mappings.get(str(row.get('Credit Account', '')), str(row.get('Credit Account', '')))
                
                # Validate data
                date = str(row.get('Date', ''))
                description = str(row.get('Description', ''))
                amount = str(row.get('Amount', ''))
                
                if self.skip_invalid.isChecked():
                    # Skip if essential data is missing
                    if not all([date, description, debit_account, credit_account, amount]):
                        skipped_rows += 1
                        continue
                    
                    # Validate amount if option is enabled
                    if self.validate_amounts.isChecked():
                        try:
                            float(amount)
                        except ValueError:
                            skipped_rows += 1
                            continue
                
                import_data.append({
                    'date': date,
                    'description': description,
                    'debit_account': debit_account,
                    'credit_account': credit_account,
                    'amount': amount
                })
            
            # Return the processed data
            self.processed_data = import_data
            self.skipped_count = skipped_rows
            
            self.accept()  # Close dialog with success
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to process import data: {str(e)}")
    
    def get_import_data(self):
        """Get the processed import data."""
        return getattr(self, 'processed_data', [])
    
    def get_import_summary(self):
        """Get import summary statistics."""
        return {
            'total_processed': len(getattr(self, 'processed_data', [])),
            'skipped_rows': getattr(self, 'skipped_count', 0),
            'mappings_used': len(getattr(self, 'final_mappings', {}))
        }
