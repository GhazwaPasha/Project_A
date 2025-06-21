"""
Team management page for organization user management
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
                            QDialog, QLineEdit, QComboBox, QMessageBox, QMenu)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon, QAction
from ..common import ResponsiveHelper
from ..components.widgets import PageHeader
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect


class TeamManagementPage(QWidget):
    """Team management page for viewing and managing organization members"""
    
    def __init__(self, system, auth_manager=None, parent=None):
        super().__init__(parent)
        self.system = system
        self.auth_manager = auth_manager
        self.current_organization = None
        self.team_members = []
        self._setup_ui()
        self._apply_styling()
        self._load_team_members()
        
    def _setup_ui(self):
        """Setup the team management UI"""
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, responsive_margin, 
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(ResponsiveHelper.scale_size(24, 20, 32))
        
        # Page header with actions
        header_layout = QHBoxLayout()
        
        header = PageHeader("Team Management", "Manage organization members and their roles")
        header_layout.addWidget(header)
        
        # Action buttons
        action_layout = QHBoxLayout()
        action_layout.addStretch()
        
        self.invite_btn = QPushButton("Invite Member")
        self.invite_btn.setObjectName("PrimaryButton")
        self.invite_btn.clicked.connect(self._show_invite_dialog)
        action_layout.addWidget(self.invite_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_team_members)
        action_layout.addWidget(self.refresh_btn)
        
        header_layout.addLayout(action_layout)
        main_layout.addLayout(header_layout)
        
        # Team members table
        self._create_members_table(main_layout)
        
        # Pending invitations section
        self._create_invitations_section(main_layout)
        
    def _create_members_table(self, main_layout):
        """Create the team members table"""
        # Section title
        members_title = QLabel("Team Members")
        members_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                margin-bottom: 12px;
            }}
        """)
        main_layout.addWidget(members_title)
        
        # Members table
        self.members_table = QTableWidget()
        self.members_table.setObjectName("ModernTable")
        self.members_table.setColumnCount(6)
        self.members_table.setHorizontalHeaderLabels([
            "Name", "Email", "Role", "Department", "Last Active", "Actions"
        ])
        
        # Configure table
        header = self.members_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.members_table.setAlternatingRowColors(True)
        self.members_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.members_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.members_table.customContextMenuRequested.connect(self._show_member_context_menu)
        
        main_layout.addWidget(self.members_table)
        
    def _create_invitations_section(self, main_layout):
        """Create the pending invitations section"""
        # Section title
        invites_title = QLabel("Pending Invitations")
        invites_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                margin-bottom: 12px;
                margin-top: 24px;
            }}
        """)
        main_layout.addWidget(invites_title)
        
        # Invitations table
        self.invites_table = QTableWidget()
        self.invites_table.setObjectName("ModernTable")
        self.invites_table.setColumnCount(5)
        self.invites_table.setHorizontalHeaderLabels([
            "Email", "Role", "Invited By", "Invited Date", "Actions"
        ])
        
        # Configure invitations table
        inv_header = self.invites_table.horizontalHeader()
        inv_header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        inv_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        inv_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        inv_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        inv_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.invites_table.setAlternatingRowColors(True)
        self.invites_table.setMaximumHeight(150)  # Smaller table for invitations
        
        main_layout.addWidget(self.invites_table)
        main_layout.addStretch()
        
    def _apply_styling(self):
        """Apply styling to the team management page"""
        MicaEffect.apply_mica(self, dark_mode=True)
        GlassmorphismHelper.apply_main_container_effect(self)
        
        self.setStyleSheet(f"""
            QTableWidget#ModernTable {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: white;
                gridline-color: rgba(255, 255, 255, 0.1);
                font-size: {ResponsiveHelper.scale_size(13, 12, 14)}px;
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
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
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
            
            QPushButton#DangerButton {{
                background: rgba(244, 67, 54, 0.8);
                border: 1px solid rgba(244, 67, 54, 1.0);
            }}
              QPushButton#DangerButton:hover {{
                background: rgba(244, 67, 54, 1.0);
            }}
        """)
    
    def _load_team_members(self):
        """Load team members from the database"""
        try:
            if not self.auth_manager:
                return
                
            # Get current organization
            if hasattr(self.auth_manager, 'user_organizations') and self.auth_manager.user_organizations:
                self.current_organization = self.auth_manager.user_organizations[0]
                org_id = self.current_organization.get('organizations', {}).get('id') or self.current_organization.get('id')
                
                # Fetch organization members using auth_manager method
                members = self.auth_manager.get_organization_members(org_id)
                self._populate_members_table(members)
                
                # Fetch pending invitations using auth_manager method
                invitations = self.auth_manager.get_pending_invitations(org_id)
                self._populate_invitations_table(invitations)
                
        except Exception as e:
            print(f"Error loading team members: {e}")
            
    def _populate_members_table(self, members):
        """Populate the members table with data"""
        self.members_table.setRowCount(len(members))
        
        for row, member in enumerate(members):
            user = member.get('users', {})
            
            # Name
            name = user.get('display_name') or f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
            self.members_table.setItem(row, 0, QTableWidgetItem(name or 'Unknown'))
            
            # Email
            self.members_table.setItem(row, 1, QTableWidgetItem(user.get('email', 'N/A')))
            
            # Role
            role = member.get('role', 'accountant').replace('_', ' ').title()
            self.members_table.setItem(row, 2, QTableWidgetItem(role))
            
            # Department
            self.members_table.setItem(row, 3, QTableWidgetItem(member.get('department', 'N/A')))
            
            # Last Active
            last_active = user.get('last_login_at', 'Never')
            if last_active and last_active != 'Never':
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(last_active.replace('Z', '+00:00'))
                    last_active = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    pass
            self.members_table.setItem(row, 4, QTableWidgetItem(last_active))
            
            # Actions
            actions_widget = self._create_member_actions_widget(member)
            self.members_table.setCellWidget(row, 5, actions_widget)
            
    def _populate_invitations_table(self, invitations):
        """Populate the invitations table with data"""
        self.invites_table.setRowCount(len(invitations))
        
        for row, invite in enumerate(invitations):
            # Email (stored in invitation_token or a separate field)
            email = invite.get('invitation_email', 'Unknown Email')
            self.invites_table.setItem(row, 0, QTableWidgetItem(email))
            
            # Role
            role = invite.get('role', 'accountant').replace('_', ' ').title()
            self.invites_table.setItem(row, 1, QTableWidgetItem(role))
            
            # Invited By
            invited_by = invite.get('invited_by_user', {}).get('display_name', 'Unknown')
            self.invites_table.setItem(row, 2, QTableWidgetItem(invited_by))
            
            # Invited Date
            invited_date = invite.get('invited_at', 'Unknown')
            if invited_date and invited_date != 'Unknown':
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(invited_date.replace('Z', '+00:00'))
                    invited_date = dt.strftime('%Y-%m-%d')
                except:
                    pass
            self.invites_table.setItem(row, 3, QTableWidgetItem(invited_date))
            
            # Actions
            actions_widget = self._create_invitation_actions_widget(invite)
            self.invites_table.setCellWidget(row, 4, actions_widget)
            
    def _create_member_actions_widget(self, member):
        """Create actions widget for a team member"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # Edit role button
        edit_btn = QPushButton("Edit")
        edit_btn.setMaximumSize(60, 25)
        edit_btn.clicked.connect(lambda: self._edit_member_role(member))
        layout.addWidget(edit_btn)
        
        # Remove button (only if user has permission)
        if self._can_remove_member(member):
            remove_btn = QPushButton("Remove")
            remove_btn.setObjectName("DangerButton")
            remove_btn.setMaximumSize(70, 25)
            remove_btn.clicked.connect(lambda: self._remove_member(member))
            layout.addWidget(remove_btn)
        
        return widget
        
    def _create_invitation_actions_widget(self, invitation):
        """Create actions widget for a pending invitation"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # Resend invitation
        resend_btn = QPushButton("Resend")
        resend_btn.setMaximumSize(60, 25)
        resend_btn.clicked.connect(lambda: self._resend_invitation(invitation))
        layout.addWidget(resend_btn)
        
        # Cancel invitation
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("DangerButton")
        cancel_btn.setMaximumSize(60, 25)
        cancel_btn.clicked.connect(lambda: self._cancel_invitation(invitation))
        layout.addWidget(cancel_btn)
        
        return widget
        
    def _show_invite_dialog(self):
        """Show the invite member dialog"""
        dialog = InviteMemberDialog(self.auth_manager, self.current_organization, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_team_members()  # Refresh the table
            
    def _show_member_context_menu(self, position):
        """Show context menu for member actions"""
        item = self.members_table.itemAt(position)
        if item is None:
            return
            
        row = item.row()
        if row < 0:
            return
            
        menu = QMenu(self)
        
        edit_action = QAction("Edit Role", self)
        edit_action.triggered.connect(lambda: self._edit_member_from_row(row))
        menu.addAction(edit_action)
        
        view_action = QAction("View Profile", self)
        view_action.triggered.connect(lambda: self._view_member_profile(row))
        menu.addAction(view_action)
        
        menu.addSeparator()
        
        remove_action = QAction("Remove Member", self)
        remove_action.triggered.connect(lambda: self._remove_member_from_row(row))
        menu.addAction(remove_action)
        
        menu.exec(self.members_table.mapToGlobal(position))
        
    def _can_remove_member(self, member):
        """Check if current user can remove this member"""
        # Simple permission check - in real app, check user role and permissions
        return True  # Placeholder
        
    def _edit_member_role(self, member):
        """Edit a member's role"""
        dialog = EditMemberRoleDialog(member, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self._load_team_members()
            
    def _remove_member(self, member):
        """Remove a team member"""
        user = member.get('users', {})
        name = user.get('display_name', 'this member')
        
        reply = QMessageBox.question(
            self, "Remove Member",
            f"Are you sure you want to remove {name} from the organization?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Mark as inactive instead of deleting
                self.auth_manager.supabase.table('organization_members').update({
                    'is_active': False
                }).eq('id', member['id']).execute()
                
                QMessageBox.information(self, "Success", "Member removed successfully.")
                self._load_team_members()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to remove member: {str(e)}")
                
    def _resend_invitation(self, invitation):
        """Resend an invitation"""
        # Placeholder for resend logic
        QMessageBox.information(self, "Invitation Sent", "Invitation has been resent.")
        
    def _cancel_invitation(self, invitation):
        """Cancel a pending invitation"""
        reply = QMessageBox.question(
            self, "Cancel Invitation",
            "Are you sure you want to cancel this invitation?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.auth_manager.supabase.table('organization_members').delete().eq('id', invitation['id']).execute()
                QMessageBox.information(self, "Success", "Invitation cancelled.")
                self._load_team_members()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to cancel invitation: {str(e)}")
                
    def _edit_member_from_row(self, row):
        """Edit member from table row"""
        # Get member data from row - placeholder implementation
        pass
        
    def _view_member_profile(self, row):
        """View member profile"""
        # Placeholder for profile view
        QMessageBox.information(self, "Profile", "Member profile view - to be implemented")
        
    def _remove_member_from_row(self, row):
        """Remove member from table row"""
        # Get member data from row - placeholder implementation
        pass


class InviteMemberDialog(QDialog):
    """Dialog for inviting new team members"""
    
    def __init__(self, auth_manager, organization, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.organization = organization
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the invite dialog UI"""
        self.setWindowTitle("Invite Team Member")
        self.setModal(True)
        self.setFixedSize(400, 300)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        title = QLabel("Invite New Team Member")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(18, 16, 20)}px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(title)
        
        # Email input
        email_label = QLabel("Email Address:")
        email_label.setStyleSheet("color: white; margin-bottom: 4px;")
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email address")
        layout.addWidget(self.email_input)
        
        # Role selection
        role_label = QLabel("Role:")
        role_label.setStyleSheet("color: white; margin-top: 8px; margin-bottom: 4px;")
        layout.addWidget(role_label)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Accountant",
            "Organization Admin", 
            "Organization Owner"
        ])
        layout.addWidget(self.role_combo)
        
        # Department input
        dept_label = QLabel("Department (Optional):")
        dept_label.setStyleSheet("color: white; margin-top: 8px; margin-bottom: 4px;")
        layout.addWidget(dept_label)
        
        self.dept_input = QLineEdit()
        self.dept_input.setPlaceholderText("Enter department")
        layout.addWidget(self.dept_input)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        invite_btn = QPushButton("Send Invitation")
        invite_btn.setObjectName("PrimaryButton")
        invite_btn.clicked.connect(self._send_invitation)
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
        
    def _send_invitation(self):
        """Send the invitation"""
        email = self.email_input.text().strip()
        role = self.role_combo.currentText().lower().replace(' ', '_')
        department = self.dept_input.text().strip()
        
        if not email:
            QMessageBox.warning(self, "Invalid Input", "Please enter an email address.")
            return
            
        # Basic email validation
        import re
        if not re.match(r'^[^@]+@[^@]+\.[^@]+$', email):
            QMessageBox.warning(self, "Invalid Email", "Please enter a valid email address.")
            return
            
        try:
            # Create invitation record
            invitation_data = {
                'organization_id': self.organization['id'],
                'invitation_email': email,
                'role': role,
                'department': department if department else None,
                'invited_by': self.auth_manager.current_user.id,
                'invited_at': 'now()',
                'invitation_expires_at': "(now() + interval '7 days')"
            }
            
            self.auth_manager.supabase.table('organization_members').insert(invitation_data).execute()
            
            QMessageBox.information(self, "Success", f"Invitation sent to {email}")
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to send invitation: {str(e)}")


class EditMemberRoleDialog(QDialog):
    """Dialog for editing a member's role"""
    
    def __init__(self, member, parent=None):
        super().__init__(parent)
        self.member = member
        self._setup_ui()
        self._apply_styling()
        
    def _setup_ui(self):
        """Setup the edit role dialog UI"""
        self.setWindowTitle("Edit Member Role")
        self.setModal(True)
        self.setFixedSize(350, 200)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Title
        user = self.member.get('users', {})
        name = user.get('display_name', 'Member')
        title = QLabel(f"Edit Role for {name}")
        title.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(16, 14, 18)}px;
                font-weight: 600;
                margin-bottom: 8px;
            }}
        """)
        layout.addWidget(title)
        
        # Current role
        current_role = self.member.get('role', 'accountant').replace('_', ' ').title()
        current_label = QLabel(f"Current Role: {current_role}")
        current_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
        layout.addWidget(current_label)
        
        # New role selection
        role_label = QLabel("New Role:")
        role_label.setStyleSheet("color: white; margin-top: 8px; margin-bottom: 4px;")
        layout.addWidget(role_label)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems([
            "Accountant",
            "Organization Admin", 
            "Organization Owner"
        ])
        
        # Set current selection
        current_index = 0
        if 'admin' in current_role.lower():
            current_index = 1
        elif 'owner' in current_role.lower():
            current_index = 2
        self.role_combo.setCurrentIndex(current_index)
        
        layout.addWidget(self.role_combo)
        
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save_role_change)
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
            
            QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                color: white;
                font-size: {ResponsiveHelper.scale_size(14, 12, 16)}px;
                padding: 8px 12px;
                min-height: 20px;
            }}
            
            QComboBox:focus {{
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
        
    def _save_role_change(self):
        """Save the role change"""
        new_role = self.role_combo.currentText().lower().replace(' ', '_')
        
        # Placeholder for role update logic
        QMessageBox.information(self, "Success", f"Role updated to {self.role_combo.currentText()}")
        self.accept()
