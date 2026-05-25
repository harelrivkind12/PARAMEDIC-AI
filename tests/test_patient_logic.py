import pytest
from app.models.api_schemas import IncidentState
from app.models.patient import Patient
from app.models.vitals import Vitals, ClinicalFlag
from app.core.constants import (
    PEDIATRIC_AGE_THRESHOLD,
    MAX_HR_PEDIATRIC,
    MIN_SBP_PEDIATRIC
)

def test_pediatric_tachycardia_suppression():
    """
    Test that a normal pediatric heart rate does not trigger 
    a false-positive adult tachycardia alert.
    """
    patient = Patient(age=3, gender="male", name="Kid")
    
    # Initialize vitals with a heart rate that is normal for a child
    # but also manually add a 'Tachycardia' flag to simulate an initial adult-based calculation
    vitals = Vitals(
        heart_rate=MAX_HR_PEDIATRIC - 5,
        systolic_bp=100,
        clinical_flags=[ClinicalFlag(name="Tachycardia", severity="High", system="Cardiovascular")]
    )
    
    state = IncidentState(
        patient=patient,
        current_vitals=vitals
    )
    
    # The validator should have automatically removed the 'Tachycardia' flag
    flag_names = [f.name for f in state.current_vitals.clinical_flags]
    assert "Tachycardia" not in flag_names

def test_pediatric_hypotension_alert():
    """
    Test that pediatric hypotension triggers the specific decompensated shock alert.
    """
    patient = Patient(age=4, gender="female", name="Kid2")
    
    # Initialize vitals with a critically low systolic BP for a child
    vitals = Vitals(
        heart_rate=150,
        systolic_bp=MIN_SBP_PEDIATRIC - 10, 
        clinical_flags=[]
    )
    
    state = IncidentState(
        patient=patient,
        current_vitals=vitals
    )
    
    # The validator should append the pediatric hypotension flag
    flag_names = [f.name for f in state.current_vitals.clinical_flags]
    assert "Pediatric Hypotension (Decompensated Shock)" in flag_names

def test_iv_failure_protocol_trigger():
    """
    Test that 2 failed IV attempts with no established access 
    triggers the immediate IO protocol alert.
    """
    patient = Patient(age=30, gender="male", name="Adult")
    vitals = Vitals(heart_rate=90, systolic_bp=120, clinical_flags=[])
    
    state = IncidentState(
        patient=patient,
        current_vitals=vitals,
        vascular_access_established=None,
        iv_attempts=2
    )
    
    # Verify that the high-priority IO escalation flag was generated
    flag_names = [f.name for f in state.current_vitals.clinical_flags]
    assert any("IV FAILURE PROTOCOL" in name for name in flag_names)

def test_no_iv_failure_when_access_established():
    """
    Test that multiple attempts do NOT trigger the failure alert 
    if access is ultimately established successfully.
    """
    patient = Patient(age=30, gender="male", name="Adult")
    vitals = Vitals(heart_rate=90, systolic_bp=120, clinical_flags=[])
    
    # Simulating a scenario where it took 3 tries, but IV was successfully secured
    state = IncidentState(
        patient=patient,
        current_vitals=vitals,
        vascular_access_established="IV",
        iv_attempts=3  
    )
    
    # The validator should ignore the attempts count since access is established
    flag_names = [f.name for f in state.current_vitals.clinical_flags]
    assert not any("IV FAILURE PROTOCOL" in name for name in flag_names)