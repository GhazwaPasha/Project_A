from PyQt6.QtCore import QThread, pyqtSignal, QObject, QTimer
from typing import Dict, Any, Optional, List
import time
import logging
from dataclasses import dataclass
from enum import Enum

class LoadingPriority(Enum):
    HIGH = "high"      # Current page - load immediately
    MEDIUM = "medium"  # Adjacent pages - load soon
    LOW = "low"        # Other pages - load when idle

@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    org_id: str
    is_valid: bool = True

class DataLoaderThread(QThread):
    """Background thread for loading page data"""
    data_loaded = pyqtSignal(str, str, dict)  # page_name, org_id, data
    loading_complete = pyqtSignal(str)  # org_id
    error_occurred = pyqtSignal(str, str)  # page_name, error_message
    
    def __init__(self, auth_manager, session_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        self.org_id = None
        self.pages_to_load = []
        self.logger = logging.getLogger(__name__)
    
    def load_pages(self, org_id: str, pages: List[str]):
        """Load data for specified pages in background"""
        self.org_id = org_id
        self.pages_to_load = pages
        self.start()
    
    def run(self):
        """Background thread execution"""
        try:
            for page_name in self.pages_to_load:
                try:
                    if self.org_id:  # Check if org_id is not None
                        data = self._load_page_data(page_name, self.org_id)
                        self.data_loaded.emit(page_name, self.org_id, data)
                    else:
                        self.logger.error("org_id is None, skipping page load")
                        self.error_occurred.emit(page_name, "org_id is None")
                except Exception as e:
                    self.logger.error(f"Error loading {page_name}: {e}")
                    self.error_occurred.emit(page_name, str(e))
            
            if self.org_id:
                self.loading_complete.emit(self.org_id)
            
        except Exception as e:
            self.logger.error(f"DataLoaderThread error: {e}")
    
    def _load_page_data(self, page_name: str, org_id: str) -> dict:
        """Load data for a specific page"""
        # Set organization context for this thread
        if self.session_manager:
            self.session_manager.set_active_organization(org_id)
        
        # Page-specific data loading logic
        if page_name == "DashboardPage":
            return self._load_dashboard_data(org_id)
        elif page_name == "JournalPage":
            return self._load_journal_data(org_id)
        elif page_name == "LedgerPage":
            return self._load_ledger_data(org_id)
        elif page_name == "ReportsPage":
            return self._load_reports_data(org_id)
        elif page_name == "HierarchicalAccountsPage":
            return self._load_accounts_data(org_id)
        elif page_name == "RemindersTasksPage":
            return self._load_reminders_data(org_id)
        else:
            return {"status": "loaded", "timestamp": time.time()}
    
    def _load_dashboard_data(self, org_id: str) -> dict:
        """Load dashboard-specific data"""
        try:
            # Load financial ratios and summary data
            from ..core.financial_ratios import FinancialRatioCalculator
            calculator = FinancialRatioCalculator(self.auth_manager.db_manager)
            ratios = calculator.calculate_ratios(org_id)
            
            return {
                "ratios": ratios,
                "status": "loaded",
                "timestamp": time.time()
            }
        except Exception as e:
            self.logger.error(f"Error loading dashboard data: {e}")
            return {"status": "error", "error": str(e)}
    
    def _load_journal_data(self, org_id: str) -> dict:
        """Load journal-specific data"""
        try:
            # Load recent journal entries
            if self.auth_manager.db_manager and self.auth_manager.db_manager.supabase:
                result = self.auth_manager.db_manager.supabase.table('journal_entries')\
                    .select('*')\
                    .eq('organization_id', org_id)\
                    .order('created_at', desc=True)\
                    .limit(50)\
                    .execute()
                
                return {
                    "journal_entries": result.data if result.data else [],
                    "status": "loaded",
                    "timestamp": time.time()
                }
            else:
                return {"status": "error", "error": "No database connection"}
        except Exception as e:
            self.logger.error(f"Error loading journal data: {e}")
            return {"status": "error", "error": str(e)}
    
    def _load_ledger_data(self, org_id: str) -> dict:
        """Load ledger-specific data"""
        try:
            # Load account balances
            if self.auth_manager.db_manager and self.auth_manager.db_manager.supabase:
                result = self.auth_manager.db_manager.supabase.table('accounts')\
                    .select('*')\
                    .eq('organization_id', org_id)\
                    .execute()
                
                return {
                    "accounts": result.data if result.data else [],
                    "status": "loaded",
                    "timestamp": time.time()
                }
            else:
                return {"status": "error", "error": "No database connection"}
        except Exception as e:
            self.logger.error(f"Error loading ledger data: {e}")
            return {"status": "error", "error": str(e)}
    
    def _load_reports_data(self, org_id: str) -> dict:
        """Load reports-specific data"""
        return {
            "reports_available": ["income_statement", "balance_sheet", "cash_flow"],
            "status": "loaded",
            "timestamp": time.time()
        }
    
    def _load_accounts_data(self, org_id: str) -> dict:
        """Load accounts-specific data"""
        try:
            if self.auth_manager.db_manager and self.auth_manager.db_manager.supabase:
                result = self.auth_manager.db_manager.supabase.table('accounts')\
                    .select('*')\
                    .eq('organization_id', org_id)\
                    .order('account_number')\
                    .execute()
                
                return {
                    "accounts": result.data if result.data else [],
                    "status": "loaded",
                    "timestamp": time.time()
                }
            else:
                return {"status": "error", "error": "No database connection"}
        except Exception as e:
            self.logger.error(f"Error loading accounts data: {e}")
            return {"status": "error", "error": str(e)}
    
    def _load_reminders_data(self, org_id: str) -> dict:
        """Load reminders-specific data"""
        try:
            # Load user-specific reminders
            if self.session_manager:
                user_id = self.session_manager.get_current_user_id()
                if user_id:
                    reminders_file = f"user_data/user_{user_id}_org_{org_id}/reminders.json"
                    
                    import json
                    import os
                    if os.path.exists(reminders_file):
                        with open(reminders_file, 'r') as f:
                            reminders = json.load(f)
                    else:
                        reminders = []
                    
                    return {
                        "reminders": reminders,
                        "status": "loaded",
                        "timestamp": time.time()
                    }
                else:
                    return {"status": "error", "error": "No user ID available"}
            else:
                return {"status": "error", "error": "No session manager"}
        except Exception as e:
            self.logger.error(f"Error loading reminders data: {e}")
            return {"status": "error", "error": str(e)}
    


class PageManager(QObject):
    """Manages page data loading, caching, and background operations"""
    
    def __init__(self, auth_manager, session_manager):
        super().__init__()
        self.auth_manager = auth_manager
        self.session_manager = session_manager
        self.logger = logging.getLogger(__name__)
        
        # Cache management
        self.page_cache: Dict[tuple, CacheEntry] = {}  # (page_name, org_id) -> CacheEntry
        self.cache_ttl = 300  # 5 minutes cache TTL
        
        # Background loading
        self.data_loader = DataLoaderThread(auth_manager, session_manager)
        self.data_loader.data_loaded.connect(self._on_data_loaded)
        self.data_loader.loading_complete.connect(self._on_loading_complete)
        self.data_loader.error_occurred.connect(self._on_loading_error)
        
        # Loading state tracking
        self.loading_pages: Dict[str, set] = {}  # org_id -> set of loading pages
        self.loading_callbacks: Dict[str, List[callable]] = {}  # org_id -> list of callbacks
        
        # Idle loading timer
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self._process_idle_loading)
        self.idle_timer.setSingleShot(True)
        self.idle_timer.start(1000)  # Start idle processing after 1 second
    
    def switch_workspace(self, org_id: str, org_name: str, callback: callable = None):
        """Switch workspace with optimized loading strategy"""
        self.logger.info(f"Switching to workspace: {org_name} ({org_id})")
        
        # Clear old cache entries for other organizations
        self._cleanup_cache(org_id)
        
        # Get current page and determine loading priorities
        current_page = self._get_current_page_name()
        adjacent_pages = self._get_adjacent_pages(current_page)
        other_pages = self._get_other_pages(current_page, adjacent_pages)
        
        # For workspace switching, we want to load ALL pages to ensure data is available
        # when user navigates to any page
        all_pages = [current_page] + adjacent_pages + other_pages
        
        # Priority 1: Load current page immediately (if not cached)
        if not self._is_cache_valid(current_page, org_id):
            self._load_page_priority(current_page, org_id, LoadingPriority.HIGH)
        
        # Priority 2: Load all other pages in background (not just adjacent)
        remaining_pages = [page for page in all_pages if page != current_page]
        if remaining_pages:
            self._load_pages_priority(remaining_pages, org_id, LoadingPriority.MEDIUM)
        
        # Register callback for completion
        if callback:
            if org_id not in self.loading_callbacks:
                self.loading_callbacks[org_id] = []
            self.loading_callbacks[org_id].append(callback)
    
    def ensure_all_pages_loaded(self, org_id: str):
        """Ensure all pages have data loaded for the given organization"""
        self.logger.info(f"Ensuring all pages loaded for organization: {org_id}")
        
        # Get all available pages
        all_pages = self._get_all_available_pages()
        
        # Load all pages in background thread to avoid blocking UI
        def load_all_pages():
            for page_name in all_pages:
                if not self._is_cache_valid(page_name, org_id):
                    self.logger.debug(f"Loading missing data for page: {page_name}")
                    self._load_page_priority(page_name, org_id, LoadingPriority.MEDIUM)
        
        # Use QTimer to defer loading to next event loop cycle
        QTimer.singleShot(0, load_all_pages)
    
    def _get_all_available_pages(self) -> List[str]:
        """Get list of all available page names"""
        return [
            'dashboard', 'journal', 'ledger', 'trial_balance', 'reports',
            'accounts', 'reminders', 'period_closing', 'team_management',
            'organization_settings', 'user_management', 'platform_overview',
            'global_organizations', 'settings'
        ]
    
    def get_page_data(self, page_name: str, org_id: str) -> Optional[dict]:
        """Get cached data for a page, load if necessary"""
        if self._is_cache_valid(page_name, org_id):
            cache_entry = self.page_cache.get((page_name, org_id))
            if cache_entry and cache_entry.is_valid:
                return cache_entry.data
        
        # Load data if not cached or invalid
        self._load_page_priority(page_name, org_id, LoadingPriority.HIGH)
        return None
    
    def _is_cache_valid(self, page_name: str, org_id: str) -> bool:
        """Check if cached data is still valid"""
        cache_entry = self.page_cache.get((page_name, org_id))
        if not cache_entry:
            return False
        
        # Check if cache has expired
        if time.time() - cache_entry.timestamp > self.cache_ttl:
            return False
        
        return cache_entry.is_valid
    
    def _cleanup_cache(self, current_org_id: str):
        """Remove cache entries for other organizations"""
        keys_to_remove = []
        for (page_name, org_id) in self.page_cache.keys():
            if org_id != current_org_id:
                keys_to_remove.append((page_name, org_id))
        
        for key in keys_to_remove:
            del self.page_cache[key]
    
    def _load_page_priority(self, page_name: str, org_id: str, priority: LoadingPriority):
        """Load a single page with specified priority"""
        if priority == LoadingPriority.HIGH:
            # Load immediately
            self._load_pages_immediate([page_name], org_id)
        elif priority == LoadingPriority.MEDIUM:
            # Load in background
            self._load_pages_background([page_name], org_id)
        else:
            # Schedule for idle loading
            self._schedule_idle_loading([page_name], org_id)
    
    def _load_pages_priority(self, pages: List[str], org_id: str, priority: LoadingPriority):
        """Load multiple pages with specified priority"""
        if priority == LoadingPriority.HIGH:
            self._load_pages_immediate(pages, org_id)
        elif priority == LoadingPriority.MEDIUM:
            self._load_pages_background(pages, org_id)
        else:
            self._schedule_idle_loading(pages, org_id)
    
    def _load_pages_immediate(self, pages: List[str], org_id: str):
        """Load pages immediately in current thread"""
        for page_name in pages:
            try:
                data = self.data_loader._load_page_data(page_name, org_id)
                self._cache_data(page_name, org_id, data)
            except Exception as e:
                self.logger.error(f"Error loading {page_name} immediately: {e}")
    
    def _load_pages_background(self, pages: List[str], org_id: str):
        """Load pages in background thread"""
        if org_id not in self.loading_pages:
            self.loading_pages[org_id] = set()
        
        # Add pages to loading set
        self.loading_pages[org_id].update(pages)
        
        # Start background loading
        if not self.data_loader.isRunning():
            self.data_loader.load_pages(org_id, pages)
    
    def _schedule_idle_loading(self, pages: List[str], org_id: str):
        """Schedule pages for idle loading"""
        # Store pages to load when idle
        if not hasattr(self, '_idle_pages'):
            self._idle_pages = {}
        
        if org_id not in self._idle_pages:
            self._idle_pages[org_id] = []
        
        self._idle_pages[org_id].extend(pages)
    
    def _process_idle_loading(self):
        """Process idle loading queue"""
        if hasattr(self, '_idle_pages') and self._idle_pages:
            for org_id, pages in self._idle_pages.items():
                if pages and not self.data_loader.isRunning():
                    # Load a few pages at a time
                    pages_to_load = pages[:3]  # Load 3 pages at a time
                    self._idle_pages[org_id] = pages[3:]  # Keep remaining pages
                    
                    self._load_pages_background(pages_to_load, org_id)
        
        # Restart timer for next idle processing
        self.idle_timer.start(2000)  # Check every 2 seconds
    
    def _on_data_loaded(self, page_name: str, org_id: str, data: dict):
        """Handle data loaded from background thread"""
        self._cache_data(page_name, org_id, data)
        
        # Remove from loading set
        if org_id in self.loading_pages:
            self.loading_pages[org_id].discard(page_name)
    
    def _on_loading_complete(self, org_id: str):
        """Handle loading completion for an organization"""
        # Call registered callbacks
        if org_id in self.loading_callbacks:
            for callback in self.loading_callbacks[org_id]:
                try:
                    callback()
                except Exception as e:
                    self.logger.error(f"Error in loading callback: {e}")
            
            del self.loading_callbacks[org_id]
    
    def _on_loading_error(self, page_name: str, error_message: str):
        """Handle loading errors"""
        self.logger.error(f"Error loading {page_name}: {error_message}")
    
    def _cache_data(self, page_name: str, org_id: str, data: dict):
        """Cache data for a page"""
        cache_entry = CacheEntry(
            data=data,
            timestamp=time.time(),
            org_id=org_id,
            is_valid=True
        )
        self.page_cache[(page_name, org_id)] = cache_entry
    
    def set_current_page_getter(self, getter_func):
        """Set a function to get the current page name"""
        self._current_page_getter = getter_func
    
    def _get_current_page_name(self) -> str:
        """Get current page name using the provided getter"""
        if hasattr(self, '_current_page_getter'):
            return self._current_page_getter()
        return "DashboardPage"  # Default
    
    def _get_adjacent_pages(self, current_page: str) -> List[str]:
        """Get pages adjacent to current page"""
        # Define page adjacency based on your navigation structure
        page_adjacency = {
            "DashboardPage": ["JournalPage", "ReportsPage"],
            "JournalPage": ["DashboardPage", "LedgerPage"],
            "LedgerPage": ["JournalPage", "TrialBalancePage"],
            "TrialBalancePage": ["LedgerPage", "ReportsPage"],
            "ReportsPage": ["TrialBalancePage", "HierarchicalAccountsPage"],
            "HierarchicalAccountsPage": ["ReportsPage", "RemindersTasksPage"],
        }
        
        return page_adjacency.get(current_page, [])
    
    def _get_other_pages(self, current_page: str, adjacent_pages: List[str]) -> List[str]:
        """Get all other pages not current or adjacent"""
        all_pages = [
            "DashboardPage", "JournalPage", "LedgerPage", "TrialBalancePage",
            "ReportsPage", "HierarchicalAccountsPage", "RemindersTasksPage",
            "PeriodClosingPage", "TeamManagementPage", "OrganizationSettingsPage",
            "UserManagementPage", "PlatformOverviewPage", "GlobalOrganizationsPage",
            "SettingsPage"
        ]
        
        exclude_pages = [current_page] + adjacent_pages
        return [page for page in all_pages if page not in exclude_pages]
    
    def invalidate_cache(self, page_name: str = None, org_id: str = None):
        """Invalidate cache entries"""
        if page_name and org_id:
            # Invalidate specific page
            key = (page_name, org_id)
            if key in self.page_cache:
                self.page_cache[key].is_valid = False
        elif org_id:
            # Invalidate all pages for organization
            for key in list(self.page_cache.keys()):
                if key[1] == org_id:
                    self.page_cache[key].is_valid = False
        else:
            # Invalidate all cache
            for cache_entry in self.page_cache.values():
                cache_entry.is_valid = False 