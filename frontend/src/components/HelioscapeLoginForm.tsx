import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Alert,
  Box,
  CircularProgress,
  Link
} from '@mui/material';
import { SolarPower as HelioscapeIcon } from '@mui/icons-material';
import axios from 'axios';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const HelioscapeLoginForm: React.FC<Props> = ({ open, onClose, onSuccess }) => {
  const [credentials, setCredentials] = useState({
    helioscope_project_id: '',
    api_token: '',
    project_name: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setCredentials(prev => ({
      ...prev,
      [field]: event.target.value
    }));
    setError(null);
  };

  const handleImportProject = async () => {
    setLoading(true);
    setError(null);

    try {
      // Validate inputs
      if (!credentials.helioscope_project_id || !credentials.api_token) {
        setError('Please enter both Project ID and API Token');
        setLoading(false);
        return;
      }

      // Call backend to import Helioscope project
      const response = await axios.post('/api/helioscope_project_intake', {
        helioscope_project_id: credentials.helioscope_project_id,
        helioscope_credentials: {
          api_token: credentials.api_token
        },
        project_name: credentials.project_name || undefined
      });

      if (response.data.project_id) {
        onSuccess?.();
        onClose();
        setCredentials({ helioscope_project_id: '', api_token: '', project_name: '' });
      } else {
        setError(response.data.error || 'Failed to import Helioscope project');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'Import failed. Please check your credentials and project ID.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setCredentials({ helioscope_project_id: '', api_token: '', project_name: '' });
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center">
          <HelioscapeIcon sx={{ mr: 2 }} />
          Import from Helioscope
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Typography variant="body2" color="text.secondary" paragraph>
          Import your Helioscope project data including design specs, simulation results, 
          DXF files, and production reports for comprehensive permit analysis.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <TextField
          fullWidth
          label="Helioscope Project ID"
          value={credentials.helioscope_project_id}
          onChange={handleInputChange('helioscope_project_id')}
          margin="normal"
          disabled={loading}
          placeholder="Enter your Helioscope project ID"
          required
        />

        <TextField
          fullWidth
          label="API Token"
          type="password"
          value={credentials.api_token}
          onChange={handleInputChange('api_token')}
          margin="normal"
          disabled={loading}
          placeholder="Enter your Helioscope API token"
          required
        />

        <TextField
          fullWidth
          label="Project Name (Optional)"
          value={credentials.project_name}
          onChange={handleInputChange('project_name')}
          margin="normal"
          disabled={loading}
          placeholder="Custom name for this project"
        />

        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            What data will be imported?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Design specifications and system sizing<br/>
            • Production reports and simulation data<br/>
            • Shade analysis and irradiance data<br/>
            • Bill of materials (modules, inverters, wiring)<br/>
            • DXF files and site images<br/>
            • Single-line diagrams
          </Typography>
        </Box>

        <Box sx={{ mt: 2, p: 2, bgcolor: 'warning.light', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom color="warning.dark">
            Enterprise API Required
          </Typography>
          <Typography variant="body2" color="warning.dark">
            This feature requires a Helioscope Enterprise subscription ($10,000/year) 
            to access the full API endpoints mentioned in your Aurora Solar meeting.
          </Typography>
        </Box>

        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Need help finding your Project ID or API token? <Link href="https://help.helioscope.com/api" target="_blank">View Helioscope API documentation</Link>
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleImportProject}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Importing...' : 'Import Project'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default HelioscapeLoginForm;