import pytest

# The base URL for our triage analysis endpoint
ANALYZE_ENDPOINT = "/api/v1/triage/analyze"

def test_analyze_endpoint_valid_trauma_payload(client, trauma_payload):
    """
    Test that the API accepts a fully valid adult trauma payload 
    and returns a successful 200 OK status.
    """
    response = client.post(ANALYZE_ENDPOINT, json=trauma_payload)
    
    # We expect a 200 OK if Pydantic validation passes 
    # and the engine processes the request successfully.
    assert response.status_code == 200

def test_analyze_endpoint_valid_pediatric_payload(client, pediatric_payload):
    """
    Test that the API correctly handles a pediatric shock scenario,
    specifically ensuring the missing weight doesn't crash the server 
    (thanks to our auto-imputation logic).
    """
    response = client.post(ANALYZE_ENDPOINT, json=pediatric_payload)
    assert response.status_code == 200

def test_analyze_endpoint_missing_required_patient_data(client, trauma_payload):
    """
    Test that the API explicitly rejects a payload if critical 
    top-level objects (like the patient) are missing.
    """
    # Create a broken payload by removing the 'patient' dictionary
    broken_payload = trauma_payload.copy()
    del broken_payload["patient"]
    
    response = client.post(ANALYZE_ENDPOINT, json=broken_payload)
    
    # FastAPI/Pydantic should automatically return a 422 Unprocessable Entity
    assert response.status_code == 422
    
    # Ensure the error message specifically mentions the missing 'patient' field
    error_detail = response.json()["detail"]
    assert any(error["loc"] == ["body", "patient"] for error in error_detail)

def test_analyze_endpoint_missing_required_vitals(client, trauma_payload):
    """
    Test that the API rejects a payload missing current vitals,
    which are mandatory for any clinical assessment.
    """
    broken_payload = trauma_payload.copy()
    del broken_payload["current_vitals"]
    
    response = client.post(ANALYZE_ENDPOINT, json=broken_payload)
    
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any(error["loc"] == ["body", "current_vitals"] for error in error_detail)

def test_analyze_endpoint_invalid_data_types(client, trauma_payload):
    """
    Test that sending a string where an integer is expected (e.g., age)
    is handled correctly (Pydantic will either cast it or throw a 422).
    If we send a completely uncastable string, it must fail safely.
    """
    broken_payload = trauma_payload.copy()
    # "thirty" cannot be cast to an integer
    broken_payload["patient"]["age"] = "thirty" 
    
    response = client.post(ANALYZE_ENDPOINT, json=broken_payload)
    
    assert response.status_code == 422
    error_detail = response.json()["detail"]
    assert any("age" in str(error["loc"]) for error in error_detail)