import json
from pathlib import Path
from typing import Any
from pydantic import BaseModel, Field, model_validator, ValidationInfo

# Ensure the JSON file is actually located in the 'protocols' directory!
GUIDELINES_PATH = Path(__file__).parent.parent / "protocols" / "guidelines.json"

def load_protocol_rules() -> dict[str, Any]:
    """Loads the single source of truth guidelines JSON file."""
    if not GUIDELINES_PATH.exists():
        raise FileNotFoundError(f"Critical configuration missing: {GUIDELINES_PATH} not found.")
    with open(GUIDELINES_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("medication_rules", {})

class MedicationCommand(BaseModel):
    """
    Represents a validated medication administration command, 
    cross-referenced against clinical protocols and patient context.
    """
    name: str = Field(
        ...,
        description="The exact name of the medication from the approved formulary."
    )
    dose: float = Field(
        ...,
        gt=0,
        description="The numerical dose to be administered."
    )
    unit: str = Field(
        ...,
        description="Unit of measurement (e.g., mg, mcg, g, mEq, units)."
    )
    route: str = Field(
        ...,
        description="Route of administration (e.g., IV, IO, IM, IN, PO, SL, INH)."
    )
    special_instructions: str | None = Field(
        None,
        description="Specific deployment directives like push rates or dilutions."
    )

    @model_validator(mode='after')
    def validate_pharmacology_limits(self, info: ValidationInfo) -> 'MedicationCommand':
        """
        Executes real-time safety guardrails. Cross-references the drug parameters
        against guidelines.json and the provided runtime patient context.
        """
        # 1. Load the strict rulebook from the JSON
        rules = load_protocol_rules()
        
        if self.name not in rules:
            raise ValueError(
                f"CRITICAL ERROR: '{self.name}' is not an approved protocol medication."
            )
            
        drug_rules = rules[self.name]
        
        # 2. Validate route of administration and measurement units
        if self.route not in drug_rules["allowed_routes"]:
            raise ValueError(
                f"PROHIBITED ROUTE: {self.name} cannot be given via '{self.route}'. "
                f"Allowed routes: {drug_rules['allowed_routes']}"
            )
            
        if self.unit not in drug_rules["allowed_units"]:
            raise ValueError(
                f"INVALID UNIT: '{self.unit}' is incorrect for {self.name}. "
                f"Allowed units: {drug_rules['allowed_units']}"
            )

        # 3. Extract patient context (if injected during validation)
        context = info.context or {}
        patient_age = context.get("patient_age")
        patient_weight = context.get("patient_weight_kg")
        active_flags = context.get("active_clinical_flags", [])

        # 4. Enforce contraindications based on clinical flags
        for flag in drug_rules.get("contraindications_flags", []):
            if flag in active_flags:
                raise ValueError(
                    f"CONTRAINDICATION TRIGGERED: Cannot administer {self.name} "
                    f"due to active clinical condition: '{flag}'."
                )

        # 5. Validate upper dosage limit with strict pediatric rules
        max_allowed_dose = drug_rules["max_single_dose"]
        
        # Execute pediatric specific hard boundaries if patient is under 18
        if patient_age is not None and patient_age < 18:
            # Check pediatric approval flag
            if not drug_rules.get("is_pediatric_approved", False):
                raise ValueError(
                    f"PROHIBITED MEDICATION: {self.name} is strictly contraindicated for pediatric patients."
                )
            
            # Calculate strict weight-based absolute ceiling if weight parameters are available
            if patient_weight is not None and "max_dose_per_kg" in drug_rules:
                calculated_peds_max = drug_rules["max_dose_per_kg"] * patient_weight
                # The ceiling is either the calculated peds max or the absolute adult max (whichever is lower)
                max_allowed_dose = min(max_allowed_dose, calculated_peds_max)

        # Final check against the resolved threshold
        if self.dose > max_allowed_dose:
            raise ValueError(
                f"DOSAGE OVERLOAD: {self.dose} {self.unit} exceeds the maximum safe single dose "
                f"limit of {max_allowed_dose} {self.unit} for this patient context."
            )

        return self