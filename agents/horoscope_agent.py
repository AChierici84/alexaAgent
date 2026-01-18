"""
Agente Oroscopo - Estrae il segno zodiacale e l'indicazione temporale, recupera dati da Horoscope API
Utilizza OpenAI per l'estrazione intelligente e la traduzione italiano-inglese
"""

import os
import requests
import json
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()


class HoroscopeState(TypedDict):
    """Stato dell'agente oroscopo"""
    query: str
    zodiac_sign: str | None
    zodiac_sign_en: str | None
    time_period: str | None  # daily, weekly, monthly, yearly
    horoscope_data: dict | None
    messages: Annotated[list, operator.add]


# Mapping segni zodiacali italiano -> inglese
ZODIAC_SIGNS_IT_EN = {
    "ariete": "aries",
    "toro": "taurus",
    "gemelli": "gemini",
    "cancro": "cancer",
    "leone": "leo",
    "vergine": "virgo",
    "bilancia": "libra",
    "scorpione": "scorpio",
    "sagittario": "sagittarius",
    "capricorno": "capricorn",
    "acquario": "aquarius",
    "pesci": "pisces"
}

# Periodi supportati da Horoscope API
VALID_PERIODS = ["daily", "weekly", "monthly", "yearly"]

# Mapping italiano -> inglese per i periodi
PERIOD_IT_EN = {
    "oggi": "daily",
    "giorno": "daily",
    "giornaliero": "daily",
    "domani": "daily",
    "ieri": "daily",
    "settimana": "weekly",
    "settimanale": "weekly",
    "mese": "monthly",
    "mensile": "monthly",
    "anno": "yearly",
    "annuale": "yearly"
}


def extract_zodiac_and_period(state: HoroscopeState) -> HoroscopeState:
    """
    Estrae il segno zodiacale e il periodo dalla query dell'utente usando OpenAI
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con il segno zodiacale e il periodo estratti
    """
    query = state["query"]
    
    # Aggiungiamo il messaggio dell'utente
    state["messages"].append(HumanMessage(content=query))
    
    try:
        # Inizializza il modello OpenAI
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Lista dei segni per il prompt
        segni_lista = ", ".join(ZODIAC_SIGNS_IT_EN.keys())
        
        prompt = f"""Analizza questa query in italiano ed estrai il segno zodiacale e l'indicazione temporale.

Segni zodiacali validi: {segni_lista}

Periodi temporali supportati:
- "oggi", "domani", "giornaliero" -> daily
- "settimana", "settimanale" -> weekly
- "mese", "mensile" -> monthly
- "anno", "annuale" -> yearly
- Se non specificato, assume "daily"

Query: {query}

Rispondi in JSON con questo formato esatto:
{{
    "zodiac_sign": "nome segno in italiano (minuscolo)",
    "time_period": "daily|weekly|monthly|yearly",
    "time_description": "descrizione breve (es. 'di oggi', 'della settimana', 'del mese', 'dell'anno')",
    "validity": "VALIDO" o "INVALIDO"
}}

Se non trovi un segno zodiacale rispondi con "zodiac_sign": "NESSUNO"
Se il periodo non è riconoscibile rispondi con "time_period": "daily"
"""
        
        # Chiama OpenAI
        response = llm.invoke([
            SystemMessage(content="Sei un assistente che estrae segni zodiacali e periodi temporali da testo italiano. Rispondi sempre in JSON."),
            HumanMessage(content=prompt)
        ])
        
        # Parsa la risposta JSON
        try:
            data = json.loads(response.content)
        except json.JSONDecodeError:
            # Se non riesce a parsare, prova a estrarre il JSON dalla risposta
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("Impossibile estrarre JSON dalla risposta")
        
        zodiac_sign = data.get("zodiac_sign", "NESSUNO").strip().lower()
        time_period = data.get("time_period", "daily").strip().lower()
        validity = data.get("validity", "INVALIDO")
        time_description = data.get("time_description", "di oggi")
        
        # Validazione segno zodiacale
        if zodiac_sign.upper() == "NESSUNO" or zodiac_sign not in ZODIAC_SIGNS_IT_EN:
            state["zodiac_sign"] = None
            state["zodiac_sign_en"] = None
            state["messages"].append(
                AIMessage(content=f"Non ho riconosciuto un segno zodiacale nella tua richiesta. Puoi dirmi per quale segno vuoi l'oroscopo? (es. {', '.join(list(ZODIAC_SIGNS_IT_EN.keys())[:3])}, ...)")
            )
            return state
        
        # Validazione periodo è tra quelli supportati
        if time_period not in VALID_PERIODS:
            state["zodiac_sign"] = None
            state["zodiac_sign_en"] = None
            state["messages"].append(
                AIMessage(content=f"Periodo non valido. Posso fornirti l'oroscopo per: giornaliero, settimanale, mensile o annuale.")
            )
            return state
        
        state["zodiac_sign"] = zodiac_sign
        state["zodiac_sign_en"] = ZODIAC_SIGNS_IT_EN[zodiac_sign]
        state["time_period"] = time_period
        
        state["messages"].append(
            AIMessage(content=f"Ho identificato: segno {zodiac_sign.capitalize()}, oroscopo {time_description}. Sto recuperando i dati...")
        )
        
    except Exception as e:
        state["zodiac_sign"] = None
        state["zodiac_sign_en"] = None
        state["time_period"] = None
        state["messages"].append(
            AIMessage(content=f"Errore nell'analisi della richiesta: {str(e)}. Controlla la tua API key di OpenAI.")
        )
    
    return state


