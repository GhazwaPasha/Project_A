-- Add missing page permissions for team_management and organization_settings
INSERT INTO public.page_permissions (page_key, role, can_view, can_create, can_edit, can_delete) VALUES

-- Team Management
('team_management', 'super_admin', true, true, true, true),
('team_management', 'organization_owner', true, true, true, true),
('team_management', 'accountant', true, false, false, false),
('team_management', 'member', true, false, false, false),

-- Organization Settings
('organization_settings', 'super_admin', true, true, true, true),
('organization_settings', 'organization_owner', true, true, true, true),
('organization_settings', 'accountant', false, false, false, false),
('organization_settings', 'member', false, false, false, false)

ON CONFLICT (page_key, role) DO UPDATE SET
    can_view = EXCLUDED.can_view,
    can_create = EXCLUDED.can_create,
    can_edit = EXCLUDED.can_edit,
    can_delete = EXCLUDED.can_delete;
