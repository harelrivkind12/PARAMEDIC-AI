from pydantic import BaseModel, Field, model_validator
from typing import Literal
from app.core.constants import SHOCK_INDEX_CRITICAL_THRESHOLD, CRITICAL_GCS_THRESHOLD

class ClinicalFlag(BaseModel):
    """
     Represents a clinical alert or flag generated based on the patient's vital signs, indicating potential abnormalities or critical conditions.
    """
    name: str = Field(
        ..., 
        description="The name of the clinical flag (e.g., 'Tachycardia', 'Hypoxia', 'Critical Shock')"
    )
    severity: Literal["Warning", "High", "Critical"] = Field(
        ..., 
        description="Severity level of the abnormality for triage prioritization"
    )
    system: Literal["Cardiovascular", "Respiratory", "Neurological", "General"] = Field(
        ..., 
        description="The physiological system associated with this flag"
    )


class Vitals(BaseModel):
    """
    Model representing the physiological vital signs of the patient and analyzing clinical abnormalities in real-time.
    """
    heart_rate: int | None = Field(default=None, ge=0, description="Heart rate in beats per minute")
    systolic_bp: int | None = Field(default=None, ge=0, description="Systolic blood pressure in mmHg")
    diastolic_bp: int | None = Field(default=None, ge=0, description="Diastolic blood pressure in mmHg")
    spo2: int | None = Field(default=None, ge=0, le=100, description="Oxygen saturation percentage")
    respiratory_rate: int | None = Field(default=None, ge=0, description="Respiratory rate in breaths per minute")
    gcs: int | None = Field(default=None, ge=3, le=15, description="Glasgow Coma Scale score")
    ecg_rhythm: Literal["NSR", "SB", "ST", "AFib", "VFib", "Asystole", "PEA", "VTach"] | None = Field(
        default="NSR", description="ECG rhythm classification")
    temperature: float | None = Field(default=None, ge=30.0, le=45.0, description="Body temperature in Celsius")
    skin_perfusion: Literal["Normal", "Pale", "Cyanotic", "Mottled"] | None = Field(
        default="Normal", description="Skin perfusion status based on clinical assessment")
    skin_moisture: Literal["Dry", "Normal", "Diaphoretic"] | None = Field(
        default="Normal", description="Skin moisture status based on clinical assessment")
    capillary_refill_delay: bool | None = Field(default=False, description="Capillary refill delay (True if >2 seconds)")
    pupils: Literal["Normal", "Pinpoint", "Dilated", "Unequal"] | None = Field(
        default="Normal", description="Pupil response status based on clinical assessment")
    

    # Computed fields
    shock_index: float | None = Field(default=None, ge=0.0, description="Computed Shock Index (HR / SBP)")
    clinical_flags: list[ClinicalFlag] = Field(default_factory=list, description="Automatically generated clinical alerts")

    @model_validator(mode='after')
    def evaluate_clinical_state(self) -> 'Vitals':
        """
        Runs physiological threshold checks and updates the list of clinical flags and computed metrics.
        """
        # Reset the list on each validation run to prevent flag duplication
        self.clinical_flags = []
        
        # 1. Calculation of Shock Index
        if self.heart_rate is not None and self.systolic_bp is not None and self.systolic_bp > 0:
            self.shock_index = round(self.heart_rate / self.systolic_bp, 2)
            if self.shock_index >= SHOCK_INDEX_CRITICAL_THRESHOLD:
                self.clinical_flags.append(ClinicalFlag(
                    name="Critical Shock Index",
                    severity="Critical",
                    system="Cardiovascular"
                ))

        # 2. Evaluation of Heart Rate and Critical Arrhythmias
        if self.systolic_bp is not None and self.systolic_bp >= 90:
            if self.skin_perfusion == "Pale" and self.skin_moisture == "Diaphoretic":
                self.clinical_flags.append(ClinicalFlag(
                    name="Compensated Shock (Pale & Diaphoretic with Normal BP)",
                    severity="High",
                    system="Cardiovascular"
                ))
            elif self.capillary_refill_delay and self.heart_rate and self.heart_rate > 100:
                self.clinical_flags.append(ClinicalFlag(
                    name="Poor Perfusion (Delayed Cap Refill + Tachycardia)",
                    severity="High",
                    system="Cardiovascular"
                ))
        elif self.systolic_bp is not None and self.systolic_bp < 90:
            if not any(f.name == "Critical Shock Index" for f in self.clinical_flags):
                self.clinical_flags.append(ClinicalFlag(
                    name="Hypotension (Decompensated)",
                    severity="High",
                    system="Cardiovascular"
                ))

        # 3. Evaluation of Blood Pressure
        if self.ecg_rhythm in ["VFib", "Asystole", "PEA"]:
            self.clinical_flags.append(ClinicalFlag(
                name=f"CARDIAC ARREST ({self.ecg_rhythm})",
                severity="Critical",
                system="Cardiovascular"
            ))
        elif self.heart_rate is not None:
            if self.heart_rate > 100:
                # Only flag tachycardia if not already flagged for shock, to avoid redundant flags in the same system. If shock is present, tachycardia is already implied and doesn't need a separate flag.
                if not any("Shock" in f.name for f in self.clinical_flags):
                    self.clinical_flags.append(ClinicalFlag(
                        name="Tachycardia",
                        severity="High" if self.heart_rate > 130 else "Warning",
                        system="Cardiovascular"
                    ))
            elif self.heart_rate < 50:
                self.clinical_flags.append(ClinicalFlag(
                    name="Bradycardia",
                    severity="High" if self.heart_rate < 40 else "Warning",
                    system="Cardiovascular"
                ))

        # 4. Evaluation of Respiratory System (Oxygen Saturation and Respiratory Rate)
        if self.skin_perfusion == "Cyanotic":
            self.clinical_flags.append(ClinicalFlag(
                name="Cyanosis (Severe Hypoxia / Hypoperfusion)",
                severity="Critical",
                system="Respiratory"
            ))
        elif self.spo2 is not None and self.spo2 < 94:
            self.clinical_flags.append(ClinicalFlag(
                name="Hypoxia",
                severity="Critical" if self.spo2 < 88 else "High",
                system="Respiratory"
            ))
        
        if self.respiratory_rate is not None:
            if self.respiratory_rate > 24 or self.respiratory_rate < 8:
                self.clinical_flags.append(ClinicalFlag(
                    name="Abnormal Respiratory Rate",
                    severity="High",
                    system="Respiratory"
                ))

        # 5. Evaluation of Neurological Status (GCS)
        if self.gcs is not None:
            if self.gcs <= CRITICAL_GCS_THRESHOLD:
                self.clinical_flags.append(ClinicalFlag(
                    name="Severe Neurological Impairment (Low GCS)",
                    severity="Critical",
                    system="Neurological"
                ))
            
            # Special consideration for pinpoint pupils + low GCS, which is a classic sign of opioid toxicity, especially if accompanied by hypoventilation
            if self.pupils == "Pinpoint" and self.gcs < 15:
                if self.respiratory_rate is not None and self.respiratory_rate < 10:
                    self.clinical_flags.append(ClinicalFlag(
                        name="Suspected Opioid Toxicity (Pinpoint Pupils + Low GCS + Hypoventilation)",
                        severity="Critical",
                        system="Neurological"
                    ))
                    
        # 6. Evaluation of Temperature Abnormalities
        if self.temperature is not None:
            if self.temperature > 38.5:
                self.clinical_flags.append(ClinicalFlag(
                    name="Fever",
                    severity="Warning",
                    system="General"
                ))
            elif self.temperature < 35.0:
                self.clinical_flags.append(ClinicalFlag(
                    name="Hypothermia",
                    severity="High" if self.temperature < 32.0 else "Warning",
                    system="General"
                )) 
                
        return self