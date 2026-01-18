"""
Agente Traduttore - Traduce testo tra diverse lingue usando OpenAI
Supporta rilevamento automatico della lingua di origine e oltre 100 lingue
"""

import os
import json
import re
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import operator
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()


class TranslatorState(TypedDict):
    """Stato dell'agente traduttore"""
    query: str
    text_to_translate: str | None
    source_language: str | None
    target_language: str | None
    translated_text: str | None
    messages: Annotated[list, operator.add]


# Lingue supportate (principali)
SUPPORTED_LANGUAGES = {
    "italiano": "it",
    "inglese": "en",
    "francese": "fr",
    "spagnolo": "es",
    "tedesco": "de",
    "portoghese": "pt",
    "russo": "ru",
    "cinese": "zh",
    "giapponese": "ja",
    "coreano": "ko",
    "arabo": "ar",
    "olandese": "nl",
    "polacco": "pl",
    "turco": "tr",
    "greco": "el",
    "svedese": "sv",
    "norvegese": "no",
    "danese": "da",
    "finlandese": "fi",
    "ceco": "cs",
    "rumeno": "ro",
    "ungherese": "hu",
    "hindi": "hi",
    "thai": "th",
    "vietnamita": "vi",
    "ebraico": "he",
    "indonesiano": "id",
    "malese": "ms",
    "ucraino": "uk",
    "catalano": "ca",
    "croato": "hr",
    "bulgaro": "bg",
    "slovacco": "sk",
    "sloveno": "sl",
    "serbo": "sr",
    "lituano": "lt",
    "lettone": "lv",
    "estone": "et"
}


def extract_translation_request(state: TranslatorState) -> TranslatorState:
    """
    Estrae il testo da tradurre e le lingue dalla query usando OpenAI
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con i dettagli della traduzione
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
        
        # Lista lingue per il prompt
        lingue_lista = ", ".join(list(SUPPORTED_LANGUAGES.keys())[:20]) + ", e altre..."
        
        prompt = f"""Analizza questa query in italiano ed estrai i dettagli della traduzione richiesta.

Lingue principali supportate: {lingue_lista}

Query: {query}

Identifica:
1. Il testo da tradurre (può essere una parola, frase o più frasi)
2. La lingua di origine (se specificata, altrimenti "auto" per rilevamento automatico)
3. La lingua di destinazione

Rispondi in JSON con questo formato:
{{
    "text": "testo da tradurre",
    "source_lang": "nome lingua origine o 'auto'",
    "target_lang": "nome lingua destinazione",
    "valid": true o false
}}

Esempi:
- "traduci hello in italiano" -> {{"text": "hello", "source_lang": "inglese", "target_lang": "italiano", "valid": true}}
- "come si dice buongiorno in francese" -> {{"text": "buongiorno", "source_lang": "italiano", "target_lang": "francese", "valid": true}}
- "traduci questa frase in inglese: mi chiamo Paolo" -> {{"text": "mi chiamo Paolo", "source_lang": "italiano", "target_lang": "inglese", "valid": true}}
- "che significa thank you" -> {{"text": "thank you", "source_lang": "auto", "target_lang": "italiano", "valid": true}}
- "traduci in spagnolo: dove si trova la stazione" -> {{"text": "dove si trova la stazione", "source_lang": "italiano", "target_lang": "spagnolo", "valid": true}}

