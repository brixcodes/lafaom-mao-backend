#!/usr/bin/env python3
"""
Script de débogage pour vérifier la conversion de devises
"""

import asyncio
import httpx
import json
from src.config import settings

async def test_currency_conversion():
    """Test de la conversion de devises"""
    
    print("=== TEST DE CONVERSION DE DEVISES ===")
    print(f"Currency API Key: {settings.CURRENCY_API_KEY}")
    print(f"Currency API URL: {settings.CURRENCY_API_URL}")
    
    if not settings.CURRENCY_API_KEY or settings.CURRENCY_API_KEY == "your_currency_api_key_here":
        print("⚠️  Aucune clé API de devises configurée - utilisation des taux par défaut")
        
        # Taux par défaut
        default_rates = {
            "USDXAF": 600.0,
            "EURXAF": 650.0,
            "XAFUSD": 0.0017,
            "XAFEUR": 0.0015,
        }
        
        print("Taux par défaut utilisés:")
        for rate, value in default_rates.items():
            print(f"  {rate}: {value}")
        
        return True
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {"apikey": settings.CURRENCY_API_KEY}
            params = {"source": "USD", "currencies": "XAF,EUR"}
            
            print(f"\n=== APPEL API DE DEVISES ===")
            print(f"URL: {settings.CURRENCY_API_URL}")
            print(f"Params: {params}")
            
            response = await client.get(settings.CURRENCY_API_URL, headers=headers, params=params)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('quotes', {})
                print(f"Taux obtenus: {json.dumps(rates, indent=2)}")
                print("✅ API de devises fonctionne")
                return True
            else:
                print(f"❌ Erreur API devises: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Erreur lors du test de l'API de devises: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_currency_conversion())
    exit(0 if result else 1)
