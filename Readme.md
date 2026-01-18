# Agent Alexa-like
## Multiagente con supervisore

Tramite lang-graph verrà implemtato un sistema multiagent alexa like che risponderà ai seguenti compiti:
1. Invocazione meteo tramite scaricamento dati da API di meteo.
2. Oroscopo con traduzione automatica
3. Conversazioni generiche, saluti e small talk 
4. Ricerca informazioni enciclopediche su Wikipedia
5. Calcolatrice (prossimamente)
6. Traduttore (prossimamente)

### Gestione Conversazionale Intelligente
Il sistema include una **gestione dello stato conversazionale** che permette agli agenti di mantenere il contesto tra richieste successive:
- Se manca un'informazione (es. località, segno zodiacale), l'agente la chiede
- Quando l'utente fornisce l'informazione mancante, il sistema completa automaticamente la richiesta precedente
- Non è necessario ripetere l'intera richiesta

**Esempio:**
```
Utente: "Che tempo fa domani?"
Alexa: "Puoi indicarmi una città?"
Utente: "Roma"
Alexa: [fornisce il meteo di Roma per domani]
```

### 🖥️ Interfaccia Gradio
Il sistema include un'interfaccia web interattiva realizzata con Gradio:

**Per avviare l'interfaccia:**
```bash
python gradio_ui.py
```

L'interfaccia web si aprirà automaticamente nel browser su `http://localhost:7860`

**Funzionalità dell'interfaccia:**
- Chat interattiva con il sistema multiagente
- Esempi di query pre-configurati
- Gestione conversazionale visuale
- Pulsante per pulire la conversazione
- Design responsive e user-friendly

### 🚀 Modalità di Utilizzo

**1. Interfaccia Web (Consigliato)**
```bash
python gradio_ui.py
```

**2. Interfaccia a Riga di Comando**
```bash
python multiagent.py
```

**3. Script Python**
```python
from multiagent import run_supervisor

result = run_supervisor("Che tempo fa a Roma domani?")
for msg in result["messages"]:
    print(msg.content)
```

Saranno implementati quattro agenti: 
- **Meteo**: Utilizza Open-Meteo API per ottenere previsioni meteo fino a 7 giorni
- **Oroscopo**: Utilizza Horoscope API per ottenere oroscopi giornalieri, settimanali, mensili e annuali con traduzione automatica italiano-inglese-italiano tramite OpenAI
- **Wikipedia**: Cerca informazioni enciclopediche su Wikipedia in italiano e utilizza OpenAI per rispondere alle domande
- **General**: Gestisce conversazioni generiche, saluti, presentazioni e qualsiasi richiesta non tecnica utilizzando OpenAI GPT-3.5
- **Funzionalità Base** (prossimamente): quest'ultimo agente avrà a disposizione tool per:
    - Calendario
    - Calcolatrice
    - Traduttore

## Agente Meteo - Dettagli Implementazione

L'agente meteo è completamente funzionale e include le seguenti caratteristiche:

### Funzionalità
1. **Estrazione intelligente**: Utilizza OpenAI GPT-3.5 per estrarre la località e l'indicazione temporale dalla query in italiano
2. **Geocoding**: Utilizza Nominatim (OpenStreetMap) per convertire nomi di città in coordinate geografiche (latitudine/longitudine)
3. **Open-Meteo API**: Recupera dati meteorologici dettagliati da https://api.open-meteo.com/ (gratuita, senza autenticazione)

### Dati Meteo Forniti
- **Temperatura**: Minima e massima giornaliera (°C)
- **Precipitazioni**: Quantità prevista (mm) e probabilità (%)
- **Vento**: Velocità massima (km/h)
- **Condizioni**: Descrizione testuale (es. "Cielo sereno", "Pioggia moderata", "Temporale")

### Periodi Temporali Supportati
- **Oggi** (offset 0 giorni)
- **Domani** (offset 1 giorno)
- **Dopodomani** (offset 2 giorni)
- **Fino a 7 giorni futuri**: Specifica il giorno della settimana o una data
- Validazione automatica: non accetta date nel passato o oltre i 7 giorni

### Codici Meteo Decodificati
L'agente traduce i weather code numerici in descrizioni italiane comprensibili:
- 0-3: Sereno/Nuvoloso
- 45-48: Nebbia
- 51-55: Pioviggine
- 61-65: Pioggia
- 71-75: Neve
- 80-82: Rovesci
- 95-99: Temporali (con o senza grandine)

### Esempio di utilizzo
```python
from agents.weather_agent import run_weather_agent

# Query di esempio
result = run_weather_agent("Che tempo farà a Roma domani?")
for msg in result["messages"]:
    print(msg.content)
```

## Agente Oroscopo - Dettagli Implementazione

L'agente oroscopo è completamente funzionale e include le seguenti caratteristiche:

