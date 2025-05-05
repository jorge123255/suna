-- Model Selection Logs Table Migration (Fixed)
-- This adds only the model selection logs table without modifying existing tables

-- Model Selection Logs Table
CREATE TABLE IF NOT EXISTS public.model_selection_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prompt_snippet TEXT NOT NULL,
    prompt_length INTEGER NOT NULL,
    task_type TEXT NOT NULL,
    confidence FLOAT NOT NULL,
    selected_model TEXT NOT NULL,
    override_reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS model_selection_logs_task_type_idx ON public.model_selection_logs(task_type);
CREATE INDEX IF NOT EXISTS model_selection_logs_selected_model_idx ON public.model_selection_logs(selected_model);
CREATE INDEX IF NOT EXISTS model_selection_logs_created_at_idx ON public.model_selection_logs(created_at);

-- Enable Row Level Security
ALTER TABLE public.model_selection_logs ENABLE ROW LEVEL SECURITY;

-- Grant access to authenticated users
CREATE POLICY model_selection_logs_policy ON public.model_selection_logs 
    USING (true)
    WITH CHECK (true);
