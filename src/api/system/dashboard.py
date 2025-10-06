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
    
    # Utilisateurs actifs
    active_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == "active")
    )
    active_users = active_users_result.scalar() or 0
    
    # Utilisateurs inactifs
    inactive_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == "inactive")
    )
    inactive_users = inactive_users_result.scalar() or 0
    
    # Utilisateurs bloqués
    blocked_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == "blocked")
    )
    blocked_users = blocked_users_result.scalar() or 0
    
    # Utilisateurs supprimés
    deleted_users_result = await db.execute(
        select(func.count(User.id)).where(User.status == "deleted")
    )
    deleted_users = deleted_users_result.scalar() or 0
    
    # Statistiques par type d'utilisateur
    user_types_result = await db.execute(
        select(User.user_type, func.count(User.id))
        .group_by(User.user_type)
    )
    user_types = user_types_result.all()
    
    user_types_stats = {}
    for user_type, count in user_types:
        user_types_stats[user_type] = count
    
    # Statistiques par rôle
    roles_stats = {}
    roles_result = await db.execute(
        select(Role.name, func.count(UserRole.user_id))
        .join(UserRole, Role.id == UserRole.role_id)
        .group_by(Role.name)
    )
    roles_data = roles_result.all()
    
    for role_name, count in roles_data:
        roles_stats[role_name] = count
    
    # Statistiques géographiques (par pays uniquement)
    geographic_stats = {
        "by_country": {}
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
    
    # Statistiques temporelles
    new_this_week_result = await db.execute(
        select(func.count(User.id)).where(
            User.created_at >= datetime.now() - timedelta(days=7)
        )
    )
    new_this_week = new_this_week_result.scalar() or 0
    
    new_this_month_result = await db.execute(
        select(func.count(User.id)).where(
            User.created_at >= datetime.now() - timedelta(days=30)
        )
    )
    new_this_month = new_this_month_result.scalar() or 0
    
    # Statistiques de sécurité
    two_factor_enabled_result = await db.execute(
        select(func.count(User.id)).where(User.two_factor_enabled == True)
    )
    two_factor_enabled = two_factor_enabled_result.scalar() or 0
    
    # Utilisateurs avec email (pas de champ email_verified dans le modèle)
    users_with_email_result = await db.execute(
        select(func.count(User.id)).where(User.email.isnot(None))
    )
    users_with_email = users_with_email_result.scalar() or 0
    
    # Utilisateurs avec dernière connexion récente
    recent_login_result = await db.execute(
        select(func.count(User.id)).where(
            User.last_login >= datetime.now() - timedelta(days=7)
        )
    )
    recent_login = recent_login_result.scalar() or 0
    
    # Utilisateurs sans connexion récente
    no_recent_login_result = await db.execute(
        select(func.count(User.id)).where(
            and_(
                User.last_login.isnot(None),
                User.last_login < datetime.now() - timedelta(days=30)
            )
        )
    )
    no_recent_login = no_recent_login_result.scalar() or 0
    
    return {
        "summary": {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": inactive_users,
            "blocked_users": blocked_users,
            "deleted_users": deleted_users
        },
        "user_types": user_types_stats,
        "roles": roles_stats,
        "geographic": geographic_stats,
        "temporal": {
            "new_this_week": new_this_week,
            "new_this_month": new_this_month
        },
        "security": {
            "two_factor_enabled": two_factor_enabled,
            "users_with_email": users_with_email,
            "recent_login": recent_login,
            "no_recent_login": no_recent_login
        }
    }