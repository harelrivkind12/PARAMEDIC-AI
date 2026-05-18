from pydantic import BaseModel, Field, model_validator
from typing import Optional
from enum import Enum

class GenderEnum(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"

class PatientStatus(BaseModel):
    """
    Represents the current status of a patient, including their name, age, and any relevant medical conditions.
    """
    gender: GenderEnum = Field(
        GenderEnum.UNKNOWN,
        description="Patient's biological sex"
    )
     
    # Identity fields
    name: str = Field(
        ..., 
        json_schema_extra={"example": "John"}
    )

    age: int = Field(
         ...,
         ge=0,
         description="Age of the patient in years"
         json_schema_extra={"example": 45}
    )

    #Medical history
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
        default_factory=list, # none of the conditions is the default, but we want to allow multiple selections
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
