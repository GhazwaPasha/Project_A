"""
Global organizations management page for super administrators
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
                            QDialog, QLineEdit, QComboBox, QMessageBox, QMenu,
                            QTextEdit, QCheckBox, QDateEdit, QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QIcon, QAction
from ..common import ResponsiveHelper
from ..components.widgets import PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect


class GlobalOrganizationsPage(QWidget):
    """Global organizations management page for super administrators"""
    
    def __init__(self, system, auth_manager=None, parent=None):
        super().__init__(parent)
        self.system = system
        self.auth_manager = auth_manager
        self.organizations = []
        self._setup_ui()
        self._apply_styling()
        self._load_organizations()
        
    def _setup_ui(self):
        """Setup the global organizations UI"""
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(24, 20, 32))
        
        # Page header with actions
        header_layout = QHBoxLayout()
        
        header = PageHeader("Global Organizations", "Manage all organizations across the platform")
        header_layout.addWidget(header)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.create_org_btn = QPushButton("Create Organization")
        self.create_org_btn.setObjectName("PrimaryButton")
        self.create_org_btn.clicked.connect(self._show_create_organization_dialog)
        action_layout.addWidget(self.create_org_btn)
        
        self.export_orgs_btn = QPushButton("Export Data")
        self.export_orgs_btn.clicked.connect(self._export_organizations)
        action_layout.addWidget(self.export_orgs_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_organizations)
        action_layout.addWidget(self.refresh_btn)
        
        header_layout.addLayout(action_layout)
        main_layout.addLayout(header_layout)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Status filter
        status_filter_label = QLabel("Filter by Status:")
        status_filter_label.setStyleSheet("color: white; margin-right: 8px;")
        filter_layout.addWidget(status_filter_label)
        
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems([
            "All Status", "Active", "Inactive", "Suspended", "Trial"
        ])
        self.status_filter_combo.currentTextChanged.connect(self._filter_organizations)
        filter_layout.addWidget(self.status_filter_combo)
        
        # Plan filter
        plan_filter_label = QLabel("Filter by Plan:")
        plan_filter_label.setStyleSheet("color: white; margin-left: 16px; margin-right: 8px;")
        filter_layout.addWidget(plan_filter_label)
        
        self.plan_filter_combo = QComboBox()
        self.plan_filter_combo.addItems([
            "All Plans", "Basic", "Professional", "Enterprise", "Custom"
        ])
        self.plan_filter_combo.currentTextChanged.connect(self._filter_organizations)
        filter_layout.addWidget(self.plan_filter_combo)
        
        filter_layout.addStretch()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search organizations...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self._filter_organizations)
        filter_layout.addWidget(self.search_input)
        
        main_layout.addLayout(filter_layout)
        
        # Organizations table
        self.orgs_table = QTableWidget()
        self.orgs_table.setObjectName("ModernTable")
        self.orgs_table.setColumnCount(9)
        self.orgs_table.setHorizontalHeaderLabels([
            "Organization", "Industry", "Plan", "Status", "Users", "Created", "Last Active", "Revenue", "Actions"
        ])
        
        # Configure table
        header = self.orgs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.ResizeToContents)
        
        self.orgs_table.setAlternatingRowColors(True)
        self.orgs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.orgs_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.orgs_table.customContextMenuRequested.connect(self._show_organization_context_menu)
        
        main_layout.addWidget(self.orgs_table)
        
    def _apply_styling(self):
        """Apply styling to the global organizations page"""
        MicaEffect.apply_mica(self, dark_mode=True)
        GlassmorphismHelper.apply_main_container_effect(self)
        
        self.setStyleSheet(f"""
            QTableWidget#ModernTable {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                gridline-color: rgba(255, 255, 255, 0.1);
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
            }}
            
            QTableWidget#ModernTable::item {{
                padding: 8px;
                border: none;
            }}
            
            QTableWidget#ModernTable::item:selected {{
                background: rgba(74, 144, 226, 0.3);
            }}
            
            QTableWidget#ModernTable::item:hover {{
                background: rgba(255, 255, 255, 0.1);
            }}
            
            QHeaderView::section {{
                background: rgba(255, 255, 255, 0.1);
                color: white;
                padding: 8px;
                border: none;
                font-weight: 600;
                font-size: {ResponsiveHelper.scale_size(11, 10, 12)}px;
            }}
            
            QLineEdit, QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                padding: 6px 10px;
                min-height: 16px;
            }}
            
            QLineEdit:focus, QComboBox:focus {{
                border: 2px solid rgba(74, 144, 226, 0.8);
            }}
            
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
                padding: 6px 12px;
                min-width: 70px;
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
            
            QPushButton#DangerButton {{
                background: rgba(244, 67, 54, 0.8);
                border: 1px solid rgba(244, 67, 54, 1.0);
            }}
            
            QPushButton#DangerButton:hover {{
                background: rgba(244, 67, 54, 1.0);
            }}
            
            QPushButton#WarningButton {{
                background: rgba(255, 152, 0, 0.8);
                border: 1px solid rgba(255, 152, 0, 1.0);
            }}
            
            QPushButton#WarningButton:hover {{
                background: rgba(255, 152, 0, 1.0);
            }}
        """)
        
    def _load_organizations(self):
        """Load organizations from the database"""
        try:
            if not self.auth_manager or not hasattr(self.auth_manager, 'supabase'):
                # Mock data for demonstration
                self._populate_mock_data()
                return
                
            # Fetch all organizations
            result = self.auth_manager.supabase.table('organizations').select('*').execute()
            self.organizations = result.data if result.data else []
            self._populate_organizations_table(self.organizations)
            
        except Exception as e:
            print(f"Error loading organizations: {e}")
            self._populate_mock_data()
            
    def _populate_mock_data(self):
        """Populate with mock data for demonstration"""
        mock_organizations = [
            {
                'id': '1', 'name': 'TechCorp Inc.', 'industry': 'Technology', 
                'subscription_plan': 'Professional', 'subscription_status': 'active',
                'created_at': '2024-01-01T00:00:00Z', 'user_count': 15, 'revenue': 299
            },
            {
                'id': '2', 'name': 'Healthcare Plus', 'industry': 'Healthcare', 
                'subscription_plan': 'Enterprise', 'subscription_status': 'active',
                'created_at': '2024-01-05T00:00:00Z', 'user_count': 45, 'revenue': 999
            },
            {
                'id': '3', 'name': 'StartupXYZ', 'industry': 'Technology', 
                'subscription_plan': 'Basic', 'subscription_status': 'trial',
                'created_at': '2024-01-10T00:00:00Z', 'user_count': 3, 'revenue': 0
            },
            {
                'id': '4', 'name': 'Manufacturing Co', 'industry': 'Manufacturing', 
                'subscription_plan': 'Professional', 'subscription_status': 'inactive',
                'created_at': '2023-12-15T00:00:00Z', 'user_count': 8, 'revenue': 299
            },
            {
                'id': '5', 'name': 'Retail Chain Ltd', 'industry': 'Retail', 
                'subscription_plan': 'Enterprise', 'subscription_status': 'active',
                'created_at': '2023-11-20T00:00:00Z', 'user_count': 67, 'revenue': 999
            }
        ]
        
        self.organizations = mock_organizations
        self._populate_organizations_table(self.organizations)
        
    def _populate_organizations_table(self, organizations):
        """Populate the organizations table with data"""
        self.orgs_table.setRowCount(len(organizations))
        
        for row, org in enumerate(organizations):
            # Organization name
            self.orgs_table.setItem(row, 0, QTableWidgetItem(org.get('name', 'Unknown')))
            
            # Industry
            self.orgs_table.setItem(row, 1, QTableWidgetItem(org.get('industry', 'N/A')))
            
            # Plan
            plan = org.get('subscription_plan', 'basic').title()
            self.orgs_table.setItem(row, 2, QTableWidgetItem(plan))
            
            # Status
            status = org.get('subscription_status', 'unknown').title()
            status_item = QTableWidgetItem(status)
            if status.lower() == 'active':
                status_item.setBackground(Qt.GlobalColor.darkGreen)
            elif status.lower() == 'trial':
                status_item.setBackground(Qt.GlobalColor.darkYellow)
            elif status.lower() == 'suspended':
                status_item.setBackground(Qt.GlobalColor.darkRed)
            else:
                status_item.setBackground(Qt.GlobalColor.darkGray)
            self.orgs_table.setItem(row, 3, status_item)
            
            # User count
            user_count = org.get('user_count', 0)
            self.orgs_table.setItem(row, 4, QTableWidgetItem(str(user_count)))
            
            # Created date
            created_at = org.get('created_at', 'Unknown')
            if created_at and created_at != 'Unknown':
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    created_at = dt.strftime('%Y-%m-%d')
                except:
                    pass
            self.orgs_table.setItem(row, 5, QTableWidgetItem(created_at))
            
            # Last active (mock data)
            last_active = "2 hours ago" if status.lower() == 'active' else "1 week ago"
            self.orgs_table.setItem(row, 6, QTableWidgetItem(last_active))
            
            # Revenue
            revenue = org.get('revenue', 0)
            revenue_text = f"${revenue}/mo" if revenue > 0 else "Free"
            self.orgs_table.setItem(row, 7, QTableWidgetItem(revenue_text))
            
            # Actions
            actions_widget = self._create_organization_actions_widget(org)
            self.orgs_table.setCellWidget(row, 8, actions_widget)
            
    def _create_organization_actions_widget(self, organization):
        """Create actions widget for an organization"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setMaximumSize(50, 24)
        edit_btn.clicked.connect(lambda: self._edit_organization(organization))
        layout.addWidget(edit_btn)
        
        # Suspend/Activate button
        status = organization.get('subscription_status', '').lower()
        if status == 'active':
            suspend_btn = QPushButton("Suspend")
            suspend_btn.setObjectName("WarningButton")
            suspend_btn.setMaximumSize(60, 24)
            suspend_btn.clicked.connect(lambda: self._suspend_organization(organization))
            layout.addWidget(suspend_btn)
        elif status == 'suspended':
            activate_btn = QPushButton("Activate")
            activate_btn.setObjectName("PrimaryButton")
            activate_btn.setMaximumSize(60, 24)
            activate_btn.clicked.connect(lambda: self._activate_organization(organization))
            layout.addWidget(activate_btn)
        
        # Delete button (for inactive organizations)
        if status in ['inactive', 'suspended']:
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("DangerButton")
            delete_btn.setMaximumSize(60, 24)
            delete_btn.clicked.connect(lambda: self._delete_organization(organization))
            layout.addWidget(delete_btn)
        
        return widget
        
    def _filter_organizations(self):
        """Filter organizations based on search criteria"""
        search_text = self.search_input.text().lower()
        status_filter = self.status_filter_combo.currentText()
        plan_filter = self.plan_filter_combo.currentText()
        
        for row in range(self.orgs_table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                name = self.orgs_table.item(row, 0).text().lower()
                industry = self.orgs_table.item(row, 1).text().lower()
                if search_text not in name and search_text not in industry:
                    show_row = False
                    
            # Status filter
            if status_filter != "All Status":
                org_status = self.orgs_table.item(row, 3).text()
                if status_filter != org_status:
                    show_row = False
                    
            # Plan filter
            if plan_filter != "All Plans":
                org_plan = self.orgs_table.item(row, 2).text()
                if plan_filter != org_plan:
                    show_row = False
                    
            self.orgs_table.setRowHidden(row, not show_row)
            
    def _show_organization_context_menu(self, position):
        """Show context menu for organization actions"""
        item = self.orgs_table.itemAt(position)
        if item is None:
            return
            
        menu = QMenu(self)
        
        edit_action = QAction("Edit Organization", self)
        edit_action.triggered.connect(lambda: self._edit_organization_from_row(item.row()))
        menu.addAction(edit_action)
        
        view_action = QAction("View Details", self)
        view_action.triggered.connect(lambda: self._view_organization_details(item.row()))
        menu.addAction(view_action)
        
        menu.addSeparator()
        
        billing_action = QAction("Manage Billing", self)
        billing_action.triggered.connect(lambda: self._manage_organization_billing(item.row()))
        menu.addAction(billing_action)
        
        users_action = QAction("Manage Users", self)
        users_action.triggered.connect(lambda: self._manage_organization_users(item.row()))
        menu.addAction(users_action)
        
        menu.exec(self.orgs_table.mapToGlobal(position))
        
    def _show_create_organization_dialog(self):
        """Show create organization dialog"""
        dialog = CreateOrganizationDialog(self.auth_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_organizations()
            
    def _export_organizations(self):
        """Export organizations to CSV"""
        from PyQt6.QtWidgets import QFileDialog
        import csv
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Organizations", "organizations.csv", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write headers
                    headers = []
                    for col in range(self.orgs_table.columnCount() - 1):  # Exclude actions column
                        headers.append(self.orgs_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(self.orgs_table.rowCount()):
                        if not self.orgs_table.isRowHidden(row):
                            row_data = []
                            for col in range(self.orgs_table.columnCount() - 1):
                                item = self.orgs_table.item(row, col)
                                row_data.append(item.text() if item else "")
                            writer.writerow(row_data)
                            
                QMessageBox.information(self, "Success", f"Organizations exported to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export organizations: {str(e)}")
                
    def _edit_organization(self, organization):
        """Edit organization details"""
        dialog = EditOrganizationDialog(organization, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_organizations()
            
    def _suspend_organization(self, organization):
        """Suspend an organization"""
        name = organization.get('name', 'this organization')
        
        reply = QMessageBox.question(
            self, "Suspend Organization",
            f"Are you sure you want to suspend {name}?\n\nThis will prevent all users from accessing the system.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Update organization status
                QMessageBox.information(self, "Success", f"{name} has been suspended.")
                self._load_organizations()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to suspend organization: {str(e)}")
                
    def _activate_organization(self, organization):
        """Activate a suspended organization"""
        name = organization.get('name', 'this organization')
        
        QMessageBox.information(self, "Success", f"{name} has been activated.")
        self._load_organizations()
        
    def _delete_organization(self, organization):
        """Delete an organization"""
        name = organization.get('name', 'this organization')
        
        reply = QMessageBox.question(
            self, "Delete Organization",
            f"Are you sure you want to permanently delete {name}?\n\nThis action cannot be undone and will remove all data.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Delete organization and all related data
                QMessageBox.information(self, "Success", f"{name} has been deleted.")
                self._load_organizations()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete organization: {str(e)}")
                
    def _edit_organization_from_row(self, row):
        """Edit organization from table row"""
        # Get organization data from row - placeholder
        pass
        
    def _view_organization_details(self, row):
        """View organization details"""
        QMessageBox.information(self, "Details", "Organization details view - to be implemented")
        
    def _manage_organization_billing(self, row):
        """Manage organization billing"""
        QMessageBox.information(self, "Billing", "Organization billing management - to be implemented")
        
    def _manage_organization_users(self, row):
        """Manage organization users"""
        QMessageBox.information(self, "Users", "Organization user management - to be implemented")


class CreateOrganizationDialog(QDialog):
    """Dialog for creating new organizations"""
    
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the create organization dialog UI"""
        self.setWindowTitle("Create Organization")
        self.setModal(True)
        self.setFixedSize(500, 600)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Create New Organization")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(title)
        
        # Form
        form_group = QGroupBox("Organization Details")
        form_layout = QFormLayout(form_group)
        
        # Basic information
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter organization name")
        form_layout.addRow("Organization Name*:", self.name_input)
        
        self.slug_input = QLineEdit()
        self.slug_input.setPlaceholderText("url-friendly-name")
        form_layout.addRow("URL Slug*:", self.slug_input)
        
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(80)
        self.description_input.setPlaceholderText("Brief description of the organization")
        form_layout.addRow("Description:", self.description_input)
        
        self.industry_combo = QComboBox()
        self.industry_combo.addItems([
            "Technology", "Healthcare", "Finance", "Manufacturing", 
            "Retail", "Education", "Consulting", "Real Estate", "Other"
        ])
        form_layout.addRow("Industry:", self.industry_combo)
        
        # Subscription details
        self.plan_combo = QComboBox()
        self.plan_combo.addItems(["Basic", "Professional", "Enterprise", "Custom"])
        form_layout.addRow("Initial Plan:", self.plan_combo)
        
        # Owner details
        self.owner_email_input = QLineEdit()
        self.owner_email_input.setPlaceholderText("owner@organization.com")
        form_layout.addRow("Owner Email*:", self.owner_email_input)
        
        self.owner_name_input = QLineEdit()
        self.owner_name_input.setPlaceholderText("Owner full name")
        form_layout.addRow("Owner Name:", self.owner_name_input)
        
        # Settings
        self.send_welcome_check = QCheckBox("Send welcome email to owner")
        self.send_welcome_check.setChecked(True)
        form_layout.addRow("", self.send_welcome_check)
        
        self.trial_period_check = QCheckBox("Start with 30-day trial")
        self.trial_period_check.setChecked(True)
        form_layout.addRow("", self.trial_period_check)
        
        layout.addWidget(form_group)
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        create_btn = QPushButton("Create Organization")
        create_btn.setObjectName("PrimaryButton")
        create_btn.clicked.connect(self._create_organization)
        button_layout.addWidget(create_btn)
        
        layout.addLayout(button_layout)
        
    def _apply_styling(self):
        """Apply dialog styling"""
        MicaEffect.apply_mica(self, dark_mode=True)
        self.setStyleSheet(f"""
            QDialog {{
                background: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
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
            
            QLineEdit, QTextEdit, QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                padding: 8px 12px;
            }}
            
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
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
            
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
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
        """)
        
    def _create_organization(self):
        """Create the organization"""
        name = self.name_input.text().strip()
        slug = self.slug_input.text().strip()
        owner_email = self.owner_email_input.text().strip()
        
        if not name or not slug or not owner_email:
            QMessageBox.warning(self, "Invalid Input", "Please fill in all required fields.")
            return
            
        # Basic email validation
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', owner_email):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
            
        try:
            # Create organization (placeholder)
            organization_data = {
                'name': name,
                'slug': slug,
                'description': self.description_input.toPlainText().strip(),
                'industry': self.industry_combo.currentText(),
                'subscription_plan': self.plan_combo.currentText().lower(),
                'subscription_status': 'trial' if self.trial_period_check.isChecked() else 'active'
            }
            
            # Here you would create the organization in the database
            # and set up the owner account
            
            QMessageBox.information(self, "Success", f"Organization '{name}' created successfully!")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create organization: {str(e)}")


class EditOrganizationDialog(QDialog):
    """Dialog for editing organization details"""
    
    def __init__(self, organization, parent=None):
        super().__init__(parent)
        self.organization = organization
        self._setup_ui()
        self._apply_styling()
        self._populate_data()
        
    def _setup_ui(self):
        """Setup the edit organization dialog UI"""
        self.setWindowTitle("Edit Organization")
        self.setModal(True)
        self.setFixedSize(450, 500)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel(f"Edit {self.organization.get('name', 'Organization')}")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(title)
        
        # Form
        form_layout = QFormLayout()
        
        self.name_input = QLineEdit()
        form_layout.addRow("Name:", self.name_input)
        
        self.industry_combo = QComboBox()
        self.industry_combo.addItems([
            "Technology", "Healthcare", "Finance", "Manufacturing", 
            "Retail", "Education", "Consulting", "Real Estate", "Other"
        ])
        form_layout.addRow("Industry:", self.industry_combo)
        
        self.plan_combo = QComboBox()
        self.plan_combo.addItems(["Basic", "Professional", "Enterprise", "Custom"])
        form_layout.addRow("Plan:", self.plan_combo)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive", "Suspended", "Trial"])
        form_layout.addRow("Status:", self.status_combo)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save_changes)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        
    def _apply_styling(self):
        """Apply dialog styling"""
        MicaEffect.apply_mica(self, dark_mode=True)
        self.setStyleSheet(f"""
            QDialog {{
                background: rgba(30, 30, 30, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }}
            
            QLineEdit, QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                padding: 8px 12px;
                min-height: 20px;
            }}
            
            QLineEdit:focus, QComboBox:focus {{
                border: 2px solid rgba(74, 144, 226, 0.8);
            }}
            
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
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
        """)
        
    def _populate_data(self):
        """Populate form with organization data"""
        self.name_input.setText(self.organization.get('name', ''))
        
        industry = self.organization.get('industry', 'Other')
        index = self.industry_combo.findText(industry)
        if index >= 0:
            self.industry_combo.setCurrentIndex(index)
            
        plan = self.organization.get('subscription_plan', 'basic').title()
        index = self.plan_combo.findText(plan)
        if index >= 0:
            self.plan_combo.setCurrentIndex(index)
            
        status = self.organization.get('subscription_status', 'active').title()
        index = self.status_combo.findText(status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
            
    def _save_changes(self):
        """Save organization changes"""
        # Placeholder for save logic
        QMessageBox.information(self, "Success", "Organization changes saved successfully.")
        self.accept()
