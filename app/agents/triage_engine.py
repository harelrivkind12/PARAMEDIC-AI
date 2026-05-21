import json
from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError, AuthenticationError
from pydantic import ValidationError

# System Core & Config
from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.prompts import TRIAGE_SYSTEM_PROMPT_TEMPLATE  # <-- Imported the prompt template

# Data Models
from app.models.api_schemas import IncidentState
from app.models.clinical_assessment import ClinicalAssessment
from app.models.medication import load_protocol_rules
from app.models.report import FieldReport

# Few-Shot Examples
from app.core.examples import TRAUMA_INPUT_EXAMPLE, TRAUMA_ASSESSMENT_EXAMPLE

logger = get_logger(__name__)


class TriageEngine:
    """
    The asynchronous core AI engine responsible for analyzing incident states, 
    generating clinical assessments via OpenAI, and enforcing real-time safety guardrails.
    """

    def __init__(self):
        """
        Initializes the AsyncOpenAI client and builds the dynamic system prompt.
        Extracts the API key securely from the settings singleton.
        """
        settings = get_settings()
        self.model_name = settings.model_name
        
        # Using AsyncOpenAI for non-blocking server architecture
        self.client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
        self.system_prompt = self._build_system_prompt()
        
        logger.info(f"TriageEngine initialized asynchronously with model: {self.model_name}")

    def _build_system_prompt(self) -> str:
        """
        Constructs the system prompt using the external template,
        injecting the current medication guidelines and few-shot examples.
        """
        guidelines = load_protocol_rules()
        guidelines_json_str = json.dumps(guidelines, indent=2)
        
        input_example_str = json.dumps(TRAUMA_INPUT_EXAMPLE, indent=2)
        output_example_str = json.dumps(TRAUMA_ASSESSMENT_EXAMPLE, indent=2)

        # Inject the strings into the placeholders in the template dynamically
        prompt = TRIAGE_SYSTEM_PROMPT_TEMPLATE.format(
            guidelines_json=guidelines_json_str,
            input_example=input_example_str,
            output_example=output_example_str
        )
        
        return prompt

    async def process_incident(self, current_incident: IncidentState) -> FieldReport:
        """
        The main asynchronous operational pipeline. 
        Takes the raw incident data, interfaces with the LLM using Structured Outputs, 
        validates pharmacological safety protocols, and generates the final FieldReport.
        """
        logger.info(f"Initiating triage analysis for patient age {current_incident.patient.age}.")
        
        user_prompt = f"Assess the following casualty data and return the structured action plan:\n\n{current_incident.model_dump_json(indent=2)}"

        try:
            logger.debug("Dispatching asynchronous request to OpenAI API...")
            
            # 1. Asynchronous API Call with Native Structured Outputs
            response = await self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=ClinicalAssessment,
                temperature=0.0,  # Zero variance for strict clinical determinism
                max_tokens=1500
            )
            
            # 2. Extract the structured Pydantic object
            raw_assessment = response.choices[0].message.parsed
            
            if not raw_assessment:
                raise ValueError("The AI engine returned an empty assessment structure.")
                
            logger.info(f"AI Assessment received. Suggested triage level: {raw_assessment.triage_level}. Executing pharmacology guardrails.")

            # 3. SAFETY VALIDATION (The Guardrail execution)
            patient_context = {
                "patient_age": current_incident.patient.age,
                "patient_weight_kg": current_incident.patient.estimated_weight_kg,
                "active_clinical_flags": [flag for flag in current_incident.current_vitals.clinical_flags]
            }
            
            validated_medications = []
            for med in raw_assessment.recommended_medications:
                try:
                    # Validate against guidelines and dynamic patient context
                    validated_med = med.model_validate(med.model_dump(), context=patient_context)
                    validated_medications.append(validated_med)
                except ValidationError as safety_error:
                    error_msg = safety_error.errors()[0]['msg']
                    logger.warning(f"BLOCKED MEDICATION: AI suggested unsafe parameter. Reason: {error_msg}")
                    # Append the block reason to the visible warnings for the paramedic
                    raw_assessment.critical_warnings.append(f"SYSTEM SAFETY OVERRIDE: {error_msg}")

            # Override the LLM's medication list with only the strictly validated ones
            raw_assessment.recommended_medications = validated_medications

            # 4. Build and return the final envelope
            report = FieldReport(
                incident_state=current_incident,
                ai_assessment=raw_assessment,
                provider_id="SYSTEM_AUTO_DISPATCH"
            )
            
            logger.info("Triage analysis complete and packaged successfully.")
            return report

        # 5. Robust Error Handling
        except AuthenticationError:
            logger.error("OpenAI authentication failed — check BA_OPENAI_API_KEY in settings")
            raise
        except RateLimitError:
            logger.error("OpenAI rate limit hit — fallback protocols required")
            raise
        except APITimeoutError:
            logger.error("Tactical communications timeout with OpenAI servers")
            raise
        except APIConnectionError:
            logger.error("Could not connect to OpenAI — check tactical network connectivity")
            raise
        except Exception as e:
            logger.error(f"Unexpected critical error during triage processing: {e}", exc_info=True)
            raise