import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, AppBar, Toolbar, Typography } from '@mui/material';
import ProjectDashboard from './components/ProjectDashboard';
import ProjectDetailView from './components/ProjectDetailView';
import ManualProjectForm from './components/ManualProjectForm';
import AIMVPForm from './components/AIMVPForm';

const theme = createTheme({
  palette: {
    primary: {
      main: '#2e7d32',
    },
    secondary: {
      main: '#ff9800',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <AppBar position="static">
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              Climatize Platform
            </Typography>
          </Toolbar>
        </AppBar>
        <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
          <Routes>
            <Route path="/" element={<ProjectDashboard />} />
            <Route path="/projects/:projectId" element={<ProjectDetailView />} />
            <Route path="/create-project" element={<ManualProjectForm />} />
            <Route path="/ai-analysis" element={<AIMVPForm />} />
          </Routes>
        </Container>
      </Router>
    </ThemeProvider>
  );
}

export default App;