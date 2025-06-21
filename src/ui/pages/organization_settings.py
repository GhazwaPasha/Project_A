"""
Organization settings page for managing organization-specific configuration
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QLineEdit, QComboBox, QTextEdit, QDateEdit, QCheckBox,
                            QGroupBox, QFormLayout, QTabWidget, QFrame, QMessageBox,
                            QFileDialog, QProgressBar)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QPixmap, QIcon
from ..common import ResponsiveHelper
from ..components.widgets import PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect


class OrganizationSettingsPage(QWidget):
    """Organization settings page for managing organization configuration"""
    
    settings_updated = pyqtSignal(dict)  # Emits when settings are updated
    
    def __init__(self, system, auth_manager=None, parent=None):
        super().__init__(parent)
        self.system = system
        self.auth_manager = auth_manager
        self.current_organization = None
        self.unsaved_changes = False
        self._setup_ui()
        self._apply_styling()
        self._load_organization_data()
        
    def _setup_ui(self):
        """Setup the organization settings UI"""
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(24, 20, 32))
        
        # Page header with save button
        header_layout = QHBoxLayout()
        
        header = PageHeader("Organization Settings", "Manage your organization's configuration and preferences")
        header_layout.addWidget(header)
        
        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        
        self.save_btn = QPushButton("Save Changes")
        self.save_btn.setObjectName("PrimaryButton")
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setEnabled(False)
        save_layout.addWidget(self.save_btn)
        
        header_layout.addLayout(save_layout)
        main_layout.addLayout(header_layout)
        
        # Tabs for different settings categories
        self.tabs = QTabWidget()
        self.tabs.setObjectName("SettingsTabs")
        
        # General settings tab
        self._create_general_tab()
        
        # Financial settings tab
        self._create_financial_tab()
        
        # User & Access tab
        self._create_access_tab()
        
        # Billing & Subscription tab
        self._create_billing_tab()
        
        main_layout.addWidget(self.tabs)
        main_layout.addStretch()
        
    def _create_general_tab(self):
        """Create the general settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Organization Identity Group
        identity_group = QGroupBox("Organization Identity")
        identity_layout = QFormLayout(identity_group)
        
        self.org_name_input = QLineEdit()
        self.org_name_input.textChanged.connect(self._mark_unsaved)
        identity_layout.addRow("Organization Name:", self.org_name_input)
        
        self.org_slug_input = QLineEdit()
        self.org_slug_input.textChanged.connect(self._mark_unsaved)
        identity_layout.addRow("Slug (URL identifier):", self.org_slug_input)
        
        self.org_description_input = QTextEdit()
        self.org_description_input.setMaximumHeight(80)
        self.org_description_input.textChanged.connect(self._mark_unsaved)
        identity_layout.addRow("Description:", self.org_description_input)
        
        self.industry_combo = QComboBox()
        self.industry_combo.addItems([
            "Technology", "Healthcare", "Finance", "Manufacturing", 
            "Retail", "Education", "Consulting", "Real Estate", "Other"
        ])
        self.industry_combo.currentTextChanged.connect(self._mark_unsaved)
        identity_layout.addRow("Industry:", self.industry_combo)
        
        layout.addWidget(identity_group)
        
        # Logo and Branding Group
        branding_group = QGroupBox("Branding")
        branding_layout = QVBoxLayout(branding_group)
        
        logo_layout = QHBoxLayout()
        self.logo_label = QLabel()
        self.logo_label.setFixedSize(80, 80)
        self.logo_label.setStyleSheet("""
            QLabel {
                border: 2px dashed rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setText("No Logo")
        logo_layout.addWidget(self.logo_label)
        
        logo_buttons_layout = QVBoxLayout()
        self.upload_logo_btn = QPushButton("Upload Logo")
        self.upload_logo_btn.clicked.connect(self._upload_logo)
        logo_buttons_layout.addWidget(self.upload_logo_btn)
        
        self.remove_logo_btn = QPushButton("Remove Logo")
        self.remove_logo_btn.clicked.connect(self._remove_logo)
        logo_buttons_layout.addWidget(self.remove_logo_btn)
        logo_buttons_layout.addStretch()
        
        logo_layout.addLayout(logo_buttons_layout)
        logo_layout.addStretch()
        branding_layout.addLayout(logo_layout)
        
        layout.addWidget(branding_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "General")
        
    def _create_financial_tab(self):
        """Create the financial settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Currency Settings Group
        currency_group = QGroupBox("Currency Settings")
        currency_layout = QFormLayout(currency_group)
        
        self.base_currency_combo = QComboBox()
        self.base_currency_combo.addItems([
            "USD - US Dollar", "EUR - Euro", "GBP - British Pound", 
            "JPY - Japanese Yen", "CAD - Canadian Dollar", "AUD - Australian Dollar",
            "CHF - Swiss Franc", "CNY - Chinese Yuan"
        ])
        self.base_currency_combo.currentTextChanged.connect(self._mark_unsaved)
        currency_layout.addRow("Base Currency:", self.base_currency_combo)
        
        self.multi_currency_check = QCheckBox("Enable multi-currency support")
        self.multi_currency_check.stateChanged.connect(self._mark_unsaved)
        currency_layout.addRow("", self.multi_currency_check)
        
        layout.addWidget(currency_group)
        
        # Fiscal Year Settings Group
        fiscal_group = QGroupBox("Fiscal Year Settings")
        fiscal_layout = QFormLayout(fiscal_group)
        
        self.fiscal_year_start = QDateEdit()
        self.fiscal_year_start.setDate(QDate(2024, 1, 1))
        self.fiscal_year_start.setDisplayFormat("MMMM dd")
        self.fiscal_year_start.dateChanged.connect(self._mark_unsaved)
        fiscal_layout.addRow("Fiscal Year Start:", self.fiscal_year_start)
        
        layout.addWidget(fiscal_group)
        
        # Tax Settings Group
        tax_group = QGroupBox("Tax Settings")
        tax_layout = QFormLayout(tax_group)
        
        self.tax_enabled_check = QCheckBox("Enable tax tracking")
        self.tax_enabled_check.setChecked(True)
        self.tax_enabled_check.stateChanged.connect(self._mark_unsaved)
        tax_layout.addRow("", self.tax_enabled_check)
        
        self.default_tax_rate = QLineEdit()
        self.default_tax_rate.setPlaceholderText("e.g., 8.5")
        self.default_tax_rate.textChanged.connect(self._mark_unsaved)
        tax_layout.addRow("Default Tax Rate (%):", self.default_tax_rate)
        
        layout.addWidget(tax_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Financial")
        
    def _create_access_tab(self):
        """Create the user access settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Access Control Group
        access_group = QGroupBox("Access Control")
        access_layout = QFormLayout(access_group)
        
        self.require_approval_check = QCheckBox("Require admin approval for new members")
        self.require_approval_check.stateChanged.connect(self._mark_unsaved)
        access_layout.addRow("", self.require_approval_check)
        
        self.invitation_expiry_combo = QComboBox()
        self.invitation_expiry_combo.addItems([
            "1 day", "3 days", "7 days", "14 days", "30 days"
        ])
        self.invitation_expiry_combo.setCurrentText("7 days")
        self.invitation_expiry_combo.currentTextChanged.connect(self._mark_unsaved)
        access_layout.addRow("Invitation Expiry:", self.invitation_expiry_combo)
        
        layout.addWidget(access_group)
        
        # Security Settings Group
        security_group = QGroupBox("Security Settings")
        security_layout = QFormLayout(security_group)
        
        self.force_2fa_check = QCheckBox("Require two-factor authentication")
        self.force_2fa_check.stateChanged.connect(self._mark_unsaved)
        security_layout.addRow("", self.force_2fa_check)
        
        self.session_timeout_combo = QComboBox()
        self.session_timeout_combo.addItems([
            "1 hour", "4 hours", "8 hours", "24 hours", "Never"
        ])
        self.session_timeout_combo.setCurrentText("8 hours")
        self.session_timeout_combo.currentTextChanged.connect(self._mark_unsaved)
        security_layout.addRow("Session Timeout:", self.session_timeout_combo)
        
        layout.addWidget(security_group)
        
        # Audit Settings Group
        audit_group = QGroupBox("Audit & Compliance")
        audit_layout = QFormLayout(audit_group)
        
        self.audit_trail_check = QCheckBox("Enable detailed audit trail")
        self.audit_trail_check.setChecked(True)
        self.audit_trail_check.stateChanged.connect(self._mark_unsaved)
        audit_layout.addRow("", self.audit_trail_check)
        
        self.data_retention_combo = QComboBox()
        self.data_retention_combo.addItems([
            "1 year", "3 years", "5 years", "7 years", "Forever"
        ])
        self.data_retention_combo.setCurrentText("7 years")
        self.data_retention_combo.currentTextChanged.connect(self._mark_unsaved)
        audit_layout.addRow("Data Retention:", self.data_retention_combo)
        
        layout.addWidget(audit_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Access & Security")
        
    def _create_billing_tab(self):
        """Create the billing and subscription tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Current Plan Group
        plan_group = QGroupBox("Current Subscription")
        plan_layout = QVBoxLayout(plan_group)
        
        plan_info_layout = QHBoxLayout()
        
        plan_details = QVBoxLayout()
        self.current_plan_label = QLabel("Basic Plan")
        self.current_plan_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(16, 14, 18)}px;
                font-weight: 600;
            }}
        """)
        plan_details.addWidget(self.current_plan_label)
        
        self.plan_status_label = QLabel("Active • Next billing: Jan 15, 2025")
        self.plan_status_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        plan_details.addWidget(self.plan_status_label)
        
        self.plan_price_label = QLabel("$29/month")
        self.plan_price_label.setStyleSheet(f"""
            QLabel {{
                color: #4CAF50;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                font-weight: 600;
                margin-top: 4px;
            }}
        """)
        plan_details.addWidget(self.plan_price_label)
        
        plan_info_layout.addLayout(plan_details)
        plan_info_layout.addStretch()
        
        upgrade_btn = QPushButton("Upgrade Plan")
        upgrade_btn.setObjectName("PrimaryButton")
        upgrade_btn.clicked.connect(self._show_upgrade_dialog)
        plan_info_layout.addWidget(upgrade_btn)
        
        plan_layout.addLayout(plan_info_layout)
        layout.addWidget(plan_group)
        
        # Usage Statistics Group
        usage_group = QGroupBox("Usage Statistics")
        usage_layout = QFormLayout(usage_group)
        
        # Users usage
        users_layout = QHBoxLayout()
        self.users_progress = QProgressBar()
        self.users_progress.setMaximum(10)
        self.users_progress.setValue(3)
        self.users_progress.setTextVisible(True)
        self.users_progress.setFormat("3 / 10 users")
        users_layout.addWidget(self.users_progress)
        usage_layout.addRow("Team Members:", users_layout)
        
        # Storage usage
        storage_layout = QHBoxLayout()
        self.storage_progress = QProgressBar()
        self.storage_progress.setMaximum(1000)  # 1GB in MB
        self.storage_progress.setValue(150)  # 150MB used
        self.storage_progress.setTextVisible(True)
        self.storage_progress.setFormat("150 MB / 1 GB")
        storage_layout.addWidget(self.storage_progress)
        usage_layout.addRow("Storage Used:", storage_layout)
        
        # Transactions usage
        transactions_layout = QHBoxLayout()
        self.transactions_progress = QProgressBar()
        self.transactions_progress.setMaximum(1000)
        self.transactions_progress.setValue(450)
        self.transactions_progress.setTextVisible(True)
        self.transactions_progress.setFormat("450 / 1,000 transactions")
        transactions_layout.addWidget(self.transactions_progress)
        usage_layout.addRow("Monthly Transactions:", transactions_layout)
        
        layout.addWidget(usage_group)
        
        # Billing History Group
        history_group = QGroupBox("Billing Actions")
        history_layout = QHBoxLayout(history_group)
        
        download_invoice_btn = QPushButton("Download Invoice")
        download_invoice_btn.clicked.connect(self._download_invoice)
        history_layout.addWidget(download_invoice_btn)
        
        update_payment_btn = QPushButton("Update Payment Method")
        update_payment_btn.clicked.connect(self._update_payment_method)
        history_layout.addWidget(update_payment_btn)
        
        history_layout.addStretch()
        
        layout.addWidget(history_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Billing")
        
    def _apply_styling(self):
        """Apply styling to the organization settings page"""
        MicaEffect.apply_mica(self, dark_mode=True)
        GlassmorphismHelper.apply_main_container_effect(self)
        
        self.setStyleSheet(f"""
            QTabWidget#SettingsTabs {{
                background: transparent;
                border: none;
            }}
            
            QTabWidget#SettingsTabs::pane {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                top: -1px;
            }}
            
            QTabWidget#SettingsTabs::tab-bar {{
                alignment: left;
            }}
            
            QTabBar::tab {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: white;
                padding: 12px 24px;
                margin-right: 4px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
            }}
            
            QTabBar::tab:selected {{
                background: rgba(74, 144, 226, 0.3);
                border-bottom: 2px solid rgba(74, 144, 226, 1.0);
            }}
            
            QTabBar::tab:hover:!selected {{
                background: rgba(255, 255, 255, 0.1);
            }}
            
            QGroupBox {{
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: 600;
                font-size: {ResponsiveHelper.scale_size(14, 13, 15)}px;
            }}
            
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 8px 0 8px;
                background: rgba(30, 30, 30, 0.8);
            }}
            
            QLineEdit, QTextEdit, QComboBox, QDateEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                padding: 8px 12px;
                min-height: 20px;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid rgba(74, 144, 226, 0.8);
            }}
            
            QCheckBox {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
            }}
            
            QCheckBox::indicator {{
                width: 16px;
                height: 16px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.1);
            }}
            
            QCheckBox::indicator:checked {{
                background: rgba(74, 144, 226, 0.8);
                border: 2px solid rgba(74, 144, 226, 1.0);
            }}
            
            QProgressBar {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                text-align: center;
                color: white;
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
                height: 20px;
            }}
            
            QProgressBar::chunk {{
                background: rgba(74, 144, 226, 0.8);
                border-radius: 5px;
            }}
            
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                padding: 8px 16px;
                min-width: 80px;
            }}
            
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            
            QPushButton#PrimaryButton {{
                background: rgba(74, 144, 226, 0.8);
                border: 1px solid rgba(74, 144, 226, 1.0);
            }}
            
            QPushButton#PrimaryButton:hover {{
                background: rgba(74, 144, 226, 1.0);
            }}
            
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.3);
                border: 1px solid rgba(255, 255, 255, 0.1);
            }}
        """)
        
    def _load_organization_data(self):
        """Load organization data from the database"""
        try:
            if not self.auth_manager or not hasattr(self.auth_manager, 'user_organizations'):
                return
                
            if self.auth_manager.user_organizations:
                self.current_organization = self.auth_manager.user_organizations[0]
                self._populate_form_data()
                
        except Exception as e:
            print(f"Error loading organization data: {e}")
            
    def _populate_form_data(self):
        """Populate form fields with organization data"""
        if not self.current_organization:
            return
            
        # General tab
        self.org_name_input.setText(self.current_organization.get('name', ''))
        self.org_slug_input.setText(self.current_organization.get('slug', ''))
        self.org_description_input.setPlainText(self.current_organization.get('description', ''))
        
        industry = self.current_organization.get('industry', 'Other')
        index = self.industry_combo.findText(industry)
        if index >= 0:
            self.industry_combo.setCurrentIndex(index)
            
        # Financial tab
        base_currency = self.current_organization.get('base_currency', 'USD')
        for i in range(self.base_currency_combo.count()):
            if self.base_currency_combo.itemText(i).startswith(base_currency):
                self.base_currency_combo.setCurrentIndex(i)
                break
                
        settings = self.current_organization.get('settings', {})
        self.multi_currency_check.setChecked(settings.get('multi_currency', False))
        self.tax_enabled_check.setChecked(settings.get('tax_enabled', True))
        self.audit_trail_check.setChecked(settings.get('audit_trail', True))
        
        # Set fiscal year start if available
        fiscal_start = self.current_organization.get('fiscal_year_start')
        if fiscal_start:
            try:
                from datetime import datetime
                date = datetime.strptime(fiscal_start, '%m-%d').date()
                self.fiscal_year_start.setDate(QDate(2024, date.month, date.day))
            except:
                pass
                
        # Reset unsaved changes flag
        self.unsaved_changes = False
        self.save_btn.setEnabled(False)
        
    def _mark_unsaved(self):
        """Mark that there are unsaved changes"""
        self.unsaved_changes = True
        self.save_btn.setEnabled(True)
        
    def _save_settings(self):
        """Save organization settings"""
        try:
            if not self.current_organization:
                QMessageBox.warning(self, "Error", "No organization selected.")
                return
                
            # Collect form data
            settings_data = {
                'name': self.org_name_input.text().strip(),
                'slug': self.org_slug_input.text().strip(),
                'description': self.org_description_input.toPlainText().strip(),
                'industry': self.industry_combo.currentText(),
                'base_currency': self.base_currency_combo.currentText().split(' - ')[0],
                'fiscal_year_start': self.fiscal_year_start.date().toString('MM-dd'),
                'settings': {
                    'multi_currency': self.multi_currency_check.isChecked(),
                    'tax_enabled': self.tax_enabled_check.isChecked(),
                    'audit_trail': self.audit_trail_check.isChecked()
                }
            }
            
            # Update organization in database
            if self.auth_manager and hasattr(self.auth_manager, 'supabase'):
                self.auth_manager.supabase.table('organizations').update(settings_data).eq(
                    'id', self.current_organization['id']
                ).execute()
                
                QMessageBox.information(self, "Success", "Organization settings saved successfully.")
                self.unsaved_changes = False
                self.save_btn.setEnabled(False)
                self.settings_updated.emit(settings_data)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
            
    def _upload_logo(self):
        """Upload organization logo"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Logo", "", 
            "Image Files (*.png *.jpg *.jpeg *.svg *.gif)"
        )
        
        if file_path:
            try:
                # Load and display the image
                pixmap = QPixmap(file_path)
                if not pixmap.isNull():
                    # Scale the image to fit the label
                    scaled_pixmap = pixmap.scaled(
                        self.logo_label.size(), 
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.logo_label.setPixmap(scaled_pixmap)
                    self.logo_label.setText("")
                    self._mark_unsaved()
                    
                    # TODO: Upload to storage service and save URL to organization
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load logo: {str(e)}")
                
    def _remove_logo(self):
        """Remove organization logo"""
        self.logo_label.clear()
        self.logo_label.setText("No Logo")
        self._mark_unsaved()
        
    def _show_upgrade_dialog(self):
        """Show plan upgrade dialog"""
        QMessageBox.information(self, "Upgrade Plan", "Plan upgrade functionality - to be implemented")
        
    def _download_invoice(self):
        """Download billing invoice"""
        QMessageBox.information(self, "Download Invoice", "Invoice download - to be implemented")
        
    def _update_payment_method(self):
        """Update payment method"""
        QMessageBox.information(self, "Update Payment", "Payment method update - to be implemented")
        
    def closeEvent(self, event):
        """Handle close event with unsaved changes check"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save them before closing?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._save_settings()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
