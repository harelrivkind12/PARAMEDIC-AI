"""
Few-shot examples for the Triage AI Engine.
These dictionaries are injected into the LLM system prompt to demonstrate
the expected input states and the rigorous, protocol-aligned outputs required.
"""

# =============================================================================
# SCENARIO 1: MASSIVE HEMORRHAGE (TRAUMA)
# =============================================================================

TRAUMA_INPUT_EXAMPLE = {
    "incident_id": "123e4567-e89b-12d3-a456-426614174000",
    "timestamp": "2026-05-20T14:30:00Z",
    "scene": {
        "incident_type": "Combat/Kinetic",
        "is_scene_safe": True,
        "mass_casualty_incident": False
    },
    "patient": {
        "age": 25,
        "gender": "Male",
        "estimated_weight_kg": 80.0,
        "mechanism_of_injury": "Blast Injury / Shrapnel",
        "chief_complaint": "Amputated right leg below knee, altered mental status."
    },
    "current_vitals": {
        "heart_rate": 135,
        "systolic_bp": 85,
        "dbp": 40,
        "respiratory_rate": 28,
        "spo2": 95,
        "gcs": 13,
        "temperature": 35.8,
        "etco2": 30,
        "pain_scale": 9,
        "clinical_flags": [
            "Active bleeding", 
            "Hypotension (Decompensated)", 
            "Altered Mental Status"
        ]
    }
}

TRAUMA_ASSESSMENT_EXAMPLE = {
    "triage_level": "Red",
    "main_threat": "Exsanguination and decompensated hemorrhagic shock.",
    "recommended_actions": [
        {
            "action_category": "Circulation/Hemorrhage",
            "intervention": "Apply high-and-tight mechanical tourniquet to right lower extremity.",
            "urgency": "Immediate",
            "clinical_rationale": "Active bleeding from blast amputation must be controlled before any other intervention per MARCH protocol."
        },
        {
            "action_category": "Circulation/Hemorrhage",
            "intervention": "Establish large-bore IV or IO access.",
            "urgency": "High",
            "clinical_rationale": "Required for immediate administration of TXA and analgesic control."
        },
        {
            "action_category": "Exposure/Environment",
            "intervention": "Initiate active warming measures (blankets, heated fluids if available).",
            "urgency": "High",
            "clinical_rationale": "Patient temperature is 35.8C. Hypothermia exacerbates the lethal triad of trauma (coagulopathy)."
        }
    ],
    "recommended_medications": [
        {
            "name": "Hexakapron (TXA)",
            "dose": 1.0,
            "unit": "g",
            "route": "IV",
            "special_instructions": "Push slowly over 10 minutes. Administer ASAP within 3 hours of injury."
        },
        {
            "name": "Ketamine",
            "dose": 50.0,
            "unit": "mg",
            "route": "IV",
            "special_instructions": "Administer for pain control. Chosen over Fentanyl due to decompensated hypotension."
        }
    ],
    "critical_warnings": [
        "Fentanyl is CONTRAINDICATED due to active 'Hypotension (Decompensated)' flag.",
        "Maintain permissive hypotension (target SBP ~90mmHg or palpable radial pulse). Do not over-resuscitate with fluids to avoid popping clots."
    ],
    "confidence_score": 98
}

# =============================================================================
# SCENARIO 2: SEVERE ANAPHYLAXIS (MEDICAL)
# =============================================================================

ANAPHYLAXIS_INPUT_EXAMPLE = {
    "incident_id": "987f6543-e21b-34d5-c678-426614174999",
    "timestamp": "2026-05-20T16:15:00Z",
    "scene": {
        "incident_type": "Civilian Emergency",
        "is_scene_safe": True,
        "mass_casualty_incident": False
    },
    "patient": {
        "age": 42,
        "gender": "Female",
        "estimated_weight_kg": 65.0,
        "mechanism_of_injury": "Medical Emergency",
        "chief_complaint": "Severe shortness of breath, facial swelling after bee sting."
    },
    "current_vitals": {
        "heart_rate": 118,
        "systolic_bp": 95,
        "dbp": 60,
        "respiratory_rate": 32,
        "spo2": 89,
        "gcs": 15,
        "temperature": 37.1,
        "etco2": 45,
        "pain_scale": 2,
        "clinical_flags": [
            "Respiratory distress",
            "Urticaria",
            "Wheezing",
            "Angioedema"
        ]
    }
}

