"""
Shared dialog components for the accounting application.
This module contains reusable dialog classes used across different pages.
"""

from ..common import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QDialog, QLineEdit, QComboBox,
    QDateEdit, QCompleter, QAbstractScrollArea, Qt, QDate, QStringListModel, QIcon,
    ResponsiveHelper, MODERN_BUTTON_STYLE, MODERN_TABLE_STYLE, MODERN_FRAME_STYLE
)
from PyQt6.QtWidgets import QAbstractItemView, QGraphicsDropShadowEffect, QTextBrowser, QTextBrowser, QScrollArea


class ModernAccountDialog(QDialog):
    """Modern styled dialog for adding/editing accounts with responsive design."""
    
    def __init__(self, parent=None, system=None, edit_mode=False, account_data=None):
        super().__init__(parent)
        self.system = system
        self.edit_mode = edit_mode
        
        if edit_mode and account_data:
            self.setWindowTitle("Edit Account")
            self.original_name = account_data[0]
            self.original_type = account_data[1]
            self.original_code = account_data[2] if len(account_data) > 2 else ""
            self.original_parent = account_data[3] if len(account_data) > 3 else ""
        else:
            self.setWindowTitle("Add New Account")
            self.original_name = ""
            self.original_type = ""
            self.original_code = ""
            self.original_parent = ""
            
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the dialog UI."""
        # Responsive dialog sizing
        dialog_width = ResponsiveHelper.scale_size(400, 320, 480)
        dialog_height = ResponsiveHelper.scale_size(430, 380, 460)
        self.setFixedSize(dialog_width, dialog_height)
        self.setModal(True)
        
        # Main layout with responsive margins and spacing
        layout = QVBoxLayout(self)
        margins = ResponsiveHelper.scale_size(32, 24, 40)
        layout.setContentsMargins(margins, 
                                 ResponsiveHelper.scale_size(24, 18, 30), 
                                 margins, 
                                 ResponsiveHelper.scale_size(24, 18, 30))
        layout.setSpacing(ResponsiveHelper.scale_size(20, 15, 25))
        
        self._create_form_fields(layout)
        self._create_buttons(layout)
        self._apply_styling()
        
    def _create_form_fields(self, layout):
        """Create form input fields."""
        # Title
        title_text = "Edit Account" if self.edit_mode else "Add New Account"
        title = QLabel(title_text)
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(20, 16, 24)}px;
                font-weight: 600;
                background: transparent;
                margin-bottom: {ResponsiveHelper.scale_size(8, 6, 10)}px;
            }}
        """)
        layout.addWidget(title)
        
        # Account code input
        self._create_code_field(layout)
        
        # Account name input
        self._create_name_field(layout)
        
        # Account type selection
        self._create_type_field(layout)
        
        # Parent account selection
        self._create_parent_field(layout)
        
    def _create_code_field(self, layout):
        """Create account code input field."""
        code_label = QLabel("Account Code:")
        code_label.setStyleSheet(self._get_label_style())
        layout.addWidget(code_label)
        
        self.code_edit = QLineEdit()
        self.code_edit.setPlaceholderText("4-digit code (e.g. 1000)")
        self.code_edit.setMaxLength(4)
        
        if self.edit_mode and self.original_code:
            self.code_edit.setText(self.original_code)
            
        self.code_edit.setStyleSheet(self._get_input_style())
        layout.addWidget(self.code_edit)
        
        # Note about auto-generation
        code_note = QLabel("Leave blank for auto-generated code based on account type.")
        code_note.setStyleSheet(self._get_note_style())
        layout.addWidget(code_note)
        
    def _create_name_field(self, layout):
        """Create account name input field."""
        name_label = QLabel("Account Name:")
        name_label.setStyleSheet(self._get_label_style())
        layout.addWidget(name_label)
        
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Enter account name")
        
        if self.edit_mode:
            self.name_edit.setText(self.original_name)
            
        self.name_edit.setStyleSheet(self._get_input_style())
        layout.addWidget(self.name_edit)
        
    def _create_type_field(self, layout):
        """Create account type selection field."""
        type_label = QLabel("Account Type:")
        type_label.setStyleSheet(self._get_label_style())
        layout.addWidget(type_label)
        
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Asset", "Liability", "Equity", "Revenue", "Expense"])
        
        if self.edit_mode:
            type_index = self.type_combo.findText(self.original_type)
            if type_index >= 0:
                self.type_combo.setCurrentIndex(type_index)
                
        self.type_combo.setStyleSheet(self._get_combo_style())
        layout.addWidget(self.type_combo)
        
    def _create_parent_field(self, layout):
        """Create parent account selection field."""
        parent_label = QLabel("Parent Account (Optional):")
        parent_label.setStyleSheet(self._get_label_style())
        layout.addWidget(parent_label)
        
        self.parent_combo = QComboBox()
        self.parent_combo.addItem("None")
        
        # Populate with existing accounts
        if self.system:
            accounts = self.system.get_chart_of_accounts(active_only=False)
            for account in accounts:
                account_name = account['name']
                if not self.edit_mode or account_name != self.original_name:
                    self.parent_combo.addItem(account_name)
        
        if self.edit_mode and self.original_parent:
            parent_index = self.parent_combo.findText(self.original_parent)
            if parent_index >= 0:
                self.parent_combo.setCurrentIndex(parent_index)
                
        self.parent_combo.setStyleSheet(self._get_combo_style())
        layout.addWidget(self.parent_combo)
        
    def _create_buttons(self, layout):
        """Create dialog buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(ResponsiveHelper.scale_size(16, 12, 20))
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(MODERN_BUTTON_STYLE)
        
        # Save button
        button_text = "Update Account" if self.edit_mode else "Add Account"
        save_button = QPushButton(button_text)
        save_button.clicked.connect(self._save_account)
        save_button.setStyleSheet(MODERN_BUTTON_STYLE)
        save_button.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
    def _save_account(self):
        """Save the account data."""
        name = self.name_edit.text().strip()
        account_type = self.type_combo.currentText()
        code = self.code_edit.text().strip()
        parent = self.parent_combo.currentText()
        
        if parent == "None":
            parent = None
            
        if not name:
            self._show_error("Account name is required.")
            return
            
        try:
            if self.edit_mode:
                # Update existing account
                self.system.update_account(self.original_name, name, account_type, code, parent)
            else:
                # Add new account
                self.system.add_account(name, account_type, code, parent)
            self.accept()
        except Exception as e:
            self._show_error(f"Error saving account: {str(e)}")
            
    def _show_error(self, message):
        """Show error message."""
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.exec()
        
    def _get_label_style(self):
        """Get label styling."""
        return f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                font-weight: 500;
                background: transparent;
            }}
        """
        
    def _get_input_style(self):
        """Get input field styling."""
        input_padding = ResponsiveHelper.scale_size(12, 8, 16)
        input_font_size = ResponsiveHelper.scale_size(14, 12, 16)
        return f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: {input_padding}px 16px;
                color: white;
                font-size: {input_font_size}px;
                outline: none;
            }}
            QLineEdit:focus {{
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.4);
                outline: none;
            }}
            QLineEdit::placeholder {{
                color: rgba(255, 255, 255, 0.5);
            }}
        """
        
    def _get_combo_style(self):
        """Get combo box styling."""
        input_padding = ResponsiveHelper.scale_size(12, 8, 16)
        input_font_size = ResponsiveHelper.scale_size(14, 12, 16)
        return f"""
            QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: {input_padding}px 16px;
                color: white;
                font-size: {input_font_size}px;
                outline: none;
            }}
            QComboBox:focus {{
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.4);
                outline: none;
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox::down-arrow {{
                width: 12px;
                height: 12px;
            }}
        """
        
    def _get_note_style(self):
        """Get note text styling."""
        return f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.6);
                font-size: {ResponsiveHelper.scale_size(12, 10, 14)}px;
                font-style: italic;
                background: transparent;
                margin-bottom: {ResponsiveHelper.scale_size(8, 6, 10)}px;
            }}
        """
        
    def _apply_styling(self):
        """Apply dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(20, 25, 35, 0.95),
                    stop:1 rgba(25, 30, 40, 0.95));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
        """)


