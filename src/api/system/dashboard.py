from fastapi import APIRouter, Depends
from sqlmodel import select, func, and_, or_
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session_async

router = APIRouter()

@router.get("/comprehensive-stats")
async def get_comprehensive_statistics(
    db: AsyncSession = Depends(get_session_async)
):
    """Récupérer toutes les statistiques du système"""
    
    # ===== STATISTIQUES UTILISATEURS =====
    # Import dynamique pour éviter les problèmes de dépendances
    from src.api.user.models import User, Role, UserRole
    
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    # Utilisateurs par statut
    users_by_status = {}
    for status in ["active", "inactive", "blocked", "deleted"]:
        result = await db.execute(
            select(func.count(User.id)).where(User.status == status)
        )
        users_by_status[status] = result.scalar() or 0
    
    # Utilisateurs par type
    user_types_result = await db.execute(
        select(User.user_type, func.count(User.id))
        .group_by(User.user_type)
    )
    user_types = {user_type: count for user_type, count in user_types_result.all()}
    
    # Utilisateurs par pays
    users_by_country_result = await db.execute(
        select(User.country_code, func.count(User.id))
        .where(User.country_code.isnot(None))
        .group_by(User.country_code)
    )
    users_by_country = {country: count for country, count in users_by_country_result.all()}
    
    # Utilisateurs avec 2FA activé
    two_factor_enabled_result = await db.execute(
        select(func.count(User.id)).where(User.two_factor_enabled == True)
    )
    two_factor_enabled = two_factor_enabled_result.scalar() or 0
    
    # Utilisateurs créés ce mois
    this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= this_month_start)
    )
    new_users_this_month = new_users_this_month_result.scalar() or 0
    
    # ===== STATISTIQUES FORMATIONS =====
    try:
        from src.api.training.models import Training, TrainingSession, TrainingSessionParticipant, StudentApplication, Specialty
        
        # Formations actives/inactives
        active_trainings_result = await db.execute(
            select(func.count(Training.id)).where(Training.status == "ACTIVE")
        )
        active_trainings = active_trainings_result.scalar() or 0
        
        inactive_trainings_result = await db.execute(
            select(func.count(Training.id)).where(Training.status == "INACTIVE")
        )
        inactive_trainings = inactive_trainings_result.scalar() or 0
        
        # Sessions de formation par statut
        sessions_by_status = {}
        for status in ["OPEN_FOR_REGISTRATION", "CLOSE_FOR_REGISTRATION", "ONGOING", "COMPLETED"]:
            result = await db.execute(
                select(func.count(TrainingSession.id)).where(TrainingSession.status == status)
            )
            sessions_by_status[status] = result.scalar() or 0
        
        # Candidats par session active
        active_sessions_result = await db.execute(
            select(TrainingSession.id, func.count(TrainingSessionParticipant.id))
            .join(TrainingSessionParticipant, TrainingSession.id == TrainingSessionParticipant.session_id)
            .where(TrainingSession.status == "OPEN_FOR_REGISTRATION")
            .group_by(TrainingSession.id)
        )
        candidates_per_active_session = {session_id: count for session_id, count in active_sessions_result.all()}
        
        # Total candidatures aux formations
        total_applications_result = await db.execute(select(func.count(StudentApplication.id)))
        total_applications = total_applications_result.scalar() or 0
        
        # Candidatures par statut
        applications_by_status = {}
        for status in ["RECEIVED", "SUBMITTED", "REFUSED", "APPROVED"]:
            result = await db.execute(
                select(func.count(StudentApplication.id)).where(StudentApplication.status == status)
            )
            applications_by_status[status] = result.scalar() or 0
        
        # ===== STATISTIQUES SPÉCIALITÉS =====
        total_specialties_result = await db.execute(select(func.count(Specialty.id)))
        total_specialties = total_specialties_result.scalar() or 0
        
        # Formations par spécialité
        trainings_by_specialty_result = await db.execute(
            select(Specialty.name, func.count(Training.id))
            .join(Training, Specialty.id == Training.specialty_id)
            .group_by(Specialty.name)
        )
        trainings_by_specialty = {specialty: count for specialty, count in trainings_by_specialty_result.all()}
        
        # Nouvelles formations ce mois
        new_trainings_this_month_result = await db.execute(
            select(func.count(Training.id)).where(Training.created_at >= this_month_start)
        )
        new_trainings_this_month = new_trainings_this_month_result.scalar() or 0
        
        # Nouvelles sessions ce mois
        new_sessions_this_month_result = await db.execute(
            select(func.count(TrainingSession.id)).where(TrainingSession.created_at >= this_month_start)
        )
        new_sessions_this_month = new_sessions_this_month_result.scalar() or 0
        
    except ImportError:
        # Si les imports échouent, on retourne des valeurs par défaut
        active_trainings = inactive_trainings = 0
        sessions_by_status = {}
        candidates_per_active_session = {}
        total_applications = 0
        applications_by_status = {}
        total_specialties = 0
        trainings_by_specialty = {}
        new_trainings_this_month = new_sessions_this_month = 0
    
    # ===== STATISTIQUES CENTRES DE FORMATION =====
    try:
        from src.api.system.models import OrganizationCenter
        
        total_centers_result = await db.execute(select(func.count(OrganizationCenter.id)))
        total_centers = total_centers_result.scalar() or 0
        
        # Centres par statut
        centers_by_status = {}
        for status in ["active", "inactive", "suspended", "deleted"]:
            result = await db.execute(
                select(func.count(OrganizationCenter.id)).where(OrganizationCenter.status == status)
            )
            centers_by_status[status] = result.scalar() or 0
        
        # Centres par type
        centers_by_type_result = await db.execute(
            select(OrganizationCenter.organization_type, func.count(OrganizationCenter.id))
            .group_by(OrganizationCenter.organization_type)
        )
        centers_by_type = {org_type: count for org_type, count in centers_by_type_result.all()}
        
    except ImportError:
        total_centers = 0
        centers_by_status = {}
        centers_by_type = {}
    
    # ===== STATISTIQUES ARTICLES/BLOG =====
    try:
        from src.api.blog.models import Post, PostCategory
        
        total_posts_result = await db.execute(select(func.count(Post.id)))
        total_posts = total_posts_result.scalar() or 0
        
        # Articles publiés vs brouillons
        published_posts_result = await db.execute(
            select(func.count(Post.id)).where(Post.published_at.isnot(None))
        )
        published_posts = published_posts_result.scalar() or 0
        
        draft_posts = total_posts - published_posts
        
        # Articles par catégorie
        posts_by_category_result = await db.execute(
            select(PostCategory.title, func.count(Post.id))
            .join(Post, PostCategory.id == Post.category_id)
            .group_by(PostCategory.title)
        )
        posts_by_category = {category: count for category, count in posts_by_category_result.all()}
        
        # Articles créés ce mois
        posts_this_month_result = await db.execute(
            select(func.count(Post.id)).where(Post.created_at >= this_month_start)
        )
        posts_this_month = posts_this_month_result.scalar() or 0
        
    except ImportError:
        total_posts = published_posts = draft_posts = posts_this_month = 0
        posts_by_category = {}
    
    # ===== STATISTIQUES OFFRES D'EMPLOI =====
    try:
        from src.api.job_offers.models import JobOffer, JobApplication
        
        total_job_offers_result = await db.execute(select(func.count(JobOffer.id)))
        total_job_offers = total_job_offers_result.scalar() or 0
        
        # Offres disponibles vs indisponibles (basé sur la date limite)
        today = datetime.now().date()
        available_offers_result = await db.execute(
            select(func.count(JobOffer.id)).where(JobOffer.submission_deadline >= today)
        )
        available_offers = available_offers_result.scalar() or 0
        
        unavailable_offers = total_job_offers - available_offers
        
        # Offres par type de contrat
        offers_by_contract_result = await db.execute(
            select(JobOffer.contract_type, func.count(JobOffer.id))
            .group_by(JobOffer.contract_type)
        )
        offers_by_contract = {contract_type: count for contract_type, count in offers_by_contract_result.all()}
        
        # Total candidatures aux offres
        total_job_applications_result = await db.execute(select(func.count(JobApplication.id)))
        total_job_applications = total_job_applications_result.scalar() or 0
        
        # Candidatures par statut
        job_applications_by_status = {}
        for status in ["RECEIVED", "REFUSED", "APPROVED"]:
            result = await db.execute(
                select(func.count(JobApplication.id)).where(JobApplication.status == status)
            )
            job_applications_by_status[status] = result.scalar() or 0
        
        # Nouvelles offres ce mois
        new_job_offers_this_month_result = await db.execute(
            select(func.count(JobOffer.id)).where(JobOffer.created_at >= this_month_start)
        )
        new_job_offers_this_month = new_job_offers_this_month_result.scalar() or 0
        
    except ImportError:
        total_job_offers = available_offers = unavailable_offers = 0
        offers_by_contract = {}
        total_job_applications = 0
        job_applications_by_status = {}
        new_job_offers_this_month = 0
    
    # ===== STATISTIQUES RÉCLAMATIONS =====
    try:
        from src.api.training.models import Reclamation
        
        total_reclamations_result = await db.execute(select(func.count(Reclamation.id)))
        total_reclamations = total_reclamations_result.scalar() or 0
        
        # Réclamations par statut
        reclamations_by_status = {}
        for status in ["NEW", "IN_PROGRESS", "CLOSED"]:
            result = await db.execute(
                select(func.count(Reclamation.id)).where(Reclamation.status == status)
            )
            reclamations_by_status[status] = result.scalar() or 0
        
        # Réclamations par priorité
        reclamations_by_priority_result = await db.execute(
            select(Reclamation.priority, func.count(Reclamation.id))
            .group_by(Reclamation.priority)
        )
        reclamations_by_priority = {priority: count for priority, count in reclamations_by_priority_result.all()}
        
    except ImportError:
        total_reclamations = 0
        reclamations_by_status = {}
        reclamations_by_priority = {}
    
    # ===== STATISTIQUES PAIEMENTS =====
    try:
        from src.api.payments.models import Payment, CinetPayPayment
        
        total_payments_result = await db.execute(select(func.count(Payment.id)))
        total_payments = total_payments_result.scalar() or 0
        
        # Paiements par statut
        payments_by_status = {}
        for status in ["pending", "accepted", "refused", "cancelled", "error", "rembourse"]:
            result = await db.execute(
                select(func.count(Payment.id)).where(Payment.status == status)
            )
            payments_by_status[status] = result.scalar() or 0
        
        # Paiements CinetPay
        total_cinetpay_result = await db.execute(select(func.count(CinetPayPayment.id)))
        total_cinetpay = total_cinetpay_result.scalar() or 0
        
    except ImportError:
        total_payments = 0
        payments_by_status = {}
        total_cinetpay = 0
    
    return {
        "users": {
            "total": total_users,
            "by_status": users_by_status,
            "by_type": user_types,
            "by_country": users_by_country,
            "two_factor_enabled": two_factor_enabled,
            "new_this_month": new_users_this_month
        },
        "trainings": {
            "total_active": active_trainings,
            "total_inactive": inactive_trainings,
            "sessions_by_status": sessions_by_status,
            "candidates_per_active_session": candidates_per_active_session,
            "new_this_month": new_trainings_this_month
        },
        "applications": {
            "total_training_applications": total_applications,
            "training_applications_by_status": applications_by_status,
            "total_job_applications": total_job_applications,
            "job_applications_by_status": job_applications_by_status
        },
        "specialties": {
            "total": total_specialties,
            "trainings_by_specialty": trainings_by_specialty
        },
        "centers": {
            "total": total_centers,
            "by_status": centers_by_status,
            "by_type": centers_by_type
        },
        "blog": {
            "total_posts": total_posts,
            "published_posts": published_posts,
            "draft_posts": draft_posts,
            "by_category": posts_by_category,
            "new_this_month": posts_this_month
        },
        "job_offers": {
            "total": total_job_offers,
            "available": available_offers,
            "unavailable": unavailable_offers,
            "by_contract_type": offers_by_contract,
            "new_this_month": new_job_offers_this_month
        },
        "reclamations": {
            "total": total_reclamations,
            "by_status": reclamations_by_status,
            "by_priority": reclamations_by_priority
        },
        "payments": {
            "total_payments": total_payments,
            "by_status": payments_by_status,
            "total_cinetpay": total_cinetpay
        },
        "sessions": {
            "new_this_month": new_sessions_this_month
        }
    }

