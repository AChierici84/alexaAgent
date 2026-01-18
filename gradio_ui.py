"""
Interfaccia Gradio per testare il sistema multiagente
Fornisce una UI web interattiva per chattare con Alexa
"""

import gradio as gr
from multiagent import run_supervisor
from conversation_manager import conversation_manager
import os
from dotenv import load_dotenv

# Carica le variabili d'ambiente
load_dotenv()


def chat_with_alexa(message, history):
    """
    Gestisce la conversazione con Alexa mostrando il reasoning durante l'elaborazione
    e poi solo il risultato finale
    
    Args:
        message: Messaggio dell'utente
        history: Storia della conversazione (lista di dizionari con 'role' e 'content')
        
    Yields:
        Tupla (stringa vuota, history aggiornata) durante il processing
        Tupla (stringa vuota, history finale) con solo il risultato
    """
    if not message or not message.strip():
        yield "", history
        return
    
    try:
        # Aggiungi il messaggio utente alla history
        history.append({"role": "user", "content": message})
        
        # Mostra "Elaborazione in corso..."
        temp_history = history.copy()
        temp_history.append({"role": "assistant", "content": "🔄 Elaborazione in corso..."})
        yield "", temp_history
        
        # Esegui il supervisore
        result = run_supervisor(message.strip())
        
        # Estrai tutti i messaggi per il reasoning
        all_messages = []
        final_response = None
        
        for msg in result.get("messages", []):
            if hasattr(msg, 'content') and msg.content:
                msg_type = msg.__class__.__name__
                
                # Salta i messaggi dell'utente
                if msg_type != 'HumanMessage':
                    all_messages.append(msg.content)
        
        # Mostra progressivamente il reasoning
        reasoning_text = ""
        for i, msg_content in enumerate(all_messages):
            reasoning_text += msg_content
            if i < len(all_messages) - 1:
                reasoning_text += "\n\n"
            
            # Aggiorna con il reasoning parziale
            temp_history = history.copy()
            temp_history.append({"role": "assistant", "content": reasoning_text})
            yield "", temp_history
        
        # Identifica la risposta finale (ultimo messaggio non di routing/debug)
        # Cerca l'ultimo messaggio sostanziale
        for msg_content in reversed(all_messages):
            # Salta messaggi di routing/sistema
            if not any(keyword in msg_content.lower() for keyword in 
                      ['ho analizzato', 'attivo l\'agente', 'ho identificato', 'sto recuperando']):
                final_response = msg_content
                break
        
        # Se non trovata una risposta sostanziale, usa l'ultimo messaggio
        if not final_response and all_messages:
            final_response = all_messages[-1]
        
        if not final_response:
            final_response = "Mi dispiace, non ho potuto elaborare la tua richiesta."
        
        # Sostituisci con solo la risposta finale (rimuove il reasoning)
        history.append({"role": "assistant", "content": final_response})
        yield "", history
        
    except Exception as e:
        error_msg = f"Errore: {str(e)}"
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": error_msg})
        return "", history


def clear_conversation():
    """Pulisce la conversazione e le richieste pendenti"""
    conversation_manager.clear_pending_request()
    return []