class JournalEntryDialog(QDialog):
    """Modern styled dialog for adding journal entries."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.setWindowTitle("New Journal Entry")
        self.setFixedSize(500, 600)
        self.setModal(True)
        self._setup_ui()
        
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Title
        title = QLabel("New Journal Entry")
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title)
        
        # Date field
        self._create_date_field(layout)
        
        # Description field
        self._create_description_field(layout)
        
        # Amount field
        self._create_amount_field(layout)
        
        # Account fields
        self._create_account_fields(layout)
        
        # Buttons
        self._create_buttons(layout)
        
        self._apply_styling()
        
    def _create_date_field(self, layout):
        """Create date input field."""
        date_label = QLabel("Date:")
        date_label.setStyleSheet(self._get_label_style())
        layout.addWidget(date_label)
        
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setStyleSheet(self._get_input_style())
        layout.addWidget(self.date_edit)
        
    def _create_description_field(self, layout):
        """Create description input field."""
        desc_label = QLabel("Description:")
        desc_label.setStyleSheet(self._get_label_style())
        layout.addWidget(desc_label)
        
        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Enter transaction description")
        self.description_edit.setStyleSheet(self._get_input_style())
        layout.addWidget(self.description_edit)
        
    def _create_amount_field(self, layout):
        """Create amount input field."""
        amount_label = QLabel("Amount:")
        amount_label.setStyleSheet(self._get_label_style())
        layout.addWidget(amount_label)
        
        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("0.00")
        self.amount_edit.setStyleSheet(self._get_input_style())
        layout.addWidget(self.amount_edit)
        
    def _create_account_fields(self, layout):
        """Create debit and credit account fields."""
        # Debit account
        debit_label = QLabel("Debit Account:")
        debit_label.setStyleSheet(self._get_label_style())
        layout.addWidget(debit_label)
        
        self.debit_combo = QComboBox()
        self._populate_accounts(self.debit_combo)
        self.debit_combo.setStyleSheet(self._get_combo_style())
        layout.addWidget(self.debit_combo)
        
        # Credit account
        credit_label = QLabel("Credit Account:")
        credit_label.setStyleSheet(self._get_label_style())
        layout.addWidget(credit_label)
        
        self.credit_combo = QComboBox()
        self._populate_accounts(self.credit_combo)
        self.credit_combo.setStyleSheet(self._get_combo_style())
        layout.addWidget(self.credit_combo)
        
    def _populate_accounts(self, combo):
        """Populate combo box with accounts."""
        if self.system:
            accounts = self.system.get_chart_of_accounts(active_only=False)
            for account in accounts:
                combo.addItem(account['name'])
                
    def _create_buttons(self, layout):
        """Create dialog buttons."""
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet(MODERN_BUTTON_STYLE)
        
        save_button = QPushButton("Add Entry")
        save_button.clicked.connect(self._save_entry)
        save_button.setStyleSheet(MODERN_BUTTON_STYLE)
        save_button.setDefault(True)
        
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(save_button)
        
        layout.addLayout(button_layout)
        
    def _save_entry(self):
        """Save the journal entry."""
        try:
            date = self.date_edit.date().toString("yyyy-MM-dd")
            description = self.description_edit.text().strip()
            amount = float(self.amount_edit.text())
            debit_account = self.debit_combo.currentText()
            credit_account = self.credit_combo.currentText()
            
            if not description:
                raise ValueError("Description is required")
            if amount <= 0:
                raise ValueError("Amount must be positive")
            if debit_account == credit_account:
                raise ValueError("Debit and credit accounts must be different")
                
            entry_data = {
                'date': date,
                'description': description,
                'debit_account': debit_account,
                'credit_account': credit_account,
                'amount': amount
            }
            self.system.add_journal_entry(entry_data)
            self.accept()
            
        except ValueError as e:
            self._show_error(str(e))
        except Exception as e:
            self._show_error(f"Error saving entry: {str(e)}")
            
    def _show_error(self, message):
        """Show error message."""
        from PyQt6.QtWidgets import QMessageBox
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Error")
        msg.setText(message)
        msg.exec()
        
    def _get_label_style(self):
        """Get label styling."""
        return """
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                font-size: 14px;
                font-weight: 500;
                background: transparent;
            }
        """
        
    def _get_input_style(self):
        """Get input field styling."""
        return """
            QLineEdit, QDateEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px 16px;
                color: white;
                font-size: 14px;
                outline: none;
            }
            QLineEdit:focus, QDateEdit:focus {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.4);
                outline: none;
            }
        """
        
    def _get_combo_style(self):
        """Get combo box styling."""
        return """
            QComboBox {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 12px 16px;
                color: white;
                font-size: 14px;
                outline: none;
            }
            QComboBox:focus {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.4);
                outline: none;
            }
        """
        
    def _apply_styling(self):
        """Apply dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(20, 25, 35, 0.95),
                    stop:1 rgba(25, 30, 40, 0.95));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
        """)
        

class ReportViewerDialog(QDialog):
    """Modern dialog for viewing generated reports with HTML content."""
    
    def __init__(self, title, content, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.content = content
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the report viewer UI."""
        # Responsive dialog sizing - larger for reports
        dialog_width = ResponsiveHelper.scale_size(800, 600, 1000)
        dialog_height = ResponsiveHelper.scale_size(600, 450, 750)
        self.resize(dialog_width, dialog_height)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        margins = ResponsiveHelper.scale_size(24, 18, 32)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(ResponsiveHelper.scale_size(16, 12, 20))
        
        # Report content viewer
        self.content_viewer = QTextBrowser()
        self.content_viewer.setHtml(self.content)
        self.content_viewer.setStyleSheet("""
            QTextBrowser {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 16px;
                color: #333;
                font-size: 12px;
                line-height: 1.4;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
        """)
        layout.addWidget(self.content_viewer)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Print button
        print_btn = QPushButton("Print")
        print_btn.setStyleSheet(MODERN_BUTTON_STYLE)
        print_btn.clicked.connect(self._print_report)
        button_layout.addWidget(print_btn)
        
        # Export button
        export_btn = QPushButton("Export")
        export_btn.setStyleSheet(MODERN_BUTTON_STYLE)
        export_btn.clicked.connect(self._export_report)
        button_layout.addWidget(export_btn)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet(MODERN_BUTTON_STYLE)
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def _print_report(self):
        """Print the report."""
        from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
        from PyQt6.QtGui import QTextDocument
        
        printer = QPrinter()
        print_dialog = QPrintDialog(printer, self)
        
        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            document = QTextDocument()
            document.setHtml(self.content)
            document.print(printer)
            
    def _export_report(self):
        """Export the report to file."""
        from PyQt6.QtWidgets import QFileDialog
        from PyQt6.QtCore import QStandardPaths
        
        # Get save file path
        default_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Report",
            f"{default_path}/report.html",
            "HTML Files (*.html);;PDF Files (*.pdf);;All Files (*)"
        )
        
        if file_path:
            if file_path.lower().endswith('.html'):
                # Save as HTML
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.content)
            elif file_path.lower().endswith('.pdf'):
                # Save as PDF
                from PyQt6.QtPrintSupport import QPrinter
                from PyQt6.QtGui import QTextDocument
                
                printer = QPrinter()
                printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
                printer.setOutputFileName(file_path)
                
                document = QTextDocument()
                document.setHtml(self.content)
                document.print(printer)
                
    def _apply_styling(self):
        """Apply dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(20, 25, 35, 0.95),
                    stop:1 rgba(25, 30, 40, 0.95));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
        """)


