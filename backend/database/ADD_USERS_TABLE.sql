-- ===============================================
-- ADD USERS TABLE AS PRECURSOR TO USER_PROFILES
-- ===============================================
-- This creates a users table that mirrors auth.users with foreign keys
-- Flow: auth.users → users → user_profiles → organization_members

-- Drop existing trigger and function if they exist
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS public.handle_new_user();

-- 1. Create users table that mirrors essential auth.users fields
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL UNIQUE,
    email_confirmed_at TIMESTAMP WITH TIME ZONE,
    phone VARCHAR(50),
    phone_confirmed_at TIMESTAMP WITH TIME ZONE,
    last_sign_in_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    -- Extract metadata fields
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    full_name VARCHAR(255),
    avatar_url TEXT,
    -- Application specific fields
    is_active BOOLEAN DEFAULT true
);

-- 2. Migrate existing data FIRST before adding foreign key constraints
DO $$
DECLARE
    user_profiles_columns TEXT;
    migration_query TEXT;
BEGIN
    -- Check if user_profiles has existing data and users table is empty
    IF EXISTS (SELECT 1 FROM public.user_profiles LIMIT 1) AND 
       NOT EXISTS (SELECT 1 FROM public.users LIMIT 1) THEN
       
        RAISE LOG 'Migrating existing user_profiles data to users table...';
        
        -- Check what columns exist in user_profiles table
        SELECT string_agg(column_name, ', ' ORDER BY ordinal_position) INTO user_profiles_columns
        FROM information_schema.columns 
        WHERE table_name = 'user_profiles' AND table_schema = 'public';
        
        RAISE LOG 'Available user_profiles columns: %', user_profiles_columns;
        
        -- Build migration query based on available columns
        -- Start with basic required fields
        migration_query := 'INSERT INTO public.users (id, email, created_at, updated_at, is_active';
        
        -- Add optional fields if they exist
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'phone') THEN
            migration_query := migration_query || ', phone';
        END IF;
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'last_sign_in_at') THEN
            migration_query := migration_query || ', last_sign_in_at';
        END IF;
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'first_name') THEN
            migration_query := migration_query || ', first_name';
        END IF;
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'last_name') THEN
            migration_query := migration_query || ', last_name';
        END IF;
        
        -- Always add full_name (we'll create it from first_name + last_name)
        migration_query := migration_query || ', full_name';
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'avatar_url') THEN
            migration_query := migration_query || ', avatar_url';
        END IF;
        
        -- Add auth.users fields
        migration_query := migration_query || ', email_confirmed_at, phone_confirmed_at';
        
        -- Close column list and start SELECT
        migration_query := migration_query || ') SELECT up.id, up.email, up.created_at, up.updated_at, true';
        
        -- Add corresponding SELECT fields
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'phone') THEN
            migration_query := migration_query || ', up.phone';
        END IF;
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'last_sign_in_at') THEN
            migration_query := migration_query || ', COALESCE(up.last_sign_in_at, au.last_sign_in_at)';
        ELSE
            migration_query := migration_query || ', au.last_sign_in_at';
        END IF;
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'first_name') THEN
            migration_query := migration_query || ', up.first_name';
        END IF;
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'last_name') THEN
            migration_query := migration_query || ', up.last_name';
        END IF;
        
        -- Create full_name from first_name + last_name or fallback to email
        migration_query := migration_query || ', CASE 
            WHEN up.first_name IS NOT NULL AND up.last_name IS NOT NULL
            THEN up.first_name || '' '' || up.last_name
            WHEN up.first_name IS NOT NULL
            THEN up.first_name
            ELSE COALESCE(
                au.raw_user_meta_data ->> ''full_name'',
                split_part(up.email, ''@'', 1)
            )
        END';
        
        IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'user_profiles' AND column_name = 'avatar_url') THEN
            migration_query := migration_query || ', up.avatar_url';
        ELSE
            migration_query := migration_query || ', au.raw_user_meta_data ->> ''avatar_url''';
        END IF;
        
        -- Add auth.users fields
        migration_query := migration_query || ', au.email_confirmed_at, au.phone_confirmed_at';
        
        -- Add FROM and WHERE clauses
        migration_query := migration_query || ' FROM public.user_profiles up LEFT JOIN auth.users au ON au.id = up.id WHERE NOT EXISTS (SELECT 1 FROM public.users u WHERE u.id = up.id)';
        
        RAISE LOG 'Executing migration query: %', migration_query;
        
        -- Execute the dynamic query
        EXECUTE migration_query;
        
        RAISE LOG 'Migrated % existing user profiles to users table', 
            (SELECT COUNT(*) FROM public.users);
    END IF;