Se non è una richiesta di traduzione, metti "valid": false
"""
        
        # Chiama OpenAI
        response = llm.invoke([
            SystemMessage(content="Sei un esperto nell'estrarre richieste di traduzione da testo in linguaggio naturale."),
            HumanMessage(content=prompt)
        ])
        
        # Parsa la risposta JSON
        try:
            data = json.loads(response.content)
        except json.JSONDecodeError:
            # Prova a estrarre il JSON dalla risposta
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                raise ValueError("Impossibile estrarre JSON dalla risposta")
        
        if not data.get("valid", False):
            state["text_to_translate"] = None
            state["messages"].append(
                AIMessage(content="Non riesco a identificare una richiesta di traduzione valida. Prova con: 'traduci [testo] in [lingua]' o 'come si dice [testo] in [lingua]'")
            )
            return state
        
        state["text_to_translate"] = data.get("text", "").strip()
        source_lang = data.get("source_lang", "auto").lower()
        target_lang = data.get("target_lang", "").lower()
        
        # Normalizza i nomi delle lingue
        if source_lang != "auto":
            # Cerca nei nomi delle lingue supportate
            source_lang_matched = None
            for lang_name, lang_code in SUPPORTED_LANGUAGES.items():
                if source_lang in lang_name or lang_name in source_lang:
                    source_lang_matched = lang_name
                    break
            state["source_language"] = source_lang_matched if source_lang_matched else source_lang
        else:
            state["source_language"] = "auto"
        
        # Target language
        target_lang_matched = None
        for lang_name, lang_code in SUPPORTED_LANGUAGES.items():
            if target_lang in lang_name or lang_name in target_lang:
                target_lang_matched = lang_name
                break
        
        if not target_lang_matched:
            state["target_language"] = None
            state["messages"].append(
                AIMessage(content=f"Lingua di destinazione '{target_lang}' non riconosciuta. Lingue supportate: {', '.join(list(SUPPORTED_LANGUAGES.keys())[:10])}, ...")
            )
            return state
        
        state["target_language"] = target_lang_matched
        
        if not state["text_to_translate"]:
            state["messages"].append(
                AIMessage(content="Non ho identificato il testo da tradurre. Puoi riformulare la richiesta?")
            )
            return state
        
        source_display = state["source_language"] if state["source_language"] != "auto" else "rilevamento automatico"
        state["messages"].append(
            AIMessage(content=f"Traduzione da {source_display} a {state['target_language']} in corso...")
        )
        
    except Exception as e:
        state["text_to_translate"] = None
        state["messages"].append(
            AIMessage(content=f"Errore nell'analisi della richiesta: {str(e)}")
        )
    
    return state


def perform_translation(state: TranslatorState) -> TranslatorState:
    """
    Esegue la traduzione usando OpenAI
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con il testo tradotto
    """
    if not state.get("text_to_translate") or not state.get("target_language"):
        return state
    
    try:
        text = state["text_to_translate"]
        source_lang = state.get("source_language", "auto")
        target_lang = state["target_language"]
        
        # Inizializza il modello OpenAI per traduzione
        llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.3,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Costruisci il prompt di traduzione
        if source_lang == "auto":
            translation_prompt = f"""Traduci il seguente testo in {target_lang}. 
Rileva automaticamente la lingua di origine e fornisci una traduzione accurata e naturale.

Testo da tradurre:
{text}

Fornisci SOLO la traduzione, senza spiegazioni o note aggiuntive."""
        else:
            translation_prompt = f"""Traduci il seguente testo da {source_lang} a {target_lang}.
Fornisci una traduzione accurata e naturale.

Testo da tradurre:
{text}

Fornisci SOLO la traduzione, senza spiegazioni o note aggiuntive."""
        
        # Chiama OpenAI per la traduzione
        response = llm.invoke([
            SystemMessage(content="Sei un traduttore professionale esperto in molteplici lingue. Fornisci traduzioni accurate, fluenti e contestualmente appropriate."),
            HumanMessage(content=translation_prompt)
        ])
        
        translated_text = response.content.strip()
        
        # Rimuovi eventuali virgolette aggiunte
        if translated_text.startswith('"') and translated_text.endswith('"'):
            translated_text = translated_text[1:-1]
        if translated_text.startswith("'") and translated_text.endswith("'"):
            translated_text = translated_text[1:-1]
        
        state["translated_text"] = translated_text
        
    except Exception as e:
        state["translated_text"] = None
        state["messages"].append(
            AIMessage(content=f"Errore durante la traduzione: {str(e)}")
        )
    
    return state


def format_translation_result(state: TranslatorState) -> TranslatorState:
    """
    Formatta il risultato della traduzione per l'utente
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con il messaggio formattato
    """
    if not state.get("translated_text"):
        return state
    
    original = state["text_to_translate"]
    translated = state["translated_text"]
    target_lang = state["target_language"]
    
    # Formatta il messaggio
    result_message = f""" Traduzione in {target_lang}:

