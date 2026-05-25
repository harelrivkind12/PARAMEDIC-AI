from pydantic import BaseModel, Field, model_validator, ConfigDict
from typing import Literal

# --- Local Constants ---
from app.core.constants import (
    PEDIATRIC_AGE_THRESHOLD, 
    MAX_HR_PEDIATRIC, 
    MIN_SBP_PEDIATRIC
)

# --- Local Models ---
from .patient import Patient
from .vitals import Vitals, ClinicalFlag  

# --- Example Data for Swagger UI ---
from app.core.examples import INCIDENT_STATE_EXAMPLE 

class IncidentState(BaseModel):
    """
    Represents the current state of a trauma incident, including patient information, 
    vital signs, and any relevant medical conditions.
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
    
    # Additional fields
    incident_type: str | None = Field(
        default=None,
        description="Type of incident (e.g., MVA, fall, stab wound, crush, chest pain)."
    )
    time_since_incident: int | None = Field(
        default=None, ge=0, 
        description="Time in minutes since the incident occurred, important for prioritizing interventions."
    )
    free_text_notes: str | None = Field(
        default=None, 
        description="Any additional free-text notes or observations about the incident or patient condition."
    )

    vascular_access_established: Literal["IV", "IO", None] = Field(
        default=None, 
        description="Indicates whether vascular access has been established and the type of access (IV or IO)."
    )
    iv_attempts: int = Field(
        default=0, ge=0, 
        description="Number of attempts made to establish IV access."
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

    # ---------------------------------------------------------
    # AI PROMPT BUILDERS 
    # ---------------------------------------------------------

    def to_ai_summary(self) -> str:
        """
        Generates the prompt body sent to the AI.
        Each section is built by a dedicated private helper for testability.
        """
        summary = []
        
        summary.extend(self._build_patient_block())
        summary.extend(self._build_incident_block())
        summary.extend(self._build_treatments_history_block())
        summary.extend(self._build_vitals_block())
        
        alarms = self._build_actionable_alerts()
        if alarms:
            summary.append("\n=== [ACTIONABLE ALERTS] ===")
            summary.extend(alarms)
        else:
            summary.append("\n=== [ACTIONABLE ALERTS] ===")
            summary.append("No critical alerts detected.")
            
        if self.free_text_notes:
            summary.append("\n=== FIELD NOTES ===")
            summary.append(self.free_text_notes)

        return "\n".join(summary)

    # --- Private Helpers ---

    def _build_patient_block(self) -> list[str]:
        block = ["=== PATIENT ==="]
        age_str = f"{self.patient.age}y" if self.patient.age else "Unknown Age"
        gender_str = self.patient.gender or "Unknown Gender"
        weight_str = f"{self.patient.estimated_weight_kg}kg" if self.patient.estimated_weight_kg else "Unknown Weight"
        
        block.append(f"{age_str}, {gender_str}, {weight_str}")
        block.append(f"Allergies: {', '.join(self.patient.allergies) if self.patient.allergies else 'None known'}")
        block.append(f"History: {', '.join(self.patient.chronic_conditions) if self.patient.chronic_conditions else 'None known'}")
        return block

    def _build_incident_block(self) -> list[str]:
        block = ["\n=== SCENE & INCIDENT ==="]
        block.append(f"Type: {self.incident_type or 'Unknown'}")
        time_str = f"{self.time_since_incident} minutes ago" if self.time_since_incident is not None else "Unknown"
        block.append(f"Time since incident: {time_str}")
        return block

    def _build_treatments_history_block(self) -> list[str]:
        block = []
        if self.administered_treatments:
            block.append("\n=== ADMINISTERED TREATMENTS (HISTORY) ===")
            for treatment in self.administered_treatments:
                block.append(f"- {treatment}")
        return block

    def _build_vitals_block(self) -> list[str]:
        block = []
        # Baseline (if exists)
        if self.baseline_vitals:
            bv = self.baseline_vitals
            block.append("\n=== BASELINE VITALS (INITIAL) ===")
            block.append(f"HR: {bv.heart_rate or '-'} | BP: {bv.systolic_bp or '-'}/{bv.diastolic_bp or '-'} | SpO2: {bv.spo2 or '-'}% | RR: {bv.respiratory_rate or '-'} | GCS: {bv.gcs or '-'}")
        
        # Current
        v = self.current_vitals
        block.append("\n=== CURRENT VITALS ===")
        block.append(f"HR: {v.heart_rate or '-'} | BP: {v.systolic_bp or '-'}/{v.diastolic_bp or '-'} | SpO2: {v.spo2 or '-'}% | RR: {v.respiratory_rate or '-'} | GCS: {v.gcs or '-'}")
        if v.ecg_rhythm:
            block.append(f"ECG Rhythm: {v.ecg_rhythm}")
        block.append(f"Vascular Access: {self.vascular_access_established or 'None'} ({self.iv_attempts} attempts made)")
        return block

    def _build_actionable_alerts(self) -> list[str]:
        alerts = []
        if self.current_vitals.clinical_flags:
            for flag in self.current_vitals.clinical_flags:
                alerts.append(f"[{flag.severity.upper()}] {flag.system}: {flag.name}")
        return alerts
    
    # ---------------------------------------------------------
    # Swagger UI Configuration 
    # ---------------------------------------------------------
    model_config = ConfigDict(
        json_schema_extra={
            "example": INCIDENT_STATE_EXAMPLE
        }
    )