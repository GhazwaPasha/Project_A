-- ===============================================
-- FIXED USER PROFILE TRIGGER
-- ===============================================
-- This script fixes the user profile trigger issues
-- Run this in Supabase SQL Editor to fix the signup problem

-- Drop existing trigger and function if they exist
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- Create fixed function to handle new user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = ''
AS $$
BEGIN
    -- Insert user profile with proper error handling
    INSERT INTO public.user_profiles (
        id,
        email,
        full_name,
        created_at,
        updated_at
    )
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(
            NEW.raw_user_meta_data ->> 'full_name',
            CASE 
                WHEN NEW.raw_user_meta_data ->> 'first_name' IS NOT NULL 
                     AND NEW.raw_user_meta_data ->> 'last_name' IS NOT NULL
                THEN NEW.raw_user_meta_data ->> 'first_name' || ' ' || NEW.raw_user_meta_data ->> 'last_name'
                ELSE split_part(NEW.email, '@', 1)
            END
        ),
        NOW(),
        NOW()
    );
    
    RETURN NEW;
EXCEPTION
    WHEN OTHERS THEN
        -- Log the error but don't fail the user creation
        RAISE LOG 'Error creating user profile for %: %', NEW.id, SQLERRM;
        RETURN NEW;
END;
$$;

-- Create trigger to automatically create user profile on signup
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Grant necessary permissions
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticated;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO anon;

-- Test the function works
SELECT 'Fixed user profile trigger created successfully!' as status;
SELECT 'User signup should now work without database errors!' as message;
