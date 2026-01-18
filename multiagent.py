"""
Sistema Multiagente Alexa-like con LangGraph
Supervisore che usa LLM per coordinare gli agenti specializzati
"""

import os
import json
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator
from dotenv import load_dotenv

from agents.weather_agent import run_weather_agent, visualize_graph
from agents.horoscope_agent import run_horoscope_agent
from agents.general_agent import run_general_agent

# Carica le variabili d'ambiente
load_dotenv()


class SupervisorState(TypedDict):
    """Stato del supervisore agente"""
    user_query: str
    selected_agent: str | None
    agent_result: dict | None
    messages: Annotated[list, operator.add]


def supervisor_router(state: SupervisorState) -> SupervisorState:
    """
    Supervisore che decide quale agente attivare basandosi sulla query dell'utente
    Usa OpenAI per una decisione intelligente
    
    Args:
        state: Lo stato del supervisore
        
    Returns:
        Lo stato aggiornato con l'agente selezionato
    """
    user_query = state["user_query"]
    
    # Aggiungiamo il messaggio dell'utente
    state["messages"].append(HumanMessage(content=user_query))
    
    try:
        # Inizializza il modello OpenAI
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Prompt per il routing
        routing_prompt = f"""Sei un supervisore di un sistema multiagente. La tua responsabilità è decidere quale agente specializzato attivare.

Agenti disponibili:
1. WEATHER - Specializzato in: meteo, condizioni atmosferiche, pioggia, neve, temperatura, umidità, sole, vento, clima
2. HOROSCOPE - Specializzato in: oroscopo, segni zodiacali, previsioni astrologiche
3. GENERAL - Specializzato in: saluti, presentazioni, small talk, conversazioni generiche, domande sull'assistente, ringraziamenti
4. WIKIPEDIA - Specializzato in: ricerca di voci, informazioni enciclopediche (non ancora disponibile)
5. BASIC - Specializzato in: calendario, calcolatrice, traduttore (non ancora disponibile)

IMPORTANTE:
- Usa GENERAL per: saluti (ciao, buongiorno), presentazioni (chi sei, cosa fai), ringraziamenti, conversazioni generiche
- Usa GENERAL come fallback per qualsiasi cosa non gestita dagli altri agenti
- Non usare mai NONE, usa sempre GENERAL se nessun altro agente è appropriato

Analizza la seguente query e decidi quale agente è il più appropriato.

Query utente: {user_query}

Rispondi in JSON con il seguente formato:
{{
    "agent": "WEATHER" | "HOROSCOPE" | "GENERAL" | "WIKIPEDIA" | "BASIC",
    "confidence": 0.0-1.0,
    "reason": "breve spiegazione"
}}

Usa GENERAL per tutto ciò che non è meteo, oroscopo, o funzionalità specifiche."""
        
        # Chiama OpenAI
        response = llm.invoke([
            SystemMessage(content="Sei un supervisore intelligente di un sistema multiagente."),
            HumanMessage(content=routing_prompt)
        ])
        
        # Parsa la risposta JSON
        try:
            decision = json.loads(response.content)
            selected_agent = decision.get("agent", "NONE").upper()
            confidence = decision.get("confidence", 0.0)
            reason = decision.get("reason", "")
            
            state["selected_agent"] = selected_agent
            
            if selected_agent != "NONE":
                state["messages"].append(
                    AIMessage(content=f"Ho analizzato la tua richiesta: {reason} (confidenza: {confidence*100:.0f}%). Attivo l'agente {selected_agent}...")
                )
            else:
                state["messages"].append(
                    AIMessage(content="Non riesco a identificare un agente appropriato per la tua richiesta.")
                )
                
        except json.JSONDecodeError:
            # Se il parsing JSON fallisce, prova a estrarre manualmente
            content_lower = response.content.lower()
            if "weather" in content_lower:
                state["selected_agent"] = "WEATHER"
                state["messages"].append(
                    AIMessage(content="Ho identificato una richiesta sul meteo. Attivo l'agente METEO...")
                )
            elif "horoscope" in content_lower or "oroscopo" in content_lower:
                state["selected_agent"] = "HOROSCOPE"
                state["messages"].append(
                    AIMessage(content="Ho identificato una richiesta sull'oroscopo. Attivo l'agente OROSCOPO...")
                )
            else:
                # Default a GENERAL per qualsiasi altra cosa
                state["selected_agent"] = "GENERAL"
                state["messages"].append(
                    AIMessage(content="Attivo l'agente conversazionale...")
                )
    
    except Exception as e:
        # In caso di errore, usa GENERAL come fallback
        state["selected_agent"] = "GENERAL"
        state["messages"].append(
            AIMessage(content=f"Errore nel routing: {str(e)}. Uso l'agente conversazionale.")
        )
    
    return state


