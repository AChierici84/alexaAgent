# Agent Alexa-like
## Multiagente con supervisore

Tramite lang-graph verrà implemtato un sistema multiagent alexa like che risponderà ai seguenti compiti:
1. Invocazione meteo tramite scaricamento dati da API di meteo.
2. Oroscopo con traduzione automatica
3. Conversazioni generiche, saluti e small talk
4. Calendario (prossimamente)
5. Calcolatrice (prossimamente)
6. Traduttore (prossimamente)

Saranno implementati quattro agenti: 
- **Meteo**: Utilizza Open-Meteo API per ottenere previsioni meteo fino a 7 giorni
- **Oroscopo**: Utilizza Horoscope API per ottenere oroscopi giornalieri, settimanali, mensili e annuali con traduzione automatica italiano-inglese-italiano tramite OpenAI
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
