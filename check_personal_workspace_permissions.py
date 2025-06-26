from src.core.config import DatabaseConfig
from supabase import create_client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Validate config
    DatabaseConfig.validate_config()
    
    # Create client with service key
    supabase = create_client(DatabaseConfig.SUPABASE_URL, DatabaseConfig.SUPABASE_SERVICE_KEY)
    
    # Get all permissions for organization_owner role
    permissions = supabase.table('page_permissions').select('*').eq('role', 'organization_owner').order('page_key').execute()
    
    logger.info(f'=== PERMISSIONS FOR ORGANIZATION_OWNER (Personal Workspace User) ===')
    logger.info(f'Total permissions: {len(permissions.data)}')
    
    viewable_pages = []
    for perm in permissions.data:
        page_key = perm['page_key']
        can_view = perm['can_view']
        can_create = perm['can_create']
        can_edit = perm['can_edit']
        can_delete = perm['can_delete']
        
        logger.info(f"{page_key:20} | View: {str(can_view):5} | Create: {str(can_create):5} | Edit: {str(can_edit):5} | Delete: {str(can_delete):5}")
        
        if can_view:
            viewable_pages.append(page_key)
    
    logger.info(f'\n=== PAGES VISIBLE TO PERSONAL WORKSPACE USERS ===')
    for i, page in enumerate(viewable_pages, 1):
        logger.info(f"{i:2}. {page}")
    
    # Also show what navigation tabs this maps to
    logger.info(f'\n=== CORRESPONDING NAVIGATION TABS ===')
    page_to_nav = {
        'dashboard': '0: Dashboard',
        'journal_entries': '1: Journal, 2: Ledger',
        'reports': '3: Trial Balance, 4: Reports', 
        'accounts': '5: Accounts',
        'settings': '7: Period Closing, 13: Settings',
        'team_management': '8: Team',
        'organization_settings': '9: Org Settings',
        'user_management': '10: User Mgmt',
        'platform_overview': '11: Platform (Super Admin)',
        'global_organizations': '12: Global Orgs (Super Admin)'
    }
    
    for page in viewable_pages:
        if page in page_to_nav:
            logger.info(f"  {page_to_nav[page]}")
    
except Exception as e:
    logger.error(f'Error: {e}')
    import traceback
    logger.error(traceback.format_exc())