def execute_weather_agent(state: SupervisorState) -> SupervisorState:
    """Esegue l'agente meteo"""
    if state.get("selected_agent") != "WEATHER":
        return state
    
    try:
        result = run_weather_agent(state["user_query"])
        state["agent_result"] = result
        
        # Aggiungi i messaggi dell'agente meteo
        for msg in result.get("messages", []):
            state["messages"].append(AIMessage(content=msg.content))
            
    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"Errore nell'esecuzione dell'agente METEO: {str(e)}")
        )
    
    return state


def execute_horoscope_agent(state: SupervisorState) -> SupervisorState:
    """Esegue l'agente oroscopo"""
    if state.get("selected_agent") != "HOROSCOPE":
        return state
    
    try:
        result = run_horoscope_agent(state["user_query"])
        state["agent_result"] = result
        
        # Aggiungi i messaggi dell'agente oroscopo
        for msg in result.get("messages", []):
            state["messages"].append(AIMessage(content=msg.content))
            
    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"Errore nell'esecuzione dell'agente OROSCOPO: {str(e)}")
        )
    
    return state


def execute_general_agent(state: SupervisorState) -> SupervisorState:
    """Esegue l'agente conversazionale generale"""
    if state.get("selected_agent") != "GENERAL":
        return state
    
    try:
        result = run_general_agent(state["user_query"])
        state["agent_result"] = result
        
        # Aggiungi i messaggi dell'agente general
        for msg in result.get("messages", []):
            state["messages"].append(AIMessage(content=msg.content))
            
    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"Errore nell'esecuzione dell'agente CONVERSAZIONALE: {str(e)}")
        )
    
    return state


def handle_unsupported_agent(state: SupervisorState) -> SupervisorState:
    """Gestisce gli agenti non ancora disponibili"""
    if state.get("selected_agent") in ["WIKIPEDIA", "BASIC"]:
        agent_name = state["selected_agent"]
        state["messages"].append(
            AIMessage(content=f"L'agente {agent_name} non è ancora disponibile. Scusa per il disagio!")
        )
    
    return state


def should_execute_agent(state: SupervisorState) -> bool:
    """Determina se eseguire un agente o terminare"""
    return state.get("selected_agent") and state["selected_agent"] != "NONE"


def build_supervisor_agent():
    """
    Costruisce il grafo del supervisore usando LangGraph
    
    Returns:
        Un CompiledGraph pronto per l'esecuzione
    """
    workflow = StateGraph(SupervisorState)
    
    # Aggiungiamo i nodi
    workflow.add_node("router", supervisor_router)
    workflow.add_node("weather_agent", execute_weather_agent)
    workflow.add_node("horoscope_agent", execute_horoscope_agent)
    workflow.add_node("general_agent", execute_general_agent)
    workflow.add_node("unsupported", handle_unsupported_agent)
    
    # Definiamo il flusso
    workflow.add_edge(START, "router")
    
    # Decisione: quale agente eseguire
    workflow.add_conditional_edges(
        "router",
        lambda state: "weather_agent" if state.get("selected_agent") == "WEATHER" 
                     else "horoscope_agent" if state.get("selected_agent") == "HOROSCOPE"
                     else "general_agent" if state.get("selected_agent") == "GENERAL"
                     else "unsupported" if state.get("selected_agent") in ["WIKIPEDIA", "BASIC"]
                     else "general_agent",  # Default a GENERAL invece di END
        {
            "weather_agent": "weather_agent",
            "horoscope_agent": "horoscope_agent",
            "general_agent": "general_agent",
            "unsupported": "unsupported"
        }
    )
    
    # Da weather_agent a END
    workflow.add_edge("weather_agent", END)
    
    # Da horoscope_agent a END
    workflow.add_edge("horoscope_agent", END)
    
    # Da general_agent a END
    workflow.add_edge("general_agent", END)
    
    # Da unsupported a END
    workflow.add_edge("unsupported", END)
    
    # Compiliamo il grafo
    graph = workflow.compile()
    
    return graph


