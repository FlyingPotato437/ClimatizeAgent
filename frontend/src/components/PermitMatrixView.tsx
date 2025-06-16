import React from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  AccessTime as TimeIcon,
  AttachMoney as MoneyIcon,
  Warning as WarningIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  LocationOn as LocationIcon
} from '@mui/icons-material';

interface Address {
  street: string;
  city: string;
  state: string;
  zip_code: string;
}

interface PermitRequirement {
  permit_type: string;
  authority: string;
  estimated_timeline: string;
  estimated_cost: number;
  complexity: 'Low' | 'Medium' | 'High';
  requirements: string[];
  status: 'Not Started' | 'In Progress' | 'Completed';
}

interface JurisdictionInfo {
  jurisdiction_name: string;
  jurisdiction_type: string;
  solar_friendly_rating: number;
  average_approval_time: string;
  typical_requirements: string[];
  special_considerations: string[];
}

interface Props {
  permitMatrix?: {
    jurisdiction_info: JurisdictionInfo;
    permit_requirements: PermitRequirement[];
    total_estimated_cost: number;
    total_estimated_timeline: string;
    risk_factors: string[];
  };
  address: Address;
}

const PermitMatrixView: React.FC<Props> = ({ permitMatrix, address }) => {
  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Low': return 'success';
      case 'Medium': return 'warning';
      case 'High': return 'error';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Completed': return 'success';
      case 'In Progress': return 'warning';
      case 'Not Started': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Completed': return <CheckIcon color="success" />;
      case 'In Progress': return <TimeIcon color="warning" />;
      case 'Not Started': return <AssignmentIcon color="disabled" />;
      default: return <AssignmentIcon color="disabled" />;
    }
  };

  const getSolarFriendlyColor = (rating: number) => {
    if (rating >= 8) return 'success';
    if (rating >= 6) return 'warning';
    return 'error';
  };

  if (!permitMatrix) {
    return (
      <Box>
        <Alert severity="info" sx={{ mb: 3 }}>
          Permit matrix is being generated for this project. This process typically takes a few minutes.
        </Alert>
        <Card>
          <CardContent>
            <Box display="flex" alignItems="center" mb={2}>
              <LocationIcon sx={{ mr: 1 }} />
              <Typography variant="h6">
                Project Location
              </Typography>
            </Box>
            <Typography variant="body1">
              {address.street}
            </Typography>
            <Typography variant="body1">
              {address.city}, {address.state} {address.zip_code}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Permit requirements and jurisdictional information will appear here once analysis is complete.
            </Typography>
          </CardContent>
        </Card>
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Permit Matrix & Jurisdictional Analysis
      </Typography>

      {/* Jurisdiction Overview */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Jurisdiction Information
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Jurisdiction
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {permitMatrix.jurisdiction_info.jurisdiction_name}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Type
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {permitMatrix.jurisdiction_info.jurisdiction_type}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Average Approval Time
                  </Typography>
                  <Typography variant="body1" fontWeight="bold">
                    {permitMatrix.jurisdiction_info.average_approval_time}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Solar Friendly Rating
                  </Typography>
                  <Box display="flex" alignItems="center">
                    <Typography variant="body1" fontWeight="bold" sx={{ mr: 1 }}>
                      {permitMatrix.jurisdiction_info.solar_friendly_rating}/10
                    </Typography>
                    <Chip
                      label={
                        permitMatrix.jurisdiction_info.solar_friendly_rating >= 8 
                          ? 'Excellent' 
                          : permitMatrix.jurisdiction_info.solar_friendly_rating >= 6 
                            ? 'Good' 
                            : 'Challenging'
                      }
                      color={getSolarFriendlyColor(permitMatrix.jurisdiction_info.solar_friendly_rating) as any}
                      size="small"
                    />
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Project Summary
              </Typography>
              <Box mb={2}>
                <Typography variant="body2" color="text.secondary">
                  Total Estimated Cost
                </Typography>
                <Typography variant="h5" color="primary">
                  ${permitMatrix.total_estimated_cost.toLocaleString()}
                </Typography>
              </Box>
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Total Timeline
                </Typography>
                <Typography variant="h6">
                  {permitMatrix.total_estimated_timeline}
                </Typography>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Risk Factors */}
      {permitMatrix.risk_factors.length > 0 && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="subtitle1" gutterBottom>
            Risk Factors to Consider:
          </Typography>
          <List dense>
            {permitMatrix.risk_factors.map((risk, index) => (
              <ListItem key={index} sx={{ py: 0 }}>
                <ListItemIcon sx={{ minWidth: 30 }}>
                  <WarningIcon fontSize="small" color="warning" />
                </ListItemIcon>
                <ListItemText primary={risk} />
              </ListItem>
            ))}
          </List>
        </Alert>
      )}

      {/* Permit Requirements Table */}
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Required Permits & Approvals
          </Typography>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Permit Type</TableCell>
                  <TableCell>Authority</TableCell>
                  <TableCell>Timeline</TableCell>
                  <TableCell>Est. Cost</TableCell>
                  <TableCell>Complexity</TableCell>
                  <TableCell>Status</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {permitMatrix.permit_requirements.map((permit, index) => (
                  <TableRow key={index}>
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        {getStatusIcon(permit.status)}
                        <Typography variant="body2" sx={{ ml: 1 }}>
                          {permit.permit_type}
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>{permit.authority}</TableCell>
                    <TableCell>{permit.estimated_timeline}</TableCell>
                    <TableCell>${permit.estimated_cost.toLocaleString()}</TableCell>
                    <TableCell>
                      <Chip
                        label={permit.complexity}
                        color={getComplexityColor(permit.complexity) as any}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={permit.status}
                        color={getStatusColor(permit.status) as any}
                        size="small"
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Detailed Requirements */}
      <Box mt={3}>
        <Typography variant="h6" gutterBottom>
          Detailed Requirements by Permit
        </Typography>
        <Grid container spacing={3}>
          {permitMatrix.permit_requirements.map((permit, index) => (
            <Grid item xs={12} md={6} key={index}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
                    <Typography variant="h6">
                      {permit.permit_type}
                    </Typography>
                    <Chip
                      label={permit.complexity}
                      color={getComplexityColor(permit.complexity) as any}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Authority: {permit.authority}
                  </Typography>
                  <Divider sx={{ my: 2 }} />
                  <Typography variant="subtitle2" gutterBottom>
                    Requirements:
                  </Typography>
                  <List dense>
                    {permit.requirements.map((req, reqIndex) => (
                      <ListItem key={reqIndex} sx={{ py: 0.5 }}>
                        <ListItemIcon sx={{ minWidth: 30 }}>
                          <AssignmentIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={req}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Typical Requirements */}
      {permitMatrix.jurisdiction_info.typical_requirements.length > 0 && (
        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Typical Jurisdiction Requirements
            </Typography>
            <Grid container spacing={2}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle2" gutterBottom>
                  Standard Requirements:
                </Typography>
                <List dense>
                  {permitMatrix.jurisdiction_info.typical_requirements.map((req, index) => (
                    <ListItem key={index} sx={{ py: 0.5 }}>
                      <ListItemIcon sx={{ minWidth: 30 }}>
                        <CheckIcon fontSize="small" color="success" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={req}
                        primaryTypographyProps={{ variant: 'body2' }}
                      />
                    </ListItem>
                  ))}
                </List>
              </Grid>
              {permitMatrix.jurisdiction_info.special_considerations.length > 0 && (
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Special Considerations:
                  </Typography>
                  <List dense>
                    {permitMatrix.jurisdiction_info.special_considerations.map((consideration, index) => (
                      <ListItem key={index} sx={{ py: 0.5 }}>
                        <ListItemIcon sx={{ minWidth: 30 }}>
                          <WarningIcon fontSize="small" color="warning" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={consideration}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default PermitMatrixView;