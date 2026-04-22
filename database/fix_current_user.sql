-- ===============================================
-- FIX EXISTING USER - CREATE MISSING USER PROFILE
-- ===============================================
-- This script creates user_profiles for existing users in auth.users
-- Run this AFTER applying the WORKING_USER_PROFILE_TRIGGER.sql

-- Create user profiles for any existing auth users that don't have profiles
INSERT INTO public.user_profiles (
    id,
    email,
    full_name,
    created_at,
    updated_at,
    last_sign_in_at
)
SELECT 
    au.id,
    au.email,
    COALESCE(
        au.raw_user_meta_data ->> 'full_name',
        CASE 
            WHEN (au.raw_user_meta_data ->> 'first_name') IS NOT NULL 
                 AND (au.raw_user_meta_data ->> 'last_name') IS NOT NULL
            THEN (au.raw_user_meta_data ->> 'first_name') || ' ' || (au.raw_user_meta_data ->> 'last_name')
            ELSE split_part(au.email, '@', 1)
        END
    ) as full_name,
    au.created_at,
    COALESCE(au.updated_at, au.created_at),
    au.last_sign_in_at
FROM auth.users au
LEFT JOIN public.user_profiles up ON au.id = up.id
WHERE up.id IS NULL
  AND au.email IS NOT NULL
  AND au.email_confirmed_at IS NOT NULL; -- Only confirmed users

-- Show the results
SELECT 
    'Existing users fixed!' as status,
    COUNT(*) as profiles_created
FROM public.user_profiles;

-- Verify all users now have profiles
SELECT 
    'Verification' as check_type,
    au.email as auth_email,
    up.email as profile_email,
    up.full_name,
    CASE 
        WHEN up.id IS NOT NULL THEN '✅ Profile exists'
        ELSE '❌ Missing profile'
    END as status
FROM auth.users au
LEFT JOIN public.user_profiles up ON au.id = up.id
ORDER BY au.created_at DESC;
