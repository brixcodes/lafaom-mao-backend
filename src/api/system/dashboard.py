from fastapi import APIRouter, Depends
from sqlmodel import select, func, and_
from datetime import datetime, timedelta
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.database import get_session_async
from src.api.user.models import User, Role, UserRole

router = APIRouter()

@router.get("/users-stats")
async def get_users_statistics(
    db: AsyncSession = Depends(get_session_async)
):
    """Récupérer les statistiques détaillées des utilisateurs par rôles et statuts"""
    
    # Statistiques générales
    total_users_result = await db.execute(select(func.count(User.id)))
    total_users = total_users_result.scalar() or 0
    
    # Utilisateurs actifs vs inactifs
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == "ACTIVE")
    )
    active_users = active_users_result.scalar() or 0
    
    inactive_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == "INACTIVE")
    )
    inactive_users = inactive_users_result.scalar() or 0
    
    pending_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == "PENDING")
    )
    pending_users = pending_users_result.scalar() or 0
    
    # Utilisateurs avec connexion récente (30 derniers jours)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_login_users_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.last_login.isnot(None),
                User.last_login >= thirty_days_ago
            )
        )
    )
    recent_login_users = recent_login_users_result.scalar() or 0
    
    # Utilisateurs créés ce mois
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_users_this_month_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= start_of_month)
    )
    new_users_this_month = new_users_this_month_result.scalar() or 0
    
    # Statistiques par rôles
    roles_stats = []
    all_roles_result = await db.execute(select(Role))
    all_roles = all_roles_result.scalars().all()
    
    for role in all_roles:
        # Nombre d'utilisateurs par rôle
        users_count_result = await db.execute(
            select(func.count(User.id))
            .join(UserRole, User.id == UserRole.user_id)
            .where(UserRole.role_id == role.id)
        )
        users_count = users_count_result.scalar() or 0
        
        # Utilisateurs actifs par rôle
        active_count_result = await db.execute(
            select(func.count(User.id))
            .join(UserRole, User.id == UserRole.user_id)
            .where(
                and_(
                    UserRole.role_id == role.id,
                    User.status == "ACTIVE"
                )
            )
        )
        active_count = active_count_result.scalar() or 0
        
        # Utilisateurs avec connexion récente par rôle
        recent_login_count_result = await db.execute(
            select(func.count(User.id))
            .join(UserRole, User.id == UserRole.user_id)
            .where(
                and_(
                    UserRole.role_id == role.id,
                    User.last_login.isnot(None),
                    User.last_login >= thirty_days_ago
                )
            )
        )
        recent_login_count = recent_login_count_result.scalar() or 0
        
        roles_stats.append({
            "role_id": role.id,
            "role_name": role.name,
            "role_description": role.description,
            "total_users": users_count,
            "active_users": active_count,
            "recent_login_users": recent_login_count,
            "inactive_users": users_count - active_count
        })
    
    # Statistiques par statut
    status_stats = {
        "ACTIVE": active_users,
        "INACTIVE": inactive_users,
        "PENDING": pending_users
    }
    
    # Répartition géographique (si les utilisateurs ont des adresses)
    geographic_stats = {
        "by_country": {},
        "by_city": {}
    }
    
    # Utilisateurs par pays
    users_by_country_result = await db.execute(
        select(User.country_code, func.count(User.id))
        .where(User.country_code.isnot(None))
        .group_by(User.country_code)
    )
    users_by_country = users_by_country_result.all()
    
    for country_code, count in users_by_country:
        geographic_stats["by_country"][country_code] = count
    
    # Utilisateurs par ville
    users_by_city_result = await db.execute(
        select(User.city, func.count(User.id))
        .where(User.city.isnot(None))
        .group_by(User.city)
    )
    users_by_city = users_by_city_result.all()
    
    for city, count in users_by_city:
        geographic_stats["by_city"][city] = count
    
    # Statistiques temporelles
    new_this_week_result = await db.execute(
        select(func.count(User.id)).where(
            User.created_at >= datetime.now() - timedelta(days=7)
        )
    )
    new_this_week = new_this_week_result.scalar() or 0
    
    new_today_result = await db.execute(
        select(func.count(User.id)).where(
            User.created_at >= datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        )
    )
    new_today = new_today_result.scalar() or 0
    
    temporal_stats = {
        "new_this_month": new_users_this_month,
        "new_this_week": new_this_week,
        "new_today": new_today
    }
    
    # Utilisateurs avec 2FA activé
    two_fa_enabled_result = await db.execute(
        select(func.count(User.id)).where(User.two_factor_enabled == True)
    )
    two_fa_enabled = two_fa_enabled_result.scalar() or 0
    
    # Utilisateurs avec email vérifié
    email_verified_result = await db.execute(
        select(func.count(User.id)).where(User.email_verified == True)
    )
    email_verified = email_verified_result.scalar() or 0
    
    # Taux de conversion (utilisateurs actifs / total)
    conversion_rate = 0
    if total_users > 0:
        conversion_rate = round((active_users / total_users) * 100, 2)
    
    # Taux d'engagement (connexions récentes / total)
    engagement_rate = 0
    if total_users > 0:
        engagement_rate = round((recent_login_users / total_users) * 100, 2)
    
    return {
        "overview": {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "pending_users": pending_users,
            "recent_login_users": recent_login_users,
            "conversion_rate": conversion_rate,
            "engagement_rate": engagement_rate
        },
        "by_status": status_stats,
        "by_roles": roles_stats,
        "geographic": geographic_stats,
        "temporal": temporal_stats,
        "security": {
            "two_fa_enabled": two_fa_enabled,
            "email_verified": email_verified,
            "two_fa_rate": round((two_fa_enabled / total_users) * 100, 2) if total_users > 0 else 0,
            "email_verification_rate": round((email_verified / total_users) * 100, 2) if total_users > 0 else 0
        },
        "generated_at": datetime.now().isoformat()
    }
