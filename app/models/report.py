import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from .api_schemas import IncidentState
from .clinical_assessment import ClinicalAssessment

class GPSLocation(BaseModel):
    """
    Represents geographic coordinates for tactical coordination and evacuation tracking.
    """
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees.")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees.")


class FieldReport(BaseModel):
    """
    The root envelope model that fuses operational metadata, the original ground truth 
    incident state, and the resulting AI clinical assessment into a single record.
    """
    report_id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        description="Unique system-wide identifier generated automatically for this report instance."
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="The exact UTC timestamp when this report envelope was initialized."
    )
    provider_id: str | None = Field(
        None,
        description="Unique identity or license number of the treating medical provider."
    )
    team_callsign: str | None = Field(
        None,
        description="Operational callsign of the responding unit or maneuvering force."
    )
    gps_location: GPSLocation | None = Field(
        None,
        description="Real-time coordinates used for dispatching secondary backup or vectoring evacuation assets."
    )
    evacuation_destination: str | None = Field(
        None,
        description="The designated casualty collection point (CCP) or trauma center hospital destination."
    )
    incident_state: IncidentState = Field(
        ...,
        description="The full input baseline clinical data, patient info, and vital signs captured from the scene."
    )
    ai_assessment: ClinicalAssessment | None = Field(
        None,
        description="The structured triage decision matrix and validated medication outputs returned by the AI engine."
    )