def create_interface():
    """Crea l'interfaccia Gradio"""
    
    # CSS personalizzato
    custom_css = """
    .gradio-container {
        font-family: 'Arial', sans-serif;
    }
    .chat-message {
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
    }
    """
    
    with gr.Blocks(title="Alexa Multiagente") as demo:
        gr.Markdown(
            """
            # Sistema Multiagente Alexa-like
            
            Interagisci con il sistema multiagente tramite questa interfaccia web.
            Il sistema utilizza diversi agenti specializzati:
            
            - **🌤️ Meteo**: Previsioni meteorologiche fino a 7 giorni
            - **⭐ Oroscopo**: Oroscopi giornalieri, settimanali e mensili
            - **📚 Wikipedia**: Informazioni enciclopediche
            - **🔢 Calculator**: Calcoli matematici, conversioni, percentuali
            - **🌍 Translator**: Traduzioni tra oltre 40 lingue
            - **💬 General**: Conversazioni generiche, saluti e small talk
            
            ### Gestione Conversazionale
            Se manca un'informazione (es. città per il meteo), l'agente la chiederà.
            Basta rispondere con l'informazione mancante nella prossima richiesta!
            """
        )
        
        with gr.Row():
            with gr.Column(scale=4):
                chatbot = gr.Chatbot(
                    label="Conversazione con Alexa",
                    height=500
                )
                
                with gr.Row():
                    msg = gr.Textbox(
                        label="Scrivi il tuo messaggio",
                        placeholder="Es: Che tempo fa a Roma domani?",
                        lines=2,
                        scale=4
                    )
                    
                with gr.Row():
                    submit_btn = gr.Button("Invia", variant="primary", scale=2)
                    clear_btn = gr.Button("Nuova Conversazione", scale=1)
        
            with gr.Column(scale=1):
                gr.Markdown("### 📝 Esempi di Query")
                
                examples = gr.Examples(
                    examples=[
                        ["Che tempo fa a Milano domani?"],
                        ["Che tempo fa?"],
                        ["Qual è l'oroscopo dell'ariete oggi?"],
                        ["Oroscopo della settimana"],
                        ["Chi era Leonardo da Vinci?"],
                        ["Cos'è la fotosintesi?"],
                        ["Quanto fa 23 * 45?"],
                        ["Converti 100 km in miglia"],
                        ["Il 20% di 150"],
                        ["Traduci hello in italiano"],
                        ["Come si dice buongiorno in francese?"],
                        ["Ciao! Come stai?"],
                        ["Grazie mille!"]
                    ],
                    inputs=msg,
                    label="Clicca su un esempio"
                )
                
                gr.Markdown(
                    """
                    ### Informazioni
                    
                    **Stato**: Sistema attivo ✅
                    
                    **Agenti disponibili**:
                    - Meteo ✅
                    - Oroscopo ✅
                    - Wikipedia ✅
                    - Calculator ✅
                    - Translator ✅
                    - General ✅
                    
                    **Funzionalità**:
                    - Riconoscimento automatico intento
                    - Gestione conversazionale
                    - Memoria delle richieste incomplete
                    """
                )
        
        # Eventi
        submit_btn.click(
            fn=chat_with_alexa,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )
        
        msg.submit(
            fn=chat_with_alexa,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot]
        )
        
        clear_btn.click(
            fn=clear_conversation,
            outputs=chatbot
        )
        
        gr.Markdown(
            """
            ---
            ### Configurazione
            
            Assicurati di avere configurato la tua `OPENAI_API_KEY` nel file `.env`
            
            ### Debug
            I log di debug vengono stampati nella console dove hai avviato l'applicazione.
            """
        )
    
    return demo


def main():
    """Avvia l'interfaccia Gradio"""
    
    # Verifica che la chiave API sia configurata
    if not os.getenv("OPENAI_API_KEY"):
        print("ATTENZIONE: OPENAI_API_KEY non configurata nel file .env")
        print("L'applicazione potrebbe non funzionare correttamente.")
    
    print("\n" + "="*70)
    print("AVVIO INTERFACCIA GRADIO")
    print("="*70)
    print("\nCreazione interfaccia web...")
    
    demo = create_interface()
    
    print("\nInterfaccia creata con successo!")
    print("\nL'interfaccia web si aprirà automaticamente nel browser")
    print("   Se non si apre, usa l'URL mostrato qui sotto\n")
    
    # Avvia il server
    demo.launch(
        server_name="0.0.0.0",  # Accessibile da altri dispositivi nella rete
        server_port=7860,
        share=False,  # Imposta True per creare un link pubblico temporaneo
        show_error=True,
        quiet=False
    )


if __name__ == "__main__":
    main()
