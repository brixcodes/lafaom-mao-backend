from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func, and_, or_
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from src.database import get_db
from src.api.user.models import User
from src.api.training.models import Training, TrainingSession, StudentApplication
from src.api.job_offers.models import JobOffer, JobApplication
from src.api.payments.models import Payment, PaymentStatusEnum
from src.api.blog.models import Post
from src.api.training.models import Reclamation
from src.api.auth.dependencies import get_current_user

router = APIRouter()

@router.get("/stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les statistiques générales du dashboard"""
    
    # Statistiques des utilisateurs
    total_users = db.exec(select(func.count(User.id))).first() or 0
    
    # Utilisateurs créés ce mois
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month = db.exec(
        select(func.count(User.id)).where(User.created_at >= start_of_month)
    ).first() or 0
    
    # Utilisateurs actifs (connexion dans les 30 derniers jours)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    active_users = db.exec(
        select(func.count(User.id)).where(
            and_(
                User.last_login.isnot(None),
                User.last_login >= thirty_days_ago
            )
        )
    ).first() or 0
    
    # Calcul du taux de croissance des utilisateurs
    last_month_start = (start_of_month - timedelta(days=1)).replace(day=1)
    users_last_month = db.exec(
        select(func.count(User.id)).where(
            and_(
                User.created_at >= last_month_start,
                User.created_at < start_of_month
            )
        )
    ).first() or 0
    
    user_growth_rate = 0
    if users_last_month > 0:
        user_growth_rate = round(((new_users_this_month - users_last_month) / users_last_month) * 100, 2)
    
    # Statistiques des formations
    total_trainings = db.exec(select(func.count(Training.id))).first() or 0
    active_sessions = db.exec(
        select(func.count(TrainingSession.id)).where(
            TrainingSession.status == "OPEN_FOR_REGISTRATION"
        )
    ).first() or 0
    
    total_applications = db.exec(select(func.count(StudentApplication.id))).first() or 0
    approved_applications = db.exec(
        select(func.count(StudentApplication.id)).where(
            StudentApplication.status == "APPROVED"
        )
    ).first() or 0
    
    completion_rate = 0
    if total_applications > 0:
        completion_rate = round((approved_applications / total_applications) * 100, 2)
    
    # Statistiques des emplois
    total_job_offers = db.exec(select(func.count(JobOffer.id))).first() or 0
    new_job_offers_this_month = db.exec(
        select(func.count(JobOffer.id)).where(JobOffer.created_at >= start_of_month)
    ).first() or 0
    
    total_job_applications = db.exec(select(func.count(JobApplication.id))).first() or 0
    approved_job_applications = db.exec(
        select(func.count(JobApplication.id)).where(
            JobApplication.status == "APPROVED"
        )
    ).first() or 0
    
    placement_rate = 0
    if total_job_applications > 0:
        placement_rate = round((approved_job_applications / total_job_applications) * 100, 2)
    
    # Statistiques des paiements
    total_revenue = db.exec(
        select(func.sum(Payment.product_amount)).where(
            Payment.status == PaymentStatusEnum.ACCEPTED
        )
    ).first() or 0
    
    this_month_revenue = db.exec(
        select(func.sum(Payment.product_amount)).where(
            and_(
                Payment.status == PaymentStatusEnum.ACCEPTED,
                Payment.created_at >= start_of_month
            )
        )
    ).first() or 0
    
    successful_transactions = db.exec(
        select(func.count(Payment.id)).where(
            Payment.status == PaymentStatusEnum.ACCEPTED
        )
    ).first() or 0
    
    pending_transactions = db.exec(
        select(func.count(Payment.id)).where(
            Payment.status == PaymentStatusEnum.PENDING
        )
    ).first() or 0
    
    # Calcul du taux de croissance des revenus
    last_month_revenue = db.exec(
        select(func.sum(Payment.product_amount)).where(
            and_(
                Payment.status == PaymentStatusEnum.ACCEPTED,
                Payment.created_at >= last_month_start,
                Payment.created_at < start_of_month
            )
        )
    ).first() or 0
    
    revenue_growth_rate = 0
    if last_month_revenue > 0:
        revenue_growth_rate = round(((this_month_revenue - last_month_revenue) / last_month_revenue) * 100, 2)
    
    # Statistiques du blog
    total_blog_posts = db.exec(select(func.count(Post.id))).first() or 0
    published_posts = db.exec(
        select(func.count(Post.id)).where(Post.published_at.isnot(None))
    ).first() or 0
    
    # Statistiques des réclamations
    total_reclamations = db.exec(select(func.count(Reclamation.id))).first() or 0
    new_reclamations = db.exec(
        select(func.count(Reclamation.id)).where(Reclamation.status == "NEW")
    ).first() or 0
    
    in_progress_reclamations = db.exec(
        select(func.count(Reclamation.id)).where(Reclamation.status == "IN_PROGRESS")
    ).first() or 0
    
    closed_reclamations = db.exec(
        select(func.count(Reclamation.id)).where(Reclamation.status == "CLOSED")
    ).first() or 0
    
    resolution_rate = 0
    if total_reclamations > 0:
        resolution_rate = round((closed_reclamations / total_reclamations) * 100, 2)
    
    return {
        "users": {
            "total": total_users,
            "new_this_month": new_users_this_month,
            "active": active_users,
            "growth_rate": user_growth_rate
        },
        "trainings": {
            "total": total_trainings,
            "active_sessions": active_sessions,
            "applications": total_applications,
            "completion_rate": completion_rate
        },
        "jobs": {
            "total_offers": total_job_offers,
            "applications": total_job_applications,
            "placement_rate": placement_rate,
            "new_this_month": new_job_offers_this_month
        },
        "payments": {
            "total_revenue": float(total_revenue or 0),
            "this_month_revenue": float(this_month_revenue or 0),
            "successful_transactions": successful_transactions,
            "pending_transactions": pending_transactions,
            "growth_rate": revenue_growth_rate
        },
        "blog": {
            "total_posts": total_blog_posts,
            "published_posts": published_posts,
            "total_views": 0,  # À implémenter si nécessaire
            "engagement_rate": 0  # À implémenter si nécessaire
        },
        "reclamations": {
            "total": total_reclamations,
            "new": new_reclamations,
            "in_progress": in_progress_reclamations,
            "closed": closed_reclamations,
            "resolution_rate": resolution_rate
        }
    }

