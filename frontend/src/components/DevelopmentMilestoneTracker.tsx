import React from 'react';
import {
  Box,
  Typography,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  StepConnector,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Grid
} from '@mui/material';
import {
  Check as CheckIcon,
  Assignment as AssignmentIcon,
  Gavel as GavelIcon,
  Cable as CableIcon
} from '@mui/icons-material';
import { styled } from '@mui/material/styles';

interface Milestones {
  site_control: string;
  permitting: string;
  interconnection: string;
}

interface Props {
  milestones: Milestones;
}

const ColorlibConnector = styled(StepConnector)(({ theme }) => ({
  [`&.${StepConnector.alternativeLabel}`]: {
    top: 22,
  },
  [`&.${StepConnector.active}`]: {
    [`& .${StepConnector.line}`]: {
      backgroundImage:
        'linear-gradient( 95deg,rgb(242,113,33) 0%,rgb(233,64,87) 50%,rgb(138,35,135) 100%)',
    },
  },
  [`&.${StepConnector.completed}`]: {
    [`& .${StepConnector.line}`]: {
      backgroundImage:
        'linear-gradient( 95deg,rgb(242,113,33) 0%,rgb(233,64,87) 50%,rgb(138,35,135) 100%)',
    },
  },
  [`& .${StepConnector.line}`]: {
    height: 3,
    border: 0,
    backgroundColor:
      theme.palette.mode === 'dark' ? theme.palette.grey[800] : '#eaeaf0',
    borderRadius: 1,
  },
}));

const DevelopmentMilestoneTracker: React.FC<Props> = ({ milestones }) => {
  const getMilestoneStatus = (status: string) => {
    switch (status) {
      case 'Not Started':
        return { label: 'Not Started', color: 'default', completed: false, active: false };
      case 'Drafted':
      case 'Matrix Generated':
      case 'Application Drafted':
        return { label: status, color: 'primary', completed: false, active: true };
      case 'Signed':
      case 'Applications Drafted':
      case 'Submitted':
        return { label: status, color: 'success', completed: true, active: false };
      default:
        return { label: status, color: 'default', completed: false, active: false };
    }
  };

  const milestoneData = [
    {
      title: 'Site Control',
      description: 'Secure site control through lease or purchase agreement',
      icon: <AssignmentIcon />,
      status: getMilestoneStatus(milestones.site_control),
      details: [
        'Property assessment completed',
        'Landowner negotiations',
        'Letter of Intent (LOI) drafted',
        'Final agreement signed'
      ]
    },
    {
      title: 'Permitting',
      description: 'Obtain all necessary permits and approvals',
      icon: <GavelIcon />,
      status: getMilestoneStatus(milestones.permitting),
      details: [
        'Permit matrix generated',
        'Applications prepared',
        'Submitted to authorities',
        'Approvals received'
      ]
    },
    {
      title: 'Interconnection',
      description: 'Complete utility interconnection process',
      icon: <CableIcon />,
      status: getMilestoneStatus(milestones.interconnection),
      details: [
        'Interconnection application drafted',
        'Submitted to utility',
        'System impact study',
        'Interconnection agreement signed'
      ]
    }
  ];

  const getProgressPercentage = () => {
    let completed = 0;
    let total = milestoneData.length;
    
    milestoneData.forEach(milestone => {
      if (milestone.status.completed) {
        completed += 1;
      } else if (milestone.status.active) {
        completed += 0.5;
      }
    });
    
    return Math.round((completed / total) * 100);
  };

  const getStepIcon = (milestone: any, index: number) => {
    if (milestone.status.completed) {
      return (
        <Box
          sx={{
            backgroundColor: 'success.main',
            color: 'white',
            borderRadius: '50%',
            width: 40,
            height: 40,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <CheckIcon />
        </Box>
      );
    }
    
    if (milestone.status.active) {
      return (
        <Box
          sx={{
            backgroundColor: 'primary.main',
            color: 'white',
            borderRadius: '50%',
            width: 40,
            height: 40,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          {milestone.icon}
        </Box>
      );
    }
    
    return (
      <Box
        sx={{
          backgroundColor: 'grey.300',
          color: 'grey.600',
          borderRadius: '50%',
          width: 40,
          height: 40,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        {milestone.icon}
      </Box>
    );
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Development Progress
      </Typography>
      
      {/* Progress Overview */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Overall Progress
            </Typography>
            <Typography variant="h4" color="primary">
              {getProgressPercentage()}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={getProgressPercentage()}
            sx={{ height: 10, borderRadius: 5 }}
          />
        </CardContent>
      </Card>

      {/* Milestone Details */}
      <Grid container spacing={3}>
        {milestoneData.map((milestone, index) => (
          <Grid item xs={12} md={4} key={index}>
            <Card 
              sx={{ 
                height: '100%',
                border: milestone.status.active ? 2 : 1,
                borderColor: milestone.status.completed 
                  ? 'success.main' 
                  : milestone.status.active 
                    ? 'primary.main' 
                    : 'grey.300'
              }}
            >
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  {getStepIcon(milestone, index)}
                  <Box ml={2}>
                    <Typography variant="h6">
                      {milestone.title}
                    </Typography>
                    <Chip
                      label={milestone.status.label}
                      color={milestone.status.color as any}
                      size="small"
                    />
                  </Box>
                </Box>
                
                <Typography variant="body2" color="text.secondary" paragraph>
                  {milestone.description}
                </Typography>
                
                <Typography variant="subtitle2" gutterBottom>
                  Key Activities:
                </Typography>
                {milestone.details.map((detail, detailIndex) => (
                  <Typography 
                    key={detailIndex}
                    variant="body2" 
                    sx={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      mb: 0.5,
                      opacity: milestone.status.completed ? 1 : 0.7
                    }}
                  >
                    • {detail}
                  </Typography>
                ))}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Timeline View */}
      <Box mt={4}>
        <Typography variant="h6" gutterBottom>
          Timeline View
        </Typography>
        <Stepper 
          orientation="vertical" 
          connector={<ColorlibConnector />}
        >
          {milestoneData.map((milestone, index) => (
            <Step 
              key={index} 
              active={milestone.status.active}
              completed={milestone.status.completed}
            >
              <StepLabel
                StepIconComponent={() => getStepIcon(milestone, index)}
              >
                <Typography variant="h6">
                  {milestone.title}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Status: {milestone.status.label}
                </Typography>
              </StepLabel>
              <StepContent>
                <Typography paragraph>
                  {milestone.description}
                </Typography>
                <Box>
                  {milestone.details.map((detail, detailIndex) => (
                    <Typography 
                      key={detailIndex}
                      variant="body2" 
                      color="text.secondary"
                      sx={{ ml: 2, mb: 0.5 }}
                    >
                      • {detail}
                    </Typography>
                  ))}
                </Box>
              </StepContent>
            </Step>
          ))}
        </Stepper>
      </Box>
    </Box>
  );
};

export default DevelopmentMilestoneTracker;