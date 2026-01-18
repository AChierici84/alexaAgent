"""
Agente Calcolatore - Parser matematico sicuro con conversioni e funzioni avanzate
Utilizza sympy per calcoli precisi e OpenAI per l'estrazione intelligente delle espressioni
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
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

# Carica le variabili d'ambiente
load_dotenv()


class CalculatorState(TypedDict):
    """Stato dell'agente calcolatore"""
    query: str
    expression: str | None
    calculation_type: str | None  # arithmetic, conversion, percentage, equation
    result: str | None
    messages: Annotated[list, operator.add]


# Conversioni unità comuni
CONVERSIONS = {
    # Lunghezza
    "km_to_mi": ("chilometri", "miglia", 0.621371),
    "mi_to_km": ("miglia", "chilometri", 1.60934),
    "m_to_ft": ("metri", "piedi", 3.28084),
    "ft_to_m": ("piedi", "metri", 0.3048),
    "cm_to_in": ("centimetri", "pollici", 0.393701),
    "in_to_cm": ("pollici", "centimetri", 2.54),
    
    # Peso
    "kg_to_lb": ("chilogrammi", "libbre", 2.20462),
    "lb_to_kg": ("libbre", "chilogrammi", 0.453592),
    "g_to_oz": ("grammi", "once", 0.035274),
    "oz_to_g": ("once", "grammi", 28.3495),
    
    # Temperatura (gestite separatamente)
    "c_to_f": ("Celsius", "Fahrenheit", "special"),
    "f_to_c": ("Fahrenheit", "Celsius", "special"),
    
    # Volume
    "l_to_gal": ("litri", "galloni", 0.264172),
    "gal_to_l": ("galloni", "litri", 3.78541),
}


def celsius_to_fahrenheit(c):
    """Converte Celsius in Fahrenheit"""
    return (c * 9/5) + 32


def fahrenheit_to_celsius(f):
    """Converte Fahrenheit in Celsius"""
    return (f - 32) * 5/9


def extract_mathematical_expression(state: CalculatorState) -> CalculatorState:
    """
    Estrae l'espressione matematica dalla query usando OpenAI
    Identifica il tipo di calcolo richiesto
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con l'espressione estratta
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
        
        prompt = f"""Analizza questa query in italiano ed estrai l'operazione matematica richiesta.

Tipi di operazioni supportate:
1. ARITHMETIC - Calcoli aritmetici: "quanto fa 2+2", "calcola 15*23", "(5+3)*2"
2. PERCENTAGE - Percentuali: "il 20% di 100", "quanto è il 15% di sconto su 50"
3. CONVERSION - Conversioni unità: "converti 100 km in miglia", "quanti piedi sono 10 metri"
4. EQUATION - Equazioni: "risolvi 2x+5=13", "trova x: x^2=16"

Query: {query}

Rispondi in JSON con questo formato:
{{
    "type": "ARITHMETIC|PERCENTAGE|CONVERSION|EQUATION",
    "expression": "espressione matematica da valutare",
    "description": "breve descrizione di cosa fare",
    "valid": true o false
}}

Esempi:
- "quanto fa 2+2" -> {{"type": "ARITHMETIC", "expression": "2+2", "valid": true}}
- "il 20% di 100" -> {{"type": "PERCENTAGE", "expression": "100 * 0.20", "valid": true}}
- "converti 10 km in miglia" -> {{"type": "CONVERSION", "expression": "10 km to mi", "valid": true}}
- "25 gradi celsius in fahrenheit" -> {{"type": "CONVERSION", "expression": "25 c to f", "valid": true}}
- "100 fahrenheit in celsius" -> {{"type": "CONVERSION", "expression": "100 f to c", "valid": true}}
- "risolvi 2x+5=13" -> {{"type": "EQUATION", "expression": "2*x+5-13", "valid": true}}

Per le conversioni usa abbreviazioni: km, mi, m, ft, cm, in, kg, lb, g, oz, l, gal, c, f

