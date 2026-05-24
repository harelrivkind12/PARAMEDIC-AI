from pydantic import BaseModel, Field, model_validator
from typing import Literal
from app.core.constants import (
    PEDIATRIC_AGE_THRESHOLD, 
    MAX_HR_PEDIATRIC, 
    MIN_SBP_PEDIATRIC
)
from .patient import Patient
from .vitals import Vitals, ClinicalFlag  
# from .report import FieldReport  # נשתמש בו בהמשך אם נרצה לעטוף הכל

class IncidentState(BaseModel):
    """
    Represents the current state of a trauma incident, including patient information, vital signs, and any relevant medical conditions.
    """
    patient: Patient = Field(
        ...,
        description="Detailed information about the patient involved in the trauma incident."
    )

    current_vitals: Vitals = Field(
        ...,
        description="Current vital signs of the patient, crucial for assessing their condition and guiding treatment decisions."
    )

    baseline_vitals: Vitals | None = Field(
        default=None,
        description="Initial vital signs recorded upon first patient contact (optional)."
    )
    
    administered_treatments: list[str] = Field(
        default_factory=list,
        description="Chronological list of treatments already administered (e.g., 'Ketamine 50mg IV at 14:05')."
    )
    
    # Additional fields can be added here as needed, such as:
    incident_type: str | None = Field(
        None,
        description="Type of incident (e.g., MVA, fall, stab wound, crush, chest pain)."
    )
    time_since_incident: int | None = Field(
        None, ge=0, 
        description="Time in minutes since the incident occurred, important for prioritizing interventions and understanding the patient's condition."
    )
    free_text_notes: str | None = Field(
        None, 
        description="Any additional free-text notes or observations about the incident or patient condition that may be relevant for analysis and decision-making."
    )

    vascular_access_established: Literal["IV", "IO", None] = Field(
        default=None, 
        description="Indicates whether vascular access has been established and the type of access (IV or IO)."
    )
    iv_attempts: int = Field(
        default=0, ge=0, 
        description="Number of attempts made to establish IV access, important for understanding the patient's vascular status and potential delays in treatment."
    )

    @model_validator(mode='after')
    def validate_incident_context(self) -> 'IncidentState':
        """
        Cross-references patient demographics (like age) with current vitals and 
        scene protocols (like IV attempts) to refine clinical alerts.
        """
        age = self.patient.age
        vitals = self.current_vitals
        
        # 1. Age-Specific Validation (Pediatric vs. Adult)
        if age is not None and age < PEDIATRIC_AGE_THRESHOLD:
            # Remove false-positive adult tachycardia alerts for pediatric patients
            if vitals.heart_rate is not None and vitals.heart_rate <= MAX_HR_PEDIATRIC:
                vitals.clinical_flags = [
                    flag for flag in vitals.clinical_flags 
                    if flag.name != "Tachycardia"
                ]
            
            # Add pediatric-specific decompensated shock alert if BP is below formula threshold
            if vitals.systolic_bp is not None and vitals.systolic_bp < MIN_SBP_PEDIATRIC:
                if not any("Pediatric Hypotension" in f.name for f in vitals.clinical_flags):
                    vitals.clinical_flags.append(ClinicalFlag(
                        name="Pediatric Hypotension (Decompensated Shock)",
                        severity="Critical",
                        system="Cardiovascular"
                    ))

        # 2. Vascular Access Protocol (ALS Rule)
        # If there is no venous access but there have been 2 or more attempts - a protocol alert is raised.
        if self.vascular_access_established is None and self.iv_attempts >= 2:
            vitals.clinical_flags.append(ClinicalFlag(
                name="IV FAILURE PROTOCOL: 2 failed peripheral attempts. Establish IO immediately.",
                severity="High",
                system="General"
            ))

        return self

    def to_ai_summary(self) -> str:
        """
        Converts the entire complex JSON structure into a clean, human-readable 
        clinical handover format to serve as the definitive prompt for the AI engine.
        """
        summary = []
        
        # Patient Block
        summary.append("=== PATIENT ===")
        age_str = f"{self.patient.age}y" if self.patient.age else "Unknown Age"
        gender_str = self.patient.gender or "Unknown Gender"
        weight_str = f"{self.patient.estimated_weight_kg}kg" if self.patient.estimated_weight_kg else "Unknown Weight"
        summary.append(f"{age_str}, {gender_str}, {weight_str}")
        summary.append(f"Allergies: {', '.join(self.patient.allergies) if self.patient.allergies else 'None known'}")
        summary.append(f"History: {', '.join(self.patient.chronic_conditions) if self.patient.chronic_conditions else 'None known'}")
        
        # Incident Block
        summary.append("\n=== SCENE & INCIDENT ===")
        summary.append(f"Type: {self.incident_type or 'Unknown'}")
        time_str = f"{self.time_since_incident} minutes ago" if self.time_since_incident is not None else "Unknown"
        summary.append(f"Time since incident: {time_str}")
        
        # Vitals & Exam Block
        v = self.current_vitals
        summary.append("\n=== CURRENT VITALS ===")
        summary.append(f"HR: {v.heart_rate or '-'} | BP: {v.systolic_bp or '-'}/{v.diastolic_bp or '-'} | SpO2: {v.spo2 or '-'}% | RR: {v.respiratory_rate or '-'} | GCS: {v.gcs or '-'}")
        if v.ecg_rhythm:
            summary.append(f"ECG Rhythm: {v.ecg_rhythm}")
        summary.append(f"Vascular Access: {self.vascular_access_established or 'None'} ({self.iv_attempts} attempts made)")
        
        # Actionable Alerts Block (The core of the logic)
        summary.append("\n=== [ACTIONABLE ALERTS] ===")
        if v.clinical_flags:
            for flag in v.clinical_flags:
                summary.append(f"[{flag.severity.upper()}] {flag.system}: {flag.name}")
        else:
            summary.append("No critical alerts detected.")
            
        # Free Text Notes
        if self.free_text_notes:
            summary.append("\n=== FIELD NOTES ===")
            summary.append(self.free_text_notes)
            
        return "\n".join(summary)