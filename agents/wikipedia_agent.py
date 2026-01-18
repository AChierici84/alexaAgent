"""
Agente Wikipedia - Cerca informazioni enciclopediche su Wikipedia in italiano
Estrae il contenuto e usa l'LLM per rispondere alla domanda dell'utente
"""

import os
import wikipedia
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()

# Configura Wikipedia in italiano
wikipedia.set_lang("it")


class WikipediaState(TypedDict):
    """Stato dell'agente Wikipedia"""
    query: str
    search_query: str | None
    search_results: list | None
    page_content: str | None
    page_title: str | None
    response: str | None
    messages: Annotated[list, operator.add]


def extract_search_terms(state: WikipediaState) -> WikipediaState:
    """
    Estrae i termini di ricerca ottimali dalla query dell'utente usando OpenAI
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con i termini di ricerca estratti
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
        
        # Prompt per l'estrazione dei termini di ricerca
        extraction_prompt = f"""Analizza la seguente domanda ed estrai i termini chiave da cercare su Wikipedia.

Esempi:
- "Chi era Leonardo da Vinci?" -> "Leonardo da Vinci"
- "Dimmi qualcosa sulla torre di Pisa" -> "Torre di Pisa"
- "Cosa è la fotosintesi clorofilliana?" -> "Fotosintesi clorofilliana"
- "Quando è stata scoperta l'America?" -> "Scoperta dell'America"

Domanda utente: {query}

Rispondi SOLO con i termini di ricerca, senza spiegazioni."""
        
        # Chiama OpenAI
        response = llm.invoke([
            SystemMessage(content="Sei un esperto nell'estrazione di termini di ricerca per Wikipedia."),
            HumanMessage(content=extraction_prompt)
        ])
        
        search_query = response.content.strip()
        state["search_query"] = search_query
        
        state["messages"].append(
            AIMessage(content=f"Termini di ricerca estratti: '{search_query}'")
        )
        
    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"Errore nell'estrazione dei termini: {str(e)}")
        )
        state["search_query"] = query  # Fallback: usa la query originale
    
    return state


def search_wikipedia(state: WikipediaState) -> WikipediaState:
    """
    Cerca su Wikipedia in italiano
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con i risultati della ricerca
    """
    search_query = state.get("search_query", state["query"])
    
    try:
        # Cerca su Wikipedia
        results = wikipedia.search(search_query, results=5)
        state["search_results"] = results
        
        if results:
            state["messages"].append(
                AIMessage(content=f"Trovati {len(results)} risultati: {', '.join(results[:3])}...")
            )
        else:
            state["messages"].append(
                AIMessage(content="Nessun risultato trovato su Wikipedia.")
            )
            
    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"Errore nella ricerca Wikipedia: {str(e)}")
        )
        state["search_results"] = []
    
    return state


def fetch_page_content(state: WikipediaState) -> WikipediaState:
    """
    Recupera il contenuto della pagina Wikipedia più rilevante
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con il contenuto della pagina
    """
    results = state.get("search_results", [])
    
    if not results:
        state["page_content"] = None
        state["page_title"] = None
        return state
    
    # Prova a recuperare la prima pagina
    for result in results[:3]:  # Prova le prime 3 per sicurezza
        try:
            page = wikipedia.page(result, auto_suggest=False)
            
            # Limita il contenuto a ~4000 caratteri per non sovraccaricare l'LLM
            content = page.content[:4000]
            if len(page.content) > 4000:
                content += "... (contenuto troncato)"
            
            state["page_content"] = content
            state["page_title"] = page.title
            state["messages"].append(
                AIMessage(content=f"Recuperata pagina: '{page.title}' ({len(page.content)} caratteri)")
            )
            break
            
        except wikipedia.exceptions.DisambiguationError as e:
            # Pagina di disambiguazione - prova con la prima opzione
            try:
                page = wikipedia.page(e.options[0], auto_suggest=False)
                content = page.content[:4000]
                if len(page.content) > 4000:
                    content += "... (contenuto troncato)"
                    
                state["page_content"] = content
                state["page_title"] = page.title
                state["messages"].append(
                    AIMessage(content=f"Trovata disambiguazione, uso: '{page.title}'")
                )
                break
            except:
                continue
                
        except wikipedia.exceptions.PageError:
            # Pagina non trovata - prova la prossima
            continue
            
        except Exception as e:
            state["messages"].append(
                AIMessage(content=f"Errore nel recupero della pagina '{result}': {str(e)}")
            )
            continue
    
    if not state.get("page_content"):
        state["messages"].append(
            AIMessage(content="Impossibile recuperare il contenuto di nessuna pagina.")
        )
    
    return state


def generate_answer(state: WikipediaState) -> WikipediaState:
    """
    Genera una risposta alla domanda dell'utente usando il contenuto di Wikipedia e l'LLM
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con la risposta generata
    """
    query = state["query"]
    page_content = state.get("page_content")
    page_title = state.get("page_title")
    
    if not page_content:
        state["response"] = "Mi dispiace, non ho trovato informazioni su Wikipedia riguardo a questa domanda."
        state["messages"].append(
            AIMessage(content=state["response"])
        )
        return state
    
    try:
        # Inizializza il modello OpenAI
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Prompt per generare la risposta
        answer_prompt = f"""Hai a disposizione il contenuto di una pagina Wikipedia. Usa queste informazioni per rispondere alla domanda dell'utente.

