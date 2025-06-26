from src.core.config import DatabaseConfig
from supabase import create_client
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Validate config
    DatabaseConfig.validate_config()
    
    # Create client with service key for admin operations
    supabase = create_client(DatabaseConfig.SUPABASE_URL, DatabaseConfig.SUPABASE_SERVICE_KEY)
    
    # Execute the SQL directly using table insert
    permissions_to_add = [
        # Team Management
        {'page_key': 'team_management', 'role': 'super_admin', 'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True},
        {'page_key': 'team_management', 'role': 'organization_owner', 'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True},
        {'page_key': 'team_management', 'role': 'accountant', 'can_view': True, 'can_create': False, 'can_edit': False, 'can_delete': False},
        {'page_key': 'team_management', 'role': 'member', 'can_view': True, 'can_create': False, 'can_edit': False, 'can_delete': False},
        
        # Organization Settings
        {'page_key': 'organization_settings', 'role': 'super_admin', 'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True},
        {'page_key': 'organization_settings', 'role': 'organization_owner', 'can_view': True, 'can_create': True, 'can_edit': True, 'can_delete': True},
        {'page_key': 'organization_settings', 'role': 'accountant', 'can_view': False, 'can_create': False, 'can_edit': False, 'can_delete': False},
        {'page_key': 'organization_settings', 'role': 'member', 'can_view': False, 'can_create': False, 'can_edit': False, 'can_delete': False},
    ]
    
    for perm in permissions_to_add:
        try:
            # Try to insert, will fail if exists due to unique constraint
            result = supabase.table('page_permissions').insert(perm).execute()
            logger.info(f"Added permission for {perm['page_key']} - {perm['role']}")
        except Exception as e:
            if 'duplicate key value' in str(e).lower():
                # Update existing permission
                result = supabase.table('page_permissions').update({
                    'can_view': perm['can_view'],
                    'can_create': perm['can_create'],
                    'can_edit': perm['can_edit'],
                    'can_delete': perm['can_delete']
                }).eq('page_key', perm['page_key']).eq('role', perm['role']).execute()
                logger.info(f"Updated permission for {perm['page_key']} - {perm['role']}")
            else:
                logger.error(f"Error adding permission for {perm['page_key']} - {perm['role']}: {e}")
    
    # Verify permissions were added
    permissions = supabase.table('page_permissions').select('*').in_('page_key', ['team_management', 'organization_settings']).execute()
    logger.info(f'Total permissions for team_management and organization_settings: {len(permissions.data)}')
    for perm in permissions.data:
        logger.info(f"  {perm['page_key']} - {perm['role']}: view={perm['can_view']}, create={perm['can_create']}, edit={perm['can_edit']}, delete={perm['can_delete']}")
    
except Exception as e:
    logger.error(f'Error: {e}')
    import traceback
    logger.error(traceback.format_exc())
