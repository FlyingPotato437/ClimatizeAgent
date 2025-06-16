import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Chip,
  LinearProgress
} from '@mui/material';
import { AI as AIIcon, LocationOn as LocationIcon, Solar as SolarIcon } from '@mui/icons-material';
import axios from 'axios';

interface FormData {
  zip_code: string;
  system_size_kw: number;
  roof_type?: string;
  property_type?: string;
}

interface ProcessingStatus {
  project_id: string;
  status: string;
  progress: number;
  current_stage: string;
  estimated_completion: string;
}

const steps = [
  'Project Input',
  'AI Analysis',
  'Results Ready'
];

const AIMVPForm: React.FC = () => {
  const [formData, setFormData] = useState<FormData>({
    zip_code: '',
    system_size_kw: 100,
    roof_type: 'flat',
    property_type: 'commercial'
  });
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [processingStatus, setProcessingStatus] = useState<ProcessingStatus | null>(null);
  const [expandedData, setExpandedData] = useState<any>(null);
  const navigate = useNavigate();

  const handleInputChange = (field: keyof FormData, value: string | number) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSubmit = async () => {
    if (!formData.zip_code || !formData.system_size_kw) {
      setError('Please enter both ZIP code and system size');
      return;
    }

    setLoading(true);
    setError(null);
    setActiveStep(1);

    try {
      const response = await axios.post('/api/agentic_ai_mvp', formData);
      
      if (response.status === 202) {
        setProjectId(response.data.project_id);
        setExpandedData(response.data.auto_expanded_data);
        setActiveStep(1);
        
        // Start polling for status
        startPolling(response.data.project_id);
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Failed to start AI analysis. Please try again.');
      setActiveStep(0);
    } finally {
      setLoading(false);
    }
  };

  const startPolling = async (project_id: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await axios.get(`/api/get_project_package/${project_id}`);
        
        if (response.status === 200) {
          // Analysis complete
          clearInterval(pollInterval);
          setActiveStep(2);
          setProcessingStatus(null);
          navigate(`/projects/${project_id}`);
        } else if (response.status === 202) {
          // Still processing
          setProcessingStatus(response.data);
        }
      } catch (err) {
        console.error('Polling error:', err);
        // Continue polling unless there's a serious error
      }
    }, 3000); // Poll every 3 seconds

    // Stop polling after 10 minutes
    setTimeout(() => {
      clearInterval(pollInterval);
      if (activeStep === 1) {
        setError('Analysis is taking longer than expected. Please check back later.');
      }
    }, 600000);
  };

  const handleReset = () => {
    setFormData({
      zip_code: '',
      system_size_kw: 100,
      roof_type: 'flat',
      property_type: 'commercial'
    });
    setActiveStep(0);
    setError(null);
    setProjectId(null);
    setProcessingStatus(null);
    setExpandedData(null);
  };

  return (
    <Box maxWidth="md" mx="auto">
      <Paper sx={{ p: 4 }}>
        <Box display="flex" alignItems="center" mb={3}>
          <AIIcon sx={{ mr: 2, color: 'primary.main', fontSize: 32 }} />
          <Typography variant="h4" component="h1">
            AI-Powered Solar Analysis
          </Typography>
        </Box>
        
        <Typography variant="body1" color="text.secondary" paragraph>
          Enter minimal project details and let our AI generate a comprehensive solar development package in minutes.
        </Typography>

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {activeStep === 0 && (
          <Grid container spacing={3}>
            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Basic Project Information
              </Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="ZIP Code"
                value={formData.zip_code}
                onChange={(e) => handleInputChange('zip_code', e.target.value)}
                placeholder="12345"
                helperText="Project location ZIP code"
                InputProps={{
                  startAdornment: <LocationIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="System Size (kW)"
                type="number"
                value={formData.system_size_kw}
                onChange={(e) => handleInputChange('system_size_kw', parseFloat(e.target.value) || 0)}
                placeholder="100"
                helperText="DC system size in kilowatts"
                InputProps={{
                  startAdornment: <SolarIcon sx={{ mr: 1, color: 'text.secondary' }} />
                }}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Roof Type"
                value={formData.roof_type}
                onChange={(e) => handleInputChange('roof_type', e.target.value)}
                SelectProps={{ native: true }}
                helperText="Primary installation type"
              >
                <option value="flat">Flat Roof</option>
                <option value="pitched">Pitched Roof</option>
                <option value="ground_mount">Ground Mount</option>
              </TextField>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                select
                label="Property Type"
                value={formData.property_type}
                onChange={(e) => handleInputChange('property_type', e.target.value)}
                SelectProps={{ native: true }}
                helperText="Type of commercial property"
              >
                <option value="commercial">Commercial Building</option>
                <option value="industrial">Industrial Facility</option>
                <option value="agricultural">Agricultural Property</option>
                <option value="municipal">Municipal Building</option>
              </TextField>
            </Grid>

            <Grid item xs={12}>
              <Box display="flex" justifyContent="space-between" alignItems="center" mt={3}>
                <Button
                  variant="outlined"
                  onClick={() => navigate('/')}
                  disabled={loading}
                >
                  Back to Dashboard
                </Button>
                <Button
                  variant="contained"
                  onClick={handleSubmit}
                  disabled={loading || !formData.zip_code || !formData.system_size_kw}
                  startIcon={loading ? <CircularProgress size={20} /> : <AIIcon />}
                  size="large"
                >
                  {loading ? 'Starting Analysis...' : 'Generate AI Analysis'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        )}

        {activeStep === 1 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              AI Analysis in Progress
            </Typography>
            
            {expandedData && (
              <Card sx={{ mb: 3 }}>
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    Auto-Expanded Project Data
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary">
                        Location: {expandedData.address.city}, {expandedData.address.state}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <Typography variant="body2" color="text.secondary">
                        System Size: {expandedData.system_size_kw} kW DC
                      </Typography>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            )}

            {processingStatus && (
              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="body1">
                    {processingStatus.current_stage}
                  </Typography>
                  <Chip 
                    label={`${processingStatus.progress}% Complete`} 
                    color="primary" 
                    size="small" 
                  />
                </Box>
                
                <LinearProgress 
                  variant="determinate" 
                  value={processingStatus.progress} 
                  sx={{ mb: 2, height: 8, borderRadius: 4 }}
                />
                
                <Typography variant="body2" color="text.secondary">
                  Estimated completion: {processingStatus.estimated_completion}
                </Typography>
              </Box>
            )}

            <Box mt={3}>
              <Typography variant="body2" color="text.secondary" paragraph>
                Our AI is analyzing your project across multiple dimensions:
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Box 
                      width={8} 
                      height={8} 
                      borderRadius="50%" 
                      bgcolor="primary.main" 
                      mr={1} 
                    />
                    <Typography variant="body2">Eligibility Screening</Typography>
                  </Box>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Box 
                      width={8} 
                      height={8} 
                      borderRadius="50%" 
                      bgcolor="primary.main" 
                      mr={1} 
                    />
                    <Typography variant="body2">System Design & Production</Typography>
                  </Box>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Box 
                      width={8} 
                      height={8} 
                      borderRadius="50%" 
                      bgcolor="primary.main" 
                      mr={1} 
                    />
                    <Typography variant="body2">Permit Requirements</Typography>
                  </Box>
                </Grid>
                <Grid item xs={12} md={6}>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Box 
                      width={8} 
                      height={8} 
                      borderRadius="50%" 
                      bgcolor="primary.main" 
                      mr={1} 
                    />
                    <Typography variant="body2">Financial Analysis</Typography>
                  </Box>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Box 
                      width={8} 
                      height={8} 
                      borderRadius="50%" 
                      bgcolor="primary.main" 
                      mr={1} 
                    />
                    <Typography variant="body2">Site Control Documents</Typography>
                  </Box>
                  <Box display="flex" alignItems="center" mb={1}>
                    <Box 
                      width={8} 
                      height={8} 
                      borderRadius="50%" 
                      bgcolor="primary.main" 
                      mr={1} 
                    />
                    <Typography variant="body2">Fundability Scoring</Typography>
                  </Box>
                </Grid>
              </Grid>
            </Box>

            <Box display="flex" justifyContent="center" mt={4}>
              <Button variant="outlined" onClick={handleReset}>
                Start New Analysis
              </Button>
            </Box>
          </Box>
        )}

        {activeStep === 2 && (
          <Box textAlign="center">
            <Typography variant="h5" color="primary" gutterBottom>
              Analysis Complete!
            </Typography>
            <Typography variant="body1" paragraph>
              Your comprehensive solar development package has been generated.
            </Typography>
            <Button
              variant="contained"
              size="large"
              onClick={() => navigate(`/projects/${projectId}`)}
            >
              View Complete Analysis
            </Button>
          </Box>
        )}
      </Paper>
    </Box>
  );
};

export default AIMVPForm;