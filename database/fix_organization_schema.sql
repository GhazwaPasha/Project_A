-- ===============================================
-- FIX ORGANIZATION SCHEMA AND CLEANUP
-- ===============================================
-- This script fixes the organization schema to properly handle
-- personal vs multi-member organizations and adds proper cleanup

-- 1. Add missing columns to organizations table
ALTER TABLE public.organizations 
ADD COLUMN IF NOT EXISTS organization_type TEXT DEFAULT 'organization' 
CHECK (organization_type IN ('personal', 'organization'));

ALTER TABLE public.organizations 
ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES public.users(id) ON DELETE CASCADE;

-- 2. Migrate existing data from settings JSON to proper columns
UPDATE public.organizations 
SET organization_type = 'personal'
WHERE settings ->> 'workspace_type' = 'personal';

UPDATE public.organizations 
SET organization_type = 'organization'
WHERE settings ->> 'workspace_type' IS NULL OR settings ->> 'workspace_type' != 'personal';

-- 3. Set created_by for personal workspaces (find owner from organization_members)
UPDATE public.organizations 
SET created_by = (
    SELECT om.user_id 
    FROM public.organization_members om 
    WHERE om.organization_id = organizations.id 
    AND om.role = 'organization_owner' 
    LIMIT 1
)
WHERE organization_type = 'personal';

-- 4. Create function to clean up personal workspaces when user is deleted
CREATE OR REPLACE FUNCTION public.cleanup_personal_workspace()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    -- Delete personal workspaces created by this user
    DELETE FROM public.organizations 
    WHERE created_by = OLD.id 
    AND organization_type = 'personal';
    
    RAISE LOG 'Cleaned up personal workspace for deleted user: % (ID: %)', OLD.email, OLD.id;
    RETURN OLD;
END;
$$;

-- 5. Create trigger for cleanup
DROP TRIGGER IF EXISTS cleanup_user_personal_workspace ON public.users;
CREATE TRIGGER cleanup_user_personal_workspace
    BEFORE DELETE ON public.users
    FOR EACH ROW
    EXECUTE FUNCTION public.cleanup_personal_workspace();

-- 6. Update the user creation trigger to use proper columns
CREATE OR REPLACE FUNCTION public.handle_new_auth_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    extracted_first_name TEXT;
    extracted_last_name TEXT;
    extracted_full_name TEXT;
    extracted_avatar_url TEXT;
    new_org_id UUID;
BEGIN
    -- Extract metadata fields
    extracted_first_name := NEW.raw_user_meta_data ->> 'first_name';
    extracted_last_name := NEW.raw_user_meta_data ->> 'last_name';
    extracted_avatar_url := NEW.raw_user_meta_data ->> 'avatar_url';
    
    -- Determine full_name with fallback logic
    extracted_full_name := COALESCE(
        NEW.raw_user_meta_data ->> 'full_name',
        CASE 
            WHEN extracted_first_name IS NOT NULL AND extracted_last_name IS NOT NULL
            THEN extracted_first_name || ' ' || extracted_last_name
            WHEN extracted_first_name IS NOT NULL
            THEN extracted_first_name
            ELSE split_part(NEW.email, '@', 1)
        END
    );

    -- Insert into users table
    INSERT INTO public.users (
        id, email, email_confirmed_at, phone, phone_confirmed_at,
        last_sign_in_at, created_at, updated_at, first_name, 
        last_name, full_name, avatar_url, is_active
    )
    VALUES (
        NEW.id, NEW.email, NEW.email_confirmed_at, NEW.phone, 
        NEW.phone_confirmed_at, NEW.last_sign_in_at, NEW.created_at,
        COALESCE(NEW.updated_at, NEW.created_at), extracted_first_name,
        extracted_last_name, extracted_full_name, extracted_avatar_url, true
    );

    -- Insert into user_profiles table
    INSERT INTO public.user_profiles (
        id, email, full_name, avatar_url, phone, created_at, 
        updated_at, last_sign_in_at
    )
    VALUES (
        NEW.id, NEW.email, extracted_full_name, extracted_avatar_url,
        NEW.phone, NEW.created_at, COALESCE(NEW.updated_at, NEW.created_at),
        NEW.last_sign_in_at
    );

    -- Create personal workspace with proper columns
    INSERT INTO public.organizations (
        name, description, settings, organization_type, created_by,
        created_at, updated_at, is_active
    )
    VALUES (
        extracted_full_name || '''s Workspace',
        'Personal accounting workspace for ' || extracted_full_name,
        '{"created_by_trigger": true}',
        'personal',
        NEW.id,
        NEW.created_at,
        COALESCE(NEW.updated_at, NEW.created_at),
        true
    )
    RETURNING id INTO new_org_id;

    -- Add user as organization owner of their personal workspace
    INSERT INTO public.organization_members (
        organization_id, user_id, role, invited_by, invited_at, 
        joined_at, is_active, permissions
    )
    VALUES (
        new_org_id, NEW.id, 'organization_owner', NEW.id, NEW.created_at,
        NEW.created_at, true, '{"auto_created": true}'
    );

    RAISE LOG 'Created user, profile, and personal workspace for: % (ID: %, Org: %)', NEW.email, NEW.id, new_org_id;
    RETURN NEW;

EXCEPTION
    WHEN unique_violation THEN
        RAISE LOG 'User already exists: % (ID: %)', NEW.email, NEW.id;
        RETURN NEW;
    WHEN OTHERS THEN
        RAISE LOG 'Error creating user setup for % (ID: %): %', NEW.email, NEW.id, SQLERRM;
        RETURN NEW;
END;
$$;

-- 7. Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_organizations_type_created_by 
ON public.organizations(organization_type, created_by);

-- 8. Verification queries
SELECT 'Organization types:' as info;
SELECT organization_type, COUNT(*) as count 
FROM public.organizations 
GROUP BY organization_type;

SELECT 'Personal workspaces with created_by:' as info;
SELECT COUNT(*) as count 
FROM public.organizations 
WHERE organization_type = 'personal' AND created_by IS NOT NULL;

SELECT 'Organizations without created_by (should be 0 for personal):' as info;
SELECT COUNT(*) as count 
FROM public.organizations 
WHERE organization_type = 'personal' AND created_by IS NULL;
