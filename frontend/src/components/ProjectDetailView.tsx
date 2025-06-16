import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  Tabs,
  Tab,
  Grid,
  Card,
  CardContent,
  Chip,
  Alert,
  CircularProgress,
  Breadcrumbs,
  Link,
  Divider
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  LocationOn as LocationIcon,
  Assessment as AssessmentIcon,
  Description as DescriptionIcon,
  AccountBalance as FinanceIcon,
  Timeline as TimelineIcon,
  Gavel as PermitIcon,
  AutoAwesome as AIIcon
} from '@mui/icons-material';
import axios from 'axios';
import DevelopmentMilestoneTracker from './DevelopmentMilestoneTracker';
import PermitMatrixView from './PermitMatrixView';
import CapitalStackView from './CapitalStackView';
import DocumentManager from './DocumentManager';
import AIPackageView from './AIPackageView';

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
    bill_of_materials: Array<{
      component_type: string;
      manufacturer?: string;
      model?: string;
      quantity: number;
    }>;
  };
  financials: {
    estimated_capex?: number;
    price_per_watt?: number;
    incentives: any[];
    capital_stack?: any;
  };
  milestones: {
    site_control: string;
    permitting: string;
    interconnection: string;
  };
  fundability_score: number;
  permit_matrix?: any;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`project-tabpanel-${index}`}
      aria-labelledby={`project-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const ProjectDetailView: React.FC = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);

  useEffect(() => {
    if (projectId) {
      fetchProject(projectId);
    }
  }, [projectId]);

  const fetchProject = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`/api/get_project/${id}`);
      setProject(response.data);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setError('Project not found.');
      } else {
        setError('Failed to load project. Please try again.');
      }
      console.error('Error fetching project:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !project) {
    return (
      <Alert 
        severity="error"
        action={
          <Button color="inherit" size="small" onClick={() => navigate('/')}>
            Back to Dashboard
          </Button>
        }
      >
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {/* Breadcrumbs */}
      <Breadcrumbs sx={{ mb: 2 }}>
        <Link
          component="button"
          variant="body1"
          onClick={() => navigate('/')}
          sx={{ textDecoration: 'none' }}
        >
          Dashboard
        </Link>
        <Typography color="text.primary">{project.project_name}</Typography>
      </Breadcrumbs>

      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={3}>
        <Box>
          <Box display="flex" alignItems="center" mb={1}>
            <Button
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate('/')}
              sx={{ mr: 2 }}
            >
              Back
            </Button>
            <Typography variant="h4" component="h1">
              {project.project_name}
            </Typography>
            <Chip
              label={project.data_source}
              color={project.data_source === 'Aurora' ? 'primary' : 'secondary'}
              sx={{ ml: 2 }}
            />
          </Box>
          <Box display="flex" alignItems="center" color="text.secondary">
            <LocationIcon fontSize="small" sx={{ mr: 1 }} />
            <Typography variant="body1">
              {project.address.street}, {project.address.city}, {project.address.state} {project.address.zip_code}
            </Typography>
          </Box>
        </Box>
        <Chip
          icon={<AssessmentIcon />}
          label={`Fundability: ${project.fundability_score}/100`}
          color={getScoreColor(project.fundability_score) as any}
          size="large"
        />
      </Box>

      {/* Quick Stats */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                System Size
              </Typography>
              <Typography variant="h5">
                {project.system_specs.system_size_dc_kw} kW DC
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Module Count
              </Typography>
              <Typography variant="h5">
                {project.system_specs.module_count}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Inverter Type
              </Typography>
              <Typography variant="h5">
                {project.system_specs.inverter_type === 'string' ? 'String' : 'Micro'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Estimated CapEx
              </Typography>
              <Typography variant="h5">
                {project.financials.estimated_capex 
                  ? `$${(project.financials.estimated_capex / 1000).toFixed(0)}k`
                  : 'TBD'
                }
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* System Specifications */}
      <Paper sx={{ mb: 3 }}>
        <Box sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            System Specifications
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Bill of Materials
              </Typography>
              {project.system_specs.bill_of_materials.map((item, index) => (
                <Box key={index} sx={{ mt: 1 }}>
                  <Typography variant="body2">
                    {item.quantity}x {item.component_type}
                    {item.manufacturer && ` - ${item.manufacturer}`}
                    {item.model && ` ${item.model}`}
                  </Typography>
                </Box>
              ))}
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="body2" color="text.secondary">
                Financial Details
              </Typography>
              <Typography variant="body2">
                Price per Watt: {project.financials.price_per_watt ? `$${project.financials.price_per_watt.toFixed(2)}/W` : 'TBD'}
              </Typography>
              <Typography variant="body2">
                Incentives: {project.financials.incentives.length} available
              </Typography>
            </Grid>
          </Grid>
        </Box>
      </Paper>

      {/* Tabbed Content */}
      <Paper>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={tabValue} onChange={handleTabChange} aria-label="project details tabs">
            <Tab 
              icon={<TimelineIcon />} 
              label="Milestones" 
              iconPosition="start"
            />
            <Tab 
              icon={<PermitIcon />} 
              label="Permits" 
              iconPosition="start"
            />
            <Tab 
              icon={<FinanceIcon />} 
              label="Capital Stack" 
              iconPosition="start"
            />
            <Tab 
              icon={<DescriptionIcon />} 
              label="Documents" 
              iconPosition="start"
            />
            <Tab 
              icon={<AIIcon />} 
              label="AI Package" 
              iconPosition="start"
            />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <DevelopmentMilestoneTracker milestones={project.milestones} />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <PermitMatrixView 
            permitMatrix={project.permit_matrix} 
            address={project.address}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <CapitalStackView 
            financials={project.financials}
            systemSize={project.system_specs.system_size_dc_kw}
          />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <DocumentManager projectId={project.project_id} />
        </TabPanel>

        <TabPanel value={tabValue} index={4}>
          <AIPackageView projectId={project.project_id} project={project} />
        </TabPanel>
      </Paper>
    </Box>
  );
};

export default ProjectDetailView;