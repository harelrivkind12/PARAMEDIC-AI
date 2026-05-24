from fastapi import FastAPI, HTTPException
from openai import RateLimitError, APITimeoutError, APIConnectionError
from app.models.api_schemas import IncidentState
from app.models.report import FieldReport
from app.agents.triage_engine import TriageEngine
from app.core.logger import get_logger

logger = get_logger(__name__)

API_DESCRIPTION = """
Autonomous AI Triage Engine for Pre-Hospital Emergency Care with Real-Time Pharmacology Guardrails.

### How to test
1. Click **POST /api/v1/triage/analyze** below
2. Click **Try it out**
3. Click **Execute** — the example is pre-filled
4. Scroll down to **"Server response"** — the analysis appears under **Response body**
"""

app = FastAPI(
    title="Tactical MICU & Triage Protocol Agent",
    description=API_DESCRIPTION,
    version="1.0.0"
)

# Initialize the Triage Engine
triage_engine = TriageEngine()
@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "operational",
        "system": "Tactical MICU AI Engine"
        "engine_model": triage_engine.model_name
        }

@app.post("/api/v1/triage/analyze", response_model=FieldReport, tags=["Clinical Triage"])
async def analyze_incident(incident: IncidentState):
    """
    Analyze an incident and generate a field report.
     - **incident**: A structured JSON payload containing patient demographics, current vitals, baseline vitals (if available), administered treatments, and incident context.
     - **returns**: A comprehensive FieldReport detailing the AI's clinical assessment, recommended interventions, and rationale.
    """
    try:
        logger.info(f"Incoming request: Analyzing incident for patient age {incident.patient.age}")
        report = await triage_engine.process_incident(incident)
        return report

     except RateLimitError:
        # 429: Too Many Requests
        raise HTTPException(
            status_code=429,
            detail="AI service is currently overloaded. Please try again shortly."
        )
    except APITimeoutError:
        # 504: Gateway Timeout
        raise HTTPException(
            status_code=504,
            detail="AI service timed out. Please try again."
        )
    except APIConnectionError:
        # 503: Service Unavailable
        raise HTTPException(
            status_code=503,
            detail="Could not reach AI service. Please check your network connection."
        )
    except Exception as e:
        # 500: Internal Server Error
        # We use exc_info=True here because we don't know what caused this error
        logger.error(f"Unexpected error in /analyze endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during tactical analysis."
        )
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)