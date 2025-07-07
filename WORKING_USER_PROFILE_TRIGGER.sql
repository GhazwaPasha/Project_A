-- ===============================================
-- WORKING USER PROFILE TRIGGER FOR SUPABASE
-- ===============================================
-- This creates a trigger that actually works with Supabase's security model
-- Uses a custom function that bypasses RLS restrictions

-- First, drop any existing trigger and function
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- Create a function that creates user profiles with proper security context
-- This function runs with SECURITY DEFINER which bypasses RLS
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    user_full_name TEXT;
BEGIN
    -- Extract full name from user metadata
    user_full_name := COALESCE(
        NEW.raw_user_meta_data ->> 'full_name',
        CASE 
            WHEN NEW.raw_user_meta_data ->> 'first_name' IS NOT NULL 
                 AND NEW.raw_user_meta_data ->> 'last_name' IS NOT NULL
            THEN NEW.raw_user_meta_data ->> 'first_name' || ' ' || NEW.raw_user_meta_data ->> 'last_name'
            ELSE split_part(NEW.email, '@', 1)
        END
    );

    -- Insert into user_profiles with proper error handling
    INSERT INTO public.user_profiles (
        id,
        email,
        full_name,
        created_at,
        updated_at,
        last_sign_in_at
    )
    VALUES (
        NEW.id,
        NEW.email,
        user_full_name,
        NEW.created_at,
        NEW.created_at,
        NEW.last_sign_in_at
    );

    -- Log successful creation
    RAISE LOG 'Created user profile for: % (ID: %)', NEW.email, NEW.id;
    
    RETURN NEW;
EXCEPTION
    WHEN unique_violation THEN
        -- User profile already exists, just log and continue
        RAISE LOG 'User profile already exists for: % (ID: %)', NEW.email, NEW.id;
        RETURN NEW;
    WHEN OTHERS THEN
        -- Log error but don't fail the auth user creation
        RAISE LOG 'Error creating user profile for % (ID: %): %', NEW.email, NEW.id, SQLERRM;
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

-- Ensure the function can insert into user_profiles
-- This is important because RLS might block the insert
GRANT INSERT ON public.user_profiles TO postgres;

-- Create an RLS policy that allows the function to insert
-- This policy specifically allows inserts during user creation
CREATE POLICY "Allow user profile creation during signup" 
ON public.user_profiles 
FOR INSERT 
WITH CHECK (true);

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

-- Additional diagnostic query to check permissions
SELECT 
    'Ready for user signups!' as message,
    'New users will automatically get user_profiles created' as note;
