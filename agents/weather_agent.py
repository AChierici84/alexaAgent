"""
Agente Meteo - Estrae la località e il tempo, recupera dati da Open-Meteo API
Utilizza OpenAI per l'estrazione intelligente e coordinate geografiche
"""

import os
import requests
import json
from datetime import datetime, timedelta
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator
from dotenv import load_dotenv
import openmeteo_requests
import requests_cache
from retry_requests import retry

# Carica le variabili d'ambiente
load_dotenv()


class AgentState(TypedDict):
    """Stato dell'agente meteo"""
    query: str
    location: str | None
    latitude: float | None
    longitude: float | None
    days_offset: int | None
    date_str: str | None
    weather_data: dict | None
    messages: Annotated[list, operator.add]


def extract_location_and_date(state: AgentState) -> AgentState:
    """
    Estrae la località e il tempo dalla query dell'utente usando OpenAI
    Valida che il tempo sia entro 7 giorni da oggi
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con la località e il tempo estratti
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
        
        # Prompt per l'estrazione della città e del tempo
        today = datetime.now().strftime("%d/%m/%Y")
        
        prompt = f"""Analizza questa query in italiano ed estrai il nome della città e l'indicazione temporale.

Data odierna: {today}

Regole:
- Se non c'è indicazione temporale, assume "oggi"
- Il tempo può essere: "oggi", "domani", "dopodomani", un giorno della settimana (es. martedì), una data specifica
- Calcola i giorni da oggi (0=oggi, 1=domani, 2=dopodomani, etc.)
- Massimo 7 giorni da oggi. Se la data è nel passato o oltre 7 giorni, rispondi "INVALIDO"
- Giorni della settimana vanno calcolati come il prossimo (es. se oggi è martedì e dice "martedì", intende martedì prossimo)

Query: {query}

Rispondi in JSON con questo formato esatto:
{{
    "location": "nome città",
    "days_offset": 0-7 (numero di giorni da oggi),
    "time_description": "descrizione breve del tempo (es. 'oggi', 'domani', 'giovedì prossimo')",
    "validity": "VALIDO" o "INVALIDO"
}}

