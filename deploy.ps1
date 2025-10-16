# Script de déploiement PowerShell pour Lafaom Backend
Write-Host "🚀 Démarrage du déploiement Lafaom Backend..." -ForegroundColor Green

# Vérifier si Docker est installé
try {
    docker --version | Out-Null
    Write-Host "✅ Docker est installé" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker n'est pas installé. Veuillez installer Docker d'abord." -ForegroundColor Red
    exit 1
}

# Vérifier si Docker Compose est installé
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose est installé" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose n'est pas installé. Veuillez installer Docker Compose d'abord." -ForegroundColor Red
    exit 1
}

# Créer le fichier .env s'il n'existe pas
if (-not (Test-Path ".env")) {
    Write-Host "📝 Création du fichier .env à partir de env.example..." -ForegroundColor Yellow
    Copy-Item "env.example" ".env"
    Write-Host "⚠️  Veuillez modifier le fichier .env avec vos vraies valeurs avant de continuer." -ForegroundColor Yellow
    Write-Host "   Notamment: SECRET_KEY, EMAIL_HOST_USER, EMAIL_HOST_PASSWORD" -ForegroundColor Yellow
    Read-Host "Appuyez sur Entrée pour continuer après avoir modifié .env"
}

# Arrêter les conteneurs existants
Write-Host "🛑 Arrêt des conteneurs existants..." -ForegroundColor Yellow
docker-compose down

# Nettoyer les images orphelines
Write-Host "🧹 Nettoyage des images orphelines..." -ForegroundColor Yellow
docker system prune -f

# Construire et démarrer les services
Write-Host "🔨 Construction et démarrage des services..." -ForegroundColor Yellow
docker-compose up --build -d

# Attendre que les services soient prêts
Write-Host "⏳ Attente que les services soient prêts..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Vérifier le statut des services
Write-Host "📊 Vérification du statut des services..." -ForegroundColor Yellow
docker-compose ps

# Afficher les logs en cas de problème
Write-Host "📋 Logs des services:" -ForegroundColor Yellow
docker-compose logs --tail=50

Write-Host "✅ Déploiement terminé!" -ForegroundColor Green
Write-Host "🌐 Services disponibles:" -ForegroundColor Cyan
Write-Host "   - Application: http://localhost:7051" -ForegroundColor White
Write-Host "   - PgAdmin: http://localhost:8080" -ForegroundColor White
Write-Host "   - Portainer: http://localhost:9000" -ForegroundColor White
Write-Host ""
Write-Host "📝 Pour voir les logs en temps réel: docker-compose logs -f" -ForegroundColor Cyan
Write-Host "🛑 Pour arrêter les services: docker-compose down" -ForegroundColor Cyan
