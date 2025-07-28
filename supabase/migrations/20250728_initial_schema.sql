-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create storage buckets
INSERT INTO storage.buckets (id, name, public) VALUES 
  ('project-files', 'project-files', true),
  ('permit-packages', 'permit-packages', true),
  ('permit-documents', 'permit-documents', true);

-- Create storage policies
CREATE POLICY "Public read access for project files" ON storage.objects
  FOR SELECT USING (bucket_id = 'project-files');

CREATE POLICY "Authenticated upload for project files" ON storage.objects
  FOR INSERT WITH CHECK (bucket_id = 'project-files' AND auth.role() = 'authenticated');

CREATE POLICY "Public read access for permit packages" ON storage.objects
  FOR SELECT USING (bucket_id = 'permit-packages');

CREATE POLICY "Service role full access to permit packages" ON storage.objects
  FOR ALL USING (bucket_id = 'permit-packages' AND auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to permit documents" ON storage.objects
  FOR ALL USING (bucket_id = 'permit-documents' AND auth.jwt() ->> 'role' = 'service_role');

-- System configurations table
CREATE TABLE system_configurations (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id TEXT UNIQUE NOT NULL,
  config JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'pending',
  permit_package_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  generated_at TIMESTAMPTZ
);

-- Create index on project_id for fast lookups
CREATE INDEX idx_system_configurations_project_id ON system_configurations(project_id);
CREATE INDEX idx_system_configurations_status ON system_configurations(status);

-- Permit history table for tracking all generated permits
CREATE TABLE permit_history (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id TEXT NOT NULL,
  package_url TEXT NOT NULL,
  system_config JSONB NOT NULL,
  status TEXT NOT NULL DEFAULT 'completed',
  generated_at TIMESTAMPTZ DEFAULT NOW(),
  downloaded_at TIMESTAMPTZ,
  download_count INTEGER DEFAULT 0
);

-- Create indexes for permit history
CREATE INDEX idx_permit_history_project_id ON permit_history(project_id);
CREATE INDEX idx_permit_history_generated_at ON permit_history(generated_at);
CREATE INDEX idx_permit_history_status ON permit_history(status);

-- Project analytics table for tracking usage
CREATE TABLE project_analytics (
  id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
  project_id TEXT NOT NULL,
  event_type TEXT NOT NULL, -- 'submission', 'analysis_complete', 'permit_generated', 'download'
  event_data JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for analytics
CREATE INDEX idx_project_analytics_project_id ON project_analytics(project_id);
CREATE INDEX idx_project_analytics_event_type ON project_analytics(event_type);
CREATE INDEX idx_project_analytics_created_at ON project_analytics(created_at);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
CREATE TRIGGER update_system_configurations_updated_at 
  BEFORE UPDATE ON system_configurations 
  FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Row Level Security (RLS) policies
ALTER TABLE system_configurations ENABLE ROW LEVEL SECURITY;
ALTER TABLE permit_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE project_analytics ENABLE ROW LEVEL SECURITY;

-- Allow service role full access (for Edge Functions)
CREATE POLICY "Service role full access to system_configurations" ON system_configurations
  FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to permit_history" ON permit_history
  FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role full access to project_analytics" ON project_analytics
  FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Allow authenticated users to read their own data (for future user authentication)
CREATE POLICY "Users can read own system_configurations" ON system_configurations
  FOR SELECT USING (auth.uid()::text = (config->>'user_id'));

CREATE POLICY "Users can read own permit_history" ON permit_history
  FOR SELECT USING (auth.uid()::text = (system_config->>'user_id'));

-- Views for easier querying
CREATE VIEW active_projects AS
SELECT 
  project_id,
  config->>'projectName' as project_name,
  config->>'address' as address,
  (config->>'systemSize')::numeric as system_size,
  status,
  created_at,
  updated_at
FROM system_configurations
WHERE status IN ('ready_for_permit_generation', 'permit_package_generated');

CREATE VIEW project_summary AS
SELECT 
  sc.project_id,
  sc.config->>'projectName' as project_name,
  sc.config->>'address' as address,
  (sc.config->>'systemSize')::numeric as system_size,
  sc.status,
  sc.created_at as submitted_at,
  sc.generated_at,
  ph.package_url,
  ph.download_count
FROM system_configurations sc
LEFT JOIN permit_history ph ON sc.project_id = ph.project_id
ORDER BY sc.created_at DESC;

-- Insert initial analytics event function
CREATE OR REPLACE FUNCTION log_project_event(
  p_project_id TEXT,
  p_event_type TEXT,
  p_event_data JSONB DEFAULT NULL
) RETURNS VOID AS $$
BEGIN
  INSERT INTO project_analytics (project_id, event_type, event_data)
  VALUES (p_project_id, p_event_type, p_event_data);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to log permit generation events
CREATE OR REPLACE FUNCTION log_permit_events()
RETURNS TRIGGER AS $$
BEGIN
  -- Log when permit package is generated
  IF NEW.status = 'permit_package_generated' AND OLD.status != 'permit_package_generated' THEN
    PERFORM log_project_event(NEW.project_id, 'permit_generated', 
      jsonb_build_object('package_url', NEW.permit_package_url));
  END IF;
  
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER system_configurations_permit_events
  AFTER UPDATE ON system_configurations
  FOR EACH ROW EXECUTE FUNCTION log_permit_events();
