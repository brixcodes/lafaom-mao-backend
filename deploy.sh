#!/bin/bash

# Script de déploiement pour Lafaom Backend
echo "🚀 Démarrage du déploiement Lafaom Backend..."

# Vérifier si Docker est installé
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé. Veuillez installer Docker d'abord."
    exit 1
fi

# Vérifier si Docker Compose est installé
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé. Veuillez installer Docker Compose d'abord."
    exit 1
fi

# Créer le fichier .env s'il n'existe pas
if [ ! -f .env ]; then
    echo "📝 Création du fichier .env à partir de env.example..."
    cp env.example .env
    echo "⚠️  Veuillez modifier le fichier .env avec vos vraies valeurs avant de continuer."
    echo "   Notamment: SECRET_KEY, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD"
    read -p "Appuyez sur Entrée pour continuer après avoir modifié .env..."
fi

# Arrêter les conteneurs existants
echo "🛑 Arrêt des conteneurs existants..."
docker-compose down

# Nettoyer les images orphelines
echo "🧹 Nettoyage des images orphelines..."
docker system prune -f

# Construire et démarrer les services
echo "🔨 Construction et démarrage des services..."
docker-compose up --build -d

# Attendre que les services soient prêts
echo "⏳ Attente que les services soient prêts..."
sleep 30

# Vérifier le statut des services
echo "📊 Vérification du statut des services..."
docker-compose ps

# Afficher les logs en cas de problème
echo "📋 Logs des services:"
docker-compose logs --tail=50

echo "✅ Déploiement terminé!"
echo "🌐 Services disponibles:"
echo "   - Application: http://localhost:7051"
echo "   - PgAdmin: http://localhost:8080"
echo "   - Portainer: http://localhost:9000"
echo ""
echo "📝 Pour voir les logs en temps réel: docker-compose logs -f"
echo "🛑 Pour arrêter les services: docker-compose down"