CONTENUTO WIKIPEDIA (pagina: "{page_title}"):
{page_content}

DOMANDA UTENTE:
{query}

ISTRUZIONI:
- Rispondi alla domanda in modo chiaro e conciso
- Usa SOLO le informazioni presenti nel contenuto Wikipedia fornito
- Non inventare informazioni
- Se la domanda non può essere risposta con il contenuto fornito, dillo chiaramente
- Mantieni un tono informativo ma amichevole
- Rispondi in italiano
- Non menzionare esplicitamente che le informazioni provengono da Wikipedia

Fornisci la tua risposta:"""
        
        # Chiama OpenAI
        response = llm.invoke([
            SystemMessage(content="Sei un assistente esperto che risponde a domande basandoti su contenuti enciclopedici."),
            HumanMessage(content=answer_prompt)
        ])
        
        state["response"] = response.content.strip()
        state["messages"].append(
            AIMessage(content=state["response"])
        )
        
    except Exception as e:
        state["response"] = f"Mi dispiace, si è verificato un errore nel generare la risposta: {str(e)}"
        state["messages"].append(
            AIMessage(content=state["response"])
        )
    
    return state


def build_graph() -> StateGraph:
    """Costruisce il grafo dell'agente Wikipedia"""
    workflow = StateGraph(WikipediaState)
    
    # Aggiungi i nodi
    workflow.add_node("extract_search", extract_search_terms)
    workflow.add_node("search", search_wikipedia)
    workflow.add_node("fetch_content", fetch_page_content)
    workflow.add_node("generate", generate_answer)
    
    # Definisci il flusso
    workflow.add_edge(START, "extract_search")
    workflow.add_edge("extract_search", "search")
    workflow.add_edge("search", "fetch_content")
    workflow.add_edge("fetch_content", "generate")
    workflow.add_edge("generate", END)
    
    return workflow.compile()


def run_wikipedia_agent(query: str) -> dict:
    """
    Esegue l'agente Wikipedia per rispondere a una domanda enciclopedica
    
    Args:
        query: La domanda dell'utente
        
    Returns:
        Un dizionario con i risultati dell'agente
    """
    # Costruisce il grafo
    graph = build_graph()
    
    # Stato iniziale
    initial_state = {
        "query": query,
        "search_query": None,
        "search_results": None,
        "page_content": None,
        "page_title": None,
        "response": None,
        "messages": []
    }
    
    # Esegui il grafo
    result = graph.invoke(initial_state)
    
    return {
        "success": result.get("response") is not None,
        "response": result.get("response", "Non sono riuscito a trovare una risposta."),
        "page_title": result.get("page_title"),
        "search_results": result.get("search_results", []),
        "messages": result.get("messages", [])
    }


def visualize_graph():
    """Visualizza il grafo dell'agente Wikipedia"""
    graph = build_graph()
    
    # Genera il grafo Mermaid
    mermaid_code = graph.get_graph().draw_mermaid()
        
    print("Grafo Mermaid dell'agente wikipedia:")
    print(mermaid_code)
        
    # Salva in un file
    with open("wikipedia_agent_graph.md", "w", encoding="utf-8") as f:
        f.write("# Grafo Agente Wikipedia\n\n")
        f.write("```mermaid\n")
        f.write(mermaid_code)
        f.write("\n```\n")
        
    print("\nGrafo salvato in wikipedia_agent_graph.md")
        
    #Prova a generare l'immagine PNG
    try:
        png_data = graph.get_graph().draw_mermaid_png()
        png_path = "wikipedia_agent_graph.png"
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
    # Test dell'agente
    print("=== Test Agente Wikipedia ===\n")
    
    test_queries = [
        "Chi era Leonardo da Vinci?",
        "Cos'è la fotosintesi?",
        "Dimmi qualcosa sulla Torre di Pisa"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        print("-" * 50)
        result = run_wikipedia_agent(query)
        print(f"Successo: {result['success']}")
        print(f"Pagina: {result['page_title']}")
        print(f"Risposta: {result['response']}")
        print("=" * 50)
