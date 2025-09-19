from datetime import datetime, timezone
from sqlalchemy import event

# Import all models
from .specialty import Specialty
from .reclamation import (
    Reclamation,
    ReclamationType,
    ReclamationStatusEnum,
    ReclamationPriorityEnum
)
from .training import (
    Training,
    TrainingSession,
    TrainingSessionParticipant,
    TrainingTypeEnum,
    TrainingStatus,
    DurationEnum,
    TrainingSessionStatusEnum
)
from .student_application import (
    StudentApplication,
    StudentAttachment,
    ApplicationStatusEnum
)

# Event listeners for automatic timestamp updates
def update_updated_at_training(mapper, connection, target):
    target.updated_at = datetime.now(timezone.utc)

# Add the event listeners for before update
event.listen(Training, 'before_update', update_updated_at_training)
event.listen(TrainingSession, 'before_update', update_updated_at_training)
event.listen(StudentApplication, 'before_update', update_updated_at_training)
event.listen(StudentAttachment, 'before_update', update_updated_at_training)
event.listen(Specialty, 'before_update', update_updated_at_training)
event.listen(TrainingSessionParticipant, 'before_update', update_updated_at_training)
event.listen(ReclamationType, 'before_update', update_updated_at_training)
event.listen(Reclamation, 'before_update', update_updated_at_training)

# Export all models and enums
__all__ = [
    # Models
    "Training",
    "TrainingSession", 
    "TrainingSessionParticipant",
    "StudentApplication",
    "StudentAttachment",
    "Specialty",
    "Reclamation",
    "ReclamationType",
    
    # Enums
    "TrainingTypeEnum",
    "TrainingStatus",
    "DurationEnum",
    "TrainingSessionStatusEnum",
    "ApplicationStatusEnum",
    "ReclamationStatusEnum",
    "ReclamationPriorityEnum",
]