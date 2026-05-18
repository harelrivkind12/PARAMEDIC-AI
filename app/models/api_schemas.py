from pydantic import BaseModel, Field
from typing import Optional

# יבוא של אבני הבניין המקומיות שלנו מהתיקייה
from models.vitals import Vitals
from models.patient import Patient
from models.field_report import FieldReportExtraction
from models.protocol import ProtocolAction # (נניח שכך נקרא למחלקה שם)