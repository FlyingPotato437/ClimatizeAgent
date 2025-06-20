"use client";

import { useState } from "react";
import { 
  Zap, 
  TrendingUp, 
  DollarSign, 
  Brain, 
  BarChart3,
  Activity,
  PlusCircle,
  Filter,
  Search,
  ArrowUpRight,
  Calendar,
  MapPin,
  Shield,
  AlertTriangle,
  CheckCircle2
} from "lucide-react";

interface Project {
  id: string;
  name: string;
  location: string;
  capacity: string;
  status: 'Analysis' | 'Approved' | 'Funded' | 'Complete';
  investment: number;
  irr: number;
  risk_score: number;
  updated: string;
}

export default function Dashboard() {
  const [projects] = useState<Project[]>([
    {
      id: "1",
      name: "Sunrise Solar Farm",
      location: "California, USA",
      capacity: "50MW",
      status: "Analysis",
      investment: 85000000,
      irr: 12.4,
      risk_score: 7.2,
      updated: "2024-01-15"
    },
    {
      id: "2", 
      name: "Desert Wind & Solar",
      location: "Arizona, USA",
      capacity: "75MW",
      status: "Approved",
      investment: 120000000,
      irr: 14.8,
      risk_score: 6.8,
      updated: "2024-01-12"
    },
    {
      id: "3",
      name: "Pacific Coast Solar",
      location: "Oregon, USA", 
      capacity: "30MW",
      status: "Funded",
      investment: 45000000,
      irr: 11.2,
      risk_score: 8.1,
      updated: "2024-01-10"
    }
  ]);



  const getStatusColor = (status: string) => {
    switch (status) {
      case 'Analysis': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'Approved': return 'bg-green-100 text-green-800 border-green-200';
      case 'Funded': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'Complete': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'Analysis': return <Activity className="w-3 h-3" />;
      case 'Approved': return <CheckCircle2 className="w-3 h-3" />;
      case 'Funded': return <DollarSign className="w-3 h-3" />;
      case 'Complete': return <CheckCircle2 className="w-3 h-3" />;
      default: return <Activity className="w-3 h-3" />;
    }
  };

  const getRiskColor = (score: number) => {
    if (score <= 5) return 'text-green-600';
    if (score <= 7) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };

  const totalInvestment = projects.reduce((sum, p) => sum + p.investment, 0);
  const avgIRR = projects.reduce((sum, p) => sum + p.irr, 0) / projects.length;
  const activeProjects = projects.filter(p => p.status !== 'Complete').length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-green-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                Portfolio Dashboard
              </h1>
              <p className="text-gray-600 mt-1">
                AI-powered solar project analysis and management
              </p>
            </div>
            <div className="flex gap-3">
              <button className="px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg font-medium transition-colors flex items-center">
                <Filter className="w-4 h-4 mr-2" />
                Filter
              </button>
              <button className="px-6 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors flex items-center">
                <PlusCircle className="w-4 h-4 mr-2" />
                New Project
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">Total Investment</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {formatCurrency(totalInvestment)}
                </p>
              </div>
              <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                <DollarSign className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="flex items-center mt-4 text-sm">
              <ArrowUpRight className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-green-600 font-medium">+12.5%</span>
              <span className="text-gray-600 ml-1">vs last quarter</span>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">Average IRR</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {avgIRR.toFixed(1)}%
                </p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                <TrendingUp className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div className="flex items-center mt-4 text-sm">
              <ArrowUpRight className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-green-600 font-medium">+2.3%</span>
              <span className="text-gray-600 ml-1">vs target</span>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">Active Projects</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">
                  {activeProjects}
                </p>
              </div>
              <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                <BarChart3 className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div className="flex items-center mt-4 text-sm">
              <Activity className="w-4 h-4 text-blue-600 mr-1" />
              <span className="text-blue-600 font-medium">{projects.filter(p => p.status === 'Analysis').length}</span>
              <span className="text-gray-600 ml-1">in analysis</span>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600 font-medium">AI Agents</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">4</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-xl flex items-center justify-center">
                <Brain className="w-6 h-6 text-orange-600" />
              </div>
            </div>
            <div className="flex items-center mt-4 text-sm">
              <Zap className="w-4 h-4 text-green-600 mr-1" />
              <span className="text-green-600 font-medium">Online</span>
              <span className="text-gray-600 ml-1">& collaborating</span>
            </div>
          </div>
        </div>

        {/* Ultrathink AI Insights Panel */}
        <div className="grid lg:grid-cols-3 gap-8 mb-8">
          <div className="lg:col-span-2">
            {/* Projects Table */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200">
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h2 className="text-xl font-bold text-gray-900">Project Portfolio</h2>
                  <div className="flex items-center gap-4">
                    <div className="relative">
                      <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
                      <input 
                        type="text" 
                        placeholder="Search projects..."
                        className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-green-500 focus:border-green-500"
                      />
                    </div>
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Investment</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IRR</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Risk</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Updated</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {projects.map((project) => (
                      <tr key={project.id} className="hover:bg-gray-50 transition-colors cursor-pointer">
                        <td className="px-6 py-4">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{project.name}</div>
                            <div className="text-sm text-gray-500 flex items-center">
                              <MapPin className="w-3 h-3 mr-1" />
                              {project.location} • {project.capacity}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-medium border ${getStatusColor(project.status)}`}>
                            {getStatusIcon(project.status)}
                            <span className="ml-1">{project.status}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-900 font-medium">
                          {formatCurrency(project.investment)}
                        </td>
                        <td className="px-6 py-4 text-sm font-medium">
                          <span className="text-green-600">{project.irr}%</span>
                        </td>
                        <td className="px-6 py-4 text-sm">
                          <div className="flex items-center">
                            <div className={`w-2 h-2 rounded-full mr-2 ${getRiskColor(project.risk_score).includes('green') ? 'bg-green-500' : getRiskColor(project.risk_score).includes('yellow') ? 'bg-yellow-500' : 'bg-red-500'}`}></div>
                            <span className={`font-medium ${getRiskColor(project.risk_score)}`}>
                              {project.risk_score}/10
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-500">
                          <div className="flex items-center">
                            <Calendar className="w-3 h-3 mr-1" />
                            {project.updated}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          {/* AI Insights Sidebar */}
          <div className="space-y-6">
            {/* Real-time Agent Activity */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-bold text-gray-900">Agent Activity</h3>
                <div className="flex items-center">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></div>
                  <span className="text-sm text-gray-600">Live</span>
                </div>
              </div>

              <div className="space-y-4">
                <div className="border border-green-200 rounded-lg p-4 bg-green-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-green-600 rounded-lg flex items-center justify-center mr-3">
                        <Brain className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">HelioScope Agent</p>
                        <p className="text-xs text-gray-600">Technical Analysis</p>
                      </div>
                    </div>
                    <span className="text-xs text-green-600 bg-green-100 px-2 py-1 rounded-full">Active</span>
                  </div>
                  <p className="text-sm text-gray-700 mt-3">
                    Analyzing shading patterns for Sunrise Solar Farm. Collaborative input requested from Permit Agent.
                  </p>
                </div>

                <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center mr-3">
                        <Shield className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">Permit Agent</p>
                        <p className="text-xs text-gray-600">Regulatory Analysis</p>
                      </div>
                    </div>
                    <span className="text-xs text-blue-600 bg-blue-100 px-2 py-1 rounded-full">Thinking</span>
                  </div>
                  <p className="text-sm text-gray-700 mt-3">
                    Reviewing local zoning requirements. Bouncing ideas with HelioScope Agent on optimal placement.
                  </p>
                </div>

                <div className="border border-purple-200 rounded-lg p-4 bg-purple-50">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center">
                      <div className="w-8 h-8 bg-purple-600 rounded-lg flex items-center justify-center mr-3">
                        <TrendingUp className="w-4 h-4 text-white" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-900">Financial Agent</p>
                        <p className="text-xs text-gray-600">Investment Analysis</p>
                      </div>
                    </div>
                    <span className="text-xs text-purple-600 bg-purple-100 px-2 py-1 rounded-full">Complete</span>
                  </div>
                  <p className="text-sm text-gray-700 mt-3">
                    IRR calculation complete: 12.4%. Waiting for final technical consensus from other agents.
                  </p>
                </div>
              </div>
            </div>

            {/* AI Recommendations */}
            <div className="bg-white rounded-2xl shadow-lg border border-gray-200 p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-4">AI Recommendations</h3>
              
              <div className="space-y-4">
                <div className="border border-orange-200 rounded-lg p-4 bg-orange-50">
                  <div className="flex items-start">
                    <AlertTriangle className="w-5 h-5 text-orange-600 mt-0.5 mr-3 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">Risk Alert</p>
                      <p className="text-xs text-gray-600 mt-1">
                        Sunrise Solar Farm shows elevated risk due to permit complexity. Recommend additional due diligence.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border border-green-200 rounded-lg p-4 bg-green-50">
                  <div className="flex items-start">
                    <CheckCircle2 className="w-5 h-5 text-green-600 mt-0.5 mr-3 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">Opportunity</p>
                      <p className="text-xs text-gray-600 mt-1">
                        Desert Wind & Solar exceeds all criteria. Agents unanimously recommend immediate funding.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="border border-blue-200 rounded-lg p-4 bg-blue-50">
                  <div className="flex items-start">
                    <Brain className="w-5 h-5 text-blue-600 mt-0.5 mr-3 flex-shrink-0" />
                    <div>
                      <p className="text-sm font-medium text-gray-900">Collaboration Insight</p>
                      <p className="text-xs text-gray-600 mt-1">
                        Agent consensus improved decision accuracy by 23% this quarter vs single-agent analysis.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 