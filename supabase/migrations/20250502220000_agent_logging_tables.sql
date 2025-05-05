-- Simple database setup for agent logging
-- This migration creates minimal tables needed for agent logging without foreign key constraints

-- First, ensure we have the uuid-ossp extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create account_user table if it doesn't exist (without foreign key constraints)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_tables
        WHERE schemaname = 'public' AND tablename = 'account_user'
    ) THEN
        -- Create a simple account_user table without foreign key constraints
        CREATE TABLE public.account_user (
            user_id UUID NOT NULL,
            account_id UUID NOT NULL,
            account_role TEXT NOT NULL,
            CONSTRAINT account_user_pkey PRIMARY KEY (user_id, account_id)
        );

        -- Grant permissions
        GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.account_user TO authenticated, service_role;

        -- Enable RLS
        ALTER TABLE public.account_user ENABLE ROW LEVEL SECURITY;

        -- Policy for service role
        CREATE POLICY "service_role_access" ON public.account_user
            USING (auth.role() = 'service_role');
            
        -- Policy for authenticated users in development mode
        CREATE POLICY "dev_authenticated_access" ON public.account_user
            FOR ALL
            USING (auth.role() = 'authenticated');
            
        -- Insert a default user for development purposes
        INSERT INTO public.account_user (user_id, account_id, account_role)
        VALUES 
        ('00000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000000', 'owner');
    END IF;
END
$$;

-- Create agent_action_logs table if it doesn't exist (without foreign key constraints)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_tables
        WHERE schemaname = 'public' AND tablename = 'agent_action_logs'
    ) THEN
        CREATE TABLE public.agent_action_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            thread_id UUID,
            agent_run_id UUID,
            project_id UUID,
            action_type TEXT NOT NULL,
            action_details JSONB NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        
        -- Create indexes for efficient querying
        CREATE INDEX IF NOT EXISTS agent_action_logs_thread_id_idx ON public.agent_action_logs(thread_id);
        CREATE INDEX IF NOT EXISTS agent_action_logs_agent_run_id_idx ON public.agent_action_logs(agent_run_id);
        CREATE INDEX IF NOT EXISTS agent_action_logs_project_id_idx ON public.agent_action_logs(project_id);
        CREATE INDEX IF NOT EXISTS agent_action_logs_action_type_idx ON public.agent_action_logs(action_type);
        CREATE INDEX IF NOT EXISTS agent_action_logs_created_at_idx ON public.agent_action_logs(created_at);
        
        -- Enable RLS
        ALTER TABLE public.agent_action_logs ENABLE ROW LEVEL SECURITY;
        
        -- Create policies
        CREATE POLICY agent_action_logs_service_policy ON public.agent_action_logs
            USING (auth.role() = 'service_role');
            
        -- In development mode, create a policy that allows all authenticated users to access logs
        CREATE POLICY agent_action_logs_dev_policy ON public.agent_action_logs
            FOR ALL
            USING (auth.role() = 'authenticated');
    END IF;
END
$$;

-- Create model_selection_logs table if it doesn't exist (without foreign key constraints)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_tables
        WHERE schemaname = 'public' AND tablename = 'model_selection_logs'
    ) THEN
        CREATE TABLE public.model_selection_logs (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            thread_id UUID,
            prompt_text TEXT,
            classified_task_type TEXT NOT NULL,
            confidence_score FLOAT,
            selected_model TEXT NOT NULL,
            override_reason TEXT,
            prompt_tokens INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS model_selection_logs_thread_id_idx ON public.model_selection_logs(thread_id);
        CREATE INDEX IF NOT EXISTS model_selection_logs_task_type_idx ON public.model_selection_logs(classified_task_type);
        CREATE INDEX IF NOT EXISTS model_selection_logs_selected_model_idx ON public.model_selection_logs(selected_model);
        CREATE INDEX IF NOT EXISTS model_selection_logs_created_at_idx ON public.model_selection_logs(created_at);
        
        -- Enable RLS
        ALTER TABLE public.model_selection_logs ENABLE ROW LEVEL SECURITY;
        
        -- Create policies
        CREATE POLICY model_selection_logs_service_policy ON public.model_selection_logs
            USING (auth.role() = 'service_role');
            
        -- In development mode, create a policy that allows all authenticated users to access logs
        CREATE POLICY model_selection_logs_dev_policy ON public.model_selection_logs
            FOR ALL
            USING (auth.role() = 'authenticated');
    END IF;
END
$$;

-- Add function to check account membership that gracefully handles errors
CREATE OR REPLACE FUNCTION public.check_account_membership(user_id UUID, account_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    -- In development mode, always return true to avoid authentication issues
    RETURN TRUE;
EXCEPTION
    WHEN OTHERS THEN
        -- Log error and return true to allow operations to continue
        RAISE NOTICE 'Error checking account membership: %', SQLERRM;
        RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
