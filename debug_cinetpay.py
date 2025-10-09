#!/usr/bin/env python3
"""
Script de débogage pour vérifier la configuration CinetPay
"""

import asyncio
import httpx
import json
from src.config import settings

async def test_cinetpay_config():
    """Test de la configuration CinetPay"""
    
    print("=== TEST DE CONFIGURATION CINETPAY ===")
    print(f"API Key: {settings.CINETPAY_API_KEY}")
    print(f"Site ID: {settings.CINETPAY_SITE_ID}")
    print(f"Notify URL: {settings.CINETPAY_NOTIFY_URL}")
    print(f"Return URL: {settings.CINETPAY_RETURN_URL}")
    print(f"Currency: {settings.CINETPAY_CURRENCY}")
    print(f"Channels: {settings.CINETPAY_CHANNELS}")
    
    # Test de l'API CinetPay avec des données minimales
    test_payload = {
        "amount": 100,
        "currency": "XAF",
        "description": "Test payment",
        "apikey": settings.CINETPAY_API_KEY,
        "site_id": settings.CINETPAY_SITE_ID,
        "transaction_id": "TEST_" + str(int(asyncio.get_event_loop().time())),
        "channels": "ALL",
        "return_url": settings.CINETPAY_RETURN_URL,
        "notify_url": settings.CINETPAY_NOTIFY_URL,
        "meta": "test-payment",
        "invoice_data": {
            "test": True
        }
    }
    
    print(f"\n=== PAYLOAD DE TEST ===")
    print(json.dumps(test_payload, indent=2))
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print(f"\n=== APPEL API CINETPAY ===")
            response = await client.post(
                "https://api-checkout.cinetpay.com/v2/payment", 
                json=test_payload
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"Response: {json.dumps(response_data, indent=2)}")
                
                if response.status_code == 200 and response_data.get("code") == "201":
                    print("✅ Configuration CinetPay OK - Test réussi")
                    return True
                else:
                    print("❌ Configuration CinetPay KO - Test échoué")
                    print(f"Erreur: {response_data.get('message', 'Unknown error')}")
                    return False
                    
            except Exception as json_error:
                print(f"❌ Erreur de parsing JSON: {json_error}")
                print(f"Raw response: {response.text}")
                return False
                
    except httpx.TimeoutException:
        print("❌ Timeout lors de l'appel API CinetPay")
        return False
    except httpx.ConnectError:
        print("❌ Erreur de connexion à l'API CinetPay")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_cinetpay_config())
    exit(0 if result else 1)
