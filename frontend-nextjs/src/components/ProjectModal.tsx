"use client";

import { useState } from "react";
import { X, Loader2 } from "lucide-react";

interface ProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProjectFormData) => void;
  isLoading?: boolean;
}

interface ProjectFormData {
  project_name: string;
  address: string;
  system_size_kw: number;
  project_type: string;
  contact_email: string;
  description: string;
}

export default function ProjectModal({ isOpen, onClose, onSubmit, isLoading = false }: ProjectModalProps) {
  const [formData, setFormData] = useState<ProjectFormData>({
    project_name: "",
    address: "",
    system_size_kw: 1000,
    project_type: "Commercial Solar",
    contact_email: "",
    description: ""
  });

  const [errors, setErrors] = useState<Partial<ProjectFormData>>({});

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate form
    const newErrors: Partial<ProjectFormData> = {};
    if (!formData.project_name.trim()) newErrors.project_name = "Project name is required";
    if (!formData.address.trim()) newErrors.address = "Address is required";
    if (formData.system_size_kw < 50 || formData.system_size_kw > 5000) {
      newErrors.system_size_kw = "System size must be between 50kW and 5MW";
    }
    if (!formData.contact_email.trim()) newErrors.contact_email = "Email is required";

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    onSubmit(formData);
  };

  const handleInputChange = (field: keyof ProjectFormData, value: string | number) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: undefined }));
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-gray-900">New Solar Project</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={isLoading}
          >
            <X className="w-5 h-5 text-gray-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Name *
            </label>
            <input
              type="text"
              value={formData.project_name}
              onChange={(e) => handleInputChange('project_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="e.g., Sunrise Solar Farm"
              disabled={isLoading}
            />
            {errors.project_name && (
              <p className="text-red-600 text-sm mt-1">{errors.project_name}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Address *
            </label>
            <input
              type="text"
              value={formData.address}
              onChange={(e) => handleInputChange('address', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="e.g., 123 Solar Drive, Austin, TX 78701"
              disabled={isLoading}
            />
            {errors.address && (
              <p className="text-red-600 text-sm mt-1">{errors.address}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              System Size (kW) *
            </label>
            <input
              type="number"
              value={formData.system_size_kw}
              onChange={(e) => handleInputChange('system_size_kw', parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="1000"
              min="50"
              max="5000"
              disabled={isLoading}
            />
            {errors.system_size_kw && (
              <p className="text-red-600 text-sm mt-1">{errors.system_size_kw}</p>
            )}
            <p className="text-gray-500 text-xs mt-1">Range: 50kW - 5MW</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Project Type
            </label>
            <select
              value={formData.project_type}
              onChange={(e) => handleInputChange('project_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              disabled={isLoading}
            >
              <option value="Commercial Solar">Commercial Solar</option>
              <option value="Industrial Solar">Industrial Solar</option>
              <option value="Utility Solar">Utility Solar</option>
              <option value="Community Solar">Community Solar</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Contact Email *
            </label>
            <input
              type="email"
              value={formData.contact_email}
              onChange={(e) => handleInputChange('contact_email', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="developer@example.com"
              disabled={isLoading}
            />
            {errors.contact_email && (
              <p className="text-red-600 text-sm mt-1">{errors.contact_email}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-green-500 focus:border-green-500 transition-colors"
              placeholder="Project description and additional details..."
              rows={3}
              disabled={isLoading}
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading && <Loader2 className="w-4 h-4 mr-2 animate-spin" />}
              {isLoading ? 'Processing...' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}