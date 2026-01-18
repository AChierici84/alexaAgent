"""
Esempio di utilizzo della gestione conversazionale
Dimostra come il sistema mantiene il contesto tra richieste successive
"""

from multiagent import run_supervisor
from conversation_manager import conversation_manager


def esempio_meteo():
    """Esempio: richiesta meteo incompleta"""
    print("\n" + "="*70)
    print("ESEMPIO 1: Richiesta Meteo Incompleta")
    print("="*70 + "\n")
    
    # Pulisci eventuali conversazioni precedenti
    conversation_manager.clear_pending_request()
    
    # Prima richiesta: manca la località
    print("👤 Utente: 'Che tempo fa domani?'\n")
    result1 = run_supervisor("Che tempo fa domani?")
    
    # Mostra risposta
    for msg in result1.get("messages", []):
        if hasattr(msg, 'content') and msg.content:
            print(f"Alexa: {msg.content}\n")
    
    # Seconda richiesta: fornisce la località
    print("👤 Utente: 'Milano'\n")
    result2 = run_supervisor("Milano")
    
    # Mostra risposta
    for msg in result2.get("messages", []):
        if hasattr(msg, 'content') and msg.content:
            print(f"Alexa: {msg.content}\n")
    
    print("="*70)


def esempio_oroscopo():
    """Esempio: richiesta oroscopo incompleta"""
    print("\n" + "="*70)
    print("ESEMPIO 2: Richiesta Oroscopo Incompleta")
    print("="*70 + "\n")
    
    # Pulisci eventuali conversazioni precedenti
    conversation_manager.clear_pending_request()
    
    # Prima richiesta: manca il segno zodiacale
    print("Utente: 'Qual è l'oroscopo di oggi?'\n")
    result1 = run_supervisor("Qual è l'oroscopo di oggi?")
    
    # Mostra risposta
    for msg in result1.get("messages", []):
        if hasattr(msg, 'content') and msg.content:
            print(f"Alexa: {msg.content}\n")
    
    # Seconda richiesta: fornisce il segno
    print("Utente: 'Leone'\n")
    result2 = run_supervisor("Leone")
    
    # Mostra risposta
    for msg in result2.get("messages", []):
        if hasattr(msg, 'content') and msg.content:
            print(f"Alexa: {msg.content}\n")
    
    print("="*70)


def esempio_completo():
    """Esempio: richiesta completa (senza pending)"""
    print("\n" + "="*70)
    print("ESEMPIO 3: Richiesta Completa")
    print("="*70 + "\n")
    
    # Pulisci eventuali conversazioni precedenti
    conversation_manager.clear_pending_request()
    
    # Richiesta completa: ha tutte le informazioni
    print("Utente: 'Che tempo fa a Roma dopodomani?'\n")
    result = run_supervisor("Che tempo fa a Roma dopodomani?")
    
    # Mostra risposta
    for msg in result.get("messages", []):
        if hasattr(msg, 'content') and msg.content:
            print(f"🤖 Alexa: {msg.content}\n")
    
    print("="*70)


if __name__ == "__main__":
    print("\n")
    print("╔" + "═"*68 + "╗")
    print("║" + " "*10 + "ESEMPI DI GESTIONE CONVERSAZIONALE" + " "*22 + "║")
    print("╚" + "═"*68 + "╝")
    
    print("\nQuesti esempi mostrano come il sistema mantiene il contesto")
    print("tra richieste successive quando mancano informazioni.\n")
    
    try:
        # Esempio 1: Meteo senza località
        esempio_meteo()
        
        input("\nPremi INVIO per continuare...")
        
        # Esempio 2: Oroscopo senza segno
        esempio_oroscopo()
        
        input("\nPremi INVIO per continuare...")
        
        # Esempio 3: Richiesta completa
        esempio_completo()
        
        print("\n✅ ESEMPI COMPLETATI\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Esempi interrotti dall'utente\n")
    except Exception as e:
        print(f"\n❌ ERRORE: {str(e)}\n")
        import traceback
        traceback.print_exc()
