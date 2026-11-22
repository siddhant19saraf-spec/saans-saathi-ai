"""ORM models. Importing this package registers every table on ``Base``."""

from app.models.ai import AiConversation, AiMessage
from app.models.air import (
    AirQualityFetchLog,
    AirQualityForecast,
    AirQualitySnapshot,
)
from app.models.base import Base
from app.models.ecoroute import EmissionCalculation, SavedJourney, SustainabilityGoal
from app.models.household import (
    Household,
    HouseholdMember,
    HouseholdPreference,
    SavedLocation,
)
from app.models.impact import PrivacyEvent, SustainabilityActivity, UsageDaily
from app.models.indoor import (
    IndoorAssessment,
    IndoorRecommendation,
    IndoorRoom,
    IndoorSensor,
    IndoorSensorReading,
    IndoorSource,
)
from app.models.profile import Profile
from app.models.routine import Recommendation, Routine, RoutineActivity, RoutineItem

__all__ = [
    "AiConversation",
    "AiMessage",
    "AirQualityFetchLog",
    "AirQualityForecast",
    "AirQualitySnapshot",
    "Base",
    "EmissionCalculation",
    "Household",
    "HouseholdMember",
    "HouseholdPreference",
    "IndoorActionEvent",
    "IndoorAssessment",
    "IndoorRecommendation",
    "IndoorRoom",
    "IndoorSensor",
    "IndoorSensorReading",
    "IndoorSource",
    "PrivacyEvent",
    "Profile",
    "Recommendation",
    "Routine",
    "RoutineActivity",
    "RoutineItem",
    "SavedJourney",
    "SavedLocation",
    "SustainabilityActivity",
    "SustainabilityGoal",
    "UsageDaily",
]
