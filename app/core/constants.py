from pathlib import Path

# ==========================================
# 1. System & Agent Thresholds
# ==========================================
# Autonomous retry loop thresholds
CONFIDENCE_RETRY_THRESHOLD = 0.85  # Retry if AI confidence is below 85%
MAX_ANALYSIS_RETRIES = 2           # Max retry attempts before accepting best result

# File paths
BASE_DIR = Path(__file__).resolve().parent.parent
PROTOCOLS_FILE_PATH = BASE_DIR / "protocols" / "guidelines.json"


# ==========================================
# 2. Critical Time Windows (The "Clutch Time" of Trauma)
# ==========================================
# "Platinum 10 Minutes" - Max recommended on-scene time for critical trauma patients
PLATINUM_TEN_MINUTES = 10 

# Reassessment buffers
# Minimum minutes before evaluating the effect of an IV/IO medication (e.g., Fentanyl)
MIN_IV_MED_REASSESSMENT_MINUTES = 5


# ==========================================
# 3. Clinical Deterioration Thresholds (The "Momentum Shifts")
# ==========================================
# A drop of this many mmHg in Systolic BP between two checks is considered rapid deterioration
RAPID_BP_DROP_THRESHOLD = 20

# Shock Index (HR / Systolic BP) above this value triggers immediate hemorrhagic shock protocols
SHOCK_INDEX_CRITICAL_THRESHOLD = 1.0


# ==========================================
# 4. Demographic & Safety Buffers
# ==========================================
# Age thresholds affecting protocol selection and medication dosages
PEDIATRIC_AGE_THRESHOLD = 18
GERIATRIC_AGE_THRESHOLD = 65

# Glasgow Coma Scale (GCS)
# GCS of 8 or below triggers immediate airway management ("Less than 8, intubate")
CRITICAL_GCS_THRESHOLD = 8


# ==========================================
# 5. Medication Warning Buffers
# ==========================================
# If an administered dose is within this percentage of the MAX allowed dose, trigger a warning
MAX_DOSE_WARNING_BUFFER_PERCENT = 10