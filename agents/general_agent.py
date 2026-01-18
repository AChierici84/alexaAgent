"""
Agente General - Gestisce small talk, saluti, presentazioni e query generiche
Utilizza OpenAI per conversazioni naturali
"""

import os
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()


class GeneralState(TypedDict):
    """Stato dell'agente general"""
    query: str
    response: str | None
    messages: Annotated[list, operator.add]


def generate_response(state: GeneralState) -> GeneralState:
    """
    Genera una risposta conversazionale usando OpenAI
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con la risposta generata
    """
    query = state["query"]
    
    # Aggiungiamo il messaggio dell'utente
    state["messages"].append(HumanMessage(content=query))
    
    try:
        # Inizializza il modello OpenAI
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,  # Più creativo per conversazioni
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # System prompt per definire la personalità dell'assistente
        system_prompt = """Sei Alexa, un assistente virtuale amichevole e disponibile in italiano.

La tua personalità:
- Cordiale, naturale e spontanea
- Varia le tue risposte, non usare sempre le stesse frasi
- Chiara e concisa nelle risposte
- Disponibile ad aiutare
- Parli sempre in italiano
- Rispondi in modo naturale e umano, non robotico

Gestisci:
- Saluti (ciao, buongiorno, buonasera, arrivederci)
- Presentazioni (chi sei, cosa sai fare)
- Ringraziamenti
- Small talk e conversazioni generiche
- Domande sulla tua funzionalità
- Qualsiasi altra domanda non tecnica

Quando rispondi ai saluti, VARIA le tue risposte. Esempi:
- "Ciao! Dimmi pure, sono qui per aiutarti."
- "Ciao! Cosa posso fare per te?"
- "Ehi! Cosa ti serve?"
- "Salve! Ti ascolto."
- "Ciao! Sono pronta ad aiutarti."
- "Buongiorno! Di cosa hai bisogno?"
- "Ciao! Eccomi, dimmi tutto."

Quando ti presentano, spiega in modo vario che sei un assistente virtuale multiagente che può:
- Fornire informazioni meteo
- Dare oroscopi
- Cercare informazioni su Wikipedia
- Rispondere a domande generali
- Conversare in modo naturale

Mantieni le risposte brevi (2-4 frasi) a meno che non sia richiesto maggior dettaglio.

IMPORTANTE: Non usare sempre "Come posso aiutarti oggi?". Sii creativa e varia le tue risposte!"""

        # Chiama OpenAI
        response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=query)
        ])
        
        response_text = response.content.strip()
        state["response"] = response_text
        
        state["messages"].append(AIMessage(content=response_text))
        
    except Exception as e:
        error_msg = f"Mi dispiace, ho avuto un problema nel generare la risposta: {str(e)}"
        state["response"] = error_msg
        state["messages"].append(AIMessage(content=error_msg))
    
    return state


def build_general_agent():
    """
    Costruisce il grafo dell'agente general usando LangGraph
    
    Returns:
        Un CompiledGraph pronto per l'esecuzione
    """
    workflow = StateGraph(GeneralState)
    
    # Aggiungiamo il nodo
    workflow.add_node("generate", generate_response)
    
    # Definiamo il flusso
    workflow.add_edge(START, "generate")
    workflow.add_edge("generate", END)
    
    # Compiliamo il grafo
    graph = workflow.compile()
    
    return graph


def run_general_agent(query: str) -> dict:
    """
    Esegue l'agente general con una query
    
    Args:
        query: La query dell'utente (es. "Ciao, come stai?")
        
    Returns:
        Un dizionario con lo stato finale
    """
    graph = build_general_agent()
    
    initial_state = {
        "query": query,
        "response": None,
        "messages": []
    }
    
    result = graph.invoke(initial_state)
    
    return result


def visualize_graph():
    """
    Visualizza il grafo dell'agente general (per debug e documentazione)
    """
    try:
        graph = build_general_agent()
        
        # Genera il grafo Mermaid
        mermaid_code = graph.get_graph().draw_mermaid()
        
        print("Grafo Mermaid dell'agente general:")
        print(mermaid_code)
        
        # Salva in un file
        with open("general_agent_graph.md", "w", encoding="utf-8") as f:
            f.write("# Grafo Agente General\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n")
        
        print("\nGrafo salvato in general_agent_graph.md")
        
        #Prova a generare l'immagine PNG
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            png_path = "general_agent_graph.png"
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"Grafo PNG salvato in: {png_path}")
        except Exception as png_error:
            print(f"PNG non generato: {png_error}")
            print("  Installa le dipendenze opzionali per generare PNG:")
            print("  pip install pygraphviz o pip install pydot")
        
    except Exception as e:
        print(f"Errore nella visualizzazione del grafo: {e}")


if __name__ == "__main__":
    
    # Visualizza il grafo
    print("\n" + "="*60)
    visualize_graph()
