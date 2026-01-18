"""
Gestione dello stato conversazionale per il sistema multiagente
Mantiene il contesto tra richieste successive
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta


class ConversationManager:
    """
    Gestisce lo stato conversazionale tra richieste multiple
    Permette agli agenti di ricordare richieste incomplete
    """
    
    def __init__(self):
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.session_timeout = timedelta(minutes=10)  # Timeout sessione: 10 minuti
    
    def get_session_id(self, user_id: str = "default") -> str:
        """Genera un ID sessione per l'utente"""
        return f"session_{user_id}"
    
    def has_pending_request(self, session_id: str = "default") -> bool:
        """
        Controlla se c'è una richiesta in sospeso per questa sessione
        
        Args:
            session_id: ID della sessione
            
        Returns:
            True se c'è una richiesta in sospeso, False altrimenti
        """
        session_id = self.get_session_id(session_id)
        
        if session_id not in self.conversations:
            print(f"[CONV_MGR] Nessuna conversazione per session {session_id}")
            return False
        
        session = self.conversations[session_id]
        
        # Verifica timeout
        if datetime.now() - session.get("timestamp", datetime.now()) > self.session_timeout:
            # Sessione scaduta
            print(f"[CONV_MGR] Sessione scaduta per {session_id}")
            del self.conversations[session_id]
            return False
        
        result = session.get("pending", False)
        print(f"[CONV_MGR] has_pending_request: {result}")
        return result
    
    def get_pending_request(self, session_id: str = "default") -> Optional[Dict[str, Any]]:
        """
        Recupera una richiesta in sospeso
        
        Args:
            session_id: ID della sessione
            
        Returns:
            Dizionario con i dati della richiesta in sospeso, o None
        """
        session_id = self.get_session_id(session_id)
        
        # Controlla direttamente senza chiamare has_pending_request per evitare doppio prefisso
        if session_id not in self.conversations:
            print(f"[CONV_MGR] Nessuna conversazione per session {session_id}")
            return None
        
        session = self.conversations[session_id]
        
        # Verifica timeout
        if datetime.now() - session.get("timestamp", datetime.now()) > self.session_timeout:
            print(f"[CONV_MGR] Sessione scaduta in get_pending_request")
            del self.conversations[session_id]
            return None
        
        if not session.get("pending", False):
            print(f"[CONV_MGR] Sessione non è pending")
            return None
        
        print(f"[CONV_MGR] Returning pending request: {session}")
        return session.copy()
    
    def save_pending_request(
        self,
        agent_type: str,
        original_query: str,
        missing_info: str,
        partial_data: Dict[str, Any],
        session_id: str = "default"
    ):
        """
        Salva una richiesta incompleta
        
        Args:
            agent_type: Tipo di agente (WEATHER, HOROSCOPE, etc.)
            original_query: Query originale dell'utente
            missing_info: Tipo di informazione mancante (location, zodiac_sign, etc.)
            partial_data: Dati già estratti dalla query
            session_id: ID della sessione
        """
        session_id = self.get_session_id(session_id)
        
        self.conversations[session_id] = {
            "pending": True,
            "agent_type": agent_type,
            "original_query": original_query,
            "missing_info": missing_info,
            "partial_data": partial_data,
            "timestamp": datetime.now()
        }
        
        print(f"[CONV_MGR] Salvata richiesta pendente: agente={agent_type}, manca={missing_info}")
    
    def complete_pending_request(
        self,
        user_response: str,
        session_id: str = "default"
    ) -> Optional[str]:
        """
        Completa una richiesta in sospeso con la nuova informazione dell'utente
        
        Args:
            user_response: Risposta dell'utente con l'informazione mancante
            session_id: ID della sessione
            
        Returns:
            Query completa ricostruita, o None se non c'è richiesta in sospeso
        """
        session_id = self.get_session_id(session_id)
        
        # Controlla direttamente senza chiamare has_pending_request per evitare doppio prefisso
        if session_id not in self.conversations:
            print(f"[CONV_MGR] Nessuna conversazione per session {session_id} in complete_pending_request")
            return None
        
        session = self.conversations[session_id]
        
        # Verifica timeout
        if datetime.now() - session.get("timestamp", datetime.now()) > self.session_timeout:
            print(f"[CONV_MGR] Sessione scaduta in complete_pending_request")
            del self.conversations[session_id]
            return None
        
        if not session.get("pending", False):
            print(f"[CONV_MGR] Sessione non è pending in complete_pending_request")
            return None
        
        original_query = session.get("original_query", "")
        missing_info = session.get("missing_info", "")
        partial_data = session.get("partial_data", {})
        
        # Ricostruisci la query completa
        if missing_info == "location":
            # Per il meteo: "Che tempo fa a [CITTÀ] [QUANDO]"
            time_desc = partial_data.get("time_description", "oggi")
            completed_query = f"Che tempo fa a {user_response} {time_desc}"
        
        elif missing_info == "zodiac_sign":
            # Per l'oroscopo: "Oroscopo del [SEGNO] [PERIODO]"
            time_desc = partial_data.get("time_description", "di oggi")
            completed_query = f"Oroscopo del {user_response} {time_desc}"
        
        else:
            # Fallback: aggiungi semplicemente la risposta alla query originale
            completed_query = f"{original_query} {user_response}"
        
        # Pulisci la richiesta in sospeso
        del self.conversations[session_id]
        
        return completed_query
    
    def clear_pending_request(self, session_id: str = "default"):
        """
        Cancella una richiesta in sospeso
        
        Args:
            session_id: ID della sessione
        """
        session_id = self.get_session_id(session_id)
        
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_agent_type(self, session_id: str = "default") -> Optional[str]:
        """
        Recupera il tipo di agente della richiesta in sospeso
        
        Args:
            session_id: ID della sessione
            
        Returns:
            Tipo di agente (WEATHER, HOROSCOPE, etc.) o None
        """
        session_id = self.get_session_id(session_id)
        
        if not self.has_pending_request(session_id):
            return None
        
        return self.conversations[session_id].get("agent_type")
    
    def cleanup_expired_sessions(self):
        """Pulisce le sessioni scadute"""
        now = datetime.now()
        expired = [
            sid for sid, session in self.conversations.items()
            if now - session.get("timestamp", now) > self.session_timeout
        ]
        
        for sid in expired:
            del self.conversations[sid]


# Istanza globale del conversation manager
conversation_manager = ConversationManager()