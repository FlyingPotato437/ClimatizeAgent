import React from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  List,
  ListItem,
  ListItemText,
  Divider,
  Alert,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  AccountBalance as BankIcon,
  Savings as SavingsIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';

interface Financials {
  estimated_capex?: number;
  price_per_watt?: number;
  incentives: any[];
  capital_stack?: {
    total_project_cost: number;
    post_incentive_cost: number;
    equity_percentage: number;
    debt_percentage: number;
    equity_amount: number;
    debt_amount: number;
    debt_details?: {
      interest_rate?: number;
      term_years?: number;
      annual_debt_service?: number;
    };
    returns?: {
      irr?: number;
      cash_on_cash?: number;
      payback_period?: number;
    };
  };
}

interface Props {
  financials: Financials;
  systemSize: number;
}

const CapitalStackView: React.FC<Props> = ({ financials, systemSize }) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const formatPercentage = (value: number) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (!financials.capital_stack) {
    return (
      <Box>
        <Alert severity="info" sx={{ mb: 3 }}>
          Capital stack analysis is being generated for this project. This information will be available once the project workflow is complete.
        </Alert>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Basic Financial Information
            </Typography>
            <Grid container spacing={3}>
              {financials.estimated_capex && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Estimated CapEx
                  </Typography>
                  <Typography variant="h5">
                    {formatCurrency(financials.estimated_capex)}
                  </Typography>
                </Grid>
              )}
              {financials.price_per_watt && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Price per Watt
                  </Typography>
                  <Typography variant="h5">
                    ${financials.price_per_watt.toFixed(2)}/W
                  </Typography>
                </Grid>
              )}
              <Grid item xs={12} sm={6}>
                <Typography variant="body2" color="text.secondary">
                  System Size
                </Typography>
                <Typography variant="h5">
                  {systemSize} kW DC
                </Typography>
              </Grid>
              {financials.incentives.length > 0 && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="body2" color="text.secondary">
                    Incentives Available
                  </Typography>
                  <Typography variant="h5">
                    {financials.incentives.length}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      </Box>
    );
  }

  const capitalStack = financials.capital_stack;

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Capital Stack Analysis
      </Typography>

      {/* Financial Summary */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <AssessmentIcon color="primary" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Total Project Cost
                </Typography>
              </Box>
              <Typography variant="h5">
                {formatCurrency(capitalStack.total_project_cost)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                ${(capitalStack.total_project_cost / systemSize / 1000).toFixed(2)}/W
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <TrendingUpIcon color="success" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Post-Incentive Cost
                </Typography>
              </Box>
              <Typography variant="h5">
                {formatCurrency(capitalStack.post_incentive_cost)}
              </Typography>
              <Typography variant="body2" color="success.main">
                {formatCurrency(capitalStack.total_project_cost - capitalStack.post_incentive_cost)} savings
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <SavingsIcon color="warning" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Equity Required
                </Typography>
              </Box>
              <Typography variant="h5">
                {formatCurrency(capitalStack.equity_amount)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatPercentage(capitalStack.equity_percentage)} of total
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={1}>
                <BankIcon color="info" sx={{ mr: 1 }} />
                <Typography variant="body2" color="text.secondary">
                  Debt Financing
                </Typography>
              </Box>
              <Typography variant="h5">
                {formatCurrency(capitalStack.debt_amount)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {formatPercentage(capitalStack.debt_percentage)} of total
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Capital Stack Visualization */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Capital Stack Breakdown
          </Typography>
          <Box mb={3}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2">
                Equity ({formatPercentage(capitalStack.equity_percentage)})
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {formatCurrency(capitalStack.equity_amount)}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={capitalStack.equity_percentage * 100}
              sx={{ 
                height: 30, 
                borderRadius: 1,
                backgroundColor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: 'warning.main'
                }
              }}
            />
          </Box>
          <Box>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="body2">
                Debt ({formatPercentage(capitalStack.debt_percentage)})
              </Typography>
              <Typography variant="body2" fontWeight="bold">
                {formatCurrency(capitalStack.debt_amount)}
              </Typography>
            </Box>
            <LinearProgress
              variant="determinate"
              value={capitalStack.debt_percentage * 100}
              sx={{ 
                height: 30, 
                borderRadius: 1,
                backgroundColor: 'grey.200',
                '& .MuiLinearProgress-bar': {
                  backgroundColor: 'info.main'
                }
              }}
            />
          </Box>
        </CardContent>
      </Card>

      {/* Incentives Breakdown */}
      {financials.incentives.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Available Incentives
            </Typography>
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Incentive Type</TableCell>
                    <TableCell>Description</TableCell>
                    <TableCell align="right">Value</TableCell>
                    <TableCell>Status</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {financials.incentives.map((incentive, index) => (
                    <TableRow key={index}>
                      <TableCell>{incentive.type || 'Federal ITC'}</TableCell>
                      <TableCell>{incentive.description || 'Investment Tax Credit'}</TableCell>
                      <TableCell align="right">
                        {incentive.value 
                          ? formatCurrency(incentive.value)
                          : formatPercentage(incentive.percentage || 0.30)
                        }
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={incentive.status || 'Available'}
                          color="success"
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
      )}

      {/* Debt Details */}
      {capitalStack.debt_details && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Debt Structure Details
            </Typography>
            <Grid container spacing={3}>
              {capitalStack.debt_details.interest_rate && (
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Interest Rate
                  </Typography>
                  <Typography variant="h6">
                    {formatPercentage(capitalStack.debt_details.interest_rate)}
                  </Typography>
                </Grid>
              )}
              {capitalStack.debt_details.term_years && (
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Term
                  </Typography>
                  <Typography variant="h6">
                    {capitalStack.debt_details.term_years} years
                  </Typography>
                </Grid>
              )}
              {capitalStack.debt_details.annual_debt_service && (
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Annual Debt Service
                  </Typography>
                  <Typography variant="h6">
                    {formatCurrency(capitalStack.debt_details.annual_debt_service)}
                  </Typography>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}

      {/* Investment Returns */}
      {capitalStack.returns && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Projected Investment Returns
            </Typography>
            <Grid container spacing={3}>
              {capitalStack.returns.irr && (
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Internal Rate of Return (IRR)
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {formatPercentage(capitalStack.returns.irr)}
                  </Typography>
                </Grid>
              )}
              {capitalStack.returns.cash_on_cash && (
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Cash-on-Cash Return
                  </Typography>
                  <Typography variant="h6" color="success.main">
                    {formatPercentage(capitalStack.returns.cash_on_cash)}
                  </Typography>
                </Grid>
              )}
              {capitalStack.returns.payback_period && (
                <Grid item xs={12} sm={4}>
                  <Typography variant="body2" color="text.secondary">
                    Payback Period
                  </Typography>
                  <Typography variant="h6">
                    {capitalStack.returns.payback_period.toFixed(1)} years
                  </Typography>
                </Grid>
              )}
            </Grid>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default CapitalStackView;