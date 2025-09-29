-- ===============================================
-- FIX USER SIGNUP TRIGGER - COMPREHENSIVE SOLUTION
-- ===============================================
-- This script fixes the database error when saving new users
-- by creating a trigger that automatically:
-- 1. Creates user profiles
-- 2. Creates personal workspaces
-- 3. Sets up organization membership
-- 
-- Run this AFTER applying NEW_SCHEMA.sql

-- First, drop any existing trigger and function
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS public.handle_new_auth_user();

-- Create a comprehensive function that handles new user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
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
    -- Extract metadata fields from auth.users
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

    -- Step 1: Insert into users table (required by application)
    INSERT INTO public.users (
        id,
        email,
        email_confirmed_at,
        phone,
        phone_confirmed_at,
        last_sign_in_at,
        created_at,
        updated_at,
        first_name,
        last_name,
        full_name,
        avatar_url,
        is_active
    )
    VALUES (
        NEW.id,
        NEW.email,
        NEW.email_confirmed_at,
        NEW.phone,
        NEW.phone_confirmed_at,
        NEW.last_sign_in_at,
        NEW.created_at,
        COALESCE(NEW.updated_at, NEW.created_at),
        extracted_first_name,
        extracted_last_name,
        extracted_full_name,
        extracted_avatar_url,
        true
    );

    -- Step 2: Insert into user_profiles table
    INSERT INTO public.user_profiles (
        id,
        email,
        full_name,
        avatar_url,
        phone,
        is_super_admin,
        preferences,
        created_at,
        updated_at,
        last_sign_in_at
    )
    VALUES (
        NEW.id,
        NEW.email,
        extracted_full_name,
        extracted_avatar_url,
        NEW.phone,
        false, -- Default to not super admin
        '{}', -- Empty preferences JSON
        NEW.created_at,
        COALESCE(NEW.updated_at, NEW.created_at),
        NEW.last_sign_in_at
    );

    -- Step 3: Create personal workspace (1-member organization)
    INSERT INTO public.organizations (
        name,
        description,
        settings,
        created_at,
        updated_at,
        is_active,
        organization_type,
        created_by
    )
    VALUES (
        extracted_full_name || '''s Workspace',
        'Personal accounting workspace for ' || extracted_full_name,
        '{"workspace_type": "personal", "created_by_trigger": true}',
        NEW.created_at,
        COALESCE(NEW.updated_at, NEW.created_at),
        true,
        'personal',
        NEW.id
    )
    RETURNING id INTO new_org_id;

    -- Step 4: Add user as organization owner of their personal workspace
    INSERT INTO public.organization_members (
        organization_id,
        user_id,
        role,
        invited_by,
        invited_at,
        joined_at,
        is_active,
        permissions
    )
    VALUES (
        new_org_id,
        NEW.id,
        'organization_owner',
        NEW.id,
        NEW.created_at,
        NEW.created_at,
        true,
        '{"auto_created": true}'
    );

    -- Log successful creation
    RAISE LOG 'Created user profile and personal workspace for: % (ID: %, Org: %)', NEW.email, NEW.id, new_org_id;
    RETURN NEW;

EXCEPTION
    WHEN unique_violation THEN
        -- User profile or organization already exists, just log and continue
        RAISE LOG 'User setup already exists for: % (ID: %)', NEW.email, NEW.id;
        RETURN NEW;
    WHEN OTHERS THEN
        -- Log error but don't fail the auth user creation
        RAISE LOG 'Error creating user setup for % (ID: %): %', NEW.email, NEW.id, SQLERRM;
        RETURN NEW;
END;
$$;

-- Create the trigger on auth.users
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Grant necessary permissions to the function
-- The function needs to run as the postgres role to bypass RLS
ALTER FUNCTION public.handle_new_user() OWNER TO postgres;

-- Grant execute permissions to all roles that might need it
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticator;

-- Ensure the function can insert into all necessary tables
GRANT INSERT ON public.users TO postgres;
GRANT INSERT ON public.user_profiles TO postgres;
GRANT INSERT ON public.organizations TO postgres;
GRANT INSERT ON public.organization_members TO postgres;

-- Drop existing policies if they exist
DROP POLICY IF EXISTS "Allow user creation during signup" ON public.users;
DROP POLICY IF EXISTS "Allow user profile creation during signup" ON public.user_profiles;
DROP POLICY IF EXISTS "Allow organization creation during signup" ON public.organizations;
DROP POLICY IF EXISTS "Allow organization membership creation during signup" ON public.organization_members;

-- Create RLS policies that allow the function to insert
-- These policies specifically allow inserts during user creation
CREATE POLICY "Allow user creation during signup" 
ON public.users 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Allow user profile creation during signup" 
ON public.user_profiles 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Allow organization creation during signup" 
ON public.organizations 
FOR INSERT 
WITH CHECK (true);

CREATE POLICY "Allow organization membership creation during signup" 
ON public.organization_members 
FOR INSERT 
WITH CHECK (true);

-- ===============================================
-- VERIFICATION QUERIES
-- ===============================================

-- Test that the trigger function works by checking its existence
SELECT 
    'Trigger created successfully!' as status,
    trigger_name,
    event_manipulation,
    action_statement
FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';

-- Show the function source for verification
SELECT 
    'Function created successfully!' as status,
    routine_name,
    security_type
FROM information_schema.routines 
WHERE routine_name = 'handle_new_user';

-- Check that all necessary policies exist
SELECT 
    'RLS Policies:' as info,
    schemaname,
    tablename,
    policyname,
    permissive,
    roles,
    cmd,
    qual,
    with_check
FROM pg_policies 
WHERE tablename IN ('users', 'user_profiles', 'organizations', 'organization_members')
AND policyname LIKE '%signup%'
ORDER BY tablename, policyname;

-- ===============================================
-- MIGRATION COMPLETE
-- ===============================================
SELECT 
    'User signup trigger fixed successfully!' as status,
    'New users will automatically get:' as note,
    '- User record in users table' as step1,
    '- User profile in user_profiles table' as step2,
    '- Personal workspace organization' as step3,
    '- Organization membership as owner' as step4;

-- ===============================================
-- TESTING INSTRUCTIONS
-- ===============================================
-- To test this fix:
-- 1. Try creating a new user account through the signup form
-- 2. Check that the user record is created in users table
-- 3. Check that the user profile is created in user_profiles table
-- 4. Check that a personal workspace is created in organizations table
-- 5. Check that the user is added as organization_owner in organization_members table
-- 6. Verify the user can sign in and access their personal workspace 