@router.get("/charts")
async def get_dashboard_charts(
    period: str = "month",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les données pour les graphiques du dashboard"""
    
    # Définir la période
    if period == "week":
        days = 7
    elif period == "month":
        days = 30
    elif period == "year":
        days = 365
    else:
        days = 30
    
    start_date = datetime.now() - timedelta(days=days)
    
    # Données des revenus par jour
    revenue_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        daily_revenue = db.exec(
            select(func.sum(Payment.product_amount)).where(
                and_(
                    Payment.status == PaymentStatusEnum.ACCEPTED,
                    Payment.created_at >= date,
                    Payment.created_at < next_date
                )
            )
        ).first() or 0
        
        revenue_data.append({
            "date": date.strftime("%Y-%m-%d"),
            "amount": float(daily_revenue or 0)
        })
    
    # Données des inscriptions utilisateurs par jour
    user_registrations = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        daily_registrations = db.exec(
            select(func.count(User.id)).where(
                and_(
                    User.created_at >= date,
                    User.created_at < next_date
                )
            )
        ).first() or 0
        
        user_registrations.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": daily_registrations
        })
    
    # Données des candidatures formations par jour
    training_applications = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        daily_applications = db.exec(
            select(func.count(StudentApplication.id)).where(
                and_(
                    StudentApplication.created_at >= date,
                    StudentApplication.created_at < next_date
                )
            )
        ).first() or 0
        
        training_applications.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": daily_applications
        })
    
    # Données des candidatures emplois par jour
    job_applications = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        daily_job_applications = db.exec(
            select(func.count(JobApplication.id)).where(
                and_(
                    JobApplication.created_at >= date,
                    JobApplication.created_at < next_date
                )
            )
        ).first() or 0
        
        job_applications.append({
            "date": date.strftime("%Y-%m-%d"),
            "count": daily_job_applications
        })
    
    return {
        "revenue_trend": revenue_data,
        "user_registrations": user_registrations,
        "training_applications": training_applications,
        "job_applications": job_applications
    }

@router.get("/activities")
async def get_recent_activities(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les activités récentes"""
    
    activities = []
    
    # Récupérer les utilisateurs récents
    recent_users = db.exec(
        select(User).order_by(User.created_at.desc()).limit(5)
    ).all()
    
    for user in recent_users:
        activities.append({
            "id": f"user_{user.id}",
            "type": "user",
            "title": f"Nouvel utilisateur: {user.first_name} {user.last_name}",
            "description": f"Email: {user.email}",
            "timestamp": user.created_at.isoformat(),
            "status": user.status
        })
    
    # Récupérer les candidatures formations récentes
    recent_training_applications = db.exec(
        select(StudentApplication).order_by(StudentApplication.created_at.desc()).limit(5)
    ).all()
    
    for app in recent_training_applications:
        activities.append({
            "id": f"training_app_{app.id}",
            "type": "training",
            "title": f"Nouvelle candidature formation",
            "description": f"Numéro: {app.application_number}",
            "timestamp": app.created_at.isoformat(),
            "status": app.status
        })
    
    # Récupérer les candidatures emplois récentes
    recent_job_applications = db.exec(
        select(JobApplication).order_by(JobApplication.created_at.desc()).limit(5)
    ).all()
    
    for app in recent_job_applications:
        activities.append({
            "id": f"job_app_{app.id}",
            "type": "job",
            "title": f"Nouvelle candidature emploi",
            "description": f"Nom: {app.first_name} {app.last_name}",
            "timestamp": app.created_at.isoformat(),
            "status": app.status
        })
    
    # Récupérer les paiements récents
    recent_payments = db.exec(
        select(Payment).order_by(Payment.created_at.desc()).limit(5)
    ).all()
    
    for payment in recent_payments:
        activities.append({
            "id": f"payment_{payment.id}",
            "type": "payment",
            "title": f"Nouveau paiement",
            "description": f"Montant: {payment.product_amount} {payment.product_currency}",
            "timestamp": payment.created_at.isoformat(),
            "status": payment.status,
            "amount": payment.product_amount
        })
    
    # Trier par timestamp et limiter
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    return activities[:limit]

@router.get("/alerts")
async def get_dashboard_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les alertes du dashboard"""
    
    alerts = []
    
    # Alertes pour les paiements en attente
    pending_payments = db.exec(
        select(func.count(Payment.id)).where(
            Payment.status == PaymentStatusEnum.PENDING
        )
    ).first() or 0
    
    if pending_payments > 0:
        alerts.append({
            "id": "pending_payments",
            "type": "warning",
            "title": "Paiements en attente",
            "message": f"{pending_payments} paiement(s) en attente de traitement",
            "action_required": True,
            "created_at": datetime.now().isoformat()
        })
    
    # Alertes pour les réclamations non traitées
    new_reclamations = db.exec(
        select(func.count(Reclamation.id)).where(Reclamation.status == "NEW")
    ).first() or 0
    
    if new_reclamations > 0:
        alerts.append({
            "id": "new_reclamations",
            "type": "error",
            "title": "Nouvelles réclamations",
            "message": f"{new_reclamations} réclamation(s) non traitée(s)",
            "action_required": True,
            "created_at": datetime.now().isoformat()
        })
    
    # Alertes pour les sessions de formation qui se terminent bientôt
    upcoming_sessions = db.exec(
        select(func.count(TrainingSession.id)).where(
            and_(
                TrainingSession.end_date.isnot(None),
                TrainingSession.end_date <= datetime.now() + timedelta(days=7),
                TrainingSession.status == "ONGOING"
            )
        )
    ).first() or 0
    
    if upcoming_sessions > 0:
        alerts.append({
            "id": "upcoming_sessions",
            "type": "info",
            "title": "Sessions se terminant bientôt",
            "message": f"{upcoming_sessions} session(s) se termine(nt) dans les 7 prochains jours",
            "action_required": False,
            "created_at": datetime.now().isoformat()
        })
    
    return alerts
