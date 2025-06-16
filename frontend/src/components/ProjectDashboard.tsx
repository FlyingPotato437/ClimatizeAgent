import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Alert,
  CircularProgress,
  Grid,
  Card,
  CardContent,
  CardActions,
  LinearProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  CloudDownload as HeliIcon,
  LocationOn as LocationIcon,
  Assessment as ScoreIcon,
  AutoAwesome as AIIcon
} from '@mui/icons-material';
import axios from 'axios';
import AuroraLoginForm from './AuroraLoginForm';

interface Project {
  project_id: string;
  project_name: string;
  data_source: string;
  address: {
    street: string;
    city: string;
    state: string;
    zip_code: string;
  };
  system_specs: {
    system_size_dc_kw: number;
    module_count: number;
    inverter_type: string;
  };
  financials: {
    estimated_capex?: number;
    price_per_watt?: number;
  };
  milestones: {
    site_control: string;
    permitting: string;
    interconnection: string;
  };
  fundability_score: number;
}

const ProjectDashboard: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('cards');
  const [auroraDialogOpen, setAuroraDialogOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get('/api/get_all_projects');
      setProjects(response.data);
    } catch (err: any) {
      setError('Failed to load projects. Please try again.');
      console.error('Error fetching projects:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleViewProject = (projectId: string) => {
    navigate(`/projects/${projectId}`);
  };

  const handleCreateProject = () => {
    navigate('/create-project');
  };

  const handleHeliLogin = () => {
    setAuroraDialogOpen(true);
  };

  const handleHeliSuccess = () => {
    // Refresh projects after successful Helioscope connection
    fetchProjects();
  };

  const handleAIAnalysis = () => {
    navigate('/ai-analysis');
  };

  const getMilestoneProgress = (milestones: Project['milestones']) => {
    const totalMilestones = 3;
    let completedMilestones = 0;
    
    if (milestones.site_control !== 'Not Started') completedMilestones++;
    if (milestones.permitting !== 'Not Started') completedMilestones++;
    if (milestones.interconnection !== 'Not Started') completedMilestones++;
    
    return Math.round((completedMilestones / totalMilestones) * 100);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getMilestoneChip = (status: string) => {
    const getColor = (status: string) => {
      switch (status) {
        case 'Not Started': return 'default';
        case 'Drafted': case 'Matrix Generated': case 'Application Drafted': return 'primary';
        case 'Signed': case 'Applications Drafted': case 'Submitted': return 'success';
        default: return 'default';
      }
    };

    return (
      <Chip
        label={status}
        color={getColor(status) as any}
        size="small"
        sx={{ mr: 0.5, mb: 0.5 }}
      />
    );
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert 
        severity="error" 
        action={
          <Button color="inherit" size="small" onClick={fetchProjects}>
            Retry
          </Button>
        }
      >
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Project Dashboard
        </Typography>
        <Box>
          <Button
            variant="contained"
            startIcon={<AIIcon />}
            onClick={handleAIAnalysis}
            sx={{ mr: 2 }}
            color="secondary"
          >
            AI Analysis
          </Button>
          <Button
            variant="outlined"
            startIcon={<HeliIcon />}
            onClick={handleHeliLogin}
            sx={{ mr: 2 }}
          >
            Connect Helioscope
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={handleCreateProject}
          >
            Manual Entry
          </Button>
        </Box>
      </Box>

      {/* Summary Stats */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Projects
              </Typography>
              <Typography variant="h4">
                {projects.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Average Score
              </Typography>
              <Typography variant="h4">
                {projects.length > 0 ? Math.round(projects.reduce((sum, p) => sum + p.fundability_score, 0) / projects.length) : 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Capacity
              </Typography>
              <Typography variant="h4">
                {Math.round(projects.reduce((sum, p) => sum + p.system_specs.system_size_dc_kw, 0))} kW
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                High Fundability
              </Typography>
              <Typography variant="h4">
                {projects.filter(p => p.fundability_score >= 80).length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Projects List */}
      {projects.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <Typography variant="h6" color="textSecondary" gutterBottom>
            No projects yet
          </Typography>
          <Typography variant="body1" color="textSecondary" paragraph>
            Get started with AI-powered analysis, manual entry, or Helioscope integration.
          </Typography>
          <Box display="flex" gap={2} justifyContent="center">
            <Button
              variant="contained"
              startIcon={<AIIcon />}
              onClick={handleAIAnalysis}
              color="secondary"
            >
              Start AI Analysis
            </Button>
            <Button
              variant="outlined"
              startIcon={<AddIcon />}
              onClick={handleCreateProject}
            >
              Manual Entry
            </Button>
          </Box>
        </Paper>
      ) : (
        <Grid container spacing={3}>
          {projects.map((project) => (
            <Grid item xs={12} md={6} lg={4} key={project.project_id}>
              <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6" component="h2" gutterBottom>
                      {project.project_name}
                    </Typography>
                    <Chip
                      label={project.data_source}
                      color={
                        project.data_source === 'Helioscope' ? 'primary' : 
                        project.data_source === 'Manual' ? 'default' : 'secondary'
                      }
                      size="small"
                    />
                  </Box>

                  <Box display="flex" alignItems="center" mb={1}>
                    <LocationIcon fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} />
                    <Typography variant="body2" color="text.secondary">
                      {project.address.city}, {project.address.state}
                    </Typography>
                  </Box>

                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {project.system_specs.system_size_dc_kw} kW DC • {project.system_specs.module_count} modules
                  </Typography>

                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="body2" color="text.secondary">
                        Fundability Score
                      </Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {project.fundability_score}/100
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={project.fundability_score}
                      color={getScoreColor(project.fundability_score) as any}
                      sx={{ height: 8, borderRadius: 4 }}
                    />
                  </Box>

                  <Box mb={2}>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Progress: {getMilestoneProgress(project.milestones)}%
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={getMilestoneProgress(project.milestones)}
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary" gutterBottom>
                      Milestones
                    </Typography>
                    <Box>
                      {getMilestoneChip(project.milestones.site_control)}
                      {getMilestoneChip(project.milestones.permitting)}
                      {getMilestoneChip(project.milestones.interconnection)}
                    </Box>
                  </Box>
                </CardContent>
                
                <CardActions>
                  <Button
                    size="small"
                    startIcon={<ViewIcon />}
                    onClick={() => handleViewProject(project.project_id)}
                  >
                    View Details
                  </Button>
                  {project.financials.estimated_capex && (
                    <Typography variant="body2" color="text.secondary" sx={{ ml: 'auto' }}>
                      ${(project.financials.estimated_capex / 1000).toFixed(0)}k
                    </Typography>
                  )}
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Helioscope Login Dialog */}
      <AuroraLoginForm
        open={auroraDialogOpen}
        onClose={() => setAuroraDialogOpen(false)}
        onSuccess={handleHeliSuccess}
      />
    </Box>
  );
};

export default ProjectDashboard;