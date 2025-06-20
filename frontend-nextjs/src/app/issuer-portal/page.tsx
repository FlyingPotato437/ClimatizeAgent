"use client";

import React, { useState } from 'react';
import { Search, Plus, Mail, Phone, DollarSign, TrendingUp, Users, Building, Filter } from 'lucide-react';

export default function IssuerPortal() {
  const [searchTerm, setSearchTerm] = useState('');

  // Mock data for the demo
  const mockInvestments = [
    {
      id: 1,
      projectName: 'SolarFarm Alpha',
      amount: 2500000,
      status: 'Active',
      irr: 12.5,
      location: 'California',
      capacity: '50MW',
      investors: 12
    },
    {
      id: 2,
      projectName: 'WindPower Beta',
      amount: 1800000,
      status: 'Funding',
      irr: 14.2,
      location: 'Texas',
      capacity: '35MW',
      investors: 8
    },
    {
      id: 3,
      projectName: 'Solar Residential',
      amount: 950000,
      status: 'Completed',
      irr: 11.8,
      location: 'Florida',
      capacity: '15MW',
      investors: 25
    }
  ];

  const mockInvestors = [
    { id: 1, name: 'Green Capital LLC', contact: 'jane@greencap.com', phone: '555-0123', totalInvested: 3500000, projects: 5 },
    { id: 2, name: 'Renewable Ventures', contact: 'mike@renewvc.com', phone: '555-0124', totalInvested: 2200000, projects: 3 },
    { id: 3, name: 'Eco Investment Fund', contact: 'sarah@ecofund.com', phone: '555-0125', totalInvested: 1800000, projects: 4 }
  ];

  const mockCommunications = [
    { id: 1, subject: 'Q4 Performance Update', type: 'Newsletter', sent: '2024-01-15', recipients: 45 },
    { id: 2, subject: 'New Investment Opportunity', type: 'Campaign', sent: '2024-01-10', recipients: 120 },
    { id: 3, subject: 'Regulatory Update', type: 'Alert', sent: '2024-01-08', recipients: 78 }
  ];

  const filteredInvestments = mockInvestments.filter(investment =>
    investment.projectName.toLowerCase().includes(searchTerm.toLowerCase()) ||
    investment.location.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="py-6">
            <h1 className="text-3xl font-bold text-gray-900">Issuer Portal</h1>
            <p className="mt-2 text-gray-600">Manage your capital raising campaigns and investor relationships</p>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <DollarSign className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Total Raised</p>
                <p className="text-2xl font-semibold text-gray-900">$12.5M</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <TrendingUp className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg IRR</p>
                <p className="text-2xl font-semibold text-gray-900">12.8%</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Building className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Active Projects</p>
                <p className="text-2xl font-semibold text-gray-900">8</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <Users className="h-8 w-8 text-orange-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Investors</p>
                <p className="text-2xl font-semibold text-gray-900">45</p>
              </div>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-8">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              <button className="border-green-500 text-green-600 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm">
                Overview
              </button>
              <button className="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm">
                Investments
              </button>
              <button className="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm">
                Investors
              </button>
              <button className="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 whitespace-nowrap py-2 px-1 border-b-2 font-medium text-sm">
                Communications
              </button>
            </nav>
          </div>
        </div>

        {/* Investment Portfolio */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex justify-between items-center">
              <h2 className="text-lg font-semibold text-gray-900">Investment Portfolio</h2>
              <button className="bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700 flex items-center">
                <Plus className="h-4 w-4 mr-2" />
                New Project
              </button>
            </div>
            <div className="mt-4 flex items-center space-x-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search projects..."
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
              </div>
              <button className="flex items-center px-4 py-2 border border-gray-300 rounded-md hover:bg-gray-50">
                <Filter className="h-4 w-4 mr-2" />
                Filter
              </button>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Project</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">IRR</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Capacity</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Investors</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredInvestments.map((investment) => (
                  <tr key={investment.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div>
                        <div className="text-sm font-medium text-gray-900">{investment.projectName}</div>
                        <div className="text-sm text-gray-500">{investment.location}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      ${investment.amount.toLocaleString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        investment.status === 'Active' ? 'bg-green-100 text-green-800' :
                        investment.status === 'Funding' ? 'bg-blue-100 text-blue-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {investment.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {investment.irr}%
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {investment.capacity}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {investment.investors}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Investor Management */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Investor Management</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {mockInvestors.map((investor) => (
                  <div key={investor.id} className="flex justify-between items-center p-4 border border-gray-200 rounded-lg">
                    <div>
                      <h3 className="text-sm font-medium text-gray-900">{investor.name}</h3>
                      <div className="flex items-center mt-1 space-x-4">
                        <span className="flex items-center text-xs text-gray-500">
                          <Mail className="h-3 w-3 mr-1" />
                          {investor.contact}
                        </span>
                        <span className="flex items-center text-xs text-gray-500">
                          <Phone className="h-3 w-3 mr-1" />
                          {investor.phone}
                        </span>
                      </div>
                      <div className="mt-1 text-xs text-gray-500">
                        ${investor.totalInvested.toLocaleString()} • {investor.projects} projects
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Communications Hub */}
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-lg font-semibold text-gray-900">Communications Hub</h2>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {mockCommunications.map((comm) => (
                  <div key={comm.id} className="p-4 border border-gray-200 rounded-lg">
                    <div className="flex justify-between items-start">
                      <div>
                        <h3 className="text-sm font-medium text-gray-900">{comm.subject}</h3>
                        <p className="text-xs text-gray-500 mt-1">{comm.type} • {comm.sent}</p>
                      </div>
                      <span className="text-xs text-gray-500">{comm.recipients} recipients</span>
                    </div>
                  </div>
                ))}
              </div>
              <button className="w-full mt-4 bg-green-600 text-white px-4 py-2 rounded-md hover:bg-green-700">
                Create New Campaign
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 