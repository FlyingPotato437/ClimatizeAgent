-- Migration for Research and Planset Button Functions

-- Research analyses table (for Research Button)
CREATE TABLE IF NOT EXISTS research_analyses (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL,
    project_data JSONB NOT NULL,
    systems_data JSONB NOT NULL,
    research_sections TEXT[] NOT NULL,
    files_count INTEGER DEFAULT 0,
    system_image_url TEXT,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE research_analyses ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Allow all operations on research_analyses" ON research_analyses
    FOR ALL USING (true);

-- Permit packages table (for Planset Button)  
CREATE TABLE IF NOT EXISTS permit_packages (
    id TEXT PRIMARY KEY,
    research_id TEXT REFERENCES research_analyses(id),
    project_id TEXT NOT NULL,
    package_data JSONB NOT NULL,
    download_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS
ALTER TABLE permit_packages ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Allow all operations on permit_packages" ON permit_packages
    FOR ALL USING (true);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_research_analyses_project_id ON research_analyses(project_id);
CREATE INDEX IF NOT EXISTS idx_research_analyses_status ON research_analyses(status);
CREATE INDEX IF NOT EXISTS idx_permit_packages_research_id ON permit_packages(research_id);
CREATE INDEX IF NOT EXISTS idx_permit_packages_project_id ON permit_packages(project_id);

-- Storage buckets (create if not exists)
INSERT INTO storage.buckets (id, name, public)
VALUES 
    ('research-files', 'research-files', true),
    ('permit-packages', 'permit-packages', true)
ON CONFLICT (id) DO NOTHING;

-- Storage policies
CREATE POLICY "Allow all operations on research-files" ON storage.objects
    FOR ALL USING (bucket_id = 'research-files');

CREATE POLICY "Allow all operations on permit-packages" ON storage.objects  
    FOR ALL USING (bucket_id = 'permit-packages');
