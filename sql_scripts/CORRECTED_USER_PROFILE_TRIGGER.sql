-- ===============================================
-- CORRECTED USER PROFILE TRIGGER WITH BETTER PERMISSIONS
-- ===============================================
-- This version addresses potential auth schema access issues

-- Drop existing trigger and function
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- Create function with explicit permissions and error handling
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = 'public, auth'
AS $$
BEGIN
    -- Log the attempt for debugging
    RAISE LOG 'Creating user profile for user ID: %, Email: %', NEW.id, NEW.email;
    
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
        NEW.created_at,
        NEW.created_at
    );
    
    RAISE LOG 'Successfully created user profile for user ID: %', NEW.id;
    RETURN NEW;
    
EXCEPTION
    WHEN OTHERS THEN
        -- Log detailed error but don't fail the user creation
        RAISE LOG 'Error creating user profile for user ID %, Email %: % - %', 
                  NEW.id, NEW.email, SQLSTATE, SQLERRM;
        RETURN NEW;
END;
$$;

-- Create trigger
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- Grant comprehensive permissions
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO service_role;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO authenticated;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO anon;
GRANT EXECUTE ON FUNCTION public.handle_new_user() TO postgres;

-- Grant access to user_profiles table for the function
GRANT INSERT ON public.user_profiles TO service_role;
GRANT INSERT ON public.user_profiles TO postgres;

-- Test message
SELECT 'Corrected user profile trigger created!' as status;
SELECT 'This version has better permissions and logging' as message;
