#!/usr/bin/env python3
"""
Script de test pour vérifier que les limites de montant sont supprimées
"""

import sys
import os

# Ajouter le répertoire src au path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import settings

def test_no_limits():
    """Test que les limites sont supprimées"""
    
    print("=== TEST DES LIMITES SUPPRIMÉES ===")
    
    # 1. Vérification de la configuration
    print("\n1. CONFIGURATION")
    print(f"   CINETPAY_CARD_MIN_AMOUNT: {settings.CINETPAY_CARD_MIN_AMOUNT} centimes")
    print(f"   CINETPAY_CARD_MAX_AMOUNT: {settings.CINETPAY_CARD_MAX_AMOUNT} centimes")
    print(f"   CINETPAY_CARD_MAX_AMOUNT: {settings.CINETPAY_CARD_MAX_AMOUNT/100} XAF")
    
    # 2. Test avec différents montants
    test_amounts = [
        {"amount": 50.0, "currency": "EUR", "xaf": 50 * 675},
        {"amount": 100.0, "currency": "EUR", "xaf": 100 * 675},
        {"amount": 200.0, "currency": "EUR", "xaf": 200 * 675},
        {"amount": 500.0, "currency": "EUR", "xaf": 500 * 675},
    ]
    
    print(f"\n2. TEST DES MONTANTS")
    for test in test_amounts:
        amount_in_cents = int(test['xaf'] * 100)
        print(f"   {test['amount']} {test['currency']} = {test['xaf']} XAF = {amount_in_cents} centimes")
        
        if amount_in_cents > settings.CINETPAY_CARD_MAX_AMOUNT:
            print(f"   ❌ DÉPASSE ENCORE LA LIMITE: {amount_in_cents} > {settings.CINETPAY_CARD_MAX_AMOUNT}")
        else:
            print(f"   ✅ DANS LA LIMITE: {amount_in_cents} <= {settings.CINETPAY_CARD_MAX_AMOUNT}")
    
    # 3. Vérification que la limite est très élevée
    print(f"\n3. VÉRIFICATION DE LA LIMITE")
    if settings.CINETPAY_CARD_MAX_AMOUNT >= 999999999:
        print(f"   ✅ Limite très élevée configurée: {settings.CINETPAY_CARD_MAX_AMOUNT}")
        return True
    else:
        print(f"   ❌ Limite encore trop basse: {settings.CINETPAY_CARD_MAX_AMOUNT}")
        return False

if __name__ == "__main__":
    result = test_no_limits()
    print(f"\n=== RÉSULTAT FINAL ===")
    print(f"Test {'réussi' if result else 'échoué'}")
    exit(0 if result else 1)