Se non è una richiesta matematica, metti "valid": false
"""
        
        # Chiama OpenAI
        response = llm.invoke([
            SystemMessage(content="Sei un esperto nell'estrarre espressioni matematiche da testo in linguaggio naturale."),
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
            state["expression"] = None
            state["calculation_type"] = None
            state["messages"].append(
                AIMessage(content="Non riesco a identificare un'operazione matematica valida nella tua richiesta.")
            )
            return state
        
        state["expression"] = data.get("expression", "").strip()
        state["calculation_type"] = data.get("type", "ARITHMETIC").upper()
        description = data.get("description", "")
        
        state["messages"].append(
            AIMessage(content=f"Ho identificato: {description}. Calcolo in corso...")
        )
        
    except Exception as e:
        state["expression"] = None
        state["calculation_type"] = None
        state["messages"].append(
            AIMessage(content=f"Errore nell'analisi della richiesta: {str(e)}")
        )
    
    return state


def perform_calculation(state: CalculatorState) -> CalculatorState:
    """
    Esegue il calcolo in base al tipo identificato
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con il risultato
    """
    if not state.get("expression"):
        return state
    
    try:
        calc_type = state.get("calculation_type", "ARITHMETIC")
        expression = state["expression"]
        
        if calc_type == "CONVERSION":
            result = handle_conversion(expression)
        elif calc_type == "EQUATION":
            result = solve_equation(expression)
        else:
            # ARITHMETIC e PERCENTAGE
            result = evaluate_expression(expression)
        
        state["result"] = result
        
    except Exception as e:
        state["result"] = None
        state["messages"].append(
            AIMessage(content=f"Errore nel calcolo: {str(e)}")
        )
    
    return state


def evaluate_expression(expression: str) -> str:
    """
    Valuta un'espressione matematica usando sympy
    
    Args:
        expression: L'espressione da valutare
        
    Returns:
        Il risultato come stringa
    """
    try:
        # Sostituzioni comuni per rendere l'espressione compatibile
        expr = expression.replace("^", "**")
        expr = expr.replace("×", "*")
        expr = expr.replace("÷", "/")
        
        # Parse con trasformazioni standard
        transformations = standard_transformations + (implicit_multiplication_application,)
        parsed = parse_expr(expr, transformations=transformations)
        
        # Valuta
        result = parsed.evalf()
        
        # Formatta il risultato
        if result.is_integer:
            return str(int(result))
        else:
            # Arrotonda a 6 decimali e rimuovi zeri finali
            result_str = f"{float(result):.6f}".rstrip('0').rstrip('.')
            return result_str
            
    except Exception as e:
        raise ValueError(f"Impossibile valutare l'espressione '{expression}': {str(e)}")


def handle_conversion(expression: str) -> str:
    """
    Gestisce le conversioni di unità
    
    Args:
        expression: Espressione di conversione (es. "10 km to mi", "25 celsius to fahrenheit")
        
    Returns:
        Il risultato della conversione
    """
    # Normalizza l'espressione
    expr_lower = expression.lower().strip()
    
    # Pattern flessibile: "numero unità_origine (to|in|a) unità_destinazione"
    match = re.match(r'(\d+\.?\d*)\s*(\w+)\s+(?:to|in|a)\s+(\w+)', expr_lower)
    
    if not match:
        raise ValueError(f"Formato conversione non riconosciuto: '{expression}'. Usa: 'numero unità_origine to unità_destinazione'")
    
    value = float(match.group(1))
    from_unit = match.group(2)
    to_unit = match.group(3)
    
    # Normalizza i nomi delle unità (gestisce sia abbreviazioni che nomi completi)
    unit_aliases = {
        'celsius': 'c',
        'fahrenheit': 'f',
        'chilometri': 'km',
        'chilometro': 'km',
        'miglia': 'mi',
        'miglio': 'mi',
        'metri': 'm',
        'metro': 'm',
        'piedi': 'ft',
        'piede': 'ft',
        'centimetri': 'cm',
        'centimetro': 'cm',
        'pollici': 'in',
        'pollice': 'in',
        'chilogrammi': 'kg',
        'chilogrammo': 'kg',
        'libbre': 'lb',
        'libbra': 'lb',
        'grammi': 'g',
        'grammo': 'g',
        'once': 'oz',
        'oncia': 'oz',
        'litri': 'l',
        'litro': 'l',
        'galloni': 'gal',
        'gallone': 'gal',
    }
    
    # Applica gli alias
    from_unit = unit_aliases.get(from_unit, from_unit)
    to_unit = unit_aliases.get(to_unit, to_unit)
    
    # Cerca la conversione
    conversion_key = f"{from_unit}_to_{to_unit}"
    
    if conversion_key not in CONVERSIONS:
        raise ValueError(f"Conversione da {from_unit} a {to_unit} non supportata")
    
    from_name, to_name, factor = CONVERSIONS[conversion_key]
    
    # Gestione speciale per temperatura
    if factor == "special":
        if conversion_key == "c_to_f":
            result = celsius_to_fahrenheit(value)
        elif conversion_key == "f_to_c":
            result = fahrenheit_to_celsius(value)
        else:
            raise ValueError("Conversione temperatura non riconosciuta")
    else:
        result = value * factor
    
    # Formatta il risultato
    if result == int(result):
        result_str = str(int(result))
    else:
        result_str = f"{result:.2f}"
    
    return f"{value} {from_name} = {result_str} {to_name}"


def solve_equation(expression: str) -> str:
    """
    Risolve un'equazione usando sympy
    
    Args:
        expression: L'equazione da risolvere (es. "2*x+5-13" per 2x+5=13)
        
    Returns:
        Le soluzioni dell'equazione
    """
    try:
        x = sp.Symbol('x')
        
        # Se l'espressione contiene '=', dividiamo
        if '=' in expression:
            left, right = expression.split('=')
            eq = sp.sympify(left) - sp.sympify(right)
        else:
            # Assumiamo che l'espressione sia già nella forma expr = 0
            eq = sp.sympify(expression)
        
        # Risolvi
        solutions = sp.solve(eq, x)
        
        if not solutions:
            return "Nessuna soluzione trovata"
        elif len(solutions) == 1:
            sol = solutions[0]
            if sol.is_integer:
                return f"x = {int(sol)}"
            else:
                return f"x = {float(sol):.6f}".rstrip('0').rstrip('.')
        else:
            sols = []
            for sol in solutions:
                if sol.is_integer:
                    sols.append(str(int(sol)))
                else:
                    sols.append(f"{float(sol):.6f}".rstrip('0').rstrip('.'))
            return f"x = {', '.join(sols)}"
            
    except Exception as e:
        raise ValueError(f"Impossibile risolvere l'equazione: {str(e)}")


def format_result(state: CalculatorState) -> CalculatorState:
    """
    Formatta il risultato finale per l'utente
    
    Args:
        state: Lo stato dell'agente
        
    Returns:
        Lo stato aggiornato con il messaggio formattato
    """
    if not state.get("result"):
        return state
    
    result = state["result"]
    calc_type = state.get("calculation_type", "ARITHMETIC")
    
    # Emoji in base al tipo
    emoji_map = {
        "ARITHMETIC": "🔢",
        "PERCENTAGE": "📊",
        "CONVERSION": "🔄",
        "EQUATION": "📐"
    }
    
    emoji = emoji_map.get(calc_type, "🔢")
    
    state["messages"].append(
        AIMessage(content=f"{emoji} Risultato: {result}")
    )
    
    return state


def build_calculator_agent():
    """
    Costruisce il grafo dell'agente calcolatore usando LangGraph
    
    Returns:
        Un CompiledGraph pronto per l'esecuzione
    """
    workflow = StateGraph(CalculatorState)
    
    # Aggiungiamo i nodi
    workflow.add_node("extract", extract_mathematical_expression)
    workflow.add_node("calculate", perform_calculation)
    workflow.add_node("format", format_result)
    
    # Definiamo il flusso
    workflow.add_edge(START, "extract")
    
    # Da extract a calculate se abbiamo un'espressione valida
    workflow.add_conditional_edges(
        "extract",
        lambda state: "calculate" if state.get("expression") else END,
        {
            "calculate": "calculate",
            END: END
        }
    )
    
    # Da calculate a format se abbiamo un risultato
    workflow.add_conditional_edges(
        "calculate",
        lambda state: "format" if state.get("result") else END,
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


def run_calculator_agent(query: str) -> dict:
    """
    Esegue l'agente calcolatore con la query dell'utente
    
    Args:
        query: La richiesta di calcolo
        
    Returns:
        Il risultato dello stato finale
    """
    graph = build_calculator_agent()
    
    initial_state = {
        "query": query,
        "expression": None,
        "calculation_type": None,
        "result": None,
        "messages": []
    }
    
    result = graph.invoke(initial_state)
    
    return result


def visualize_graph():
    """
    Visualizza il grafo dell'agente calcolatore
    """
    graph = build_calculator_agent()
    
    try:
        # Genera la rappresentazione Mermaid
        mermaid_code = graph.get_graph().draw_mermaid()
        
        # Salva il diagramma Mermaid
        mermaid_path = "calculator_agent_graph.md"
        with open(mermaid_path, "w", encoding="utf-8") as f:
            f.write("# Grafo Agente Calcolatore\n\n")
            f.write("```mermaid\n")
            f.write(mermaid_code)
            f.write("\n```\n")
        print(f"✓ Diagramma Mermaid salvato in: {mermaid_path}")
        
         # 2. Prova a generare l'immagine PNG
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            png_path = "calculator_agent_graph.png"
            with open(png_path, "wb") as f:
                f.write(png_data)
            print(f"Grafo PNG salvato in: {png_path}")
        except Exception as png_error:
            print(f"PNG non generato: {png_error}")
            print("  Installa le dipendenze opzionali per generare PNG:")
            print("  pip install pygraphviz o pip install pydot")
        
        # Stampa in console
        print("\n" + "="*70)
        print("STRUTTURA DEL GRAFO AGENTE CALCOLATORE")
        print("="*70)
        print("\n```mermaid")
        print(mermaid_code)
        print("```\n")
        
    except Exception as e:
        print(f"Errore nella visualizzazione: {e}")


def main():
    """Test dell'agente calcolatore"""
    print("=" * 70)
    print("TEST AGENTE CALCOLATORE")
    print("=" * 70)
    
    test_queries = [
        "quanto fa 2+2",
        "calcola (15 + 23) * 2",
        "il 20% di 150",
        "converti 100 km in miglia",
        "quanti gradi fahrenheit sono 25 celsius",
        "risolvi 2x + 5 = 13"
    ]
    
    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print(f"{'='*70}")
        
        result = run_calculator_agent(query)
        
        for msg in result.get("messages", []):
            if hasattr(msg, 'content'):
                print(f"{msg.content}")


if __name__ == "__main__":
    main()
    
    visualize_graph()