def get_horoscope_data(state: HoroscopeState) -> HoroscopeState:
    """
    Recupera i dati dell'oroscopo da Horoscope API
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con i dati dell'oroscopo
    """
    if not state.get("zodiac_sign_en"):
        return state
    
    try:
        zodiac_sign_en = state["zodiac_sign_en"]
        time_period = state.get("time_period", "daily")
        
        # Mappa i periodi: daily richiede anche il parametro day
        if time_period == "daily":
            # Per daily, usiamo TODAY come parametro day
            url = f"https://horoscope-app-api.vercel.app/api/v1/get-horoscope/{time_period}?sign={zodiac_sign_en}&day=TODAY"
        else:
            # Per weekly, monthly, yearly non serve il parametro day
            url = f"https://horoscope-app-api.vercel.app/api/v1/get-horoscope/{time_period}?sign={zodiac_sign_en}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # L'API restituisce {"data": {"date": ..., "horoscope_data": ...}, "status": 200, "success": true}
        if data.get("success") and "data" in data:
            state["horoscope_data"] = data["data"]
        else:
            raise ValueError("Formato risposta API non valido")
        
    except requests.exceptions.RequestException as e:
        state["horoscope_data"] = None
        state["messages"].append(
            AIMessage(content=f"Errore nel recupero dei dati dall'API Horoscope: {str(e)}")
        )
    except Exception as e:
        state["horoscope_data"] = None
        state["messages"].append(
            AIMessage(content=f"Errore imprevisto: {str(e)}")
        )
    
    return state


