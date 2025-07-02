-- Fix journal_entries table structure
-- Add missing columns that the application expects

-- Add missing columns to journal_entries table
ALTER TABLE public.journal_entries 
ADD COLUMN IF NOT EXISTS total_amount DECIMAL(15,2) NOT NULL DEFAULT 0;

ALTER TABLE public.journal_entries 
ADD COLUMN IF NOT EXISTS reference VARCHAR(100);

ALTER TABLE public.journal_entries 
ADD COLUMN IF NOT EXISTS is_posted BOOLEAN DEFAULT false;

ALTER TABLE public.journal_entries 
ADD COLUMN IF NOT EXISTS posted_by UUID REFERENCES public.user_profiles(id);

ALTER TABLE public.journal_entries 
ADD COLUMN IF NOT EXISTS posted_at TIMESTAMP WITH TIME ZONE;

-- Ensure organization_id column exists and has proper reference
DO $$ 
BEGIN
    -- Check if organization_id column exists and has UUID type
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'journal_entries' 
        AND column_name = 'organization_id' 
        AND data_type = 'uuid'
    ) THEN
        -- Add organization_id if it doesn't exist or is wrong type
        ALTER TABLE public.journal_entries 
        ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES public.organizations(id) ON DELETE CASCADE;
    END IF;
END $$;

-- Ensure created_by column exists
ALTER TABLE public.journal_entries 
ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES public.user_profiles(id);

-- Ensure entry_number column exists
ALTER TABLE public.journal_entries 
ADD COLUMN IF NOT EXISTS entry_number VARCHAR(50);

-- Add unique constraint on entry_number per organization (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'journal_entries_organization_id_entry_number_key'
    ) THEN
        ALTER TABLE public.journal_entries 
        ADD CONSTRAINT journal_entries_organization_id_entry_number_key 
        UNIQUE (organization_id, entry_number);
    END IF;
END $$;

-- Update any existing entries to have default total_amount if NULL
UPDATE public.journal_entries 
SET total_amount = 0 
WHERE total_amount IS NULL;

-- Add timestamps if they don't exist
ALTER TABLE public.journal_entries 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT now();

ALTER TABLE public.journal_entries 
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT now();

-- Create indexes for performance (if they don't exist)
CREATE INDEX IF NOT EXISTS idx_journal_entries_org_id ON public.journal_entries(organization_id);
CREATE INDEX IF NOT EXISTS idx_journal_entries_date ON public.journal_entries(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_entries_number ON public.journal_entries(organization_id, entry_number);

-- Add trigger for updated_at if function exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column') THEN
        -- Drop trigger if it exists
        DROP TRIGGER IF EXISTS update_journal_entries_updated_at ON public.journal_entries;
        
        -- Create trigger
        CREATE TRIGGER update_journal_entries_updated_at 
            BEFORE UPDATE ON public.journal_entries 
            FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
    END IF;
END $$;

-- Verify the table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'journal_entries' 
ORDER BY ordinal_position;

-- Summary
SELECT 'journal_entries table structure updated successfully!' as status; 