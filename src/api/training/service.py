from typing import List, Optional, Tuple
from datetime import datetime, timezone
from fastapi import Depends
from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import select, or_

from src.api.payments.models import Payment, PaymentStatusEnum
from src.database import get_session_async
from src.api.training.models import (
    Training,
    TrainingSession,
    StudentApplication,
    StudentAttachment,
    TrainingSessionParticipant,
    Specialty,
    Reclamation,
    ReclamationType,
    ReclamationStatusEnum,
    ReclamationPriorityEnum,
)
from src.api.training.schemas import (
    StudentApplicationCreateInput,
    StudentApplicationFilter,
    StudentAttachmentInput,
    TrainingCreateInput,
    TrainingFilter,
    TrainingSessionCreateInput,
    TrainingSessionFilter,
    TrainingSessionUpdateInput,
    TrainingUpdateInput,
    SpecialtyCreateInput,
    SpecialtyUpdateInput,
    SpecialtyFilter,
    ReclamationCreateInput,
    ReclamationFilter,
    ReclamationAdminUpdateInput,
    ReclamationTypeCreateInput,
)
from src.api.user.service import UserService
from src.api.user.models import User, UserTypeEnum
from src.api.payments.schemas import PaymentInitInput
from src.api.payments.service import PaymentService
from src.config import settings
from src.helper.file_helper import FileHelper
from src.helper.moodle import MoodleService, MoodleAPIError
from src.helper.notifications import SendPasswordNotification
try:
    from src.helper.moodle import (
        moodle_create_course_task,
        moodle_ensure_user_task,
        moodle_enrol_user_task,
    )
except Exception:
    moodle_create_course_task = None
    moodle_ensure_user_task = None
    moodle_enrol_user_task = None

import secrets
import string

def generate_password(length: int = 12) -> str:
    # Define allowed characters
    alphabet = string.ascii_letters + string.digits + string.punctuation
    # Securely pick characters
    password = ''.join(secrets.choice(alphabet) for _ in range(length))
    return password

