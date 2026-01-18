# Agent Alexa-like
## Multiagente con supervisore

Tramite lang-graph verrà implemtato un sistema multiagent alexa like che risponderà ai seguenti compiti:
1. Invocazione meteo tramite scaricamento dati da API di meteo.
2. Oroscopo tramite API Aztro con traduzione automatica
3. Calendario
4. Calcolatrice
5. Traduttore

Saranno implementati tre agenti: 
- **Meteo**: Utilizza Open-Meteo API per ottenere previsioni meteo fino a 7 giorni
- **Oroscopo**: Utilizza Horoscope API per ottenere oroscopi giornalieri, settimanali, mensili e annuali con traduzione automatica italiano-inglese-italiano tramite OpenAI
- **Funzionalità Base**: quest'ultimo agente avrà a disposizione tool per:
    - Calendario
    - Calcolatrice
    - Traduttore

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

### Test
Esegui il file di test:
```bash
python test_horoscope.py
```