def translate_and_format_horoscope(state: HoroscopeState) -> HoroscopeState:
    """
    Traduce l'oroscopo dall'inglese all'italiano usando OpenAI e formatta il risultato
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con l'oroscopo tradotto
    """
    if not state.get("horoscope_data"):
        return state
    
    try:
        data = state["horoscope_data"]
        zodiac_sign = state["zodiac_sign"].capitalize()
        time_period = state.get("time_period", "daily")
        
        # Estrai i campi principali dall'API Horoscope
        # Formato: {"date": "...", "horoscope_data": "..."}
        description = data.get("horoscope_data", "")
        date_info = data.get("date", "")
        
        # Inizializza il modello OpenAI per la traduzione
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Traduci la descrizione principale
        translation_prompt = f"""Traduci questo oroscopo dall'inglese all'italiano in modo fluente e naturale:

{description}

Mantieni lo stesso tono e stile, ma rendilo scorrevole in italiano."""
        
        response = llm.invoke([
            SystemMessage(content="Sei un traduttore esperto dall'inglese all'italiano, specializzato in oroscopi."),
            HumanMessage(content=translation_prompt)
        ])
        
        description_it = response.content.strip()
        
        # Mappa i periodi per la descrizione
        period_label = {
            "daily": "di oggi",
            "weekly": "della settimana",
            "monthly": "del mese",
            "yearly": "dell'anno"
        }.get(time_period, "di oggi")
        
        # Formatta il messaggio finale
        final_message = f""" Oroscopo {period_label} per {zodiac_sign}

{description_it}"""
        
        if date_info:
            final_message += f"\n\n Periodo: {date_info}"
        
        state["messages"].append(AIMessage(content=final_message))
        
    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"Errore nella traduzione dell'oroscopo: {str(e)}")
        )
    
    return state


def build_horoscope_agent():
    """
    Costruisce il grafo dell'agente oroscopo usando LangGraph
    
    Returns:
        Un CompiledGraph pronto per l'esecuzione
    """
    workflow = StateGraph(HoroscopeState)
    
    # Aggiungiamo i nodi
    workflow.add_node("extract", extract_zodiac_and_period)
    workflow.add_node("fetch_horoscope", get_horoscope_data)
    workflow.add_node("translate", translate_and_format_horoscope)
    
    # Definiamo il flusso
    workflow.add_edge(START, "extract")
    
    # Da extract a fetch_horoscope se abbiamo il segno zodiacale
    workflow.add_conditional_edges(
        "extract",
        lambda state: "fetch" if state.get("zodiac_sign_en") else "end",
        {
            "fetch": "fetch_horoscope",
            "end": END
        }
    )
    
    # Da fetch_horoscope a translate se abbiamo i dati
    workflow.add_conditional_edges(
        "fetch_horoscope",
        lambda state: "translate" if state.get("horoscope_data") else "end",
        {
            "translate": "translate",
            "end": END
        }
    )
    
    # Da translate a END
    workflow.add_edge("translate", END)
    
    # Compiliamo il grafo
    graph = workflow.compile()
    
    return graph


def run_horoscope_agent(query: str) -> dict:
    """
    Esegue l'agente oroscopo con una query
    
    Args:
        query: La query dell'utente (es. "oroscopo dell'ariete oggi")
        
    Returns:
        Un dizionario con lo stato finale
    """
    graph = build_horoscope_agent()
    
    initial_state = {
        "query": query,
        "zodiac_sign": None,
        "zodiac_sign_en": None,
        "time_period": None,
        "horoscope_data": None,
        "messages": []
    }
    
    result = graph.invoke(initial_state)
    
    return result


def visualize_graph():
    """
    Visualizza il grafo dell'agente oroscopo (per debug e documentazione)
    """
    try:
        import matplotlib.pyplot as plt
        from langgraph.graph import StateGraph
        
        graph = build_horoscope_agent()
        
        # Genera il grafo Mermaid
        mermaid_code = graph.get_graph().draw_mermaid()
        
        print("Grafo Mermaid dell'agente oroscopo:")
        print(mermaid_code)
        
        # Salva in un file
        with open("horoscope_agent_graph.md", "w", encoding="utf-8") as f:
            f.write("# Grafo Agente Oroscopo\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n")
            
        # 2. Prova a generare l'immagine PNG
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            png_path = "horoscope_agent_graph.png"
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"Grafo PNG salvato in: {png_path}")
        except Exception as png_error:
            print(f"PNG non generato: {png_error}")
            print("  Installa le dipendenze opzionali per generare PNG:")
            print("  pip install pygraphviz o pip install pydot")
        
        print("\nGrafo salvato in horoscope_agent_graph.md")
        
    except Exception as e:
        print(f"Errore nella visualizzazione del grafo: {e}")


if __name__ == "__main__":
    
    # Visualizza il grafo
    print("\n" + "="*50 + "\n")
    visualize_graph()