class TrainingService:
    def __init__(self, session: AsyncSession = Depends(get_session_async)) -> None:
        self.session = session

    # Trainings
    async def create_training(self, data : TrainingCreateInput) -> Training:
        training = Training(**data.model_dump(exclude_none=True))
        self.session.add(training)
        await self.session.commit()
        await self.session.refresh(training)
        return training

    async def update_training(self, training: Training, data : TrainingUpdateInput) -> Training:
        for key, value in data.model_dump(exclude_none=True).items():
            setattr(training, key, value)
        self.session.add(training)
        await self.session.commit()
        await self.session.refresh(training)
        return training

    async def get_training_by_id(self, training_id: str) -> Optional[Training]:
        statement = select(Training).where(Training.id == training_id, Training.delete_at.is_(None))
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def list_trainings(self, filters: TrainingFilter) -> Tuple[List[Training], int]:
        statement = select(Training).where(Training.delete_at.is_(None))
        count_query = select(func.count(Training.id)).where(Training.delete_at.is_(None))

        if filters.search is not None:
            like_clause = or_(
                Training.title.contains(filters.search),
                Training.presentation.contains(filters.search),
                Training.program.contains(filters.search),
                Training.target_skills.contains(filters.search),
            )
            statement = statement.where(like_clause)
            count_query = count_query.where(like_clause)

        if filters.status is not None:
            statement = statement.where(Training.status == filters.status)
            count_query = count_query.where(Training.status == filters.status)

        if filters.specialty_id is not None:
            statement = statement.where(Training.specialty_id == filters.specialty_id)
            count_query = count_query.where(Training.specialty_id == filters.specialty_id)

        if filters.order_by == "created_at":
            statement = statement.order_by(Training.created_at if filters.asc == "asc" else Training.created_at.desc())
        elif filters.order_by == "title":
            statement = statement.order_by(Training.title if filters.asc == "asc" else Training.title.desc())

        total_count = (await self.session.execute(count_query)).scalar_one()

        statement = statement.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        result = await self.session.execute(statement)
        return result.scalars().all(), total_count

    async def delete_training(self, training: Training) -> Training:
        training.delete_at = datetime.now(timezone.utc)
        self.session.add(training)
        await self.session.commit()
        return training

    # Training Sessions
    async def create_training_session(self, data:  TrainingSessionCreateInput) -> TrainingSession:
        session = TrainingSession(**data.model_dump(exclude_none=True))
        self.session.add(session)
        await self.session.commit()
        await self.session.refresh(session)
        # Create Moodle course and store moodle_course_id (best-effort)
        # Dispatch background task to create Moodle course
        try:
            # Fetch training for names
            tr_stmt = select(Training).where(Training.id == session.training_id)
            tr_res = await self.session.execute(tr_stmt)
            training = tr_res.scalars().first()
            fullname = f"{training.title} | Session {session.id[:8]}"
            shortname = f"{training.title[:20]}-{session.id[:6]}" if training else f"Session-{session.id[:6]}"
            if moodle_create_course_task:
                moodle_create_course_task.apply_async(kwargs={"fullname": fullname, "shortname": shortname})
            else:
                moodle = MoodleService()
                course_id = await moodle.create_course(fullname=fullname, shortname=shortname)
                session.moodle_course_id = course_id
                self.session.add(session)
                await self.session.commit()
                await self.session.refresh(session)
        except Exception:
            pass
        return session

    async def update_training_session(self, training_session: TrainingSession, data :TrainingSessionUpdateInput) -> TrainingSession:
        for key, value in data.model_dump(exclude_none=True).items():
            setattr(training_session, key, value)
        self.session.add(training_session)
        await self.session.commit()
        await self.session.refresh(training_session)
        return training_session

    async def get_training_session_by_id(self, session_id: str) -> Optional[TrainingSession]:
        statement = select(TrainingSession).where(TrainingSession.id == session_id, TrainingSession.delete_at.is_(None))
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def list_training_sessions(self, filters: TrainingSessionFilter) -> Tuple[List[TrainingSession], int]:
        statement = select(TrainingSession).where(TrainingSession.delete_at.is_(None))
        count_query = select(func.count(TrainingSession.id)).where(TrainingSession.delete_at.is_(None))

        if filters.training_id is not None:
            statement = statement.where(TrainingSession.training_id == filters.training_id)
            count_query = count_query.where(TrainingSession.training_id == filters.training_id)

        if filters.center_id is not None:
            statement = statement.where(TrainingSession.center_id == filters.center_id)
            count_query = count_query.where(TrainingSession.center_id == filters.center_id)

        if filters.status is not None:
            statement = statement.where(TrainingSession.status == filters.status)
            count_query = count_query.where(TrainingSession.status == filters.status)

        if filters.order_by == "created_at":
            statement = statement.order_by(TrainingSession.created_at if filters.asc == "asc" else TrainingSession.created_at.desc())
        elif filters.order_by == "registration_deadline":
            statement = statement.order_by(TrainingSession.registration_deadline if filters.asc == "asc" else TrainingSession.registration_deadline.desc())
        elif filters.order_by == "start_date":
            statement = statement.order_by(TrainingSession.start_date if filters.asc == "asc" else TrainingSession.start_date.desc())

        total_count = (await self.session.execute(count_query)).scalar_one()

        statement = statement.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        result = await self.session.execute(statement)
        return result.scalars().all(), total_count

    async def delete_training_session(self, training_session: TrainingSession) -> TrainingSession:
        training_session.delete_at = datetime.now(timezone.utc)
        self.session.add(training_session)
        await self.session.commit()
        return training_session
    
    

    # Student Applications
    async def start_student_application(self, data :StudentApplicationCreateInput) -> StudentApplication:
        user_service = UserService(self.session)

        user = await user_service.get_by_email(data.email)
        
        if user is None:
            # create a user with default or provided password
            default_password =generate_password(8)
            create_input = type("Obj", (), {
                "first_name": data.first_name or "",
                "last_name": data.last_name or "",
                "country_code": data.country_code or "CM",
                "mobile_number": data.phone_number or "",
                "email": data.email,
                "password": default_password,
                "user_type": UserTypeEnum.STUDENT,
            })
            user = await user_service.create(create_input)
            
            SendPasswordNotification(
            
                email=data.email,
                name=user.full_name(),
                password= default_password
                
            ).send_notification()  

        # Validate target session when provided
        if data.target_session_id is not None:
            session_stmt = select(TrainingSession).where(TrainingSession.id == data.target_session_id)
            session_res = await self.session.execute(session_stmt)
            target_session = session_res.scalars().first()
            if target_session is None:
                raise ValueError("SESSION_NOT_FOUND")
            from datetime import date as _date
            if target_session.registration_deadline < _date.today():
                raise ValueError("SESSION_REGISTRATION_CLOSED")
            if target_session.status != "OPEN_FOR_REGISTRATION":
                raise ValueError("SESSION_NOT_OPEN")
            if target_session.available_slots is not None and target_session.available_slots <= 0:
                raise ValueError("SESSION_NO_SLOTS")
        else:
            raise ValueError("TARGET_SESSION_ID_REQUIRED")

        # Generate application number: APP-TRAIN-{seq}-{YYYYMMDDHHMMSS}
        # Use training_id from the target session
        training_id = target_session.training_id
        count_stmt = select(func.count(StudentApplication.id)).where(StudentApplication.training_id == training_id)
        count_res = await self.session.execute(count_stmt)
        seq = (count_res.scalar() or 0) + 1
        application_number = f"APP-TRAIN-{seq:04d}-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        application = StudentApplication(
            user_id=user.id,
            training_id=training_id,
            target_session_id=data.target_session_id,
            application_number=application_number,
            registration_fee=target_session.registration_fee,
            training_fee=target_session.training_fee,
            currency=target_session.currency,
            
        )
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application
  
    async def update_student_application(self, application: StudentApplication, data) -> StudentApplication:
        for key, value in data.model_dump(exclude_none=True).items():
            setattr(application, key, value)
        self.session.add(application)
        await self.session.commit()
        await self.session.refresh(application)
        return application


    async def submit_student_application(self, application: StudentApplication) -> dict:
        # Initiate payment for registration_fee; fallback to training_fee if needed
        # Use the target session to get fees
        session_stmt = select(TrainingSession).where(TrainingSession.id == application.target_session_id)
        session_res = await self.session.execute(session_stmt)
        target_session = session_res.scalars().first()
        if target_session is None:
            return {"message": "failed", "reason": "SESSION_NOT_FOUND"}

        # Validate required attachments from session
        if target_session.required_attachments:
            existing = await self.list_attachments_by_application(application.id)
            existing_types = {a.document_type for a in existing}
            for required in target_session.required_attachments:
                if required not in existing_types:
                    return {"message": "failed", "reason": f"MISSING_ATTACHMENT:{required}"}

        amount = target_session.registration_fee or 0.0
        payment_service = PaymentService(self.session)
        payment_input = PaymentInitInput(
            payable=application,
            amount=amount,
            product_currency=target_session.currency,
            description=f"Payment for training application fee of session {target_session.id}",
            payment_provider="CINETPAY",
        )
        payment = await payment_service.initiate_payment(payment_input)
        return payment

    async def get_student_application_by_id(self, application_id: int) -> Optional[StudentApplication]:
        statement = select(StudentApplication).where(StudentApplication.id == application_id, StudentApplication.delete_at.is_(None))
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_full_student_application_by_id(self, application_id: int, user_id : Optional[str]) -> Optional[StudentApplication]:
        statement = (
            select(StudentApplication)
            .where(StudentApplication.id == application_id, StudentApplication.delete_at.is_(None))
            .options(selectinload(StudentApplication.training))
            .options(selectinload(StudentApplication.training_session))
            .options(selectinload(StudentApplication.user))
            .options(selectinload(StudentApplication.attachments))
        )
        
        if user_id is not None:
            statement = statement.where(StudentApplication.user_id == user_id)
            
        result = await self.session.execute(statement)
        return result.scalars().first()
    
    
    
    async def get_student_application(self, filters: StudentApplicationFilter,user_id : Optional[str]) -> Tuple[List[Training], int]:
        statement = (
            select(
                StudentApplication.id,
                StudentApplication.application_number,
                StudentApplication.status,
                StudentApplication.target_session_id,
                StudentApplication.refusal_reason,  
                StudentApplication.registration_fee,
                StudentApplication.training_fee,
                StudentApplication.currency,
                StudentApplication.created_at,
                StudentApplication.updated_at,
                StudentApplication.training_id,
                Training.title.label("training_title"),
                TrainingSession.start_date.label("training_session_start_date"),
                TrainingSession.end_date.label("training_session_end_date"),
                User.email.label("user_email"),
                User.first_name.label("user_first_name"),
                User.last_name.label("user_last_name"),
            )
            .join(User, User.id == StudentApplication.user_id)
            .join(Training, Training.id == StudentApplication.training_id)
            .join(Payment, Payment.payable_id == StudentApplication.id)
            .where(Payment.payment_type == StudentApplication.__class__.__name__)
            .where(StudentApplication.delete_at.is_(None))
        )
        
        count_query = (
            select(func.count(StudentApplication.id))
            .join(User, User.id == StudentApplication.user_id)
            .join(Training, Training.id == StudentApplication.training_id)         
            .join(Payment, Payment.payable_id == StudentApplication.id)
            .where(Payment.payment_type == StudentApplication.__class__.__name__)
            .where(StudentApplication.delete_at.is_(None))
        )
        
        if user_id is not None:
            statement = statement.where(StudentApplication.user_id == user_id)
            count_query = count_query.where(StudentApplication.user_id == user_id)
            
        
        if filters.is_paid is not None and filters.is_paid == True:
            statement = statement.where(Payment.status == PaymentStatusEnum.ACCEPTED)
            count_query = count_query.where(Payment.status ==  PaymentStatusEnum.ACCEPTED)

        if filters.search is not None:
            like_clause = or_(
                User.first_name.contains(filters.search),
                User.first_name.contains(filters.search),
                Training.title.contains(filters.search),
                Training.presentation.contains(filters.search),
            )
            statement = statement.where(like_clause)
            count_query = count_query.where(like_clause)

        if filters.status is not None:
            statement = statement.where(StudentApplication.status == filters.status)
            count_query = count_query.where(StudentApplication.status == filters.status)
            
        if filters.training_id is not None:
            statement = statement.where(StudentApplication.training_id == filters.training_id)
            count_query = count_query.where(StudentApplication.training_id == filters.training_id)
            
        if filters.training_session_id is not None:
            statement = statement.where(StudentApplication.target_session_id == filters.training_session_id)
            count_query = count_query.where(StudentApplication.target_session_id == filters.training_session_id)

        if filters.order_by == "created_at":
            statement = statement.order_by(Training.created_at if filters.asc == "asc" else Training.created_at.desc())


        total_count = (await self.session.execute(count_query)).scalar_one()

        statement = statement.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        result = await self.session.execute(statement)
        return result.scalars().all(), total_count
    
    async def delete_student_application(self, application: StudentApplication) -> StudentApplication:
        await self.dissociate_student_attachment(application_id=application.id)
        await self.session.delete(application)
        await self.session.commit()
        return application

    async def enroll_student_to_session(self, application: StudentApplication) -> TrainingSessionParticipant:
        participant = TrainingSessionParticipant(
            session_id=application.target_session_id,
            user_id=application.user_id,
            joined_at=datetime.now(timezone.utc),
        )
        self.session.add(participant)
        # decrement available slots if applicable
        if application.target_session_id is not None:
            stmt = select(TrainingSession).where(TrainingSession.id == application.target_session_id)
            res = await self.session.execute(stmt)
            sess = res.scalars().first()
            if sess and sess.available_slots is not None and sess.available_slots > 0:
                sess.available_slots -= 1
                self.session.add(sess)
        await self.session.commit()
        await self.session.refresh(participant)

        # Enrol on Moodle (best-effort)
        try:
            # Ensure we have moodle course id
            if sess and sess.moodle_course_id:
                # Fetch user for identity
                user_service = UserService(self.session)
                user = await user_service.get_by_id(application.user_id)
                if user and user.email:
                    if moodle_ensure_user_task and moodle_enrol_user_task:
                        # This is best-effort; mapping persistence should be handled after callback, or we could keep it inline
                        moodle_ensure_user_task.apply_async(kwargs={
                            "email": user.email,
                            "firstname": user.first_name,
                            "lastname": user.last_name,
                        })
                        # We cannot know moodle_user_id from task immediately; for idempotency, enrol task can resolve user by email internally if you extend it
                    else:
                        moodle = MoodleService()
                        moodle_user_id = user.moodle_user_id
                        if not moodle_user_id:
                            moodle_user_id = await moodle.ensure_user(
                                email=user.email,
                                firstname=user.first_name,
                                lastname=user.last_name,
                            )
                            # persist mapping
                            user.moodle_user_id = moodle_user_id
                            self.session.add(user)
                            await self.session.commit()
                            await self.session.refresh(user)
                        await moodle.enrol_user_manual(user_id=moodle_user_id, course_id=sess.moodle_course_id)
        except Exception:
            pass
        return participant

    # Attachments
    async def create_student_attachment(self, user_id: str, application_id: int, input : StudentAttachmentInput) -> StudentAttachment:
        # Replace existing attachment of same type
        existing_stmt = (
            select(StudentAttachment)
            .join(StudentApplication, StudentApplication.id == StudentAttachment.application_id)
            .where(StudentApplication.user_id == user_id)
            .where(StudentAttachment.document_type == input.name, StudentAttachment.application_id == application_id))
        existing_res = await self.session.execute(existing_stmt)
        existing = existing_res.scalars().first()
        if existing is not None:
            FileHelper.delete_file(existing.file_path)
            await self.session.delete(existing)
            await self.session.commit()

        url, _, _ = await FileHelper.upload_file(input.file, f"/student-applications/{application_id}", input.name)
        attachment = StudentAttachment(application_id=application_id, file_path=url, document_type=input.name)
        self.session.add(attachment)
        await self.session.commit()
        await self.session.refresh(attachment)
        return attachment

    async def dissociate_student_attachment(self, application_id: int) -> None:
        statement = update(StudentAttachment).where(StudentAttachment.application_id == application_id).values(application_id=None)
        await self.session.execute(statement)
        await self.session.commit()

    async def get_student_attachment_by_id(self, attachment_id: int , user_id : Optional[str]) -> Optional[StudentAttachment]:
        existing_stmt = (
            select(StudentAttachment)
            .join(StudentApplication, StudentApplication.id == StudentAttachment.application_id)
            .where( StudentAttachment.id == attachment_id))
        if user_id is not None:
            existing_stmt = existing_stmt.where(StudentApplication.user_id == user_id)
        result = await self.session.execute(existing_stmt)
        return result.scalars().first()


    async def list_attachments_by_application(self, application_id: int , user_id : Optional[str]) -> List[StudentAttachment]:
        statement = (
            select(StudentAttachment)
            .where(StudentAttachment.application_id == application_id, StudentAttachment.delete_at.is_(None))
            .order_by(StudentAttachment.created_at)
        )
        
        if user_id is not None:
            statement = statement.where(StudentApplication.user_id == user_id)
            
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def delete_student_attachment(self, attachment: StudentAttachment) -> StudentAttachment:
        FileHelper.delete_file(attachment.file_path)
        self.session.delete(attachment)
        await self.session.commit()
        return attachment

    # Specialty CRUD Operations
    async def create_specialty(self, data: SpecialtyCreateInput) -> Specialty:
        """Create a new specialty"""
        specialty = Specialty(**data.model_dump())
        self.session.add(specialty)
        await self.session.commit()
        await self.session.refresh(specialty)
        return specialty

    async def get_specialty_by_id(self, specialty_id: int) -> Optional[Specialty]:
        """Get specialty by ID"""
        statement = select(Specialty).where(
            Specialty.id == specialty_id,
            Specialty.delete_at.is_(None)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_specialty_by_name(self, name: str) -> Optional[Specialty]:
        """Get specialty by name"""
        statement = select(Specialty).where(
            Specialty.name == name,
            Specialty.delete_at.is_(None)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def list_specialties(self, filters: SpecialtyFilter) -> Tuple[List[Specialty], int]:
        """List specialties with pagination and filtering"""
        statement = select(Specialty).where(Specialty.delete_at.is_(None))
        count_query = select(func.count(Specialty.id)).where(Specialty.delete_at.is_(None))

        # Apply search filter
        if filters.search is not None:
            search_filter = or_(
                Specialty.name.contains(filters.search),
                Specialty.description.contains(filters.search)
            )
            statement = statement.where(search_filter)
            count_query = count_query.where(search_filter)

        # Apply ordering
        if filters.order_by == "created_at":
            statement = statement.order_by(
                Specialty.created_at if filters.asc == "asc" else Specialty.created_at.desc()
            )
        elif filters.order_by == "name":
            statement = statement.order_by(
                Specialty.name if filters.asc == "asc" else Specialty.name.desc()
            )

        # Get total count
        total_count = (await self.session.execute(count_query)).scalar_one()

        # Apply pagination
        statement = statement.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        result = await self.session.execute(statement)
        return result.scalars().all(), total_count

    async def update_specialty(self, specialty: Specialty, data: SpecialtyUpdateInput) -> Specialty:
        """Update specialty"""
        for key, value in data.model_dump(exclude_none=True).items():
            setattr(specialty, key, value)
        self.session.add(specialty)
        await self.session.commit()
        await self.session.refresh(specialty)
        return specialty

    async def delete_specialty(self, specialty: Specialty) -> Specialty:
        """Soft delete specialty"""
        specialty.delete_at = datetime.now(timezone.utc)
        self.session.add(specialty)
        await self.session.commit()
        return specialty

    async def get_all_active_specialties(self) -> List[Specialty]:
        """Get all active specialties for dropdown lists"""
        statement = select(Specialty).where(
            Specialty.delete_at.is_(None)
        ).order_by(Specialty.name)
        result = await self.session.execute(statement)
        return result.scalars().all()

    # Reclamation CRUD Operations
    async def create_reclamation(self, data: ReclamationCreateInput, user_id: str) -> Reclamation:
        """Create a new reclamation by user"""
        # Generate reclamation number: REC-{seq}-{YYYYMMDDHHMMSS}
        count_stmt = select(func.count(Reclamation.id))
        count_res = await self.session.execute(count_stmt)
        seq = (count_res.scalar() or 0) + 1
        reclamation_number = f"REC-{seq:04d}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        reclamation = Reclamation(
            reclamation_number=reclamation_number,
            application_number=data.application_number,
            subject=data.subject,
            reclamation_type=data.reclamation_type,
            priority=data.priority,
            description=data.description,
            status=ReclamationStatusEnum.NEW
        )
        self.session.add(reclamation)
        await self.session.commit()
        await self.session.refresh(reclamation)
        return reclamation

    async def get_reclamation_by_id(self, reclamation_id: int, user_id: Optional[str] = None) -> Optional[Reclamation]:
        """Get reclamation by ID, optionally filtered by user"""
        statement = select(Reclamation).where(
            Reclamation.id == reclamation_id,
            Reclamation.delete_at.is_(None)
        )
        
        # If user_id provided, ensure user can only access their own reclamations
        # We need to join with StudentApplication to get user_id
        if user_id is not None:
            from src.api.user.models import User
            statement = (
                statement
                .join(StudentApplication, StudentApplication.application_number == Reclamation.application_number)
                .where(StudentApplication.user_id == user_id)
            )
        
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def list_user_reclamations(self, user_id: str, filters: ReclamationFilter) -> Tuple[List[Reclamation], int]:
        """List reclamations for a specific user with pagination"""
        from src.api.user.models import User
        
        statement = (
            select(Reclamation)
            .join(StudentApplication, StudentApplication.application_number == Reclamation.application_number)
            .where(StudentApplication.user_id == user_id, Reclamation.delete_at.is_(None))
        )
        
        count_query = (
            select(func.count(Reclamation.id))
            .join(StudentApplication, StudentApplication.application_number == Reclamation.application_number)
            .where(StudentApplication.user_id == user_id, Reclamation.delete_at.is_(None))
        )

        # Apply search filter
        if filters.search is not None:
            search_filter = or_(
                Reclamation.subject.contains(filters.search),
                Reclamation.description.contains(filters.search),
                Reclamation.reclamation_number.contains(filters.search),
                Reclamation.application_number.contains(filters.search)
            )
            statement = statement.where(search_filter)
            count_query = count_query.where(search_filter)

        # Apply status filter
        if filters.status is not None:
            statement = statement.where(Reclamation.status == filters.status)
            count_query = count_query.where(Reclamation.status == filters.status)

        # Apply priority filter
        if filters.priority is not None:
            statement = statement.where(Reclamation.priority == filters.priority)
            count_query = count_query.where(Reclamation.priority == filters.priority)

        # Apply ordering
        if filters.order_by == "created_at":
            statement = statement.order_by(
                Reclamation.created_at if filters.asc == "asc" else Reclamation.created_at.desc()
            )
        elif filters.order_by == "subject":
            statement = statement.order_by(
                Reclamation.subject if filters.asc == "asc" else Reclamation.subject.desc()
            )
        elif filters.order_by == "priority":
            statement = statement.order_by(
                Reclamation.priority if filters.asc == "asc" else Reclamation.priority.desc()
            )

        # Get total count
        total_count = (await self.session.execute(count_query)).scalar_one()

        # Apply pagination
        statement = statement.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        result = await self.session.execute(statement)
        return result.scalars().all(), total_count

    async def list_all_reclamations(self, filters: ReclamationFilter) -> Tuple[List[Reclamation], int]:
        """List all reclamations for admin with pagination and filtering"""
        statement = select(Reclamation).where(Reclamation.delete_at.is_(None))
        count_query = select(func.count(Reclamation.id)).where(Reclamation.delete_at.is_(None))

        # Apply search filter
        if filters.search is not None:
            search_filter = or_(
                Reclamation.subject.contains(filters.search),
                Reclamation.description.contains(filters.search),
                Reclamation.reclamation_number.contains(filters.search),
                Reclamation.application_number.contains(filters.search)
            )
            statement = statement.where(search_filter)
            count_query = count_query.where(search_filter)

        # Apply filters
        if filters.status is not None:
            statement = statement.where(Reclamation.status == filters.status)
            count_query = count_query.where(Reclamation.status == filters.status)
            
        if filters.priority is not None:
            statement = statement.where(Reclamation.priority == filters.priority)
            count_query = count_query.where(Reclamation.priority == filters.priority)
            
        if filters.reclamation_type is not None:
            statement = statement.where(Reclamation.reclamation_type == filters.reclamation_type)
            count_query = count_query.where(Reclamation.reclamation_type == filters.reclamation_type)
            
        if filters.admin_id is not None:
            statement = statement.where(Reclamation.admin_id == filters.admin_id)
            count_query = count_query.where(Reclamation.admin_id == filters.admin_id)
            
        if filters.application_number is not None:
            statement = statement.where(Reclamation.application_number == filters.application_number)
            count_query = count_query.where(Reclamation.application_number == filters.application_number)

        # Apply ordering
        if filters.order_by == "created_at":
            statement = statement.order_by(
                Reclamation.created_at if filters.asc == "asc" else Reclamation.created_at.desc()
            )
        elif filters.order_by == "subject":
            statement = statement.order_by(
                Reclamation.subject if filters.asc == "asc" else Reclamation.subject.desc()
            )
        elif filters.order_by == "priority":
            statement = statement.order_by(
                Reclamation.priority if filters.asc == "asc" else Reclamation.priority.desc()
            )

        # Get total count
        total_count = (await self.session.execute(count_query)).scalar_one()

        # Apply pagination
        statement = statement.offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        result = await self.session.execute(statement)
        return result.scalars().all(), total_count

    async def update_reclamation_status(self, reclamation: Reclamation, data: ReclamationAdminUpdateInput) -> Reclamation:
        """Update reclamation status and other admin fields"""
        for key, value in data.model_dump(exclude_none=True).items():
            setattr(reclamation, key, value)
            
        # Set closure date if status is CLOSED
        if data.status == ReclamationStatusEnum.CLOSED:
            reclamation.closure_date = datetime.now(timezone.utc)
            
        self.session.add(reclamation)
        await self.session.commit()
        await self.session.refresh(reclamation)
        return reclamation

    async def delete_reclamation(self, reclamation: Reclamation) -> Reclamation:
        """Soft delete reclamation"""
        reclamation.delete_at = datetime.now(timezone.utc)
        self.session.add(reclamation)
        await self.session.commit()
        return reclamation

    # Reclamation Type Operations
    async def create_reclamation_type(self, data: ReclamationTypeCreateInput) -> ReclamationType:
        """Create a new reclamation type"""
        reclamation_type = ReclamationType(**data.model_dump())
        self.session.add(reclamation_type)
        await self.session.commit()
        await self.session.refresh(reclamation_type)
        return reclamation_type

    async def get_reclamation_type_by_id(self, type_id: int) -> Optional[ReclamationType]:
        """Get reclamation type by ID"""
        statement = select(ReclamationType).where(
            ReclamationType.id == type_id,
            ReclamationType.delete_at.is_(None)
        )
        result = await self.session.execute(statement)
        return result.scalars().first()

    async def get_all_reclamation_types(self) -> List[ReclamationType]:
        """Get all active reclamation types for dropdown lists"""
        statement = select(ReclamationType).where(
            ReclamationType.delete_at.is_(None)
        ).order_by(ReclamationType.name)
        result = await self.session.execute(statement)
        return result.scalars().all()
