from openai import AsyncOpenAI, RateLimitError, APITimeoutError, APIConnectionError, AuthenticationError
from pydantic import ValidationError

# System Core & Config
from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.prompts import build_system_prompt, build_user_prompt

# Data Models
from app.models.api_schemas import IncidentState
from app.models.clinical_assessment import ClinicalAssessment
from app.models.report import FieldReport

logger = get_logger(__name__)

class TriageEngine:
    """
    The asynchronous core AI engine responsible for analyzing incident states, 
    generating clinical assessments via OpenAI, and enforcing real-time safety guardrails.
    """

    def __init__(self):
        """
        Initializes the AsyncOpenAI client and fetches the pre-built system prompt.
        """
        settings = get_settings()
        self.model_name = settings.model_name
        self.client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
        
        # Pulling the fully constructed system prompt from the prompts module
        self.system_prompt = build_system_prompt()
        
        logger.info(f"TriageEngine initialized asynchronously with model: {self.model_name}")

    async def process_incident(self, current_incident: IncidentState) -> FieldReport:
        """
        The main asynchronous operational pipeline.
        """
        logger.info(f"Initiating triage analysis for patient age {current_incident.patient.age}.")
        
        # Build the user prompt using the helper function
        user_prompt = build_user_prompt(current_incident)

        try:
            logger.debug("Dispatching asynchronous request to OpenAI API...")
            
            response = await self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=ClinicalAssessment,
                temperature=0.0,
                max_tokens=1500
            )
            
            raw_assessment = response.choices[0].message.parsed
            if not raw_assessment:
                raise ValueError("The AI engine returned an empty assessment structure.")
                
            logger.info(f"AI Assessment received (Triage: {raw_assessment.triage_level}). Executing pharmacology guardrails.")

            # SAFETY VALIDATION (The Guardrails)
            patient_context = {
                "patient_age": current_incident.patient.age,
                "patient_weight_kg": current_incident.patient.estimated_weight_kg,
                "active_clinical_flags": [flag for flag in current_incident.current_vitals.clinical_flags]
            }
            
            validated_medications = []
            for med in raw_assessment.recommended_medications:
                try:
                    validated_med = med.model_validate(med.model_dump(), context=patient_context)
                    validated_medications.append(validated_med)
                except ValidationError as safety_error:
                    error_msg = safety_error.errors()[0]['msg']
                    logger.warning(f"BLOCKED MEDICATION: {error_msg}")
                    raw_assessment.critical_warnings.append(f"SYSTEM SAFETY OVERRIDE: {error_msg}")

            raw_assessment.recommended_medications = validated_medications

            report = FieldReport(
                incident_state=current_incident,
                ai_assessment=raw_assessment,
                provider_id="SYSTEM_AUTO_DISPATCH"
            )
            
            logger.info("Triage analysis complete and packaged successfully.")
            return report

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