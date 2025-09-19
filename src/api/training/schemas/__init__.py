# Training schemas
from .training import (
    TrainingCreateInput,
    TrainingUpdateInput,
    TrainingOut,
    TrainingFilter,
    TrainingSessionCreateInput,
    TrainingSessionUpdateInput,
    TrainingSessionOut,
    TrainingSessionFilter,
    TrainingOutSuccess,
    TrainingsPageOutSuccess,
    TrainingSessionOutSuccess,
    TrainingSessionsPageOutSuccess,
    StrengthInput,
    BenefitInput,
)

# Specialty schemas
from .specialty import (
    SpecialtyCreateInput,
    SpecialtyUpdateInput,
    SpecialtyOut,
    SpecialtyFilter,
    SpecialtyOutSuccess,
    SpecialtyListOutSuccess,
    SpecialtiesPageOutSuccess,
)

# Student application schemas
from .student_application import (
    StudentApplicationCreateInput,
    StudentApplicationUpdateInput,
    StudentApplicationSubmitInput,
    StudentApplicationOut,
    StudentApplicationFullOut,
    StudentApplicationFilter,
    StudentAttachmentInput,
    StudentAttachmentOut,
    StudentApplicationOutSuccess,
    StudentApplicationsPageOutSuccess,
    StudentAttachmentOutSuccess,
    StudentAttachmentListOutSuccess,
)

# Reclamation schemas
from .reclamation import (
    ReclamationCreateInput,
    ReclamationAdminUpdateInput,
    ReclamationOut,
    ReclamationFullOut,
    ReclamationFilter,
    ReclamationTypeCreateInput,
    ReclamationTypeOut,
    ReclamationOutSuccess,
    ReclamationListOutSuccess,
    ReclamationsPageOutSuccess,
    ReclamationTypeOutSuccess,
    ReclamationTypeListOutSuccess,
)

# Export all schemas
__all__ = [
    # Training
    "TrainingCreateInput",
    "TrainingUpdateInput", 
    "TrainingOut",
    "TrainingFilter",
    "TrainingSessionCreateInput",
    "TrainingSessionUpdateInput",
    "TrainingSessionOut", 
    "TrainingSessionFilter",
    "TrainingOutSuccess",
    "TrainingsPageOutSuccess",
    "TrainingSessionOutSuccess",
    "TrainingSessionsPageOutSuccess",
    "StrengthInput",
    "BenefitInput",
    
    # Specialty
    "SpecialtyCreateInput",
    "SpecialtyUpdateInput",
    "SpecialtyOut",
    "SpecialtyFilter", 
    "SpecialtyOutSuccess",
    "SpecialtyListOutSuccess",
    "SpecialtiesPageOutSuccess",
    
    # Student Application
    "StudentApplicationCreateInput",
    "StudentApplicationUpdateInput",
    "StudentApplicationSubmitInput",
    "StudentApplicationOut",
    "StudentApplicationFullOut",
    "StudentApplicationFilter",
    "StudentAttachmentInput",
    "StudentAttachmentOut",
    "StudentApplicationOutSuccess",
    "StudentApplicationsPageOutSuccess", 
    "StudentAttachmentOutSuccess",
    "StudentAttachmentListOutSuccess",
    
    # Reclamation
    "ReclamationCreateInput",
    "ReclamationAdminUpdateInput",
    "ReclamationOut",
    "ReclamationFullOut", 
    "ReclamationFilter",
    "ReclamationTypeCreateInput",
    "ReclamationTypeOut",
    "ReclamationOutSuccess",
    "ReclamationListOutSuccess",
    "ReclamationsPageOutSuccess",
    "ReclamationTypeOutSuccess",
    "ReclamationTypeListOutSuccess",
]