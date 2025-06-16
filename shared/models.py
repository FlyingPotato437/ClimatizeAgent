from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime
from enum import Enum

class RoofType(str, Enum):
    FLAT = "flat"
    PITCHED = "pitched"
    GROUND_MOUNT = "ground_mount"

class InterconnectionStatus(str, Enum):
    NOT_STARTED = "Not Started"
    APPLICATION_DRAFTED = "Application Drafted"
    SUBMITTED = "Submitted"
    APPROVED = "Approved"
    REJECTED = "Rejected"

class Address(BaseModel):
    street: str
    city: str
    state: str
    zip_code: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    parcel_id: Optional[str] = None

class BillOfMaterialItem(BaseModel):
    component_type: str = Field(..., description="e.g., 'module', 'inverter', 'racking', 'battery'")
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    quantity: int
    unit_cost: Optional[float] = None

class BatterySpecs(BaseModel):
    power_kw: float
    energy_kwh: float
    duration_hours: float
    purpose: str = "peak_shaving"
    estimated_cost: Optional[float] = None

class SystemSpecs(BaseModel):
    system_size_dc_kw: float
    system_size_ac_kw: Optional[float] = None
    module_count: int
    inverter_type: str = Field(..., description="'string' or 'microinverter'")
    roof_type: RoofType
    annual_kwh_load: Optional[float] = None
    bill_of_materials: List[BillOfMaterialItem]
    battery_specs: Optional[BatterySpecs] = None

class ProductionMetrics(BaseModel):
    annual_production_kwh: float
    specific_yield: float  # kWh/kWp
    performance_ratio: float
    kwh_per_kw: float
    capacity_factor: float
    first_year_degradation: float = 0.02
    annual_degradation: float = 0.005

class PermitRequirement(BaseModel):
    permit_type: str
    description: str
    required: bool
    status: str = "pending"  # pending, approved, rejected, not_required
    flag_color: str = "yellow"  # red, yellow, green
    estimated_timeline_days: Optional[int] = None
    notes: Optional[str] = None

class PermitMatrix(BaseModel):
    jurisdiction_name: str
    jurisdiction_type: str
    solar_friendly_rating: int  # 1-10
    average_approval_time: str
    requirements: List[PermitRequirement]
    red_flags: List[str] = []
    green_flags: List[str] = []
    total_estimated_days: Optional[int] = None

class InterconnectionScore(BaseModel):
    score: int  # 0-100
    utility_name: str
    substation_distance_miles: Optional[float] = None
    available_capacity_mw: Optional[float] = None
    queue_position: Optional[int] = None
    estimated_timeline: str
    risk_factors: List[str] = []

class ProForma(BaseModel):
    capex_total: float
    capex_per_watt: float
    itc_percentage: float
    itc_amount: float
    simple_payback_years: float
    irr_band_low: float
    irr_band_high: float
    lcoe_cents_per_kwh: float
    net_present_value: float

class CapitalStackItem(BaseModel):
    source_type: str  # "debt", "equity", "grant", "tax_credit"
    source_name: str
    amount: float
    percentage_of_total: float
    terms: Optional[str] = None
    rate: Optional[float] = None

class CapitalStack(BaseModel):
    total_project_cost: float
    items: List[CapitalStackItem]
    climatize_loan_amount: Optional[float] = None
    climatize_loan_terms: Optional[str] = None

class Financials(BaseModel):
    estimated_capex: Optional[float] = None
    price_per_watt: Optional[float] = None
    incentives: List[dict] = []
    capital_stack: Optional[CapitalStack] = None
    pro_forma: Optional[ProForma] = None

class DevelopmentMilestone(BaseModel):
    milestone_name: str
    status: str
    completion_date: Optional[datetime] = None
    required_documents: List[str] = []
    completed_documents: List[str] = []
    blockers: List[str] = []

class Milestones(BaseModel):
    site_control: str = "Not Started"  # Not Started, LOI Drafted, Lease Drafted, Signed
    permitting: str = "Not Started"  # Not Started, Matrix Generated, Applications Drafted, Submitted, Approved
    interconnection: str = "Not Started"  # Not Started, Application Drafted, Submitted, Approved
    engineering: str = "Not Started"  # Not Started, Conceptual, Detailed, Stamped
    offtake: str = "Not Started"  # Not Started, PPA Drafted, Negotiating, Signed
    financing: str = "Not Started"  # Not Started, Package Prepared, In Diligence, Committed
    detailed_milestones: List[DevelopmentMilestone] = []

class SiteControlDocument(BaseModel):
    document_type: str  # "LOI", "Lease", "Purchase Agreement"
    status: str  # "Draft", "Sent", "Negotiating", "Signed"
    generated_date: datetime
    document_content: Optional[str] = None
    document_url: Optional[str] = None

class ProjectDocuments(BaseModel):
    site_control: Optional[SiteControlDocument] = None
    permit_applications: List[Dict[str, Any]] = []
    interconnection_application: Optional[Dict[str, Any]] = None
    pv_layout_pdf_url: Optional[str] = None
    financial_package_url: Optional[str] = None
    full_package_zip_url: Optional[str] = None

class UnifiedProjectModel(BaseModel):
    project_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_name: str
    data_source: str  # 'Aurora', 'Manual', 'HelioScope'
    created_date: datetime = Field(default_factory=datetime.now)
    updated_date: datetime = Field(default_factory=datetime.now)
    
    # Core inputs
    address: Address
    system_specs: SystemSpecs
    
    # Generated outputs
    production_metrics: Optional[ProductionMetrics] = None
    permit_matrix: Optional[PermitMatrix] = None
    interconnection_score: Optional[InterconnectionScore] = None
    financials: Financials
    milestones: Milestones = Field(default_factory=Milestones)
    
    # Documents and packages
    project_documents: ProjectDocuments = Field(default_factory=ProjectDocuments)
    
    # Scoring
    fundability_score: int = 0
    fundability_factors: Dict[str, Any] = {}
    readiness_score: int = 0
    
    # Next steps
    next_steps: List[str] = []
    climatize_funding_options: List[Dict[str, Any]] = []

class FeasibilityPackage(BaseModel):
    """Output format for the Quick-Look Feasibility Pack v0"""
    project_id: str
    generation_date: datetime
    
    # Inputs echo
    site_address: str
    coordinates: Optional[Dict[str, float]] = None
    roof_type: str
    annual_kwh_load: Optional[float] = None
    
    # PV Design Outputs
    pv_layout_image_url: Optional[str] = None
    system_size_dc_kw: float
    system_size_ac_kw: float
    
    # Production Outputs
    annual_production_kwh: float
    specific_yield: float
    performance_ratio: float
    
    # Battery Sizing
    battery_recommendation: Optional[BatterySpecs] = None
    
    # Interconnection
    interconnection_score: int
    interconnection_notes: str
    
    # Permitting
    permit_checklist: List[Dict[str, Any]]
    red_flags: List[str]
    green_flags: List[str]
    
    # Financials
    pro_forma_summary: ProForma
    
    # Next Steps
    next_steps: List[str]
    climatize_funding_cta: str