Se non trovi una città rispondi con "location": "NESSUNA"
Se il tempo è invalido rispondi con "validity": "INVALIDO"
"""
        
        # Chiama OpenAI
        response = llm.invoke([
            SystemMessage(content="Sei un assistente che estrae città e date da testo italiano. Rispondi sempre in JSON."),
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
        
        location = data.get("location", "NESSUNA").strip()
        days_offset = data.get("days_offset", 0)
        validity = data.get("validity", "INVALIDO")
        time_description = data.get("time_description", "oggi")
        
        # Validazione
        if location.upper() == "NESSUNA":
            state["location"] = None
            state["messages"].append(
                AIMessage(content="Non ho riconosciuto una località specifica nella tua richiesta. Puoi indicarmi una città?")
            )
            return state
        
        if validity.upper() == "INVALIDO" or not (0 <= days_offset <= 7):
            state["location"] = None
            state["days_offset"] = None
            state["messages"].append(
                AIMessage(content=f"Scusa, posso fornire il meteo solo per i prossimi 7 giorni da oggi, non nel passato. {location} quale giorno?")
            )
            return state
        
        state["location"] = location
        state["days_offset"] = days_offset
        
        # Calcola la data
        target_date = datetime.now() + timedelta(days=days_offset)
        state["date_str"] = target_date.strftime("%d/%m/%Y")
        
        if days_offset == 0:
            time_label = "oggi"
        elif days_offset == 1:
            time_label = "domani"
        elif days_offset == 2:
            time_label = "dopodomani"
        else:
            time_label = f"tra {days_offset} giorni"
        
        state["messages"].append(
            AIMessage(content=f"Ho identificato: città {location}, meteo per {time_label}. Sto recuperando i dati...")
        )
        
    except Exception as e:
        state["location"] = None
        state["days_offset"] = None
        state["messages"].append(
            AIMessage(content=f"Errore nell'analisi della richiesta: {str(e)}. Controlla la tua API key di OpenAI.")
        )
    
    return state


def get_coordinates(state: AgentState) -> AgentState:
    """
    Ottiene le coordinate geografiche della località usando Nominatim (OpenStreetMap)
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con le coordinate
    """
    if not state.get("location"):
        return state
    
    try:
        location = state["location"]
        
        # Usa Nominatim per geocoding (gratuito, no API key)
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": f"{location}, Italia",
            "format": "json",
            "limit": 1
        }
        headers = {
            "User-Agent": "WeatherAgent/1.0"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data and len(data) > 0:
            state["latitude"] = float(data[0]["lat"])
            state["longitude"] = float(data[0]["lon"])
            
            state["messages"].append(
                AIMessage(content=f"Coordinate trovate: {state['latitude']:.4f}°N, {state['longitude']:.4f}°E")
            )
        else:
            state["latitude"] = None
            state["longitude"] = None
            state["messages"].append(
                AIMessage(content=f"Non riesco a trovare le coordinate per {location}. Verifica il nome della città.")
            )
    
    except Exception as e:
        state["latitude"] = None
        state["longitude"] = None
        state["messages"].append(
            AIMessage(content=f"Errore nel recupero delle coordinate: {str(e)}")
        )
    
    return state


def fetch_weather(state: AgentState) -> AgentState:
    """
    Recupera i dati meteo da Open-Meteo API
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con i dati meteo
    """
    if not state.get("location") or state.get("latitude") is None or state.get("longitude") is None:
        state["messages"].append(
            AIMessage(content="Non posso recuperare i dati meteo senza coordinate valide.")
        )
        return state
    
    try:
        location = state["location"]
        latitude = state["latitude"]
        longitude = state["longitude"]
        days_offset = state.get("days_offset", 0)
        
        # Setup Open-Meteo API client con cache e retry
        cache_session = requests_cache.CachedSession('.cache', expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)
        
        # Parametri per Open-Meteo API
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "windspeed_10m_max",
                "weathercode"
            ],
            "timezone": "Europe/Rome",
            "forecast_days": 8
        }
        
        # Chiama l'API
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]
        
        # Processa i dati giornalieri
        daily = response.Daily()
        daily_temperature_max = daily.Variables(0).ValuesAsNumpy()
        daily_temperature_min = daily.Variables(1).ValuesAsNumpy()
        daily_precipitation = daily.Variables(2).ValuesAsNumpy()
        daily_precipitation_probability = daily.Variables(3).ValuesAsNumpy()
        daily_windspeed = daily.Variables(4).ValuesAsNumpy()
        daily_weathercode = daily.Variables(5).ValuesAsNumpy()
        
        # Estrai i dati per il giorno richiesto
        if days_offset < len(daily_temperature_max):
            # Decodifica il weather code
            weather_descriptions = {
                0: "Cielo sereno",
                1: "Prevalentemente sereno",
                2: "Parzialmente nuvoloso",
                3: "Nuvoloso",
                45: "Nebbia",
                48: "Nebbia con brina",
                51: "Pioviggine leggera",
                53: "Pioviggine moderata",
                55: "Pioviggine intensa",
                61: "Pioggia leggera",
                63: "Pioggia moderata",
                65: "Pioggia forte",
                71: "Neve leggera",
                73: "Neve moderata",
                75: "Neve intensa",
                80: "Rovesci leggeri",
                81: "Rovesci moderati",
                82: "Rovesci violenti",
                95: "Temporale",
                96: "Temporale con grandine leggera",
                99: "Temporale con grandine"
            }
            
            weathercode = int(daily_weathercode[days_offset])
            condition = weather_descriptions.get(weathercode, f"Codice {weathercode}")
            
            # Determina il giorno in formato leggibile
            if days_offset == 0:
                time_label = "oggi"
            elif days_offset == 1:
                time_label = "domani"
            elif days_offset == 2:
                time_label = "dopodomani"
            else:
                time_label = f"tra {days_offset} giorni"
            
            weather_data = {
                "location": location,
                "latitude": latitude,
                "longitude": longitude,
                "days_offset": days_offset,
                "date": state.get("date_str"),
                "temperature_max": f"{daily_temperature_max[days_offset]:.1f}°C",
                "temperature_min": f"{daily_temperature_min[days_offset]:.1f}°C",
                "precipitation": f"{daily_precipitation[days_offset]:.1f} mm",
                "precipitation_probability": f"{daily_precipitation_probability[days_offset]:.0f}%",
                "windspeed": f"{daily_windspeed[days_offset]:.1f} km/h",
                "condition": condition,
                "weathercode": weathercode,
                "status": "recuperato",
                "source": "Open-Meteo API"
            }
            
            state["weather_data"] = weather_data
            
            # Crea la risposta formattata
            response_text = f"\n{'='*60}\n"
            response_text += f"METEO A {location.upper()}\n"
            response_text += f"{'='*60}\n"
            response_text += f"{time_label.capitalize()} ({state.get('date_str')})\n"
            response_text += f"Coordinate: {latitude:.4f}°N, {longitude:.4f}°E\n\n"
            response_text += f"Condizione: {condition}\n"
            response_text += f"Temperatura: Min {weather_data['temperature_min']} / Max {weather_data['temperature_max']}\n"
            response_text += f"Precipitazioni: {weather_data['precipitation']} (probabilità {weather_data['precipitation_probability']})\n"
            response_text += f"Vento: {weather_data['windspeed']}\n"
            response_text += f"\nFonte: Open-Meteo API\n"
            response_text += f"{'='*60}\n"
            
            state["messages"].append(AIMessage(content=response_text))
        else:
            state["messages"].append(
                AIMessage(content=f"Dati meteo non disponibili per il giorno richiesto.")
            )
            state["weather_data"] = {"error": "Giorno non disponibile"}
        
    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"Scusa, non riesco a recuperare i dati meteo per {state['location']}. Errore: {str(e)}")
        )
        state["weather_data"] = {"error": str(e)}
    
    return state


def build_weather_agent():
    """
    Costruisce il grafo dell'agente meteo usando LangGraph
    
    Returns:
        Un CompiledGraph pronto per l'esecuzione
    """
    workflow = StateGraph(AgentState)
    
    # Aggiungiamo i nodi
    workflow.add_node("extract_location_and_date", extract_location_and_date)
    workflow.add_node("get_coordinates", get_coordinates)
    workflow.add_node("fetch_weather", fetch_weather)
    
    # Definiamo il flusso
    workflow.add_edge(START, "extract_location_and_date")
    workflow.add_edge("extract_location_and_date", "get_coordinates")
    workflow.add_edge("get_coordinates", "fetch_weather")
    workflow.add_edge("fetch_weather", END)
    
    # Compiliamo il grafo
    graph = workflow.compile()
    
    return graph


def visualize_graph():
    """
    Visualizza il grafo dell'agente meteo in vari formati
    Genera:
    1. Diagramma Mermaid in console e file .md
    2. File PNG del grafo (se disponibili le dipendenze)
    3. Dettagli testuali della struttura
    
    Returns:
        Una stringa con la rappresentazione ASCII del grafo
    """
    graph = build_weather_agent()
    
    try:
        # 1. Genera la rappresentazione Mermaid
        mermaid_code = graph.get_graph().draw_mermaid()
        
        # Salva il diagramma Mermaid in un file .md
        mermaid_path = "weather_agent_graph.md"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write("# Grafo Agente Meteo\n\n")
            f.write("Questo grafo mostra il flusso dell'agente meteo:\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n")
        print(f"✓ Diagramma Mermaid salvato in: {mermaid_path}")
        
        # 2. Prova a generare l'immagine PNG
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            png_path = "weather_agent_graph.png"
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"Grafo PNG salvato in: {png_path}")
        except Exception as png_error:
            print(f"PNG non generato: {png_error}")
            print("  Installa le dipendenze opzionali per generare PNG:")
            print("  pip install pygraphviz o pip install pydot")
        
        # Stampa il diagramma in console
        print("\n" + "="*60)
        print("STRUTTURA DEL GRAFO DELL'AGENTE METEO")
        print("="*60)
        print("\n```mermaid")
        print(mermaid_code)
        print("```\n")
        
    except Exception as e:
        print(f"Errore nella visualizzazione: {e}")
    
    # Stampa la struttura del grafo
    print("="*60)
    print("DETTAGLI DEL GRAFO")
    print("="*60)
    graph_structure = graph.get_graph()
    print(f"Nodi: {list(graph_structure.nodes.keys())}")
    print(f"Archi: {[(edge[0], edge[1]) for edge in graph_structure.edges]}")
    print("="*60 + "\n")

# Funzione per eseguire l'agente
def run_weather_agent(query: str) -> dict:
    """
    Esegue l'agente meteo con la query dell'utente
    
    Args:
        query: La domanda dell'utente
        
    Returns:
        Il risultato finale dello stato dell'agente
    """
    
    graph = build_weather_agent()
    
    initial_state = {
        "query": query,
        "location": None,
        "latitude": None,
        "longitude": None,
        "days_offset": None,
        "date_str": None,
        "weather_data": None,
        "messages": []
    }
    
    result = graph.invoke(initial_state)
    
    return result


 
if __name__ == "__main__":
    
    # Visualizza il grafo
    print("\n")
    visualize_graph()
    print("\n")
    
