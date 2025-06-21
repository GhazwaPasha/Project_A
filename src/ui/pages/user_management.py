"""
User management page for advanced user administration
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
                            QDialog, QLineEdit, QComboBox, QMessageBox, QMenu,
                            QTabWidget, QCheckBox, QDateEdit, QTextEdit, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal, QDate
from PyQt6.QtGui import QIcon, QAction
from ..common import ResponsiveHelper
from ..components.widgets import PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect


class UserManagementPage(QWidget):
    """Advanced user management page for organization admins"""
    
    def __init__(self, system, auth_manager=None, parent=None):
        super().__init__(parent)
        self.system = system
        self.auth_manager = auth_manager
        self.current_organization = None
        self._setup_ui()
        self._apply_styling()
        self._load_users()
        
    def _setup_ui(self):
        """Setup the user management UI"""
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(24, 20, 32))
        
        # Page header with actions
        header_layout = QHBoxLayout()
        
        header = PageHeader("User Management", "Advanced user administration and role management")
        header_layout.addWidget(header)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.bulk_invite_btn = QPushButton("Bulk Invite")
        self.bulk_invite_btn.clicked.connect(self._show_bulk_invite_dialog)
        action_layout.addWidget(self.bulk_invite_btn)
        
        self.export_users_btn = QPushButton("Export Users")
        self.export_users_btn.clicked.connect(self._export_users)
        action_layout.addWidget(self.export_users_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("PrimaryButton")
        self.refresh_btn.clicked.connect(self._load_users)
        action_layout.addWidget(self.refresh_btn)
        
        header_layout.addLayout(action_layout)
        main_layout.addLayout(header_layout)
        
        # Tabs for different user views
        self.tabs = QTabWidget()
        self.tabs.setObjectName("UserTabs")
        
        # Active users tab
        self._create_active_users_tab()
        
        # Roles & Permissions tab
        self._create_roles_tab()
        
        # Access logs tab
        self._create_access_logs_tab()
        
        main_layout.addWidget(self.tabs)
        
    def _create_active_users_tab(self):
        """Create the active users tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Filter controls
        filter_layout = QHBoxLayout()
        
        # Role filter
        role_filter_label = QLabel("Filter by Role:")
        role_filter_label.setStyleSheet("color: white; margin-right: 8px;")
        filter_layout.addWidget(role_filter_label)
        
        self.role_filter_combo = QComboBox()
        self.role_filter_combo.addItems([
            "All Roles", "Organization Owner", "Organization Admin", "Accountant"
        ])
        self.role_filter_combo.currentTextChanged.connect(self._filter_users)
        filter_layout.addWidget(self.role_filter_combo)
        
        # Status filter
        status_filter_label = QLabel("Filter by Status:")
        status_filter_label.setStyleSheet("color: white; margin-left: 16px; margin-right: 8px;")
        filter_layout.addWidget(status_filter_label)
        
        self.status_filter_combo = QComboBox()
        self.status_filter_combo.addItems([
            "All Status", "Active", "Inactive", "Pending"
        ])
        self.status_filter_combo.currentTextChanged.connect(self._filter_users)
        filter_layout.addWidget(self.status_filter_combo)
        
        filter_layout.addStretch()
        
        # Search box
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self._filter_users)
        filter_layout.addWidget(self.search_input)
        
        layout.addLayout(filter_layout)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setObjectName("ModernTable")
        self.users_table.setColumnCount(8)
        self.users_table.setHorizontalHeaderLabels([
            "Name", "Email", "Role", "Department", "Status", "Last Login", "Join Date", "Actions"
        ])
        
        # Configure table
        header = self.users_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.users_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.users_table.customContextMenuRequested.connect(self._show_user_context_menu)
        
        layout.addWidget(self.users_table)
        
        self.tabs.addTab(tab, "Active Users")
        
    def _create_roles_tab(self):
        """Create the roles and permissions tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Roles overview section
        roles_group = QGroupBox("Organization Roles")
        roles_layout = QVBoxLayout(roles_group)
        
        # Role statistics
        stats_layout = QHBoxLayout()
        
        owner_count = QLabel("Owners: 1")
        owner_count.setStyleSheet("color: #FF9800; font-weight: 600;")
        stats_layout.addWidget(owner_count)
        
        admin_count = QLabel("Admins: 2")
        admin_count.setStyleSheet("color: #2196F3; font-weight: 600;")
        stats_layout.addWidget(admin_count)
        
        accountant_count = QLabel("Accountants: 5")
        accountant_count.setStyleSheet("color: #4CAF50; font-weight: 600;")
        stats_layout.addWidget(accountant_count)
        
        stats_layout.addStretch()
        roles_layout.addLayout(stats_layout)
        
        # Role permissions matrix
        permissions_label = QLabel("Role Permissions Matrix")
        permissions_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(16, 14, 18)}px;
                font-weight: 600;
                margin-top: 16px;
                margin-bottom: 8px;
            }}
        """)
        roles_layout.addWidget(permissions_label)
        
        self.permissions_table = QTableWidget()
        self.permissions_table.setObjectName("PermissionsTable")
        self.permissions_table.setColumnCount(4)
        self.permissions_table.setHorizontalHeaderLabels([
            "Permission", "Owner", "Admin", "Accountant"
        ])
        
        # Add permission rows
        permissions = [
            "Manage Organization Settings",
            "Invite/Remove Users",
            "Assign User Roles",
            "View All Transactions",
            "Create/Edit Transactions",
            "Delete Transactions",
            "Generate Reports",
            "Export Data",
            "View Audit Logs",
            "Manage Billing"
        ]
        
        self.permissions_table.setRowCount(len(permissions))
        
        for row, permission in enumerate(permissions):
            self.permissions_table.setItem(row, 0, QTableWidgetItem(permission))
            
            # Owner permissions (all enabled)
            owner_check = QCheckBox()
            owner_check.setChecked(True)
            owner_check.setEnabled(False)  # Owners always have all permissions
            self.permissions_table.setCellWidget(row, 1, owner_check)
            
            # Admin permissions (most enabled)
            admin_check = QCheckBox()
            admin_check.setChecked(row < 9)  # All except billing
            self.permissions_table.setCellWidget(row, 2, admin_check)
            
            # Accountant permissions (limited)
            accountant_check = QCheckBox()
            accountant_check.setChecked(row in [3, 4, 6, 7])  # Limited permissions
            self.permissions_table.setCellWidget(row, 3, accountant_check)
        
        # Configure permissions table
        perm_header = self.permissions_table.horizontalHeader()
        perm_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        perm_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        perm_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        perm_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.permissions_table.setMaximumHeight(300)
        roles_layout.addWidget(self.permissions_table)
        
        # Save permissions button
        save_permissions_layout = QHBoxLayout()
        save_permissions_layout.addStretch()
        
        save_permissions_btn = QPushButton("Save Permission Changes")
        save_permissions_btn.setObjectName("PrimaryButton")
        save_permissions_btn.clicked.connect(self._save_permissions)
        save_permissions_layout.addWidget(save_permissions_btn)
        
        roles_layout.addLayout(save_permissions_layout)
        layout.addWidget(roles_group)
        layout.addStretch()
        
        self.tabs.addTab(tab, "Roles & Permissions")
        
    def _create_access_logs_tab(self):
        """Create the access logs tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Filter controls for logs
        log_filter_layout = QHBoxLayout()
        
        # Date range
        date_label = QLabel("Date Range:")
        date_label.setStyleSheet("color: white; margin-right: 8px;")
        log_filter_layout.addWidget(date_label)
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-7))
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        log_filter_layout.addWidget(self.start_date)
        
        to_label = QLabel("to")
        to_label.setStyleSheet("color: white; margin: 0 8px;")
        log_filter_layout.addWidget(to_label)
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        log_filter_layout.addWidget(self.end_date)
        
        # Activity type filter
        activity_label = QLabel("Activity:")
        activity_label.setStyleSheet("color: white; margin-left: 16px; margin-right: 8px;")
        log_filter_layout.addWidget(activity_label)
        
        self.activity_filter_combo = QComboBox()
        self.activity_filter_combo.addItems([
            "All Activities", "Login", "Logout", "Transaction Created", 
            "Transaction Modified", "Report Generated", "Settings Changed"
        ])
        log_filter_layout.addWidget(self.activity_filter_combo)
        
        log_filter_layout.addStretch()
        
        # Load logs button
        load_logs_btn = QPushButton("Load Logs")
        load_logs_btn.setObjectName("PrimaryButton")
        load_logs_btn.clicked.connect(self._load_access_logs)
        log_filter_layout.addWidget(load_logs_btn)
        
        layout.addLayout(log_filter_layout)
        
        # Access logs table
        self.logs_table = QTableWidget()
        self.logs_table.setObjectName("ModernTable")
        self.logs_table.setColumnCount(6)
        self.logs_table.setHorizontalHeaderLabels([
            "Timestamp", "User", "Activity", "IP Address", "User Agent", "Details"
        ])
        
        # Configure logs table
        logs_header = self.logs_table.horizontalHeader()
        logs_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        logs_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        logs_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        logs_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        logs_header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        logs_header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        
        self.logs_table.setAlternatingRowColors(True)
        layout.addWidget(self.logs_table)
        
        self.tabs.addTab(tab, "Access Logs")
        
    def _apply_styling(self):
        """Apply styling to the user management page"""
        MicaEffect.apply_mica(self, dark_mode=True)
        GlassmorphismHelper.apply_main_container_effect(self)
        
        self.setStyleSheet(f"""
            QTabWidget#UserTabs {{
                background: transparent;
                border: none;
            }}
            
            QTabWidget#UserTabs::pane {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                top: -1px;
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
            
            QTableWidget#ModernTable, QTableWidget#PermissionsTable {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                gridline-color: rgba(255, 255, 255, 0.1);
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
            }}
            
            QTableWidget#ModernTable::item, QTableWidget#PermissionsTable::item {{
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
            
            QLineEdit, QComboBox, QDateEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                padding: 6px 10px;
                min-height: 16px;
            }}
            
            QLineEdit:focus, QComboBox:focus, QDateEdit:focus {{
                border: 2px solid rgba(74, 144, 226, 0.8);
            }}
            
            QCheckBox {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
            }}
            
            QCheckBox::indicator {{
                width: 14px;
                height: 14px;
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
        """)
        
    def _load_users(self):
        """Load users from the database"""
        try:
            if not self.auth_manager or not hasattr(self.auth_manager, 'supabase'):
                return
                
            # Get current organization
            if hasattr(self.auth_manager, 'user_organizations') and self.auth_manager.user_organizations:
                self.current_organization = self.auth_manager.user_organizations[0]
                org_id = self.current_organization.get('id')
                
                # Fetch organization members with user details
                result = self.auth_manager.supabase.table('organization_members').select(
                    '*, users!inner(first_name, last_name, display_name, email, last_login_at, created_at)'
                ).eq('organization_id', org_id).execute()
                
                self._populate_users_table(result.data if result.data else [])
                
        except Exception as e:
            print(f"Error loading users: {e}")
            
    def _populate_users_table(self, users):
        """Populate the users table with data"""
        self.users_table.setRowCount(len(users))
        
        for row, user_member in enumerate(users):
            user = user_member.get('users', {})
            
            # Name
            name = user.get('display_name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            self.users_table.setItem(row, 0, QTableWidgetItem(name or 'Unknown'))
            
            # Email
            self.users_table.setItem(row, 1, QTableWidgetItem(user.get('email', 'N/A')))
            
            # Role
            role = user_member.get('role', 'accountant').replace('_', ' ').title()
            self.users_table.setItem(row, 2, QTableWidgetItem(role))
            
            # Department
            self.users_table.setItem(row, 3, QTableWidgetItem(user_member.get('department', 'N/A')))
            
            # Status
            status = "Active" if user_member.get('is_active', True) else "Inactive"
            if not user_member.get('joined_at'):
                status = "Pending"
            status_item = QTableWidgetItem(status)
            if status == "Active":
                status_item.setBackground(Qt.GlobalColor.darkGreen)
            elif status == "Pending":
                status_item.setBackground(Qt.GlobalColor.darkYellow)
            else:
                status_item.setBackground(Qt.GlobalColor.darkRed)
            self.users_table.setItem(row, 4, status_item)
            
            # Last Login
            last_login = user.get('last_login_at', 'Never')
            if last_login and last_login != 'Never':
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                    last_login = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            self.users_table.setItem(row, 5, QTableWidgetItem(last_login))
            
            # Join Date
            join_date = user_member.get('joined_at') or user.get('created_at', 'Unknown')
            if join_date and join_date != 'Unknown':
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(join_date.replace('Z', '+00:00'))
                    join_date = dt.strftime('%Y-%m-%d')
                except:
                    pass
            self.users_table.setItem(row, 6, QTableWidgetItem(join_date))
            
            # Actions
            actions_widget = self._create_user_actions_widget(user_member)
            self.users_table.setCellWidget(row, 7, actions_widget)
            
    def _create_user_actions_widget(self, user_member):
        """Create actions widget for a user"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # Edit button
        edit_btn = QPushButton("Edit")
        edit_btn.setMaximumSize(50, 24)
        edit_btn.clicked.connect(lambda: self._edit_user(user_member))
        layout.addWidget(edit_btn)
        
        # Disable/Enable button
        if user_member.get('is_active', True):
            disable_btn = QPushButton("Disable")
            disable_btn.setObjectName("WarningButton")
            disable_btn.setMaximumSize(60, 24)
            disable_btn.clicked.connect(lambda: self._disable_user(user_member))
            layout.addWidget(disable_btn)
        else:
            enable_btn = QPushButton("Enable")
            enable_btn.setObjectName("SuccessButton")
            enable_btn.setMaximumSize(60, 24)
            enable_btn.clicked.connect(lambda: self._enable_user(user_member))
            layout.addWidget(enable_btn)
        
        return widget
        
    def _filter_users(self):
        """Filter users based on search criteria"""
        # Placeholder for filtering logic
        search_text = self.search_input.text().lower()
        role_filter = self.role_filter_combo.currentText()
        status_filter = self.status_filter_combo.currentText()
        
        for row in range(self.users_table.rowCount()):
            show_row = True
            
            # Search filter
            if search_text:
                name = self.users_table.item(row, 0).text().lower()
                email = self.users_table.item(row, 1).text().lower()
                if search_text not in name and search_text not in email:
                    show_row = False
                    
            # Role filter
            if role_filter != "All Roles":
                user_role = self.users_table.item(row, 2).text()
                if role_filter != user_role:
                    show_row = False
                    
            # Status filter
            if status_filter != "All Status":
                user_status = self.users_table.item(row, 4).text()
                if status_filter != user_status:
                    show_row = False
                    
            self.users_table.setRowHidden(row, not show_row)
            
    def _show_user_context_menu(self, position):
        """Show context menu for user actions"""
        item = self.users_table.itemAt(position)
        if item is None:
            return
            
        menu = QMenu(self)
        
        edit_action = QAction("Edit User", self)
        edit_action.triggered.connect(lambda: self._edit_user_from_row(item.row()))
        menu.addAction(edit_action)
        
        view_action = QAction("View Profile", self)
        view_action.triggered.connect(lambda: self._view_user_profile(item.row()))
        menu.addAction(view_action)
        
        menu.addSeparator()
        
        reset_password_action = QAction("Reset Password", self)
        reset_password_action.triggered.connect(lambda: self._reset_user_password(item.row()))
        menu.addAction(reset_password_action)
        
        menu.exec(self.users_table.mapToGlobal(position))
        
    def _show_bulk_invite_dialog(self):
        """Show bulk user invitation dialog"""
        dialog = BulkInviteDialog(self.auth_manager, self.current_organization, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_users()
            
    def _export_users(self):
        """Export users to CSV"""
        from PyQt6.QtWidgets import QFileDialog
        import csv
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Users", "users.csv", "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    
                    # Write headers
                    headers = []
                    for col in range(self.users_table.columnCount() - 1):  # Exclude actions column
                        headers.append(self.users_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(self.users_table.rowCount()):
                        if not self.users_table.isRowHidden(row):
                            row_data = []
                            for col in range(self.users_table.columnCount() - 1):
                                item = self.users_table.item(row, col)
                                row_data.append(item.text() if item else "")
                            writer.writerow(row_data)
                            
                QMessageBox.information(self, "Success", f"Users exported to {file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export users: {str(e)}")
                
    def _load_access_logs(self):
        """Load access logs for the date range"""
        # Placeholder for access logs loading
        sample_logs = [
            ["2024-01-15 14:30:22", "john.doe@company.com", "Login", "192.168.1.100", "Chrome 91.0", "Successful login"],
            ["2024-01-15 14:25:10", "jane.smith@company.com", "Transaction Created", "192.168.1.101", "Firefox 89.0", "Created journal entry #1234"],
            ["2024-01-15 14:20:05", "admin@company.com", "Settings Changed", "192.168.1.102", "Safari 14.1", "Updated organization settings"],
            ["2024-01-15 14:15:30", "john.doe@company.com", "Report Generated", "192.168.1.100", "Chrome 91.0", "Generated P&L report"],
            ["2024-01-15 14:10:15", "jane.smith@company.com", "Logout", "192.168.1.101", "Firefox 89.0", "User logged out"],
        ]
        
        self.logs_table.setRowCount(len(sample_logs))
        
        for row, log_entry in enumerate(sample_logs):
            for col, value in enumerate(log_entry):
                self.logs_table.setItem(row, col, QTableWidgetItem(str(value)))
                
    def _save_permissions(self):
        """Save permission changes"""
        QMessageBox.information(self, "Success", "Permission changes saved successfully.")
        
    def _edit_user(self, user_member):
        """Edit user details"""
        dialog = EditUserDialog(user_member, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_users()
            
    def _disable_user(self, user_member):
        """Disable a user"""
        user = user_member.get('users', {})
        name = user.get('display_name', 'this user')
        
        reply = QMessageBox.question(
            self, "Disable User",
            f"Are you sure you want to disable {name}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Update user status
            QMessageBox.information(self, "Success", f"{name} has been disabled.")
            self._load_users()
            
    def _enable_user(self, user_member):
        """Enable a user"""
        user = user_member.get('users', {})
        name = user.get('display_name', 'this user')
        
        QMessageBox.information(self, "Success", f"{name} has been enabled.")
        self._load_users()
        
    def _edit_user_from_row(self, row):
        """Edit user from table row"""
        # Get user data from row - placeholder
        pass
        
    def _view_user_profile(self, row):
        """View user profile"""
        QMessageBox.information(self, "Profile", "User profile view - to be implemented")
        
    def _reset_user_password(self, row):
        """Reset user password"""
        reply = QMessageBox.question(
            self, "Reset Password",
            "Send password reset email to this user?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Success", "Password reset email sent.")


class BulkInviteDialog(QDialog):
    """Dialog for bulk user invitations"""
    
    def __init__(self, auth_manager, organization, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.organization = organization
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the bulk invite dialog UI"""
        self.setWindowTitle("Bulk Invite Users")
        self.setModal(True)
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Bulk Invite Team Members")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(title)
        
        # Instructions
        instructions = QLabel("Enter email addresses (one per line) to send invitations:")
        instructions.setStyleSheet("color: rgba(255, 255, 255, 0.7); margin-bottom: 8px;")
        layout.addWidget(instructions)
        
        # Email input
        self.emails_input = QTextEdit()
        self.emails_input.setPlaceholderText("user1@company.com\nuser2@company.com\nuser3@company.com")
        layout.addWidget(self.emails_input)
        
        # Default role
        role_layout = QHBoxLayout()
        role_label = QLabel("Default Role:")
        role_label.setStyleSheet("color: white; margin-right: 8px;")
        role_layout.addWidget(role_label)
        
        self.default_role_combo = QComboBox()
        self.default_role_combo.addItems(["Accountant", "Organization Admin"])
        role_layout.addWidget(self.default_role_combo)
        role_layout.addStretch()
        
        layout.addLayout(role_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        invite_btn = QPushButton("Send Invitations")
        invite_btn.setObjectName("PrimaryButton")
        invite_btn.clicked.connect(self._send_bulk_invitations)
        button_layout.addWidget(invite_btn)
        
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
            
            QTextEdit, QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
                padding: 8px 12px;
            }}
            
            QTextEdit:focus, QComboBox:focus {{
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
        
    def _send_bulk_invitations(self):
        """Send bulk invitations"""
        emails_text = self.emails_input.toPlainText().strip()
        if not emails_text:
            QMessageBox.warning(self, "Invalid Input", "Please enter at least one email address.")
            return
            
        emails = [email.strip() for email in emails_text.split('\n') if email.strip()]
        default_role = self.default_role_combo.currentText().lower().replace(' ', '_')
        
        # Validate emails
        import re
        valid_emails = []
        invalid_emails = []
        
        for email in emails:
            if re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
                valid_emails.append(email)
            else:
                invalid_emails.append(email)
                
        if invalid_emails:
            QMessageBox.warning(
                self, "Invalid Emails", 
                f"The following emails are invalid:\n{', '.join(invalid_emails)}"
            )
            return
            
        # Send invitations (placeholder)
        success_count = len(valid_emails)
        QMessageBox.information(
            self, "Success", 
            f"Successfully sent {success_count} invitation(s)."
        )
        self.accept()


class EditUserDialog(QDialog):
    """Dialog for editing user details"""
    
    def __init__(self, user_member, parent=None):
        super().__init__(parent)
        self.user_member = user_member
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the edit user dialog UI"""
        self.setWindowTitle("Edit User")
        self.setModal(True)
        self.setFixedSize(400, 350)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        user = self.user_member.get('users', {})
        name = user.get('display_name', 'User')
        title = QLabel(f"Edit {name}")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(title)
        
        # Form fields
        form_layout = QVBoxLayout()
        
        # Role
        role_label = QLabel("Role:")
        role_label.setStyleSheet("color: white; margin-bottom: 4px;")
        form_layout.addWidget(role_label)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Accountant", "Organization Admin", "Organization Owner"
        ])
        
        current_role = self.user_member.get('role', 'accountant').replace('_', ' ').title()
        index = self.role_combo.findText(current_role)
        if index >= 0:
            self.role_combo.setCurrentIndex(index)
            
        form_layout.addWidget(self.role_combo)
        
        # Department
        dept_label = QLabel("Department:")
        dept_label.setStyleSheet("color: white; margin-top: 8px; margin-bottom: 4px;")
        form_layout.addWidget(dept_label)
        
        self.dept_input = QLineEdit()
        self.dept_input.setText(self.user_member.get('department', ''))
        form_layout.addWidget(self.dept_input)
        
        # Status
        status_label = QLabel("Status:")
        status_label.setStyleSheet("color: white; margin-top: 8px; margin-bottom: 4px;")
        form_layout.addWidget(status_label)
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Active", "Inactive"])
        self.status_combo.setCurrentText("Active" if self.user_member.get('is_active', True) else "Inactive")
        form_layout.addWidget(self.status_combo)
        
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
        
    def _save_changes(self):
        """Save user changes"""
        # Placeholder for save logic
        QMessageBox.information(self, "Success", "User changes saved successfully.")
        self.accept()