def visualize_supervisor_graph():
    """
    Visualizza il grafo del supervisore in vari formati
    Genera:
    1. Diagramma Mermaid in console e file .md
    2. File PNG del grafo (se disponibili le dipendenze)
    3. Visualizzazione con matplotlib e networkx
    4. Dettagli testuali della struttura
    """
    graph = build_supervisor_agent()
    
    try:
        # 1. Genera la rappresentazione Mermaid
        mermaid_code = graph.get_graph().draw_mermaid()
        
        # Salva il diagramma Mermaid in un file .md
        mermaid_path = "supervisor_graph.md"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write("# Grafo Supervisore Multiagente\n\n")
            f.write("Questo grafo mostra il flusso del supervisore che coordina i vari agenti:\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n")
        print(f"✓ Diagramma Mermaid salvato in: {mermaid_path}")
        
        # 2. Prova a generare l'immagine PNG
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            png_path = "supervisor_graph.png"
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"✓ Grafo PNG salvato in: {png_path}")
        except Exception as png_error:
            print(f"⚠ PNG non generato: {png_error}")
        
        # Stampa il diagramma in console
        print("\n" + "="*70)
        print("STRUTTURA DEL GRAFO SUPERVISORE MULTIAGENTE")
        print("="*70)
        print("\n```mermaid")
        print(mermaid_code)
        print("```\n")
        
    except Exception as e:
        print(f"Errore nella visualizzazione Mermaid: {e}")
    
    # Stampa la struttura del grafo
    print("="*70)
    print("DETTAGLI DEL GRAFO SUPERVISORE")
    print("="*70)
    graph_structure = graph.get_graph()
    print(f"Nodi: {list(graph_structure.nodes.keys())}")
    print(f"Archi: {[(edge[0], edge[1]) for edge in graph_structure.edges]}")
    print("="*70 + "\n")


def run_supervisor(query: str) -> dict:
    """
    Esegue il supervisore con la query dell'utente
    
    Args:
        query: La domanda dell'utente
        
    Returns:
        Il risultato finale dello stato del supervisore
    """
    graph = build_supervisor_agent()
    
    initial_state = {
        "user_query": query,
        "selected_agent": None,
        "agent_result": None,
        "messages": []
    }
    
    result = graph.invoke(initial_state)
    
    return result


def main():
    """
    Funzione principale del sistema multiagente
    Implementa il supervisore intelligente
    """
    print("=" * 70)
    print("BENVENUTO NEL SISTEMA MULTIAGENTE ALEXA-LIKE")
    print("=" * 70)
    print("\nIl sistema usa un supervisore intelligente basato su LLM")
    print("per decidere quale agente specializzato attivare.\n")
    print("Agenti disponibili:")
    print("  • METEO - Ottiene dati meteorologici")
    print("  • OROSCOPO - Fornisce oroscopi tradotti in italiano")
    print("  • GENERAL - Gestisce conversazioni, saluti e domande generiche")
    print("  • WIKIPEDIA - Ricerca informazioni (prossimamente)")
    print("  • BASIC - Calendario, Calcolatrice, Traduttore (prossimamente)")
    print("\nComandi speciali:")
    print("  - 'grafo' - Visualizza il grafo del supervisore")
    print("  - 'grafo-meteo' - Visualizza il grafo dell'agente meteo")
    print("  - 'grafo-oroscopo' - Visualizza il grafo dell'agente oroscopo")
    print("  - 'grafo-general' - Visualizza il grafo dell'agente conversazionale")
    print("  - 'esci' - Esce dall'applicazione\n")
    
    while True:
        user_query = input("Tu: ").strip()
        
        if user_query.lower() in ["esci", "exit", "quit"]:
            print("Arrivederci!")
            break
        
        if user_query.lower() == "grafo":
            print("\n")
            visualize_supervisor_graph()
            print("\n")
            continue
        
        if user_query.lower() == "grafo-meteo":
            print("\n")
            visualize_graph()
            print("\n")
            continue
        
        if user_query.lower() == "grafo-oroscopo":
            print("\n")
            from agents.horoscope_agent import visualize_graph as visualize_horoscope_graph
            visualize_horoscope_graph()
            print("\n")
            continue
        
        if user_query.lower() == "grafo-general":
            print("\n")
            from agents.general_agent import visualize_graph as visualize_general_graph
            visualize_general_graph()
            print("\n")
            continue
        
        if not user_query:
            continue
        
        print("\n→ Supervisore in elaborazione...\n")
        
        # Esegui il supervisore
        result = run_supervisor(user_query)
        
        # Mostra i messaggi
        for msg in result.get("messages", []):
            print(f"Alexa: {msg.content}\n")


if __name__ == "__main__":
    main()
