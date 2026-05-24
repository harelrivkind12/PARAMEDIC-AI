from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Literal
from enum import Enum

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class Patient(BaseModel):
    """
    Represents the current status of a patient, including their name, age, and any relevant medical conditions.
    """
    gender: GenderEnum = Field(
        default=GenderEnum.UNKNOWN,
        description="Patient's biological sex"
    )
     
    # Identity fields
    name: str | None = Field(
        default=None, 
        json_schema_extra={"example": "John"}
    )

    age: int | None = Field(
         default=None,
         ge=0,
         description="Age of the patient in years",
         json_schema_extra={"example": 45}
    )

    # Physical status (Made optional so the validator can do its magic)
    estimated_weight_kg: float | None = Field(
        default=None,
        gt=0,
        description="Patient's estimated weight in kilograms, crucial for accurate medication dosing and fluid management.",
        json_schema_extra={"example": 70.5}
    )

    height_cm: float | None = Field(
        default=None,
        gt=0,
        description="Patient's height in centimeters, used for calculating body surface area and other clinical assessments.",
        json_schema_extra={"example": 175.0}
    )

    # Medical history
    chronic_conditions: List[Literal[
        "Heart Failure (CHF)",          
        "Chronic Kidney Disease (CKD)", 
        "Past MI (History of Heart Attack)", 
        "Ischemic Heart Disease (IHD)", 
        "Hypertension",                 
        "Diabetes Mellitus",            
        "COPD / Asthma",                
        "CVA / TIA",
        "Active Cancer",               
        "None",                         
        "Other"                         
    ]] = Field(
        default_factory=list,
        description="A list of the patient's known core chronic illnesses. Crucial for determining drug contraindications and fluid management.",
        json_schema_extra={"example": ["Heart Failure (CHF)", "Diabetes Mellitus"]}
    )

    allergies: List[Literal[
        "NKDA (No Known Drug Allergies)", 
        "Penicillin",                   
        "Sulfa Drugs",                   
        "NSAIDs / Aspirin",              
        "Latex",                         
        "Iodine / Contrast Media",       
        "Other"                          
    ]] = Field(
        default_factory=list,
        description="High-alert allergies that impact immediate pre-hospital treatment.",
        json_schema_extra={"example": ["Penicillin"]}
    )
     
    regular_medications: List[Literal[
        "Anticoagulants / Blood Thinners (e.g., Eliquis, Coumadin, Xarelto, Plavix)", 
        "Beta-Blockers (e.g., Proton, Normalol)",                                     
        "Insulin / Oral Hypoglycemics",                                               
        "Anticonvulsants (e.g., Valproic Acid, Tegretol)",                           
        "Antihypertensives",                                                          
        "None",
        "Other"
    ]] = Field(
        default_factory=list,
        description="Core medication classes that alter physiological responses or treatment protocols.",
        json_schema_extra={"example": ["Anticoagulants / Blood Thinners (e.g., Eliquis, Coumadin, Xarelto, Plavix)"]}
    )

    @model_validator(mode='after')
    def estimate_missing_weight(self) -> 'Patient':
        """
        Auto-calculates estimated weight if missing, using APLS formulas for pediatrics
        or height-based estimation for adults.
        """
        # If the weight was already entered manually by the paramedic, no need to estimate
        if self.estimated_weight_kg is not None:
            return self
            
        # 1. Estimation by age (focus on pediatrics - critical for medication dosages)
        if self.age is not None:
            if self.age < 1:
                self.estimated_weight_kg = 5.0  # Average infant
            elif self.age <= 5:
                self.estimated_weight_kg = (self.age * 2) + 8.0  # APLS formula for ages 1-5
            elif self.age <= 12:
                self.estimated_weight_kg = (self.age * 3) + 7.0  # APLS formula for ages 6-12
            elif self.age < 18:
                self.estimated_weight_kg = 50.0  # Adolescent / Teenager
            else:
                # If adult and height is unknown, assume 70 kg as a medical default
                self.estimated_weight_kg = 70.0 if not self.height_cm else None

        # 2. Estimation by height (if age is unknown or for an adult with known height)
        if self.estimated_weight_kg is None and self.height_cm is not None:
            # Assume a normal average BMI of 22
            # Formula: Weight = BMI * (height in meters squared)
            height_m = self.height_cm / 100.0
            self.estimated_weight_kg = round(22.0 * (height_m ** 2), 1)

        # 3. If no age, height, or weight - assume 70 kg for safety (standard adult dose)
        if self.estimated_weight_kg is None:
            self.estimated_weight_kg = 70.0

        return self