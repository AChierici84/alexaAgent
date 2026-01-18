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