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
import { CloudDownload as AuroraIcon } from '@mui/icons-material';
import axios from 'axios';

interface Props {
  open: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

const AuroraLoginForm: React.FC<Props> = ({ open, onClose, onSuccess }) => {
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
    apiKey: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [authMethod, setAuthMethod] = useState<'credentials' | 'apiKey'>('credentials');

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setCredentials(prev => ({
      ...prev,
      [field]: event.target.value
    }));
    setError(null);
  };

  const handleConnect = async () => {
    setLoading(true);
    setError(null);

    try {
      // Validate inputs
      if (authMethod === 'credentials') {
        if (!credentials.username || !credentials.password) {
          setError('Please enter both username and password');
          setLoading(false);
          return;
        }
      } else {
        if (!credentials.apiKey) {
          setError('Please enter your Aurora API key');
          setLoading(false);
          return;
        }
      }

      // Call backend to establish Aurora connection
      const response = await axios.post('/api/aurora/connect', {
        authMethod,
        ...credentials
      });

      if (response.data.success) {
        onSuccess?.();
        onClose();
        setCredentials({ username: '', password: '', apiKey: '' });
      } else {
        setError(response.data.message || 'Failed to connect to Aurora');
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Connection failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    if (!loading) {
      setCredentials({ username: '', password: '', apiKey: '' });
      setError(null);
      onClose();
    }
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        <Box display="flex" alignItems="center">
          <AuroraIcon sx={{ mr: 2 }} />
          Connect to Aurora Solar
        </Box>
      </DialogTitle>
      
      <DialogContent>
        <Typography variant="body2" color="text.secondary" paragraph>
          Connect your Aurora Solar account to automatically import solar designs and project data.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Authentication Method
          </Typography>
          <Box display="flex" gap={1}>
            <Button
              variant={authMethod === 'credentials' ? 'contained' : 'outlined'}
              onClick={() => setAuthMethod('credentials')}
              size="small"
            >
              Username/Password
            </Button>
            <Button
              variant={authMethod === 'apiKey' ? 'contained' : 'outlined'}
              onClick={() => setAuthMethod('apiKey')}
              size="small"
            >
              API Key
            </Button>
          </Box>
        </Box>

        {authMethod === 'credentials' ? (
          <Box>
            <TextField
              fullWidth
              label="Aurora Username"
              value={credentials.username}
              onChange={handleInputChange('username')}
              margin="normal"
              disabled={loading}
            />
            <TextField
              fullWidth
              label="Aurora Password"
              type="password"
              value={credentials.password}
              onChange={handleInputChange('password')}
              margin="normal"
              disabled={loading}
            />
          </Box>
        ) : (
          <Box>
            <TextField
              fullWidth
              label="Aurora API Key"
              value={credentials.apiKey}
              onChange={handleInputChange('apiKey')}
              margin="normal"
              disabled={loading}
              placeholder="Enter your Aurora Solar API key"
            />
            <Typography variant="caption" color="text.secondary">
              You can find your API key in your Aurora Solar account settings under "API Access".
            </Typography>
          </Box>
        )}

        <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            What happens after connecting?
          </Typography>
          <Typography variant="body2" color="text.secondary">
            • Climatize will sync your existing Aurora designs<br/>
            • New designs will automatically appear in your dashboard<br/>
            • Permit analysis and financial modeling will be generated automatically<br/>
            • Your Aurora data remains secure and private
          </Typography>
        </Box>

        <Box sx={{ mt: 2 }}>
          <Typography variant="caption" color="text.secondary">
            Don't have Aurora Solar? <Link href="https://www.aurorasolar.com" target="_blank">Learn more</Link> about Aurora's solar design platform.
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={loading}>
          Cancel
        </Button>
        <Button
          onClick={handleConnect}
          variant="contained"
          disabled={loading}
          startIcon={loading ? <CircularProgress size={20} /> : null}
        >
          {loading ? 'Connecting...' : 'Connect Aurora'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default AuroraLoginForm;