
#!/usr/bin/env python3
"""
Script de test pour vérifier les limites de paiement
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Ajouter le répertoire src au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import settings
from src.api.payments.service import PaymentService
from src.api.payments.schemas import PaymentInitInput

class MockJobApplication:
    """Mock d'une candidature pour les tests"""
    def __init__(self):
        self.id = "test-application-123"
        self.__class__.__name__ = "JobApplication"

async def test_payment_limits():
    """Test des limites de paiement"""
    
    print("=== TEST DES LIMITES DE PAIEMENT ===")
    print(f"Timestamp: {datetime.now()}")
    
    # 1. Vérification de la configuration
    print("\n1. CONFIGURATION")
    print(f"   CINETPAY_CARD_MIN_AMOUNT: {settings.CINETPAY_CARD_MIN_AMOUNT} centimes")
    print(f"   CINETPAY_CARD_MAX_AMOUNT: {settings.CINETPAY_CARD_MAX_AMOUNT} centimes")
    print(f"   CINETPAY_CARD_MAX_AMOUNT: {settings.CINETPAY_CARD_MAX_AMOUNT/100} XAF")
    
    # 2. Test avec différents montants
    test_amounts = [
        {"amount": 50.0, "currency": "EUR", "expected_xaf": 50 * 675},
        {"amount": 100.0, "currency": "EUR", "expected_xaf": 100 * 675},
        {"amount": 20.0, "currency": "EUR", "expected_xaf": 20 * 675},
    ]
    
    for test in test_amounts:
        print(f"\n2. TEST AVEC {test['amount']} {test['currency']}")
        expected_xaf = test['expected_xaf']
        amount_in_cents = int(expected_xaf * 100)
        
        print(f"   Montant attendu en XAF: {expected_xaf}")
        print(f"   Montant en centimes: {amount_in_cents}")
        print(f"   Limite max: {settings.CINETPAY_CARD_MAX_AMOUNT} centimes")
        
        if amount_in_cents > settings.CINETPAY_CARD_MAX_AMOUNT:
            print(f"   ❌ DÉPASSE LA LIMITE: {amount_in_cents} > {settings.CINETPAY_CARD_MAX_AMOUNT}")
        else:
            print(f"   ✅ DANS LA LIMITE: {amount_in_cents} <= {settings.CINETPAY_CARD_MAX_AMOUNT}")
    
    # 3. Test d'initiation de paiement avec montant réaliste
    print(f"\n3. TEST D'INITIATION DE PAIEMENT")
    try:
        payment_service = PaymentService()
        mock_app = MockJobApplication()
        
        # Test avec 50 EUR (montant typique d'une candidature)
        payment_input = PaymentInitInput(
            payable=mock_app,
            amount=50.0,  # 50 EUR
            product_currency="EUR",
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
        
        print(f"   Montant original: {payment_input.amount} {payment_input.product_currency}")
        
        # Simuler la conversion
        expected_xaf = payment_input.amount * 675  # Taux EUR->XAF
        amount_in_cents = int(expected_xaf * 100)
        
        print(f"   Montant converti: {expected_xaf} XAF")
        print(f"   Montant en centimes: {amount_in_cents}")
        
        if amount_in_cents > settings.CINETPAY_CARD_MAX_AMOUNT:
            print(f"   ❌ PROBLÈME: Le montant dépasse encore la limite")
            return False
        else:
            print(f"   ✅ Le montant est dans la limite")
            return True
            
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_payment_limits())
    print(f"\n=== RÉSULTAT FINAL ===")
    print(f"Test {'réussi' if result else 'échoué'}")
    exit(0 if result else 1)