"{translated}"

Testo originale: "{original}\""""
    
    state["messages"].append(AIMessage(content=result_message))
    
    return state


def build_translator_agent():
    """
    Costruisce il grafo dell'agente traduttore usando LangGraph
    
    Returns:
        Un CompiledGraph pronto per l'esecuzione
    """
    workflow = StateGraph(TranslatorState)
    
    # Aggiungiamo i nodi
    workflow.add_node("extract", extract_translation_request)
    workflow.add_node("translate", perform_translation)
    workflow.add_node("format", format_translation_result)
    
    # Definiamo il flusso
    workflow.add_edge(START, "extract")
    
    # Da extract a translate se abbiamo i dettagli necessari
    workflow.add_conditional_edges(
        "extract",
        lambda state: "translate" if state.get("text_to_translate") and state.get("target_language") else END,
        {
            "translate": "translate",
            END: END
        }
    )
    
    # Da translate a format se abbiamo la traduzione
    workflow.add_conditional_edges(
        "translate",
        lambda state: "format" if state.get("translated_text") else END,
        {
            "format": "format",
            END: END
        }
    )
    
    # Da format a END
    workflow.add_edge("format", END)
    
    # Compiliamo il grafo
    graph = workflow.compile()
    
    return graph


def run_translator_agent(query: str) -> dict:
    """
    Esegue l'agente traduttore con la query dell'utente
    
    Args:
        query: La richiesta di traduzione
        
    Returns:
        Il risultato dello stato finale
    """
    graph = build_translator_agent()
    
    initial_state = {
        "query": query,
        "text_to_translate": None,
        "source_language": None,
        "target_language": None,
        "translated_text": None,
        "messages": []
    }
    
    result = graph.invoke(initial_state)
    
    return result


def visualize_graph():
    """
    Visualizza il grafo dell'agente traduttore
    """
    graph = build_translator_agent()
    
    try:
        # Genera la rappresentazione Mermaid
        mermaid_code = graph.get_graph().draw_mermaid()
        
        # Salva il diagramma Mermaid
        mermaid_path = "translator_agent_graph.md"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write("# Grafo Agente Traduttore\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n")
        print(f"✓ Diagramma Mermaid salvato in: {mermaid_path}")
        
         # 2. Prova a generare l'immagine PNG
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            png_path = "translator_agent_graph.png"
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"Grafo PNG salvato in: {png_path}")
        except Exception as png_error:
            print(f"PNG non generato: {png_error}")
            print("  Installa le dipendenze opzionali per generare PNG:")
            print("  pip install pygraphviz o pip install pydot")
        
        # Stampa in console
        print("\n" + "="*70)
        print("STRUTTURA DEL GRAFO AGENTE TRADUTTORE")
        print("="*70)
        print("\n```mermaid")
        print(mermaid_code)
        print("```\n")
        
    except Exception as e:
        print(f"Errore nella visualizzazione: {e}")


def main():
    """Test dell'agente traduttore"""
    print("=" * 70)
    print("TEST AGENTE TRADUTTORE")
    print("=" * 70)
    
    test_queries = [
        "traduci hello in italiano",
        "come si dice buongiorno in francese",
        "traduci in inglese: dove si trova la stazione?",
        "che significa thank you",
        "traduci questa frase in spagnolo: il ristorante è chiuso"
    ]
    
    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print(f"{'='*70}")
        
        result = run_translator_agent(query)
        
        for msg in result.get("messages", []):
            if hasattr(msg, 'content'):
                print(f"{msg.content}")


if __name__ == "__main__":
    main()
    
    # Visualizza il grafo
    print("\n" + "="*60)
    visualize_graph()
