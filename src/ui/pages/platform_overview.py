"""
Super admin platform overview page for system administrators
"""
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                            QTableWidget, QTableWidgetItem, QHeaderView, QFrame, 
                            QGroupBox, QProgressBar, QGridLayout, QStackedWidget, QButtonGroup, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont
from ..common import ResponsiveHelper
from ..components.widgets import PageHeader, MetricCard
from ..components.styles import ModernStyles, GlassmorphismHelper
from ..components.mica_effect import MicaEffect


class PlatformOverviewPage(QWidget):
    """Platform overview page for super administrators"""
    
    def __init__(self, system, auth_manager=None, parent=None):
        super().__init__(parent)
        self.system = system
        self.auth_manager = auth_manager
        self._setup_ui()
        self._apply_styling()
        self._load_platform_stats()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._load_platform_stats)
        self.refresh_timer.start(60000)  # Refresh every minute
        
    def _setup_ui(self):
        """Setup the platform overview UI"""
        main_layout = QVBoxLayout(self)
        responsive_margin = ResponsiveHelper.scale_size(32, 24, 48)
        main_layout.setContentsMargins(responsive_margin, 0,  # Remove top margin for seamless flow
                                     responsive_margin, responsive_margin)
        main_layout.setSpacing(16)  # Standardized spacing
        
        # Page header with admin actions
        header_layout = QHBoxLayout()
        
        header = PageHeader("Platform Overview", "System administration and monitoring dashboard")
        header_layout.addWidget(header)
        
        # Quick admin actions
        admin_actions_layout = QHBoxLayout()
        admin_actions_layout.addStretch()
        
        self.maintenance_btn = QPushButton("Maintenance Mode")
        self.maintenance_btn.setObjectName("WarningButton")
        self.maintenance_btn.clicked.connect(self._toggle_maintenance_mode)
        admin_actions_layout.addWidget(self.maintenance_btn)
        
        self.backup_btn = QPushButton("Create Backup")
        self.backup_btn.clicked.connect(self._create_system_backup)
        admin_actions_layout.addWidget(self.backup_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("PrimaryButton")
        self.refresh_btn.clicked.connect(self._load_platform_stats)
        admin_actions_layout.addWidget(self.refresh_btn)
        
        header_layout.addLayout(admin_actions_layout)
        main_layout.addLayout(header_layout)
        
        # Platform metrics
        self._create_metrics_section(main_layout)
        
        # Create custom tab selector with modern styling (matching journal page)
        self._create_tab_selector(main_layout)
        
        # Create stacked widget for tab content
        self.stacked_widget = QStackedWidget()
        
        # System health tab
        self.health_tab = self._create_system_health_tab()
        self.stacked_widget.addWidget(self.health_tab)
        
        # Recent activity tab
        self.activity_tab = self._create_activity_tab()
        self.stacked_widget.addWidget(self.activity_tab)
        
        # Alerts tab
        self.alerts_tab = self._create_alerts_tab()
        self.stacked_widget.addWidget(self.alerts_tab)
        
        # Set default tab
        self.stacked_widget.setCurrentIndex(0)
        main_layout.addWidget(self.stacked_widget, 1)  # Use default stretch factor for natural spacing
    
    def _create_tab_selector(self, layout):
        """Create tab selector with modern styling matching journal page."""
        # Container for tab selector
        tab_container_layout = QHBoxLayout()
        tab_container_layout.setContentsMargins(0, 8, 0, 8)  # Match journal tab margins
        tab_container_layout.setSpacing(12)
        
        # Create container frame like level filter
        tab_group = QFrame()
        tab_group.setStyleSheet("""
            QFrame {
                background: rgba(255, 255, 255, 0.03);
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                padding: 4px;
            }
        """)
        
        tab_layout = QHBoxLayout(tab_group)
        tab_layout.setSpacing(4)
        tab_layout.setContentsMargins(4, 4, 4, 4)
        
        # Tab buttons with modern styling
        self.tab_buttons = QButtonGroup(self)
        tab_options = [("System Health", 0), ("Recent Activity", 1), ("Alerts", 2)]
        
        for i, (tab_name, tab_index) in enumerate(tab_options):
            btn = QPushButton(tab_name)
            btn.setCheckable(True)
            if i == 0:  # Default to first tab
                btn.setChecked(True)
            btn.setStyleSheet(self._get_tab_filter_button_style())
            btn.clicked.connect(lambda checked, idx=tab_index: self._switch_tab(idx))
            self.tab_buttons.addButton(btn, tab_index)
            tab_layout.addWidget(btn)
        
        tab_container_layout.addWidget(tab_group)
        tab_container_layout.addStretch()  # Push tabs to the left
        
        layout.addLayout(tab_container_layout)
        
    def _switch_tab(self, tab_index):
        """Switch to the specified tab."""
        self.stacked_widget.setCurrentIndex(tab_index)
        
    def _get_tab_filter_button_style(self):
        """Get modern tab filter button styling to match journal page."""
        return """
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 13px;
                font-weight: 500;
                margin: 0;
                min-width: 80px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.08);
                color: white;
            }
            QPushButton:checked {
                background: rgba(0, 120, 215, 0.3);
                color: white;
            }
            QPushButton:checked:hover {
                background: rgba(0, 120, 215, 0.4);
            }
        """
        
    def _create_metrics_section(self, main_layout):
        """Create the platform metrics cards section"""
        metrics_layout = QGridLayout()
        metrics_layout.setSpacing(ResponsiveHelper.scale_size(16, 12, 20))
        
        # Row 1: Core metrics
        self.total_orgs_card = MetricCard("Total Organizations", "0", "↗ +5 this month", clickable=True)
        self.total_users_card = MetricCard("Total Users", "0", "↗ +23 this month", clickable=True)
        self.active_sessions_card = MetricCard("Active Sessions", "0", "Real-time", clickable=True)
        self.monthly_revenue_card = MetricCard("Monthly Revenue", "$0", "↗ +12.5%", clickable=True)
        
        metrics_layout.addWidget(self.total_orgs_card, 0, 0)
        metrics_layout.addWidget(self.total_users_card, 0, 1)
        metrics_layout.addWidget(self.active_sessions_card, 0, 2)
        metrics_layout.addWidget(self.monthly_revenue_card, 0, 3)
        
        # Row 2: System metrics
        self.system_uptime_card = MetricCard("System Uptime", "99.9%", "Last 30 days", clickable=True)
        self.db_performance_card = MetricCard("DB Performance", "Good", "Avg response: 45ms", clickable=True)
        self.storage_used_card = MetricCard("Storage Used", "0 GB", "of 1TB available", clickable=True)
        self.api_requests_card = MetricCard("API Requests", "0", "Last 24 hours", clickable=True)
        
        metrics_layout.addWidget(self.system_uptime_card, 1, 0)
        metrics_layout.addWidget(self.db_performance_card, 1, 1)
        metrics_layout.addWidget(self.storage_used_card, 1, 2)
        metrics_layout.addWidget(self.api_requests_card, 1, 3)
        
        main_layout.addLayout(metrics_layout)
        
    def _create_system_health_tab(self):
        """Create the system health monitoring tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(20)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # System services status
        services_group = QGroupBox("System Services")
        services_layout = QVBoxLayout(services_group)
        
        # Service status indicators
        services = [
            ("Web Application", "Healthy", "200ms avg response"),
            ("Database", "Healthy", "45ms avg query time"),
            ("File Storage", "Healthy", "99.9% availability"),
            ("Email Service", "Healthy", "2min avg delivery"),
            ("Backup Service", "Healthy", "Last backup: 2 hours ago"),
            ("Monitoring", "Healthy", "All checks passing")
        ]
        
        for service_name, status, details in services:
            service_layout = QHBoxLayout()
            
            # Service name
            name_label = QLabel(service_name)
            name_label.setStyleSheet("color: white; font-weight: 600; min-width: 120px;")
            service_layout.addWidget(name_label)
            
            # Status indicator
            status_label = QLabel(status)
            if status == "Healthy":
                status_label.setStyleSheet("color: #4CAF50; font-weight: 600; min-width: 80px;")
            else:
                status_label.setStyleSheet("color: #F44336; font-weight: 600; min-width: 80px;")
            service_layout.addWidget(status_label)
            
            # Details
            details_label = QLabel(details)
            details_label.setStyleSheet("color: rgba(255, 255, 255, 0.7);")
            service_layout.addWidget(details_label)
            
            service_layout.addStretch()
            services_layout.addLayout(service_layout)
            
        layout.addWidget(services_group)
        
        # Resource usage
        resources_group = QGroupBox("Resource Usage")
        resources_layout = QVBoxLayout(resources_group)
        
        # CPU usage
        cpu_layout = QHBoxLayout()
        cpu_layout.addWidget(QLabel("CPU Usage:"))
        self.cpu_progress = QProgressBar()
        self.cpu_progress.setMaximum(100)
        self.cpu_progress.setValue(35)
        self.cpu_progress.setFormat("35%")
        cpu_layout.addWidget(self.cpu_progress)
        resources_layout.addLayout(cpu_layout)
        
        # Memory usage
        memory_layout = QHBoxLayout()
        memory_layout.addWidget(QLabel("Memory Usage:"))
        self.memory_progress = QProgressBar()
        self.memory_progress.setMaximum(100)
        self.memory_progress.setValue(62)
        self.memory_progress.setFormat("62% (4.2GB / 8GB)")
        memory_layout.addWidget(self.memory_progress)
        resources_layout.addLayout(memory_layout)
        
        # Disk usage
        disk_layout = QHBoxLayout()
        disk_layout.addWidget(QLabel("Disk Usage:"))
        self.disk_progress = QProgressBar()
        self.disk_progress.setMaximum(100)
        self.disk_progress.setValue(28)
        self.disk_progress.setFormat("28% (280GB / 1TB)")
        disk_layout.addWidget(self.disk_progress)
        resources_layout.addLayout(disk_layout)
        
        layout.addWidget(resources_group)
        layout.addStretch()
        
        
        return tab
        
    def _create_activity_tab(self):
        """Create the recent activity monitoring tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Activity filters
        filter_layout = QHBoxLayout()
        
        activity_label = QLabel("Filter Activity:")
        activity_label.setStyleSheet("color: white; margin-right: 8px;")
        filter_layout.addWidget(activity_label)
        
        self.activity_filter = QComboBox()
        self.activity_filter.addItems([
            "All Activity", "User Registrations", "Organization Created", 
            "Login Activity", "System Events", "Errors"
        ])
        filter_layout.addWidget(self.activity_filter)
        
        filter_layout.addStretch()
        
        auto_refresh_label = QLabel("Auto-refresh:")
        auto_refresh_label.setStyleSheet("color: white; margin-right: 8px;")
        filter_layout.addWidget(auto_refresh_label)
        
        from PyQt6.QtWidgets import QCheckBox
        self.auto_refresh_check = QCheckBox("Enabled")
        self.auto_refresh_check.setChecked(True)
        self.auto_refresh_check.stateChanged.connect(self._toggle_auto_refresh)
        filter_layout.addWidget(self.auto_refresh_check)
        
        layout.addLayout(filter_layout)
        
        # Activity table
        self.activity_table = QTableWidget()
        self.activity_table.setObjectName("ModernTable")
        self.activity_table.setColumnCount(5)
        self.activity_table.setHorizontalHeaderLabels([
            "Timestamp", "Event Type", "User/Organization", "Details", "IP Address"
        ])
        
        # Configure table
        activity_header = self.activity_table.horizontalHeader()
        activity_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        activity_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        activity_header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        activity_header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        activity_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        
        self.activity_table.setAlternatingRowColors(True)
        
        # Sample activity data
        sample_activity = [
            ["2024-01-15 15:30:22", "User Registration", "john.doe@newcompany.com", "New user registered", "192.168.1.100"],
            ["2024-01-15 15:28:15", "Organization Created", "TechCorp Inc.", "New organization created by admin", "192.168.1.101"],
            ["2024-01-15 15:25:10", "Login", "jane.smith@company.com", "Successful login", "192.168.1.102"],
            ["2024-01-15 15:22:05", "System Event", "Backup Service", "Automated backup completed", "localhost"],
            ["2024-01-15 15:20:30", "Login", "admin@platform.com", "Super admin login", "192.168.1.103"],
        ]
        
        self.activity_table.setRowCount(len(sample_activity))
        for row, activity in enumerate(sample_activity):
            for col, value in enumerate(activity):
                self.activity_table.setItem(row, col, QTableWidgetItem(str(value)))
                
        layout.addWidget(self.activity_table)
        
        
        return tab
        
    def _create_alerts_tab(self):
        """Create the system alerts tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Alert summary
        alert_summary_layout = QHBoxLayout()
        
        critical_alerts = QLabel("🔴 Critical: 0")
        critical_alerts.setStyleSheet("color: #F44336; font-weight: 600; font-size: 14px;")
        alert_summary_layout.addWidget(critical_alerts)
        
        warning_alerts = QLabel("🟡 Warning: 2")
        warning_alerts.setStyleSheet("color: #FF9800; font-weight: 600; font-size: 14px;")
        alert_summary_layout.addWidget(warning_alerts)
        
        info_alerts = QLabel("🔵 Info: 5")
        info_alerts.setStyleSheet("color: #2196F3; font-weight: 600; font-size: 14px;")
        alert_summary_layout.addWidget(info_alerts)
        
        alert_summary_layout.addStretch()
        
        clear_all_btn = QPushButton("Clear All Resolved")
        clear_all_btn.clicked.connect(self._clear_resolved_alerts)
        alert_summary_layout.addWidget(clear_all_btn)
        
        layout.addLayout(alert_summary_layout)
        
        # Alerts table
        self.alerts_table = QTableWidget()
        self.alerts_table.setObjectName("ModernTable")
        self.alerts_table.setColumnCount(6)
        self.alerts_table.setHorizontalHeaderLabels([
            "Severity", "Alert Type", "Message", "First Occurred", "Last Occurred", "Actions"
        ])
        
        # Configure alerts table
        alerts_header = self.alerts_table.horizontalHeader()
        alerts_header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        alerts_header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        alerts_header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        alerts_header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        alerts_header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        alerts_header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        
        self.alerts_table.setAlternatingRowColors(True)
        
        # Sample alerts
        sample_alerts = [
            ["Warning", "High Memory Usage", "System memory usage above 80%", "2024-01-15 14:30", "2024-01-15 15:30"],
            ["Warning", "Slow Database Query", "Query execution time exceeded 5 seconds", "2024-01-15 13:45", "2024-01-15 15:25"],
            ["Info", "New Organization", "5 new organizations created today", "2024-01-15 09:00", "2024-01-15 15:20"],
            ["Info", "Backup Completed", "Daily backup completed successfully", "2024-01-15 02:00", "2024-01-15 02:00"],
            ["Info", "User Registration Spike", "User registrations 25% above average", "2024-01-15 10:30", "2024-01-15 15:15"],
        ]
        
        self.alerts_table.setRowCount(len(sample_alerts))
        for row, alert in enumerate(sample_alerts):
            # Severity with color
            severity_item = QTableWidgetItem(alert[0])
            if alert[0] == "Critical":
                severity_item.setBackground(Qt.GlobalColor.darkRed)
            elif alert[0] == "Warning":
                severity_item.setBackground(Qt.GlobalColor.darkYellow)
            else:
                severity_item.setBackground(Qt.GlobalColor.darkBlue)
            self.alerts_table.setItem(row, 0, severity_item)
            
            # Other columns
            for col in range(1, 5):
                self.alerts_table.setItem(row, col, QTableWidgetItem(alert[col]))
                
            # Action buttons
            actions_widget = self._create_alert_actions_widget(alert)
            self.alerts_table.setCellWidget(row, 5, actions_widget)
            
        layout.addWidget(self.alerts_table)
        
        
        return tab
        
    def _create_alert_actions_widget(self, alert):
        """Create actions widget for an alert"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(4)
        
        # Acknowledge button
        ack_btn = QPushButton("Ack")
        ack_btn.setMaximumSize(50, 24)
        ack_btn.clicked.connect(lambda: self._acknowledge_alert(alert))
        layout.addWidget(ack_btn)
        
        # Resolve button
        resolve_btn = QPushButton("Resolve")
        resolve_btn.setMaximumSize(60, 24)
        resolve_btn.clicked.connect(lambda: self._resolve_alert(alert))
        layout.addWidget(resolve_btn)
        
        return widget
        
    def _apply_styling(self):
        """Apply styling to the platform overview page"""
        MicaEffect.apply_mica(self, dark_mode=True)
        GlassmorphismHelper.apply_main_container_effect(self)
        
        self.setStyleSheet(f"""
            QTabWidget#PlatformTabs {{
                background: transparent;
                border: none;
            }}
            
            QTabWidget#PlatformTabs::pane {{
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
            
            QProgressBar {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                text-align: center;
                color: white;
                font-size: {ResponsiveHelper.scale_size(11, 10, 12)}px;
                height: 18px;
            }}
            
            QProgressBar::chunk {{
                background: rgba(74, 144, 226, 0.8);
                border-radius: 5px;
            }}
            
            QComboBox, QCheckBox {{
                color: white;
                font-size: {ResponsiveHelper.scale_size(12, 11, 13)}px;
            }}
            
            QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
                padding: 4px 8px;
                min-width: 120px;
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
            
            QPushButton#WarningButton {{
                background: rgba(255, 152, 0, 0.8);
                border: 1px solid rgba(255, 152, 0, 1.0);
            }}
            
            QPushButton#WarningButton:hover {{
                background: rgba(255, 152, 0, 1.0);
            }}
        """)
        
    def _load_platform_stats(self):
        """Load platform statistics"""
        try:
            if not self.auth_manager or not hasattr(self.auth_manager, 'supabase'):
                return
                
            # Get organization count
            orgs_result = self.auth_manager.supabase.table('organizations').select('count').execute()
            org_count = len(orgs_result.data) if orgs_result.data else 0
            self.total_orgs_card.set_value(str(org_count))
            
            # Get user count  
            users_result = self.auth_manager.supabase.table('users').select('count').execute()
            user_count = len(users_result.data) if users_result.data else 0
            self.total_users_card.set_value(str(user_count))
            
            # Mock data for other metrics
            self.active_sessions_card.set_value("47")
            self.monthly_revenue_card.set_value("$12,450")
            self.system_uptime_card.set_value("99.9%")
            self.db_performance_card.set_value("Good")
            self.storage_used_card.set_value("280 GB")
            self.api_requests_card.set_value("15,432")
            
        except Exception as e:
            print(f"Error loading platform stats: {e}")
            
    def _toggle_maintenance_mode(self):
        """Toggle system maintenance mode"""
        from PyQt6.QtWidgets import QMessageBox
        reply = QMessageBox.question(
            self, "Maintenance Mode",
            "Are you sure you want to enable maintenance mode?\n\nThis will prevent users from accessing the system.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Maintenance Mode", "Maintenance mode enabled.")
            
    def _create_system_backup(self):
        """Create system backup"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Backup", "System backup initiated. You will be notified when complete.")
        
    def _toggle_auto_refresh(self, state):
        """Toggle auto-refresh for activity monitoring"""
        if state == Qt.CheckState.Checked.value:
            self.refresh_timer.start(60000)
        else:
            self.refresh_timer.stop()
            
    def _clear_resolved_alerts(self):
        """Clear all resolved alerts"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Alerts Cleared", "All resolved alerts have been cleared.")
        
    def _acknowledge_alert(self, alert):
        """Acknowledge an alert"""
        print(f"Alert acknowledged: {alert[1]}")
        
    def _resolve_alert(self, alert):
        """Resolve an alert"""
        print(f"Alert resolved: {alert[1]}")
        
    def closeEvent(self, event):
        """Clean up when closing"""
        if hasattr(self, 'refresh_timer'):
            self.refresh_timer.stop()
        event.accept()
    
    def refresh_data(self):
        """Refresh platform overview data when organization context changes."""
        try:
            print("🔄 Platform Overview: Refreshing data due to organization change...")
            self._load_platform_stats()
        except Exception as e:
            print(f"Error refreshing platform overview data: {e}")