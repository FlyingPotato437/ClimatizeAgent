import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  CircularProgress,
  Divider
} from '@mui/material';
import {
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
  AttachMoney as MoneyIcon,
  Timeline as TimelineIcon,
  Description as DocumentIcon,
  Lightbulb as LightbulbIcon
} from '@mui/icons-material';
import axios from 'axios';

interface AIPackageViewProps {
  projectId: string;
  project: any;
}

const AIPackageView: React.FC<AIPackageViewProps> = ({ projectId, project }) => {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState<string | null>(null);

  const handleDownloadPackage = async () => {
    setDownloading(true);
    setDownloadError(null);

    try {
      const response = await axios.get(`/api/download_project_package/${projectId}`);
      
      if (response.data.download_url) {
        // Open download URL in new tab
        window.open(response.data.download_url, '_blank');
      }
    } catch (err: any) {
      setDownloadError('Failed to generate download package. Please try again.');
      console.error('Download error:', err);
    } finally {
      setDownloading(false);
    }
  };

  const eligibilityScreening = project.eligibility_screening || {};
  const capitalStack = project.financials?.capital_stack || {};
  const permitMatrix = project.permit_matrix || {};
  const developmentChecklist = project.development_checklist || [];

  const getEligibilityStatus = () => {
    if (eligibilityScreening.eligible) {
      return { color: 'success', label: 'Eligible', icon: <CheckCircleIcon /> };
    } else if (eligibilityScreening.eligible === false) {
      return { color: 'error', label: 'Not Eligible', icon: <WarningIcon /> };
    }
    return { color: 'info', label: 'Pending', icon: <InfoIcon /> };
  };

  const eligibilityStatus = getEligibilityStatus();

  return (
    <Box>
      {/* Header with Download Button */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">
          AI-Generated Project Package
        </Typography>
        <Button
          variant="contained"
          startIcon={downloading ? <CircularProgress size={16} /> : <DownloadIcon />}
          onClick={handleDownloadPackage}
          disabled={downloading}
        >
          {downloading ? 'Generating...' : 'Download Package'}
        </Button>
      </Box>

      {downloadError && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {downloadError}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Eligibility Screening */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                {eligibilityStatus.icon}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Eligibility Screening
                </Typography>
                <Chip 
                  label={eligibilityStatus.label} 
                  color={eligibilityStatus.color as any}
                  size="small"
                  sx={{ ml: 'auto' }}
                />
              </Box>
              
              {eligibilityScreening.incentive_score && (
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    Incentive Score: {eligibilityScreening.incentive_score}/100
                  </Typography>
                </Box>
              )}

              {eligibilityScreening.warnings && eligibilityScreening.warnings.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Considerations:
                  </Typography>
                  <List dense>
                    {eligibilityScreening.warnings.map((warning: string, index: number) => (
                      <ListItem key={index} sx={{ py: 0 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <WarningIcon fontSize="small" color="warning" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={warning}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Fundability Score */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <LightbulbIcon />
                <Typography variant="h6" sx={{ ml: 1 }}>
                  Fundability Analysis
                </Typography>
              </Box>
              
              <Box textAlign="center" mb={2}>
                <Typography variant="h3" color="primary">
                  {project.fundability_score || 0}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  out of 100
                </Typography>
              </Box>

              {project.fundability_factors && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Key Factors:
                  </Typography>
                  <List dense>
                    {Object.entries(project.fundability_factors).map(([key, value]) => (
                      <ListItem key={key} sx={{ py: 0 }}>
                        <ListItemText 
                          primary={`${key.replace(/_/g, ' ')}: ${value}`}
                          primaryTypographyProps={{ variant: 'body2' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Climatize Financing Options */}
        {capitalStack.climatize_advantages && (
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <MoneyIcon sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Climatize Financing Advantages
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <List>
                  {capitalStack.climatize_advantages.map((advantage: string, index: number) => (
                    <ListItem key={index}>
                      <ListItemIcon>
                        <CheckCircleIcon color="success" />
                      </ListItemIcon>
                      <ListItemText primary={advantage} />
                    </ListItem>
                  ))}
                </List>
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}

        {/* Development Checklist */}
        {developmentChecklist.length > 0 && (
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <TimelineIcon sx={{ mr: 1 }} />
                <Typography variant="h6">
                  Development Checklist
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Grid container spacing={2}>
                  {developmentChecklist.map((item: any, index: number) => (
                    <Grid item xs={12} md={6} key={index}>
                      <Card variant="outlined">
                        <CardContent sx={{ py: 2 }}>
                          <Box display="flex" alignItems="center" mb={1}>
                            <Chip 
                              label={item.category}
                              size="small"
                              variant="outlined"
                            />
                            <Chip 
                              label={item.priority}
                              size="small"
                              color={item.priority === 'high' ? 'error' : item.priority === 'medium' ? 'warning' : 'default'}
                              sx={{ ml: 1 }}
                            />
                          </Box>
                          <Typography variant="body2" gutterBottom>
                            {item.task}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            Timeline: {item.estimated_timeline}
                          </Typography>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}

        {/* Site Control Documents */}
        {project.project_documents?.site_control && (
          <Grid item xs={12}>
            <Accordion>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <DocumentIcon sx={{ mr: 1 }} />
                <Typography variant="h6">
                  AI-Generated Site Control Documents
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Letter of Intent Status: {project.project_documents.site_control.status}
                </Typography>
                <Typography variant="body2" color="text.secondary" paragraph>
                  Generated: {new Date(project.project_documents.site_control.generated_date).toLocaleDateString()}
                </Typography>
                
                {project.project_documents.site_control.document_content && (
                  <Paper sx={{ p: 2, bgcolor: 'grey.50', mt: 2 }}>
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', fontSize: '0.8rem' }}>
                      {project.project_documents.site_control.document_content.substring(0, 500)}...
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                      Preview - Download full package for complete document
                    </Typography>
                  </Paper>
                )}
              </AccordionDetails>
            </Accordion>
          </Grid>
        )}
      </Grid>

      {/* Footer Information */}
      <Box mt={4}>
        <Divider sx={{ mb: 2 }} />
        <Typography variant="body2" color="text.secondary" align="center">
          This comprehensive analysis was generated by Climatize AI in under 10 minutes.
          Download the complete package for detailed financial models, permit requirements, and site control documents.
        </Typography>
      </Box>
    </Box>
  );
};

export default AIPackageView;