# =============================================================================
# SCENARIO 3: PEDIATRIC SHOCK (TESTING WEIGHT IMPUTATION & PEDIATRIC LIMITS)
# =============================================================================

PEDIATRIC_SHOCK_INPUT_EXAMPLE = {
    "incident_id": "pedi-4455-6677-8899-abcdef123456",
    "timestamp": "2026-05-20T17:00:00Z",
    "scene": {
        "incident_type": "Civilian Emergency",
        "is_scene_safe": True,
        "mass_casualty_incident": False
    },
    "patient": {
        "age": 4,
        "gender": "Male",
        "estimated_weight_kg": None, # Intentionally left blank to trigger APLS imputation (4*2+8 = 16kg)
        "mechanism_of_injury": "Medical / Suspected Sepsis",
        "chief_complaint": "Lethargic, extremely hot to touch, not responding to parents."
    },
    "current_vitals": {
        "heart_rate": 165,
        "systolic_bp": 68,
        "dbp": 35,
        "respiratory_rate": 45,
        "spo2": 92,
        "gcs": 11,
        "temperature": 40.1,
        "etco2": 25,
        "pain_scale": 0,
        "clinical_flags": [
            "Tachycardia",
            "Pediatric Hypotension (Decompensated Shock)",
            "Altered Mental Status"
        ]
    }
}

PEDIATRIC_SHOCK_ASSESSMENT_EXAMPLE = {
    "triage_level": "Red",
    "main_threat": "Decompensated pediatric shock (likely septic) with critical hypotension.",
    "recommended_actions": [
        {
            "action_category": "Airway/Breathing",
            "intervention": "Administer high-flow oxygen via pediatric NRB mask.",
            "urgency": "High",
            "clinical_rationale": "High metabolic demand and poor perfusion require maximizing oxygen delivery."
        },
        {
            "action_category": "Circulation",
            "intervention": "Establish IV or IO access immediately. Administer Normal Saline fluid bolus 20ml/kg (320ml total for 16kg patient).",
            "urgency": "Immediate",
            "clinical_rationale": "First-line treatment for pediatric shock is aggressive fluid resuscitation."
        }
    ],
    "recommended_medications": [
        {
            "name": "Normal Saline (0.9% NaCl)",
            "dose": 320.0,
            "unit": "ml",
            "route": "IV/IO",
            "special_instructions": "Push rapidly (over 5-10 minutes). Reassess lung sounds and BP after bolus."
        },
        {
            "name": "Ceftriaxone (Rocephin)",
            "dose": 800.0, # 50mg/kg for a 16kg child
            "unit": "mg",
            "route": "IV/IO",
            "special_instructions": "Administer early if sepsis is suspected."
        }
    ],
    "critical_warnings": [
        "Patient weight was imputed as 16kg using APLS formula. Verify weight if possible.",
        "Monitor closely for signs of fluid overload (crackles in lungs) during rapid fluid bolus."
    ],
    "confidence_score": 96
}

# =============================================================================
# SCENARIO 4: TACTICAL MCI & IV FAILURE PROTOCOL
# =============================================================================

