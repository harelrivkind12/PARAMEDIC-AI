# PARAMEDIC-AI
PARAMEDIC-AI: Intelligent PreHospital Decision Support System. An advanced AI-driven platform for EMS teams, leveraging LLMs and structured Pydantic data validation to assist in real-time triage, protocol adherence, and clinical decision-making. Enhances patient outcomes in high-pressure environments by transforming field data into actionable care.

# ⚙️What It Actually Does
The Tactical MICU & Triage Protocol Agent is an autonomous pre-hospital decision-support engine. It bridges the gap between raw, chaotic field telemetry and strict, protocol-aligned clinical actions during high-stress civilian or combat trauma scenarios.

Asynchronous Data Ingestion: Consumes structured casualty telemetry (IncidentState) containing vital signs, active clinical indicators, mechanisms of injury, and procedural states.

Automated Contextual Validation: Runs high-speed deterministic Pydantic validation before the AI layer. It automatically adjusts pediatric vital sign thresholds (e.g., suppressing adult tachycardia alerts) and triggers immediate protocol alerts (e.g., forcing Intraosseous (IO) access after multiple failed peripheral IV attempts).

Dynamic Weight Imputation: Uses clinical Advanced Pediatric Life Support (APLS) formulas and height-based BMI statistics to auto-calculate missing casualty weights in real time, preventing weight-based medication calculation failures.

Protocol-Grounded Analysis: Transforms parsed incident data into clean clinical handover briefs (to_ai_summary), routing them to OpenAI's native Structured Outputs engine (response_format). The AI evaluates the case exclusively using a pre-loaded local formulary repository (guidelines.json).

Safety Guardrails Loop: Intercepts raw AI recommendations and programmatically cross-references dosages, maximum thresholds, and active physiological contraindications (e.g., dropping Fentanyl approval if the patient develops hypotension) before packaging the final actionable payload (FieldReport).

# ⚠️Current Limitations Worth Knowing
Stateless Execution: The engine is inherently stateless to prevent cross-casualty data bleed and latency degradation. Tracking structural trendlines or changes over a prolonged timeline requires the calling client/database to preserve state and provide the updated chronological history inside the administered_treatments list on subsequent API requests.

Network Dependency: The core clinical assessment mechanism depends on secure, asynchronous connectivity to OpenAI's upstream API infrastructure. In deep-field or compromised-network conditions, the system relies on fallback modes.

Formulary Rigidity: The pharmacology guardrails validate against a strictly defined static schema. Complex, multi-variable drug interactions outside of the defined contraindications_flags are currently limited by the structured rule dictionary.

# Tech Stack
Python / FastAPI — async API, handles the real-time nature of the use case
Pydantic V2 — deep validation across all the models (more on this below)
LangChain + OpenAI GPT-4o — structured output via with_structured_output() so the AI returns typed Pydantic objects, not raw text
pydantic-settings — clean config management with .env support

# Project Structure

├── app/
|   ├── main.py                      # The main FastAPI application, server entry point, and API routes
│   ├── models/
│   │   ├── patient.py               # Patient demographics and smart weight imputation logic
│   │   ├── vitals.py                # Vital signs and clinical flags definitions
│   │   ├── api_schemas.py           # IncidentState: the core data model & AI prompt builder
│   │   ├── clinical_assessment.py   # AI structured output schema and pharmacology guardrails
│   |   ├── examples.py              # Pre-built trauma scenarios (e.g., INCIDENT_STATE_EXAMPLE)
│   │   ├── report.py                # FieldReport schema (final API response payload)
│   │   └── medication.py            # Local formulary rules and contraindications definitions
│   │
│   ├── agents/
│   │   |── triage_engine.py         # The async core engine connecting to OpenAI and enforcing safety
│   |   └── prompts.py               # system prompt + directive instructions + prompt builder
│   │
│   └── core/
│       ├── prompts.py               # System prompts templates and prompt compilation functions
│       ├── constants.py             # Medical thresholds (PEDIATRIC_AGE, MIN_SBP, etc.)
│       ├── config.py                # Pydantic BaseSettings for environment variables validation
│       └── logger.py                # Standardized tactical system logging
│
└── tests/
    ├── test_imputation.py       # Tests for auto-calculating missing pediatric/adult weights
    ├── test_guardrails.py       # Tests for medication contraindications and pediatric limits
    └── test_incident_state.py   # Tests for protocol validation (e.g., IV failure to IO)

# MVP Status
This repository represents a production-ready REST API built with FastAPI. It ingests chaotic trauma data (IncidentState), enriches it (e.g., smart pediatric weight imputation), and uses an AI engine to evaluate the clinical picture.

Crucially, it is not just an LLM wrapper. The AI's structured output is intercepted by deterministic, code-based safety guardrails that block contraindicated medications in real-time, ensuring a medically safe, actionable FieldReport.

# How to Run
1. Install dependencies:

python -m venv venv
source venv/bin/activate  # on Windows: venv\Scripts\activate
pip install -r requirements.txt
2. Set up your environment:

cp .env.example .env   # on Windows: copy .env.example .env
Open .env and add your OpenAI API key:

BA_OPENAI_API_KEY=your_key_here
BA_MODEL_NAME=gpt-4o
3. Start the server:

uvicorn main:app --reload
4. Open the interactive docs:
Navigate to:

http://localhost:8000/docs
in your browser
Click POST /api/v1/triage/analyze → Try it out → Execute to run your first analysis. The example is pre-filled automatically.

# Pre-Built Test Scenarios

# Running the Tests

# Environment Variables
BA_OPENAI_API_KEY=your_key_here
BA_MODEL_NAME=gpt-4o

# Roadmap

* **Live Field UI:** A simple, high-visibility tablet interface where a paramedic or tactical medic can log vital signs and treatments by pressing quick-action buttons as things happen, rather than filling in raw JSON. The AI analysis would run instantly whenever the provider requests a protocol refresh. This transforms the system from a developer API into a tool a real medic could actually use in a high-stress environment.

* **Mass Casualty Incident (MCI) Memory:** Tracking patient statuses, triage categories, and resource allocation across an entire multi-casualty scene, ensuring the AI can prioritize evacuation and prevent contradicting its own earlier clinical advice within the same incident.

* **Deployment:** A live, secure URL with demo access so the triage engine and its pharmacology guardrails can be stress-tested without cloning the repository or configuring an OpenAI API key.



