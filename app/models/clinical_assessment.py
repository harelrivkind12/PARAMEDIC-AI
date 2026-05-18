from pydantic import BaseModel, Field
from typing import Literal

class ClinicalAssessment(BaseModel):
    """
    Represents a clinical assessment of a patient, including the Glasgow Coma Scale (GCS) score and the Richmond Agitation-Sedation Scale (RASS) score.
    """
    gcs_score: int = Field(..., ge=3, le=15, description="Glasgow Coma Scale score (3-15)")
    rass_score: int = Field(..., ge=-5, le=4, description="Richmond Agitation-Sedation Scale score (-5 to +4)")