END $$;

-- 3. Now update foreign key constraints after data migration
-- Update user_profiles to reference users instead of auth.users directly
DO $$ 
BEGIN
    -- Check if user_profiles exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_profiles') THEN
        -- Drop the old foreign key constraint to auth.users if it exists
        ALTER TABLE public.user_profiles DROP CONSTRAINT IF EXISTS user_profiles_id_fkey;
        
        -- Add new foreign key to users table
        ALTER TABLE public.user_profiles 
        ADD CONSTRAINT user_profiles_id_fkey 
        FOREIGN KEY (id) REFERENCES public.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- 4. Update organization_members to reference users
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'organization_members') THEN
        -- Drop old foreign key constraint if it exists
        ALTER TABLE public.organization_members DROP CONSTRAINT IF EXISTS organization_members_user_id_fkey;
        
        -- Add new foreign key to users table
        ALTER TABLE public.organization_members 
        ADD CONSTRAINT organization_members_user_id_fkey 
        FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;
    END IF;
END $$;

-- 5. Update any other tables that reference user_profiles to reference users
-- Check accounts table
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'accounts' AND column_name = 'created_by') THEN
        ALTER TABLE public.accounts DROP CONSTRAINT IF EXISTS accounts_created_by_fkey;
        ALTER TABLE public.accounts 
        ADD CONSTRAINT accounts_created_by_fkey 
        FOREIGN KEY (created_by) REFERENCES public.users(id);
    END IF;
END $$;

-- Check journal_entries table
DO $$ 
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'journal_entries' AND column_name = 'created_by') THEN
        ALTER TABLE public.journal_entries DROP CONSTRAINT IF EXISTS journal_entries_created_by_fkey;
        ALTER TABLE public.journal_entries 
        ADD CONSTRAINT journal_entries_created_by_fkey 
        FOREIGN KEY (created_by) REFERENCES public.users(id);
    END IF;
END $$;

-- 6. Create trigger function to automatically create users record
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

    -- Automatically create user_profile if table exists
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_profiles') THEN
        INSERT INTO public.user_profiles (
            id,
            email,
            full_name,
            avatar_url,
            phone,
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
            NEW.created_at,
            COALESCE(NEW.updated_at, NEW.created_at),
            NEW.last_sign_in_at
        );
    END IF;

    RAISE LOG 'Created user record for: % (ID: %)', NEW.email, NEW.id;
    RETURN NEW;

EXCEPTION
    WHEN unique_violation THEN
        RAISE LOG 'User already exists: % (ID: %)', NEW.email, NEW.id;
        RETURN NEW;
    WHEN OTHERS THEN
        RAISE LOG 'Error creating user record for % (ID: %): %', NEW.email, NEW.id, SQLERRM;
        RETURN NEW;
END;
$$;

-- 7. Create the trigger
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_auth_user();

-- 8. Grant necessary permissions
ALTER FUNCTION public.handle_new_auth_user() OWNER TO postgres;
GRANT EXECUTE ON FUNCTION public.handle_new_auth_user() TO service_role;
GRANT EXECUTE ON FUNCTION public.handle_new_auth_user() TO authenticator;

-- Grant table permissions
GRANT INSERT ON public.users TO postgres;
GRANT INSERT ON public.user_profiles TO postgres;

-- 9. Enable RLS on users table
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for users table
CREATE POLICY "users_select_own" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "users_update_own" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Super admins can access all users
CREATE POLICY "users_all_super_admin" ON public.users
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles up
            WHERE up.id = auth.uid()
            AND up.is_super_admin = true
        )
    );

-- 10. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_users_email ON public.users(email);
CREATE INDEX IF NOT EXISTS idx_users_last_sign_in ON public.users(last_sign_in_at);
CREATE INDEX IF NOT EXISTS idx_users_created_at ON public.users(created_at);

-- 11. Verification queries
SELECT 
    'Users table created successfully!' as status,
    'Trigger will automatically create users from auth.users' as note;

-- Show the trigger and function
SELECT 
    trigger_name,
    event_manipulation,
    action_statement
FROM information_schema.triggers 
WHERE trigger_name = 'on_auth_user_created';

SELECT 
    routine_name,
    security_type
FROM information_schema.routines 
WHERE routine_name = 'handle_new_auth_user';
