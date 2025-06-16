import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Button,
  Alert,
  Chip,
  Divider,
  Grid,
  CircularProgress
} from '@mui/material';
import {
  Description as DocumentIcon,
  Download as DownloadIcon,
  Archive as ArchiveIcon,
  Assignment as AssignmentIcon,
  AccountBalance as FinanceIcon,
  Gavel as PermitIcon,
  CloudDownload as CloudDownloadIcon,
  Folder as FolderIcon
} from '@mui/icons-material';
import axios from 'axios';

interface Document {
  id: string;
  name: string;
  type: 'LOI' | 'Permit Application' | 'Financial Model' | 'Report' | 'Other';
  size: string;
  created_date: string;
  status: 'Draft' | 'Final' | 'Submitted';
  download_url: string;
}

interface Props {
  projectId: string;
}

const DocumentManager: React.FC<Props> = ({ projectId }) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadingPackage, setDownloadingPackage] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDocuments();
  }, [projectId]);

  const fetchDocuments = async () => {
    try {
      setLoading(true);
      setError(null);
      // In a real implementation, this would fetch from an API
      // For now, we'll simulate some documents
      const mockDocuments: Document[] = [
        {
          id: '1',
          name: 'Site Lease Letter of Intent.pdf',
          type: 'LOI',
          size: '245 KB',
          created_date: '2024-01-15',
          status: 'Draft',
          download_url: `/api/documents/${projectId}/loi.pdf`
        },
        {
          id: '2',
          name: 'Building Permit Application.pdf',
          type: 'Permit Application',
          size: '1.2 MB',
          created_date: '2024-01-16',
          status: 'Draft',
          download_url: `/api/documents/${projectId}/building-permit.pdf`
        },
        {
          id: '3',
          name: 'Electrical Permit Application.pdf',
          type: 'Permit Application',
          size: '890 KB',
          created_date: '2024-01-16',
          status: 'Draft',
          download_url: `/api/documents/${projectId}/electrical-permit.pdf`
        },
        {
          id: '4',
          name: 'Project Financial Model.xlsx',
          type: 'Financial Model',
          size: '512 KB',
          created_date: '2024-01-17',
          status: 'Final',
          download_url: `/api/documents/${projectId}/financial-model.xlsx`
        }
      ];
      
      setDocuments(mockDocuments);
    } catch (err: any) {
      setError('Failed to load documents. Please try again.');
      console.error('Error fetching documents:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadDocument = async (document: Document) => {
    try {
      // In a real implementation, this would download the file
      window.open(document.download_url, '_blank');
    } catch (err) {
      console.error('Error downloading document:', err);
    }
  };

  const handleDownloadPackage = async () => {
    try {
      setDownloadingPackage(true);
      // In a real implementation, this would create and download a ZIP package
      const response = await axios.get(`/api/documents/${projectId}/package`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `project-${projectId}-documents.zip`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error downloading package:', err);
      // For demo purposes, show an alert
      alert('Document package download feature will be available once the backend is fully configured.');
    } finally {
      setDownloadingPackage(false);
    }
  };

  const getDocumentIcon = (type: Document['type']) => {
    switch (type) {
      case 'LOI':
        return <AssignmentIcon />;
      case 'Permit Application':
        return <PermitIcon />;
      case 'Financial Model':
        return <FinanceIcon />;
      case 'Report':
        return <DocumentIcon />;
      default:
        return <DocumentIcon />;
    }
  };

  const getStatusColor = (status: Document['status']) => {
    switch (status) {
      case 'Final':
        return 'success';
      case 'Submitted':
        return 'info';
      case 'Draft':
        return 'warning';
      default:
        return 'default';
    }
  };

  const groupDocumentsByType = (docs: Document[]) => {
    const grouped = docs.reduce((acc, doc) => {
      if (!acc[doc.type]) {
        acc[doc.type] = [];
      }
      acc[doc.type].push(doc);
      return acc;
    }, {} as Record<string, Document[]>);
    
    return grouped;
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error">
        {error}
      </Alert>
    );
  }

  const groupedDocuments = groupDocumentsByType(documents);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h6">
          Project Documents
        </Typography>
        <Button
          variant="contained"
          startIcon={downloadingPackage ? <CircularProgress size={20} /> : <ArchiveIcon />}
          onClick={handleDownloadPackage}
          disabled={downloadingPackage || documents.length === 0}
        >
          {downloadingPackage ? 'Preparing...' : 'Download Package'}
        </Button>
      </Box>

      {documents.length === 0 ? (
        <Alert severity="info">
          No documents have been generated yet. Documents will appear here as they are created during the project workflow.
        </Alert>
      ) : (
        <Grid container spacing={3}>
          {/* Document Summary */}
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Document Summary
                </Typography>
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    Total Documents
                  </Typography>
                  <Typography variant="h4">
                    {documents.length}
                  </Typography>
                </Box>
                <Box mb={2}>
                  <Typography variant="body2" color="text.secondary">
                    Ready for Download
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {documents.filter(doc => doc.status === 'Final').length}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">
                    In Draft
                  </Typography>
                  <Typography variant="h6" color="warning.main">
                    {documents.filter(doc => doc.status === 'Draft').length}
                  </Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Document List */}
          <Grid item xs={12} md={8}>
            {Object.entries(groupedDocuments).map(([type, docs]) => (
              <Card key={type} sx={{ mb: 2 }}>
                <CardContent>
                  <Box display="flex" alignItems="center" mb={2}>
                    <FolderIcon sx={{ mr: 1 }} />
                    <Typography variant="h6">
                      {type}
                    </Typography>
                    <Chip
                      label={`${docs.length} file${docs.length !== 1 ? 's' : ''}`}
                      size="small"
                      sx={{ ml: 2 }}
                    />
                  </Box>
                  <List dense>
                    {docs.map((document, index) => (
                      <React.Fragment key={document.id}>
                        <ListItem>
                          <ListItemIcon>
                            {getDocumentIcon(document.type)}
                          </ListItemIcon>
                          <ListItemText
                            primary={document.name}
                            secondary={
                              <Box>
                                <Typography variant="body2" color="text.secondary">
                                  {document.size} • Created {new Date(document.created_date).toLocaleDateString()}
                                </Typography>
                                <Chip
                                  label={document.status}
                                  color={getStatusColor(document.status) as any}
                                  size="small"
                                  sx={{ mt: 0.5 }}
                                />
                              </Box>
                            }
                          />
                          <ListItemSecondaryAction>
                            <IconButton
                              edge="end"
                              onClick={() => handleDownloadDocument(document)}
                              disabled={document.status === 'Draft'}
                            >
                              <DownloadIcon />
                            </IconButton>
                          </ListItemSecondaryAction>
                        </ListItem>
                        {index < docs.length - 1 && <Divider />}
                      </React.Fragment>
                    ))}
                  </List>
                </CardContent>
              </Card>
            ))}
          </Grid>
        </Grid>
      )}

      {/* Document Generation Status */}
      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Document Generation Status
        </Typography>
        <Typography variant="body2">
          Documents are automatically generated as the project progresses through different milestones. 
          Draft documents are created first and will be marked as "Final" once they are ready for use.
        </Typography>
      </Alert>
    </Box>
  );
};

export default DocumentManager;