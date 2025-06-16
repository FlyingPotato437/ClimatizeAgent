import React, { useState } from 'react';
import { useForm, useFieldArray, Controller } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Grid,
  MenuItem,
  IconButton,
  Divider,
  Alert,
  CircularProgress
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon } from '@mui/icons-material';
import axios from 'axios';

interface BillOfMaterialItem {
  component_type: string;
  manufacturer: string;
  model: string;
  quantity: number;
}

interface FormData {
  project_name: string;
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
    bill_of_materials: BillOfMaterialItem[];
  };
  financials: {
    estimated_capex: number;
    price_per_watt: number;
  };
}

const ManualProjectForm: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const { control, handleSubmit, formState: { errors }, reset } = useForm<FormData>({
    defaultValues: {
      project_name: '',
      address: {
        street: '',
        city: '',
        state: '',
        zip_code: ''
      },
      system_specs: {
        system_size_dc_kw: 0,
        module_count: 0,
        inverter_type: 'string',
        bill_of_materials: [
          { component_type: 'module', manufacturer: '', model: '', quantity: 0 }
        ]
      },
      financials: {
        estimated_capex: 0,
        price_per_watt: 0
      }
    }
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: 'system_specs.bill_of_materials'
  });

  const onSubmit = async (data: FormData) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.post('/api/manual_intake_handler', {
        ...data,
        data_source: 'Manual'
      });
      
      setSuccess(true);
      setTimeout(() => {
        navigate('/');
      }, 2000);
    } catch (err: any) {
      setError(err.response?.data?.message || 'Failed to create project. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const addBOMItem = () => {
    append({ component_type: 'module', manufacturer: '', model: '', quantity: 0 });
  };

  const removeBOMItem = (index: number) => {
    if (fields.length > 1) {
      remove(index);
    }
  };

  if (success) {
    return (
      <Paper sx={{ p: 4, textAlign: 'center' }}>
        <Alert severity="success" sx={{ mb: 2 }}>
          Project created successfully! Redirecting to dashboard...
        </Alert>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 4 }}>
      <Typography variant="h4" gutterBottom>
        Create New Solar Project
      </Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      <form onSubmit={handleSubmit(onSubmit)}>
        <Grid container spacing={3}>
          {/* Project Name */}
          <Grid item xs={12}>
            <Controller
              name="project_name"
              control={control}
              rules={{ required: 'Project name is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Project Name"
                  error={!!errors.project_name}
                  helperText={errors.project_name?.message}
                />
              )}
            />
          </Grid>

          {/* Address Section */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Project Address
            </Typography>
          </Grid>
          
          <Grid item xs={12}>
            <Controller
              name="address.street"
              control={control}
              rules={{ required: 'Street address is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Street Address"
                  error={!!errors.address?.street}
                  helperText={errors.address?.street?.message}
                />
              )}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <Controller
              name="address.city"
              control={control}
              rules={{ required: 'City is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="City"
                  error={!!errors.address?.city}
                  helperText={errors.address?.city?.message}
                />
              )}
            />
          </Grid>

          <Grid item xs={12} sm={3}>
            <Controller
              name="address.state"
              control={control}
              rules={{ required: 'State is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="State"
                  error={!!errors.address?.state}
                  helperText={errors.address?.state?.message}
                />
              )}
            />
          </Grid>

          <Grid item xs={12} sm={3}>
            <Controller
              name="address.zip_code"
              control={control}
              rules={{ required: 'ZIP code is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="ZIP Code"
                  error={!!errors.address?.zip_code}
                  helperText={errors.address?.zip_code?.message}
                />
              )}
            />
          </Grid>

          {/* System Specifications */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              System Specifications
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Controller
              name="system_specs.system_size_dc_kw"
              control={control}
              rules={{ 
                required: 'System size is required',
                min: { value: 0.1, message: 'System size must be greater than 0' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="System Size (kW DC)"
                  type="number"
                  error={!!errors.system_specs?.system_size_dc_kw}
                  helperText={errors.system_specs?.system_size_dc_kw?.message}
                />
              )}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <Controller
              name="system_specs.module_count"
              control={control}
              rules={{ 
                required: 'Module count is required',
                min: { value: 1, message: 'Module count must be at least 1' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Module Count"
                  type="number"
                  error={!!errors.system_specs?.module_count}
                  helperText={errors.system_specs?.module_count?.message}
                />
              )}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <Controller
              name="system_specs.inverter_type"
              control={control}
              rules={{ required: 'Inverter type is required' }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  select
                  label="Inverter Type"
                  error={!!errors.system_specs?.inverter_type}
                  helperText={errors.system_specs?.inverter_type?.message}
                >
                  <MenuItem value="string">String Inverter</MenuItem>
                  <MenuItem value="microinverter">Microinverter</MenuItem>
                </TextField>
              )}
            />
          </Grid>

          {/* Bill of Materials */}
          <Grid item xs={12}>
            <Box display="flex" justifyContent="space-between" alignItems="center">
              <Typography variant="subtitle1">
                Bill of Materials
              </Typography>
              <Button
                startIcon={<AddIcon />}
                onClick={addBOMItem}
                variant="outlined"
                size="small"
              >
                Add Item
              </Button>
            </Box>
          </Grid>

          {fields.map((field, index) => (
            <Grid container item xs={12} spacing={2} key={field.id}>
              <Grid item xs={12} sm={3}>
                <Controller
                  name={`system_specs.bill_of_materials.${index}.component_type`}
                  control={control}
                  rules={{ required: 'Component type is required' }}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      select
                      label="Component Type"
                      size="small"
                    >
                      <MenuItem value="module">Module</MenuItem>
                      <MenuItem value="inverter">Inverter</MenuItem>
                      <MenuItem value="racking">Racking</MenuItem>
                      <MenuItem value="other">Other</MenuItem>
                    </TextField>
                  )}
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Controller
                  name={`system_specs.bill_of_materials.${index}.manufacturer`}
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Manufacturer"
                      size="small"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={12} sm={3}>
                <Controller
                  name={`system_specs.bill_of_materials.${index}.model`}
                  control={control}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Model"
                      size="small"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={10} sm={2}>
                <Controller
                  name={`system_specs.bill_of_materials.${index}.quantity`}
                  control={control}
                  rules={{ 
                    required: 'Quantity is required',
                    min: { value: 1, message: 'Quantity must be at least 1' }
                  }}
                  render={({ field }) => (
                    <TextField
                      {...field}
                      fullWidth
                      label="Quantity"
                      type="number"
                      size="small"
                    />
                  )}
                />
              </Grid>
              <Grid item xs={2} sm={1}>
                <IconButton
                  onClick={() => removeBOMItem(index)}
                  disabled={fields.length === 1}
                  color="error"
                >
                  <DeleteIcon />
                </IconButton>
              </Grid>
            </Grid>
          ))}

          {/* Financials */}
          <Grid item xs={12}>
            <Typography variant="h6" gutterBottom>
              Financial Information
            </Typography>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Controller
              name="financials.estimated_capex"
              control={control}
              rules={{ 
                required: 'Estimated CapEx is required',
                min: { value: 0, message: 'CapEx must be 0 or greater' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Estimated CapEx ($)"
                  type="number"
                  error={!!errors.financials?.estimated_capex}
                  helperText={errors.financials?.estimated_capex?.message}
                />
              )}
            />
          </Grid>

          <Grid item xs={12} sm={6}>
            <Controller
              name="financials.price_per_watt"
              control={control}
              rules={{ 
                required: 'Price per watt is required',
                min: { value: 0, message: 'Price per watt must be 0 or greater' }
              }}
              render={({ field }) => (
                <TextField
                  {...field}
                  fullWidth
                  label="Price per Watt ($/W)"
                  type="number"
                  step="0.01"
                  error={!!errors.financials?.price_per_watt}
                  helperText={errors.financials?.price_per_watt?.message}
                />
              )}
            />
          </Grid>

          {/* Submit Button */}
          <Grid item xs={12}>
            <Divider sx={{ my: 2 }} />
            <Box display="flex" justifyContent="space-between">
              <Button
                variant="outlined"
                onClick={() => navigate('/')}
                disabled={loading}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                variant="contained"
                disabled={loading}
                startIcon={loading ? <CircularProgress size={20} /> : null}
              >
                {loading ? 'Creating Project...' : 'Create Project'}
              </Button>
            </Box>
          </Grid>
        </Grid>
      </form>
    </Paper>
  );
};

export default ManualProjectForm;