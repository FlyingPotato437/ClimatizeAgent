"""
Enhanced project data models with validation and business logic.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from enum import Enum
import re


class RoofType(str, Enum):
    """Roof installation types."""
    FLAT = "flat"
    PITCHED = "pitched"
    GROUND_MOUNT = "ground_mount"


class InterconnectionStatus(str, Enum):
    """Interconnection application status."""
    NOT_STARTED = "Not Started"
    APPLICATION_DRAFTED = "Application Drafted"
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"


class ProjectStatus(str, Enum):
    """Overall project status."""
    SCREENING = "screening"
    DEVELOPMENT = "development"
    PERMITTING = "permitting"
    CONSTRUCTION = "construction"
    OPERATIONAL = "operational"
    CANCELLED = "cancelled"


class Address(BaseModel):
    """Enhanced address model with validation."""
    street: str = Field(..., min_length=5, max_length=200)
    city: str = Field(..., min_length=2, max_length=100)
    state: str = Field(..., min_length=2, max_length=2)
    zip_code: str = Field(..., pattern=r'^\d{5}(-\d{4})?$')
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    parcel_id: Optional[str] = None
    county: Optional[str] = None
    
    @field_validator('state')
    @classmethod
    def validate_state(cls, v):
        """Validate US state codes."""
        valid_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
        }
        if v.upper() not in valid_states:
            raise ValueError(f'Invalid state code: {v}')
        return v.upper()


class BillOfMaterialItem(BaseModel):
    """Bill of materials item with cost tracking."""
    component_type: str = Field(..., description="Component category")
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    quantity: int = Field(..., gt=0)
    unit_cost: Optional[float] = Field(None, ge=0)
    total_cost: Optional[float] = Field(None, ge=0)
    specifications: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('component_type')
    def validate_component_type(cls, v):
        """Validate component types."""
        valid_types = {
            'module', 'inverter', 'racking', 'battery', 'electrical',
            'monitoring', 'labor', 'other'
        }
        if v.lower() not in valid_types:
            raise ValueError(f'Invalid component type: {v}')
        return v.lower()
    
    @root_validator
    def calculate_total_cost(cls, values):
        """Auto-calculate total cost if unit cost provided."""
        if values.get('unit_cost') and values.get('quantity'):
            values['total_cost'] = values['unit_cost'] * values['quantity']
        return values


class BatterySpecs(BaseModel):
    """Enhanced battery specifications."""
    power_kw: float = Field(..., gt=0)
    energy_kwh: float = Field(..., gt=0)
    duration_hours: float = Field(..., gt=0)
    purpose: str = "peak_shaving"
    estimated_cost: Optional[float] = Field(None, ge=0)
    chemistry: Optional[str] = None
    cycles: Optional[int] = None
    efficiency: Optional[float] = Field(None, ge=0, le=1)
    
    @validator('duration_hours')
    def validate_duration(cls, v, values):
        """Validate duration matches power/energy ratio."""
        if 'power_kw' in values and 'energy_kwh' in values:
            calculated_duration = values['energy_kwh'] / values['power_kw']
            if abs(v - calculated_duration) > 0.1:
                raise ValueError('Duration must match energy/power ratio')
        return v


class SystemSpecs(BaseModel):
    """Enhanced system specifications with validation."""
    system_size_dc_kw: float = Field(..., gt=0, le=10000)
    system_size_ac_kw: Optional[float] = Field(None, gt=0, le=10000)
    module_count: int = Field(..., gt=0)
    inverter_type: str = Field(..., description="Inverter technology")
    roof_type: RoofType
    annual_kwh_load: Optional[float] = Field(None, ge=0)
    bill_of_materials: List[BillOfMaterialItem] = Field(default_factory=list)
    battery_specs: Optional[BatterySpecs] = None
    tilt_angle: Optional[float] = Field(None, ge=0, le=90)
    azimuth: Optional[float] = Field(None, ge=0, le=360)
    
    @validator('inverter_type')
    def validate_inverter_type(cls, v):
        """Validate inverter types."""
        valid_types = {'string', 'microinverter', 'power_optimizer', 'central'}
        if v.lower() not in valid_types:
            raise ValueError(f'Invalid inverter type: {v}')
        return v.lower()
    
    @validator('system_size_ac_kw')
    def validate_ac_size(cls, v, values):
        """Validate AC size vs DC size."""
        if v and 'system_size_dc_kw' in values:
            dc_size = values['system_size_dc_kw']
            if v > dc_size:
                raise ValueError('AC size cannot exceed DC size')
            if v < dc_size * 0.7:
                raise ValueError('AC size seems too low compared to DC size')
        return v


class ProductionMetrics(BaseModel):
    """Enhanced production metrics with validation."""
    annual_production_kwh: float = Field(..., gt=0)
    specific_yield: float = Field(..., gt=0, description="kWh/kWp")
    performance_ratio: float = Field(..., gt=0, le=1)
    kwh_per_kw: float = Field(..., gt=0)
    capacity_factor: float = Field(..., gt=0, le=1)
    first_year_degradation: float = Field(0.02, ge=0, le=0.1)
    annual_degradation: float = Field(0.005, ge=0, le=0.02)
    irradiance_kwh_m2: Optional[float] = Field(None, gt=0)
    shading_loss: Optional[float] = Field(None, ge=0, le=0.5)
    
    @validator('specific_yield')
    def validate_specific_yield(cls, v):
        """Validate reasonable specific yield values."""
        if v < 800 or v > 2500:
            raise ValueError('Specific yield outside reasonable range (800-2500 kWh/kWp)')
        return v


class PermitRequirement(BaseModel):
    """Enhanced permit requirement tracking."""
    permit_type: str
    description: str
    required: bool = True
    status: str = "pending"
    priority: str = "medium"
    estimated_timeline: str = "TBD"
    estimated_cost: float = Field(0, ge=0)
    complexity: str = "medium"
    authority: str = "TBD"
    requirements: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    
    @validator('status')
    def validate_status(cls, v):
        """Validate permit status."""
        valid_statuses = {
            'pending', 'in_progress', 'submitted', 'approved', 
            'rejected', 'not_required', 'on_hold'
        }
        if v.lower() not in valid_statuses:
            raise ValueError(f'Invalid permit status: {v}')
        return v.lower()


class PermitMatrix(BaseModel):
    """Enhanced permit matrix with comprehensive tracking."""
    jurisdiction_info: Dict[str, Any] = Field(default_factory=dict)
    permit_requirements: List[PermitRequirement] = Field(default_factory=list)
    total_estimated_cost: float = Field(0, ge=0)
    total_estimated_timeline: str = "TBD"
    risk_factors: List[str] = Field(default_factory=list)
    green_flags: List[str] = Field(default_factory=list)
    development_checklist: List[Dict[str, Any]] = Field(default_factory=list)
    critical_path: List[Dict[str, Any]] = Field(default_factory=list)


class InterconnectionScore(BaseModel):
    """Enhanced interconnection analysis."""
    score: int = Field(..., ge=0, le=100)
    utility_name: str
    substation_distance_miles: Optional[float] = Field(None, ge=0)
    available_capacity_mw: Optional[float] = Field(None, ge=0)
    queue_position: Optional[int] = Field(None, ge=1)
    estimated_timeline: str = "TBD"
    estimated_cost: float = Field(0, ge=0)
    risk_factors: List[str] = Field(default_factory=list)
    requirements: List[str] = Field(default_factory=list)
    study_required: bool = False


class ProForma(BaseModel):
    """Enhanced financial pro forma."""
    capex_total: float = Field(..., gt=0)
    capex_per_watt: float = Field(..., gt=0)
    itc_percentage: float = Field(..., ge=0, le=0.5)
    itc_amount: float = Field(..., ge=0)
    simple_payback_years: float = Field(..., gt=0)
    irr_band_low: float = Field(..., ge=0)
    irr_band_high: float = Field(..., ge=0)
    lcoe_cents_per_kwh: float = Field(..., gt=0)
    net_present_value: float
    debt_service_coverage_ratio: Optional[float] = Field(None, ge=0)
    cash_on_cash_return: Optional[float] = Field(None, ge=0)


class CapitalStackItem(BaseModel):
    """Enhanced capital stack item."""
    source_type: str = Field(..., description="Funding source type")
    source_name: str
    amount: float = Field(..., ge=0)
    percentage_of_total: float = Field(..., ge=0, le=1)
    terms: Optional[str] = None
    rate: Optional[float] = Field(None, ge=0)
    
    @validator('source_type')
    def validate_source_type(cls, v):
        """Validate funding source types."""
        valid_types = {
            'debt', 'equity', 'grant', 'tax_credit', 'bridge_loan',
            'mezzanine', 'revenue_based', 'lease'
        }
        if v.lower() not in valid_types:
            raise ValueError(f'Invalid source type: {v}')
        return v.lower()


class CapitalStack(BaseModel):
    """Enhanced capital stack with validation."""
    total_project_cost: float = Field(..., gt=0)
    items: List[CapitalStackItem] = Field(default_factory=list)
    climatize_loan_amount: Optional[float] = Field(None, ge=0)
    climatize_loan_terms: Optional[str] = None
    post_incentive_cost: Optional[float] = Field(None, ge=0)
    
    @root_validator
    def validate_percentages(cls, values):
        """Validate capital stack percentages sum to 100%."""
        items = values.get('items', [])
        if items:
            total_percentage = sum(item.percentage_of_total for item in items)
            if abs(total_percentage - 1.0) > 0.01:
                raise ValueError('Capital stack percentages must sum to 100%')
        return values


class Financials(BaseModel):
    """Enhanced financial model."""
    estimated_capex: Optional[float] = Field(None, gt=0)
    price_per_watt: Optional[float] = Field(None, gt=0, le=10)
    incentives: List[Dict[str, Any]] = Field(default_factory=list)
    capital_stack: Optional[CapitalStack] = None
    pro_forma: Optional[ProForma] = None
    
    @validator('price_per_watt')
    def validate_price_per_watt(cls, v):
        """Validate reasonable price per watt."""
        if v and (v < 0.5 or v > 6.0):
            raise ValueError('Price per watt outside reasonable range ($0.50-$6.00/W)')
        return v


class DevelopmentMilestone(BaseModel):
    """Enhanced development milestone tracking."""
    milestone_name: str
    status: str
    completion_percentage: int = Field(0, ge=0, le=100)
    completion_date: Optional[datetime] = None
    required_documents: List[str] = Field(default_factory=list)
    completed_documents: List[str] = Field(default_factory=list)
    blockers: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    alerts: List[Dict[str, Any]] = Field(default_factory=list)


class Milestones(BaseModel):
    """Enhanced milestone tracking with percentages."""
    site_control: str = "Not Started"
    permitting: str = "Not Started"
    interconnection: str = "Not Started"
    engineering: str = "Not Started"
    offtake: str = "Not Started"
    financing: str = "Not Started"
    detailed_milestones: List[DevelopmentMilestone] = Field(default_factory=list)
    overall_completion_percentage: int = Field(0, ge=0, le=100)


class SiteControlDocument(BaseModel):
    """Enhanced site control document tracking."""
    document_type: str = Field(..., description="Document type")
    status: str = Field(..., description="Document status")
    generated_date: datetime
    document_content: Optional[str] = None
    document_url: Optional[str] = None
    template_version: Optional[str] = None
    customizations: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('document_type')
    def validate_document_type(cls, v):
        """Validate document types."""
        valid_types = {'LOI', 'Lease', 'Purchase Agreement', 'Option Agreement'}
        if v not in valid_types:
            raise ValueError(f'Invalid document type: {v}')
        return v


class ProjectDocuments(BaseModel):
    """Enhanced project document management."""
    site_control: Optional[SiteControlDocument] = None
    permit_applications: List[Dict[str, Any]] = Field(default_factory=list)
    interconnection_application: Optional[Dict[str, Any]] = None
    pv_layout_pdf_url: Optional[str] = None
    financial_package_url: Optional[str] = None
    full_package_zip_url: Optional[str] = None
    engineering_drawings: List[str] = Field(default_factory=list)
    environmental_reports: List[str] = Field(default_factory=list)


class EligibilityScreening(BaseModel):
    """Project eligibility screening results."""
    eligible: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    incentive_score: int = Field(0, ge=0, le=100)
    interconnection_risk: str = "medium"
    permitting_risk: str = "medium"
    screening_date: datetime = Field(default_factory=datetime.now)


class UnifiedProjectModel(BaseModel):
    """Enhanced unified project model with comprehensive validation."""
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str = Field(..., min_length=3, max_length=200)
    data_source: str = Field(..., description="Data source origin")
    status: ProjectStatus = ProjectStatus.SCREENING
    created_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)
    
    # Core inputs
    address: Address
    system_specs: SystemSpecs
    
    # Screening results
    eligibility_screening: Optional[EligibilityScreening] = None
    
    # Generated outputs
    production_metrics: Optional[ProductionMetrics] = None
    permit_matrix: Optional[PermitMatrix] = None
    interconnection_score: Optional[InterconnectionScore] = None
    financials: Financials
    milestones: Milestones = Field(default_factory=Milestones)
    
    # Documents and packages
    project_documents: ProjectDocuments = Field(default_factory=ProjectDocuments)
    
    # Scoring and analysis
    fundability_score: int = Field(0, ge=0, le=100)
    fundability_factors: Dict[str, Any] = Field(default_factory=dict)
    readiness_score: int = Field(0, ge=0, le=100)
    
    # AI enhancements
    development_checklist: List[Dict[str, Any]] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    climatize_funding_options: List[Dict[str, Any]] = Field(default_factory=list)
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('data_source')
    def validate_data_source(cls, v):
        """Validate data sources."""
        valid_sources = {'Helioscope', 'Manual', 'Aurora', 'AI_Generated'}
        if v not in valid_sources:
            raise ValueError(f'Invalid data source: {v}')
        return v
    
    @root_validator
    def update_timestamp(cls, values):
        """Update timestamp on any change."""
        values['updated_date'] = datetime.now()
        return values


class FeasibilityPackage(BaseModel):
    """Enhanced feasibility package for AI MVP."""
    project_id: str
    generation_date: datetime = Field(default_factory=datetime.now)
    
    # Project overview
    project_overview: Dict[str, Any] = Field(default_factory=dict)
    
    # Site analysis
    site_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Permit analysis
    permit_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Interconnection analysis
    interconnection_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Financial analysis
    financial_analysis: Dict[str, Any] = Field(default_factory=dict)
    
    # Documents
    site_control_documents: Dict[str, Any] = Field(default_factory=dict)
    
    # Action items
    development_checklist: List[Dict[str, Any]] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    
    # Climatize value proposition
    climatize_funding_options: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Package metadata
    generation_method: str = "AI_Powered"
    processing_time_seconds: Optional[float] = None