TACTICAL_IV_FAILURE_INPUT_EXAMPLE = {
    "incident_id": "tact-9988-7766-5544-fedcba654321",
    "timestamp": "2026-05-20T18:45:00Z",
    "scene": {
        "incident_type": "Combat/Kinetic",
        "is_scene_safe": False, # Care Under Fire / Tactical Field Care
        "mass_casualty_incident": True
    },
    "patient": {
        "age": 28,
        "gender": "Male",
        "estimated_weight_kg": 85.0,
        "mechanism_of_injury": "Gunshot Wound (GSW) to abdomen",
        "chief_complaint": "Severe abdominal pain, pale, diaphoretic."
    },
    "current_vitals": {
        "heart_rate": 140,
        "systolic_bp": 80,
        "dbp": 45,
        "respiratory_rate": 24,
        "spo2": 94,
        "gcs": 14,
        "temperature": 36.2,
        "etco2": 32,
        "pain_scale": 8,
        "clinical_flags": [
            "Hypotension (Decompensated)",
            "IV FAILURE PROTOCOL: 2 failed peripheral attempts. Establish IO immediately."
        ]
    },
    "vascular_access_established": None,
    "iv_attempts": 2
}

TACTICAL_IV_FAILURE_ASSESSMENT_EXAMPLE = {
    "triage_level": "Red",
    "main_threat": "Non-compressible torso hemorrhage. Hemorrhagic shock.",
    "recommended_actions": [
        {
            "action_category": "Circulation",
            "intervention": "STOP IV attempts. Establish Humeral or Tibial Intraosseous (IO) access immediately.",
            "urgency": "Immediate",
            "clinical_rationale": "Protocol limits IV attempts to 2 in critical trauma to prevent treatment delay."
        },
        {
            "action_category": "Evacuation",
            "intervention": "Rapid evacuation to surgical facility.",
            "urgency": "Immediate",
            "clinical_rationale": "Non-compressible hemorrhage cannot be definitively treated in the field."
        }
    ],
    "recommended_medications": [
        {
            "name": "Hexakapron (TXA)",
            "dose": 1.0,
            "unit": "g",
            "route": "IO",
            "special_instructions": "Administer via IO once established. Flush IO line well."
        },
        {
            "name": "Ketamine",
            "dose": 50.0,
            "unit": "mg",
            "route": "IO",
            "special_instructions": "Analgesia of choice for hypotensive trauma patient."
        }
    ],
    "critical_warnings": [
        "SCENE IS NOT SAFE. Prioritize basic hemorrhage control and move to cover before advanced interventions.",
        "Do not delay evacuation for further access attempts."
    ],
    "confidence_score": 99
}

ANAPHYLAXIS_ASSESSMENT_EXAMPLE = {
    "triage_level": "Red",
    "main_threat": "Anaphylactic shock with impending airway compromise.",
    "recommended_actions": [
        {
            "action_category": "Airway",
            "intervention": "Position patient upright and apply high-flow oxygen via Non-Rebreather Mask (15 LPM).",
            "urgency": "Immediate",
            "clinical_rationale": "SpO2 is 89% with visible angioedema. Maximizing oxygenation is critical before potential airway loss."
        },
        {
            "action_category": "Circulation/Hemorrhage",
            "intervention": "Establish IV access.",
            "urgency": "High",
            "clinical_rationale": "Required for secondary fluid resuscitation and IV antihistamines/corticosteroids."
        },
        {
            "action_category": "Airway",
            "intervention": "Prepare advanced airway equipment (Intubation/Cricothyrotomy kit).",
            "urgency": "High",
            "clinical_rationale": "Facial swelling indicates high risk of rapid airway occlusion if epinephrine fails."
        }
    ],
    "recommended_medications": [
        {
            "name": "Adrenaline (Epinephrine)",
            "dose": 0.3,
            "unit": "mg",
            "route": "IM",
            "special_instructions": "Administer immediately into the anterolateral thigh. Do not delay for IV access. Repeat in 5-15 mins if no improvement."
        },
        {
            "name": "ventolin",
            "dose": 5.0,
            "unit": "mg",
            "route": "INH",
            "special_instructions": "Administer via nebulizer to treat severe bronchospasm and wheezing."
        },
        {
            "name": "solumedrol",
            "dose": 125.0,
            "unit": "mg",
            "route": "IV",
            "special_instructions": "Administer to prevent secondary/biphasic anaphylactic reactions."
        }
    ],
    "critical_warnings": [
        "Epinephrine is the absolute first-line treatment. DO NOT delay IM administration to establish IV access or administer secondary drugs."
    ],
    "confidence_score": 95
}