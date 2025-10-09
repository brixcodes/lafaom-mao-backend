#!/usr/bin/env python3
"""
Script de test complet pour diagnostiquer le problème de paiement
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import settings
from src.api.payments.service import PaymentService, CinetPayService
from src.api.payments.schemas import PaymentInitInput, CinetPayInit
from src.api.job_offers.models import JobApplication

class MockJobApplication:
    """Mock d'une candidature pour les tests"""
    def __init__(self):
        self.id = "test-application-123"
        self.__class__.__name__ = "JobApplication"

async def test_payment_flow():
    """Test complet du flux de paiement"""
    
    print("=== DIAGNOSTIC COMPLET DU FLUX DE PAIEMENT ===")
    print(f"Timestamp: {datetime.now()}")
    
    # 1. Vérification de la configuration
    print("\n1. VÉRIFICATION DE LA CONFIGURATION")
    print(f"   CINETPAY_API_KEY: {settings.CINETPAY_API_KEY}")
    print(f"   CINETPAY_SITE_ID: {settings.CINETPAY_SITE_ID}")
    print(f"   CINETPAY_NOTIFY_URL: {settings.CINETPAY_NOTIFY_URL}")
    print(f"   CINETPAY_RETURN_URL: {settings.CINETPAY_RETURN_URL}")
    print(f"   CURRENCY_API_KEY: {settings.CURRENCY_API_KEY}")
    print(f"   CURRENCY_API_URL: {settings.CURRENCY_API_URL}")
    
    # 2. Test de conversion de devises
    print("\n2. TEST DE CONVERSION DE DEVISES")
    try:
        payment_service = PaymentService()
        rates = await payment_service.get_currency_rates("USD", ["XAF"])
        print(f"   Taux USD->XAF: {rates}")
    except Exception as e:
        print(f"   ❌ Erreur conversion devises: {e}")
        return False
    
    # 3. Test de création de données de paiement
    print("\n3. TEST DE CRÉATION DES DONNÉES DE PAIEMENT")
    try:
        mock_app = MockJobApplication()
        payment_input = PaymentInitInput(
            payable=mock_app,
            amount=100.0,
            product_currency="USD",
            description="Test payment for job application",
            payment_provider="CINETPAY",
            customer_name="Test",
            customer_surname="User",
            customer_email="test@example.com",
            customer_phone_number="123456789",
            customer_address="Test Address",
            customer_city="Test City",
            customer_country="CM"
        )
        print(f"   ✅ Données de paiement créées: {payment_input}")
    except Exception as e:
        print(f"   ❌ Erreur création données: {e}")
        return False
    
    # 4. Test d'initiation du paiement
    print("\n4. TEST D'INITIATION DU PAIEMENT")
    try:
        result = await payment_service.initiate_payment(payment_input)
        print(f"   Résultat: {json.dumps(result, indent=2, default=str)}")
        
        if result.get("success"):
            print("   ✅ Paiement initié avec succès")
            return True
        else:
            print(f"   ❌ Échec de l'initiation: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"   ❌ Erreur lors de l'initiation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_payment_flow())
    print(f"\n=== RÉSULTAT FINAL ===")
    print(f"Test {'réussi' if result else 'échoué'}")
    exit(0 if result else 1)
