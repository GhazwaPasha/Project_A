-- ===============================================
-- FIX EXISTING USERS WITHOUT USER PROFILES
-- ===============================================
-- This script creates user_profiles for existing auth.users
-- Run this AFTER running FIXED_USER_PROFILE_TRIGGER.sql

-- Insert user profiles for any auth.users that don't have a profile yet
INSERT INTO public.user_profiles (
    id,
    email,
    full_name,
    created_at,
    updated_at
)
SELECT 
    au.id,
    au.email,
    COALESCE(
        au.raw_user_meta_data ->> 'full_name',
        CASE 
            WHEN au.raw_user_meta_data ->> 'first_name' IS NOT NULL 
                 AND au.raw_user_meta_data ->> 'last_name' IS NOT NULL
            THEN au.raw_user_meta_data ->> 'first_name' || ' ' || au.raw_user_meta_data ->> 'last_name'
            ELSE split_part(au.email, '@', 1)
        END
    ) as full_name,
    au.created_at,
    NOW()
FROM auth.users au
LEFT JOIN public.user_profiles up ON au.id = up.id
WHERE up.id IS NULL
  AND au.email IS NOT NULL;

-- Show results
SELECT 
    'Fixed existing users!' as status,
    COUNT(*) as users_fixed
FROM public.user_profiles;

-- Show all user profiles to verify
SELECT 
    id,
    email,
    full_name,
    created_at
FROM public.user_profiles
ORDER BY created_at DESC;
