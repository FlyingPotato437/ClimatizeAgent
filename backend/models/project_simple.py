"""
Simplified project data models for getting the backend running.
"""
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from enum import Enum


class RoofType(str, Enum):
    """Roof installation types."""
    FLAT = "flat"
    PITCHED = "pitched"
    GROUND_MOUNT = "ground_mount"


class ProjectStatus(str, Enum):
    """Overall project status."""
    SCREENING = "screening"
    DEVELOPMENT = "development"
    PERMITTING = "permitting"
    CONSTRUCTION = "construction"
    OPERATIONAL = "operational"
    CANCELLED = "cancelled"


class Address(BaseModel):
    """Simplified address model."""
    street: str
    city: str
    state: str
    zip_code: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    parcel_id: Optional[str] = None
    county: Optional[str] = None


class BatterySpecs(BaseModel):
    """Simplified battery specifications."""
    power_kw: float
    energy_kwh: float
    duration_hours: float
    purpose: str = "peak_shaving"
    estimated_cost: Optional[float] = None


class SystemSpecs(BaseModel):
    """Simplified system specifications."""
    system_size_dc_kw: float
    system_size_ac_kw: Optional[float] = None
    module_count: int
    inverter_type: str
    roof_type: RoofType
    annual_kwh_load: Optional[float] = None
    battery_specs: Optional[BatterySpecs] = None


class ProductionMetrics(BaseModel):
    """Simplified production metrics."""
    annual_production_kwh: float
    specific_yield: float
    performance_ratio: float
    kwh_per_kw: float
    capacity_factor: float


class PermitMatrix(BaseModel):
    """Simplified permit matrix."""
    jurisdiction_info: Dict[str, Any] = Field(default_factory=dict)
    permit_requirements: List[Dict[str, Any]] = Field(default_factory=list)
    total_estimated_cost: float = 0
    total_estimated_timeline: str = "TBD"


class InterconnectionScore(BaseModel):
    """Simplified interconnection analysis."""
    score: int
    utility_name: str
    substation_distance_miles: Optional[float] = None
    available_capacity_mw: Optional[float] = None
    estimated_timeline: str = "TBD"
    estimated_cost: float = 0


class ProForma(BaseModel):
    """Simplified financial pro forma."""
    capex_total: float
    capex_per_watt: float
    itc_percentage: float
    itc_amount: float
    simple_payback_years: float
    irr_band_low: float
    irr_band_high: float
    lcoe_cents_per_kwh: float
    net_present_value: float


class Financials(BaseModel):
    """Simplified financial model."""
    estimated_capex: Optional[float] = None
    price_per_watt: Optional[float] = None
    incentives: List[Dict[str, Any]] = Field(default_factory=list)
    pro_forma: Optional[ProForma] = None


class Milestones(BaseModel):
    """Simplified milestone tracking."""
    site_control: str = "Not Started"
    permitting: str = "Not Started"
    interconnection: str = "Not Started"
    engineering: str = "Not Started"
    offtake: str = "Not Started"
    financing: str = "Not Started"
    overall_completion_percentage: int = 0


class ProjectDocuments(BaseModel):
    """Simplified project document management."""
    pv_layout_pdf_url: Optional[str] = None
    financial_package_url: Optional[str] = None
    full_package_zip_url: Optional[str] = None


class EligibilityScreening(BaseModel):
    """Project eligibility screening results."""
    eligible: bool
    rejection_reasons: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    incentive_score: int = 0
    screening_date: datetime = Field(default_factory=datetime.now)


class UnifiedProjectModel(BaseModel):
    """Simplified unified project model."""
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str
    data_source: str
    status: ProjectStatus = ProjectStatus.SCREENING
    created_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)
    
    # Core inputs
    address: Address
    system_specs: SystemSpecs
    
    # Optional components  
    eligibility_screening: Optional[EligibilityScreening] = None
    production_metrics: Optional[ProductionMetrics] = None
    permit_matrix: Optional[PermitMatrix] = None
    interconnection_score: Optional[InterconnectionScore] = None
    financials: Optional[Financials] = None
    milestones: Milestones = Field(default_factory=Milestones)
    project_documents: ProjectDocuments = Field(default_factory=ProjectDocuments)
    
    # Scoring
    fundability_score: int = 0
    readiness_score: int = 0
    
    # AI enhancements
    development_checklist: List[Dict[str, Any]] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)


class FeasibilityPackage(BaseModel):
    """Simplified feasibility package."""
    project_id: str
    generation_date: datetime = Field(default_factory=datetime.now)
    project_overview: Dict[str, Any] = Field(default_factory=dict)
    site_analysis: Dict[str, Any] = Field(default_factory=dict)
    permit_analysis: Dict[str, Any] = Field(default_factory=dict)
    interconnection_analysis: Dict[str, Any] = Field(default_factory=dict)
    financial_analysis: Dict[str, Any] = Field(default_factory=dict)
    development_checklist: List[Dict[str, Any]] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
    generation_method: str = "AI_Powered"
    processing_time_seconds: Optional[float] = None 