### Funzionalità
1. **Estrazione intelligente**: Utilizza OpenAI per estrarre il segno zodiacale e l'indicazione temporale dalla query in italiano
2. **Traduzione automatica**: Traduce i segni zodiacali dall'italiano all'inglese per interrogare l'API
3. **Horoscope API**: Recupera l'oroscopo da https://horoscope-app-api.vercel.app/ (gratuita, senza autenticazione)
4. **Traduzione risposta**: Traduce l'oroscopo dall'inglese all'italiano in modo fluente usando OpenAI
5. **Formattazione ricca**: Include emoji e formattazione per una migliore esperienza utente

### Segni Zodiacali Supportati
Ariete, Toro, Gemelli, Cancro, Leone, Vergine, Bilancia, Scorpione, Sagittario, Capricorno, Acquario, Pesci

### Periodi Temporali
- **Giornaliero** (daily) - oggi, domani
- **Settimanale** (weekly)
- **Mensile** (monthly)
- **Annuale** (yearly)

### Esempio di utilizzo
```python
from agents.horoscope_agent import run_horoscope_agent

# Query di esempio
result = run_horoscope_agent("Qual è l'oroscopo dell'ariete oggi?")
for msg in result["messages"]:
    print(msg.content)
```

## Agente General - Dettagli Implementazione

L'agente conversazionale generale gestisce interazioni naturali e funge da fallback per qualsiasi richiesta non tecnica.

### Funzionalità
1. **Conversazioni naturali**: Utilizza OpenAI GPT-3.5 con temperatura più alta (0.7) per risposte più creative e naturali
2. **Personalità definita**: Si presenta come "Alexa", assistente amichevole e professionale
3. **Fallback intelligente**: Gestisce automaticamente tutto ciò che non è coperto dagli agenti specializzati
4. **Risposte concise**: Mantiene le risposte brevi (2-4 frasi) per una migliore esperienza conversazionale

### Tipologie di Richieste Gestite
- **Saluti**
- **Presentazioni**
- **Ringraziamenti**
- **Small talk**
- **Domande sull'assistente**
- **Domande sulla data corrente**
- **Fallback**: Qualsiasi richiesta non coperta da meteo, oroscopo o altri agenti specializzati

### Caratteristiche della Personalità
- Cordiale e professionale
- Comunicazione chiara e concisa
- Parla sempre in italiano
- Disponibile ad aiutare e informare

### Esempio di utilizzo
```python
from agents.general_agent import run_general_agent

# Query di esempio
result = run_general_agent("Ciao! Come stai?")
for msg in result["messages"]:
    print(msg.content)
```

### Integrazione con il Sistema
L'agente General è integrato nel supervisore come:
- **Agente predefinito**: Utilizzato quando nessun altro agente è appropriato
- **Gestione errori**: Attivato in caso di errori nel routing
- **Sempre disponibile**: Non può mai risultare "non disponibile"

## Agente Wikipedia - Dettagli Implementazione

L'agente Wikipedia cerca e recupera informazioni enciclopediche da Wikipedia in italiano.

### Funzionalità
1. **Identificazione domande enciclopediche**: Riconosce automaticamente domande che richiedono informazioni enciclopediche
2. **Estrazione termini di ricerca**: Utilizza OpenAI per estrarre i termini chiave dalla domanda
3. **Ricerca Wikipedia**: Cerca su Wikipedia italiana (it.wikipedia.org) senza bisogno di API key
4. **Recupero contenuto**: Estrae il contenuto della pagina più rilevante
5. **Risposta intelligente**: Utilizza OpenAI per rispondere alla domanda basandosi sul contenuto Wikipedia

### Tipologie di Domande Gestite
- **Personaggi storici**: "Chi era Leonardo da Vinci?"
- **Definizioni**: "Cos'è la fotosintesi?"
- **Eventi storici**: "Quando è stata scoperta l'America?"
- **Luoghi e monumenti**: "Dimmi qualcosa sulla Torre di Pisa"
- **Cultura generale**: Qualsiasi domanda enciclopedica

### API Utilizzate
- **Wikipedia API**: Gratuita, nessuna autenticazione richiesta
- **Lingua**: Italiano (it.wikipedia.org)
- **OpenAI**: Per estrazione termini e generazione risposte

### Gestione Errori
- Gestisce automaticamente disambiguazioni
- Prova risultati alternativi se una pagina non è trovata
- Limita il contenuto a ~4000 caratteri per efficienza

### Esempio di utilizzo
```python
from agents.wikipedia_agent import run_wikipedia_agent

# Query di esempio
result = run_wikipedia_agent("Chi era Leonardo da Vinci?")
print(result['response'])
```

### Integrazione con il Sistema
L'agente Wikipedia è attivato dal supervisore quando rileva domande enciclopediche e fornisce risposte basate su fatti verificabili da Wikipedia.
