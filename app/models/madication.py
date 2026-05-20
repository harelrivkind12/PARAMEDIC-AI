import json
from pathlib import Path
from typing import Any, Literal
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
        # Cross-reference active patient flags with the medication's prohibited flags in the JSON
        for flag in drug_rules.get("contraindications_flags", []):
            if flag in active_flags:
                raise ValueError(
                    f"CONTRAINDICATION TRIGGERED: Cannot administer {self.name} "
                    f"due to active clinical condition: '{flag}'."
                )

        # 5. Validate upper dosage limit (prevent lethal adult doses in pediatric patients)
        max_allowed_dose = drug_rules["max_single_dose"]
        
        # Calculate specific pediatric adjustment if the patient is a child (< 18) and weight is available
        if patient_age is not None and patient_age < 18 and patient_weight is not None:
            # Example pediatric rule of thumb: limit max dose relative to weight for specific ALS drugs
            # (If needed, the JSON can be expanded to hold a dedicated 'mg_per_kg_max' field)
            if self.name in ["Fentanyl", "Ketamine", "Midazolam"]:
                calculated_peds_max = max_allowed_dose * (patient_weight / 70.0)
                # Logical lower bound to avoid zeroing out the dose, while preventing a full adult dose for a toddler
                max_allowed_dose = min(max_allowed_dose, max(calculated_peds_max, max_allowed_dose * 0.2))

        if self.dose > max_allowed_dose:
            raise ValueError(
                f"DOSAGE OVERLOAD: {self.dose} {self.unit} exceeds the maximum safe single dose "
                f"limit of {max_allowed_dose} {self.unit} for this patient context."
            )

        return self