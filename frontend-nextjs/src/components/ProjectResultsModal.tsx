"use client";

import { X, Download, Eye, TrendingUp, AlertTriangle, CheckCircle2 } from "lucide-react";

interface WorkflowResponse {
  project_id: string;
  workflow_status: string;
  success: boolean;
  processing_time_seconds: number;
  agent_results: {
    research?: any;
    design?: any;
    site_qualification?: any;
    permitting?: any;
  };
  final_package: {
    overall_recommendation?: {
      recommendation: string;
      confidence_score: number;
    };
    executive_summary?: any;
    financial_projections?: any;
    implementation_timeline?: any;
    risk_assessment?: any;
  };
}

interface ProjectResultsModalProps {
  isOpen: boolean;
  onClose: () => void;
  result: WorkflowResponse | null;
}

export default function ProjectResultsModal({ isOpen, onClose, result }: ProjectResultsModalProps) {
  if (!isOpen || !result) return null;

  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation) {
      case 'PROCEED':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case 'CAUTION':
        return <AlertTriangle className="w-5 h-5 text-yellow-600" />;
      case 'DEFER':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      default:
        return <TrendingUp className="w-5 h-5 text-blue-600" />;
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'PROCEED':
        return 'text-green-700 bg-green-100';
      case 'CAUTION':
        return 'text-yellow-700 bg-yellow-100';
      case 'DEFER':
        return 'text-red-700 bg-red-100';
      default:
        return 'text-blue-700 bg-blue-100';
    }
  };

  const recommendation = result.final_package?.overall_recommendation;
  const confidenceScore = recommendation?.confidence_score || 0;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">Project Analysis Results</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        {/* Analysis Status */}
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
          <div className="flex items-center">
            <CheckCircle2 className="w-5 h-5 text-green-600 mr-2" />
            <span className="text-green-700 font-medium">Analysis Complete</span>
          </div>
          <p className="text-green-600 text-sm mt-1">
            Processing completed in {result.processing_time_seconds.toFixed(1)} seconds
          </p>
        </div>

        {/* Overall Recommendation */}
        {recommendation && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Overall Recommendation</h3>
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center">
                  {getRecommendationIcon(recommendation.recommendation)}
                  <span className={`ml-2 px-3 py-1 rounded-full text-sm font-medium ${getRecommendationColor(recommendation.recommendation)}`}>
                    {recommendation.recommendation}
                  </span>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">{confidenceScore}%</div>
                  <div className="text-xs text-gray-500">Confidence</div>
                </div>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div 
                  className="bg-green-600 h-2 rounded-full transition-all duration-500"
                  style={{ width: `${confidenceScore}%` }}
                ></div>
              </div>
            </div>
          </div>
        )}

        {/* Agent Results Summary */}
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-3">Agent Analysis</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {result.agent_results.research && (
              <div className="border rounded-lg p-3">
                <div className="flex items-center mb-2">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                  <span className="text-sm font-medium text-gray-900">Research Agent</span>
                </div>
                <p className="text-xs text-gray-600">Feasibility analysis completed</p>
              </div>
            )}
            
            {result.agent_results.design && (
              <div className="border rounded-lg p-3">
                <div className="flex items-center mb-2">
                  <div className="w-2 h-2 bg-green-500 rounded-full mr-2"></div>
                  <span className="text-sm font-medium text-gray-900">Design Agent</span>
                </div>
                <p className="text-xs text-gray-600">System design completed</p>
              </div>
            )}
            
            {result.agent_results.site_qualification && (
              <div className="border rounded-lg p-3">
                <div className="flex items-center mb-2">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mr-2"></div>
                  <span className="text-sm font-medium text-gray-900">Site Qualification</span>
                </div>
                <p className="text-xs text-gray-600">Site assessment completed</p>
              </div>
            )}
            
            {result.agent_results.permitting && (
              <div className="border rounded-lg p-3">
                <div className="flex items-center mb-2">
                  <div className="w-2 h-2 bg-orange-500 rounded-full mr-2"></div>
                  <span className="text-sm font-medium text-gray-900">Permitting Agent</span>
                </div>
                <p className="text-xs text-gray-600">Permit analysis completed</p>
              </div>
            )}
          </div>
        </div>

        {/* Financial Projections */}
        {result.final_package?.financial_projections && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Financial Overview</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-gray-600">Estimated Cost:</span>
                  <div className="font-semibold text-gray-900">
                    ${(result.final_package.financial_projections.estimated_project_cost || 0).toLocaleString()}
                  </div>
                </div>
                <div>
                  <span className="text-gray-600">Annual Production:</span>
                  <div className="font-semibold text-gray-900">
                    {(result.final_package.financial_projections.estimated_annual_production || 0).toLocaleString()} kWh
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Timeline */}
        {result.final_package?.implementation_timeline && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Implementation Timeline</h3>
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="text-sm text-gray-600">
                Total Project Duration: <span className="font-semibold text-gray-900">
                  {result.final_package.implementation_timeline.total_project_duration}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end space-x-3 pt-4 border-t">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors flex items-center"
          >
            <Eye className="w-4 h-4 mr-2" />
            View Details
          </button>
          <button
            onClick={async () => {
              try {
                const response = await fetch(`http://localhost:8000/api/v1/projects/${result.project_id}/download`);
                if (response.ok) {
                  const blob = await response.blob();
                  const url = window.URL.createObjectURL(blob);
                  const link = document.createElement('a');
                  link.href = url;
                  link.download = `solar_project_${result.project_id}_report.json`;
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                  window.URL.revokeObjectURL(url);
                } else {
                  alert('Download failed. Please try again.');
                }
              } catch (error) {
                console.error('Download error:', error);
                alert('Download failed. Please try again.');
              }
            }}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center"
          >
            <Download className="w-4 h-4 mr-2" />
            Download Report
          </button>
        </div>
      </div>
    </div>
  );
}