@router.get("/payment-stats")
async def get_payment_statistics(
    db: AsyncSession = Depends(get_session_async)
):
    """Récupérer toutes les statistiques détaillées sur les paiements"""
    
    # ===== STATISTIQUES PAIEMENTS GÉNÉRAUX =====
    try:
        from src.api.payments.models import Payment, CinetPayPayment
        
        # Total des paiements
        total_payments_result = await db.execute(select(func.count(Payment.id)))
        total_payments = total_payments_result.scalar() or 0
        
        # Paiements par statut
        payments_by_status = {}
        for status in ["pending", "accepted", "refused", "cancelled", "error", "rembourse"]:
            result = await db.execute(
                select(func.count(Payment.id)).where(Payment.status == status)
            )
            payments_by_status[status] = result.scalar() or 0
        
        # Montants totaux par statut
        amounts_by_status = {}
        for status in ["pending", "accepted", "refused", "cancelled", "error", "rembourse"]:
            result = await db.execute(
                select(func.sum(Payment.product_amount)).where(Payment.status == status)
            )
            amounts_by_status[status] = float(result.scalar() or 0)
        
        # Paiements par devise
        payments_by_currency_result = await db.execute(
            select(Payment.product_currency, func.count(Payment.id), func.sum(Payment.product_amount))
            .group_by(Payment.product_currency)
        )
        payments_by_currency = {}
        for currency, count, total_amount in payments_by_currency_result.all():
            payments_by_currency[currency] = {
                "count": count,
                "total_amount": float(total_amount or 0)
            }
        
        # Paiements par méthode
        payments_by_method_result = await db.execute(
            select(Payment.payment_type, func.count(Payment.id), func.sum(Payment.product_amount))
            .group_by(Payment.payment_type)
        )
        payments_by_method = {}
        for method, count, total_amount in payments_by_method_result.all():
            payments_by_method[method] = {
                "count": count,
                "total_amount": float(total_amount or 0)
            }
        
        # Paiements CinetPay
        total_cinetpay_result = await db.execute(select(func.count(CinetPayPayment.id)))
        total_cinetpay = total_cinetpay_result.scalar() or 0
        
        # CinetPay par statut
        cinetpay_by_status = {}
        for status in ["pending", "accepted", "refused", "cancelled", "error", "rembourse"]:
            result = await db.execute(
                select(func.count(CinetPayPayment.id)).where(CinetPayPayment.status == status)
            )
            cinetpay_by_status[status] = result.scalar() or 0
        
        # Montants CinetPay par statut
        cinetpay_amounts_by_status = {}
        for status in ["pending", "accepted", "refused", "cancelled", "error", "rembourse"]:
            result = await db.execute(
                select(func.sum(CinetPayPayment.amount)).where(CinetPayPayment.status == status)
            )
            cinetpay_amounts_by_status[status] = float(result.scalar() or 0)
        
        # Paiements par devise CinetPay
        cinetpay_by_currency_result = await db.execute(
            select(CinetPayPayment.currency, func.count(CinetPayPayment.id), func.sum(CinetPayPayment.amount))
            .group_by(CinetPayPayment.currency)
        )
        cinetpay_by_currency = {}
        for currency, count, total_amount in cinetpay_by_currency_result.all():
            cinetpay_by_currency[currency] = {
                "count": count,
                "total_amount": float(total_amount or 0)
            }
        
        # Paiements par méthode CinetPay
        cinetpay_by_method_result = await db.execute(
            select(CinetPayPayment.payment_method, func.count(CinetPayPayment.id), func.sum(CinetPayPayment.amount))
            .where(CinetPayPayment.payment_method.isnot(None))
            .group_by(CinetPayPayment.payment_method)
        )
        cinetpay_by_method = {}
        for method, count, total_amount in cinetpay_by_method_result.all():
            cinetpay_by_method[method] = {
                "count": count,
                "total_amount": float(total_amount or 0)
            }
        
    except ImportError:
        total_payments = 0
        payments_by_status = {}
        amounts_by_status = {}
        payments_by_currency = {}
        payments_by_method = {}
        total_cinetpay = 0
        cinetpay_by_status = {}
        cinetpay_amounts_by_status = {}
        cinetpay_by_currency = {}
        cinetpay_by_method = {}
    
    # ===== STATISTIQUES PAIEMENTS FORMATIONS =====
    try:
        from src.api.training.models import StudentApplication, TrainingFeeInstallmentPayment
        
        # Candidatures avec paiements
        applications_with_payment_result = await db.execute(
            select(func.count(StudentApplication.id)).where(StudentApplication.payment_id.isnot(None))
        )
        applications_with_payment = applications_with_payment_result.scalar() or 0
        
        # Candidatures sans paiement
        applications_without_payment_result = await db.execute(
            select(func.count(StudentApplication.id)).where(StudentApplication.payment_id.is_(None))
        )
        applications_without_payment = applications_without_payment_result.scalar() or 0
        
        # Montants totaux des frais d'étude de dossier (tous statuts confondus)
        total_registration_fees_result = await db.execute(
            select(func.sum(StudentApplication.registration_fee))
        )
        total_registration_fees = float(total_registration_fees_result.scalar() or 0)
        
        # Montants totaux des frais de formation (tous statuts confondus)
        total_training_fees_result = await db.execute(
            select(func.sum(StudentApplication.training_fee))
        )
        total_training_fees = float(total_training_fees_result.scalar() or 0)
        
        # Montants des frais d'inscription par statut de candidature
        registration_fees_by_status = {}
        for status in ["RECEIVED", "SUBMITTED", "REFUSED", "APPROVED"]:
            result = await db.execute(
                select(func.sum(StudentApplication.registration_fee)).where(StudentApplication.status == status)
            )
            registration_fees_by_status[status] = float(result.scalar() or 0)
        
        # Montants des frais de formation par statut de candidature
        training_fees_by_status = {}
        for status in ["RECEIVED", "SUBMITTED", "REFUSED", "APPROVED"]:
            result = await db.execute(
                select(func.sum(StudentApplication.training_fee)).where(StudentApplication.status == status)
            )
            training_fees_by_status[status] = float(result.scalar() or 0)
        
        # Candidatures par devise
        applications_by_currency_result = await db.execute(
            select(StudentApplication.currency, func.count(StudentApplication.id), 
                   func.sum(StudentApplication.registration_fee), func.sum(StudentApplication.training_fee))
            .group_by(StudentApplication.currency)
        )
        applications_by_currency = {}
        for currency, count, reg_fee, train_fee in applications_by_currency_result.all():
            applications_by_currency[currency] = {
                "count": count,
                "total_registration_fee": float(reg_fee or 0),
                "total_training_fee": float(train_fee or 0)
            }
        
        # Paiements échelonnés
        total_installments_result = await db.execute(select(func.count(TrainingFeeInstallmentPayment.id)))
        total_installments = total_installments_result.scalar() or 0
        
        # Montant total des échéances
        total_installment_amount_result = await db.execute(select(func.sum(TrainingFeeInstallmentPayment.amount)))
        total_installment_amount = float(total_installment_amount_result.scalar() or 0)
        
        # Reste à payer total
        total_remaining_result = await db.execute(select(func.sum(TrainingFeeInstallmentPayment.rest_to_pay)))
        total_remaining = float(total_remaining_result.scalar() or 0)
        
        # Échéances par devise
        installments_by_currency_result = await db.execute(
            select(TrainingFeeInstallmentPayment.currency, func.count(TrainingFeeInstallmentPayment.id),
                   func.sum(TrainingFeeInstallmentPayment.amount), func.sum(TrainingFeeInstallmentPayment.rest_to_pay))
            .group_by(TrainingFeeInstallmentPayment.currency)
        )
        installments_by_currency = {}
        for currency, count, total_amount, remaining in installments_by_currency_result.all():
            installments_by_currency[currency] = {
                "count": count,
                "total_amount": float(total_amount or 0),
                "remaining": float(remaining or 0)
            }
        
    except ImportError:
        applications_with_payment = applications_without_payment = 0
        total_registration_fees = total_training_fees = 0.0
        registration_fees_by_status = {}
        training_fees_by_status = {}
        applications_by_currency = {}
        total_installments = 0
        total_installment_amount = total_remaining = 0.0
        installments_by_currency = {}
    
    # ===== STATISTIQUES PAIEMENTS OFFRES D'EMPLOI =====
    try:
        from src.api.job_offers.models import JobApplication
        
        # Candidatures avec paiements
        job_applications_with_payment_result = await db.execute(
            select(func.count(JobApplication.id)).where(JobApplication.payment_id.isnot(None))
        )
        job_applications_with_payment = job_applications_with_payment_result.scalar() or 0
        
        # Candidatures sans paiement
        job_applications_without_payment_result = await db.execute(
            select(func.count(JobApplication.id)).where(JobApplication.payment_id.is_(None))
        )
        job_applications_without_payment = job_applications_without_payment_result.scalar() or 0
        
        # Montant total des frais de soumission (tous statuts confondus)
        total_submission_fees_result = await db.execute(
            select(func.sum(JobApplication.submission_fee))
        )
        total_submission_fees = float(total_submission_fees_result.scalar() or 0)
        
        # Frais de soumission par statut
        submission_fees_by_status = {}
        for status in ["RECEIVED", "REFUSED", "APPROVED"]:
            result = await db.execute(
                select(func.sum(JobApplication.submission_fee)).where(JobApplication.status == status)
            )
            submission_fees_by_status[status] = float(result.scalar() or 0)
        
        # Candidatures par devise
        job_applications_by_currency_result = await db.execute(
            select(JobApplication.currency, func.count(JobApplication.id), func.sum(JobApplication.submission_fee))
            .group_by(JobApplication.currency)
        )
        job_applications_by_currency = {}
        for currency, count, total_fee in job_applications_by_currency_result.all():
            job_applications_by_currency[currency] = {
                "count": count,
                "total_submission_fee": float(total_fee or 0)
            }
        
    except ImportError:
        job_applications_with_payment = job_applications_without_payment = 0
        total_submission_fees = 0.0
        submission_fees_by_status = {}
        job_applications_by_currency = {}
    
    # ===== STATISTIQUES TEMPORELLES =====
    this_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_week_start = datetime.now() - timedelta(days=7)
    
    try:
        # Paiements ce mois
        payments_this_month_result = await db.execute(
            select(func.count(Payment.id), func.sum(Payment.product_amount))
            .where(Payment.created_at >= this_month_start)
        )
        payments_this_month_count, payments_this_month_amount = payments_this_month_result.first()
        payments_this_month_amount = float(payments_this_month_amount or 0)
        
        # Paiements cette semaine
        payments_this_week_result = await db.execute(
            select(func.count(Payment.id), func.sum(Payment.product_amount))
            .where(Payment.created_at >= this_week_start)
        )
        payments_this_week_count, payments_this_week_amount = payments_this_week_result.first()
        payments_this_week_amount = float(payments_this_week_amount or 0)
        
        # CinetPay ce mois
        cinetpay_this_month_result = await db.execute(
            select(func.count(CinetPayPayment.id), func.sum(CinetPayPayment.amount))
            .where(CinetPayPayment.created_at >= this_month_start)
        )
        cinetpay_this_month_count, cinetpay_this_month_amount = cinetpay_this_month_result.first()
        cinetpay_this_month_amount = float(cinetpay_this_month_amount or 0)
        
    except ImportError:
        payments_this_month_count = payments_this_month_amount = 0
        payments_this_week_count = payments_this_week_amount = 0
        cinetpay_this_month_count = cinetpay_this_month_amount = 0
    
    return {
        "general_payments": {
            "total_payments": total_payments,
            "by_status": payments_by_status,
            "amounts_by_status": amounts_by_status,
            "by_currency": payments_by_currency,
            "by_method": payments_by_method,
            "this_month": {
                "count": payments_this_month_count,
                "amount": payments_this_month_amount
            },
            "this_week": {
                "count": payments_this_week_count,
                "amount": payments_this_week_amount
            }
        },
        "cinetpay_payments": {
            "total": total_cinetpay,
            "by_status": cinetpay_by_status,
            "amounts_by_status": cinetpay_amounts_by_status,
            "by_currency": cinetpay_by_currency,
            "by_method": cinetpay_by_method,
            "this_month": {
                "count": cinetpay_this_month_count,
                "amount": cinetpay_this_month_amount
            }
        },
        "training_payments": {
            "applications_with_payment": applications_with_payment,
            "applications_without_payment": applications_without_payment,
            "total_registration_fees": total_registration_fees,
            "total_training_fees": total_training_fees,
            "registration_fees_by_status": registration_fees_by_status,
            "training_fees_by_status": training_fees_by_status,
            "by_currency": applications_by_currency,
            "installments": {
                "total_installments": total_installments,
                "total_amount": total_installment_amount,
                "total_remaining": total_remaining,
                "by_currency": installments_by_currency
            }
        },
        "job_payments": {
            "applications_with_payment": job_applications_with_payment,
            "applications_without_payment": job_applications_without_payment,
            "total_submission_fees": total_submission_fees,
            "submission_fees_by_status": submission_fees_by_status,
            "by_currency": job_applications_by_currency
        }
    }