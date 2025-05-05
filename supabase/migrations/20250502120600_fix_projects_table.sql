-- Fix for projects table null name constraint
-- This adds a default value for the name column and updates any existing null values

-- First, update any existing records with null names
UPDATE public.projects
SET name = 'Unnamed Project'
WHERE name IS NULL;

-- Then, alter the table to set a default value for future inserts
ALTER TABLE public.projects
ALTER COLUMN name SET DEFAULT 'Unnamed Project';

-- Ensure the not-null constraint is in place
ALTER TABLE public.projects
ALTER COLUMN name SET NOT NULL;