class CustomReportBuilderDialog(QDialog):
    """Dialog for building custom reports with account selection."""
    
    def __init__(self, system, parent=None):
        super().__init__(parent)
        self.system = system
        self.setWindowTitle("Custom Report Builder")
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the custom report builder UI."""
        # Responsive dialog sizing
        dialog_width = ResponsiveHelper.scale_size(600, 480, 720)
        dialog_height = ResponsiveHelper.scale_size(500, 400, 600)
        self.resize(dialog_width, dialog_height)
        self.setModal(True)
        
        # Main layout
        layout = QVBoxLayout(self)
        margins = ResponsiveHelper.scale_size(24, 18, 32)
        layout.setContentsMargins(margins, margins, margins, margins)
        layout.setSpacing(ResponsiveHelper.scale_size(16, 12, 20))
        
        # Title
        title = QLabel("Custom Report Builder")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(20, 16, 24)}px;
                font-weight: 600;
                background: transparent;
                margin-bottom: {ResponsiveHelper.scale_size(16, 12, 20)}px;
            }}
        """)
        layout.addWidget(title)
        
        # Report options
        options_layout = QVBoxLayout()
        
        # Report type
        type_layout = QHBoxLayout()
        type_label = QLabel("Report Type:")
        type_label.setStyleSheet(self._get_label_style())
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Account Summary", "Transaction List", "Balance Report"])
        self.type_combo.setStyleSheet(self._get_input_style())
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        type_layout.addStretch()
        options_layout.addLayout(type_layout)
        
        # Date range
        date_layout = QHBoxLayout()
        from_label = QLabel("From Date:")
        from_label.setStyleSheet(self._get_label_style())
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setStyleSheet(self._get_input_style())
        
        to_label = QLabel("To Date:")
        to_label.setStyleSheet(self._get_label_style())
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setStyleSheet(self._get_input_style())
        
        date_layout.addWidget(from_label)
        date_layout.addWidget(self.from_date)
        date_layout.addWidget(to_label)
        date_layout.addWidget(self.to_date)
        date_layout.addStretch()
        options_layout.addLayout(date_layout)
        
        layout.addLayout(options_layout)
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        generate_btn = QPushButton("Generate Report")
        generate_btn.setStyleSheet(MODERN_BUTTON_STYLE)
        generate_btn.clicked.connect(self._generate_custom_report)
        button_layout.addWidget(generate_btn)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setStyleSheet(MODERN_BUTTON_STYLE)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
    def _generate_custom_report(self):
        """Generate the custom report."""
        report_type = self.type_combo.currentText()
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        
        # Generate report content based on type
        if report_type == "Account Summary":
            content = self._generate_account_summary(from_date, to_date)
        elif report_type == "Transaction List":
            content = self._generate_transaction_list(from_date, to_date)
        else:  # Balance Report
            content = self._generate_balance_report(from_date, to_date)
        
        # Show report
        dialog = ReportViewerDialog(f"Custom {report_type}", content, self)
        dialog.exec()
        self.accept()
        
    def _generate_account_summary(self, from_date, to_date):
        """Generate account summary report."""
        balances = self.system.get_trial_balance(from_date, to_date)
        
        content = f"<h2>Account Summary ({from_date} to {to_date})</h2>"
        content += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        content += "<tr style='font-weight: bold;'><td>Account</td><td>Balance</td></tr>"
        
        for account, balance in balances.items():
            content += f"<tr><td>{account}</td><td style='text-align: right;'>${balance:,.2f}</td></tr>"
        
        content += "</table>"
        return content
        
    def _generate_transaction_list(self, from_date, to_date):
        """Generate transaction list report."""
        entries = self.system.get_journal_entries(from_date, to_date)
        
        content = f"<h2>Transaction List ({from_date} to {to_date})</h2>"
        content += "<table border='1' style='border-collapse: collapse; width: 100%;'>"
        content += "<tr style='font-weight: bold;'><td>Date</td><td>Description</td><td>Debit</td><td>Credit</td><td>Amount</td></tr>"
        
        for entry in entries:
            debit_account = entry.get('debit_account', 'N/A')
            credit_account = entry.get('credit_account', 'N/A')
            entry_date = entry.get('date', entry.get('entry_date', 'N/A'))
            description = entry.get('description', 'N/A')
            amount = entry.get('amount', 0)
            content += f"<tr><td>{entry_date}</td><td>{description}</td><td>{debit_account}</td><td>{credit_account}</td><td style='text-align: right;'>${amount:,.2f}</td></tr>"
        
        content += "</table>"
        return content
        
    def _generate_balance_report(self, from_date, to_date):
        """Generate balance report."""
        return self._generate_account_summary(from_date, to_date)  # Same as account summary for now
        
    def _get_label_style(self):
        """Get label styling."""
        return f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                font-weight: 500;
                background: transparent;
            }}
        """
        
    def _get_input_style(self):
        """Get input field styling."""
        return """
            QLineEdit, QComboBox, QDateEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                padding: 8px 12px;
                color: white;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {
                background: rgba(255, 255, 255, 0.15);
                border-color: rgba(255, 255, 255, 0.4);
            }
        """
        
    def _apply_styling(self):
        """Apply dialog styling."""
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(20, 25, 35, 0.95),
                    stop:1 rgba(25, 30, 40, 0.95));
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 16px;
            }
        """)
