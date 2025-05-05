-- Thread Tables Migration
-- This adds the thread and thread_messages tables

-- Thread Messages Table
CREATE TABLE IF NOT EXISTS public.thread_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    thread_id UUID NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    role TEXT NOT NULL DEFAULT 'user',
    metadata JSONB
);

-- Create index for thread_messages
CREATE INDEX IF NOT EXISTS thread_messages_thread_id_idx ON public.thread_messages(thread_id);
CREATE INDEX IF NOT EXISTS thread_messages_created_at_idx ON public.thread_messages(created_at);

-- Threads Table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS public.threads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB
);

-- Create index for threads
CREATE INDEX IF NOT EXISTS threads_created_at_idx ON public.threads(created_at);

-- Enable Row Level Security
ALTER TABLE public.thread_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.threads ENABLE ROW LEVEL SECURITY;

-- Grant access to authenticated users
CREATE POLICY thread_messages_policy ON public.thread_messages 
    USING (true)
    WITH CHECK (true);

CREATE POLICY threads_policy ON public.threads 
    USING (true)
    WITH CHECK (true);
