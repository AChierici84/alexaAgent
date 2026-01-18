# Agent Alexa-like
## Multiagente con supervisore

Tramite lang-graph verrà implemtato un sistema multiagent alexa like che risponderà ai seguenti compiti:
1. Invocazione meteo tramite scaricamento dati da API di meteo
2. Oroscopo con traduzione automatica
3. Conversazioni generiche, saluti e small talk 
4. Ricerca informazioni enciclopediche su Wikipedia
5. **Calcolatrice matematica** - Calcoli, conversioni unità, percentuali, equazioni
6. **Traduttore multilingua** - Traduzioni tra oltre 40 lingue

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

Saranno implementati sei agenti: 
- **Meteo**: Utilizza Open-Meteo API per ottenere previsioni meteo fino a 7 giorni
- **Oroscopo**: Utilizza Horoscope API per ottenere oroscopi giornalieri, settimanali e mensili con traduzione automatica italiano-inglese-italiano tramite OpenAI
- **Wikipedia**: Cerca informazioni enciclopediche su Wikipedia in italiano e utilizza OpenAI per rispondere alle domande
- **Calculator**: Parser matematico con sympy per calcoli precisi, conversioni unità, percentuali ed equazioni
- **Translator**: Traduttore multilingua che supporta oltre 40 lingue tramite OpenAI
- **General**: Gestisce conversazioni generiche, saluti, presentazioni e qualsiasi richiesta non tecnica utilizzando OpenAI GPT-3.5

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
## Agente Calculator - Dettagli Implementazione

L'agente Calculator esegue calcoli matematici precisi e affidabili utilizzando il parser matematico sympy.

### Funzionalità
1. **Parser matematico**: Utilizza sympy per calcoli deterministici e precisi (nessun errore LLM)
2. **Estrazione intelligente**: OpenAI estrae l'espressione matematica dalla query in linguaggio naturale
3. **Supporto operazioni multiple**: Aritmetica, percentuali, conversioni unità, equazioni
4. **Conversioni unità**: Lunghezza, peso, temperatura, volume

### Tipi di Operazioni Supportate

#### 1. Calcoli Aritmetici
- Operazioni base: `+`, `-`, `*`, `/`, `**` (potenza)
- Parentesi e precedenza operatori
- Funzioni matematiche: sin, cos, radici, logaritmi

**Esempi:**
- "quanto fa 2+2"
- "calcola (15 + 23) * 2"
- "qual è la radice quadrata di 144"

#### 2. Percentuali
- Calcolo percentuale di un numero
- Percentuali di sconto

**Esempi:**
- "il 20% di 150"
- "calcola il 15% di sconto su 50 euro"

#### 3. Conversioni Unità
**Lunghezza:**
- km ↔ miglia (mi)
- metri (m) ↔ piedi (ft)
- centimetri (cm) ↔ pollici (in)

**Peso:**
- chilogrammi (kg) ↔ libbre (lb)
- grammi (g) ↔ once (oz)

**Temperatura:**
- Celsius (c) ↔ Fahrenheit (f)

**Volume:**
- litri (l) ↔ galloni (gal)

**Esempi:**
- "converti 100 km in miglia"
- "quanti gradi fahrenheit sono 25 celsius"
- "converti 5 kg in libbre"

#### 4. Equazioni
- Risoluzione equazioni lineari e quadratiche
- Supporto variabile x

**Esempi:**
- "risolvi 2x + 5 = 13"
- "trova x: x^2 = 16"

### Vantaggi rispetto a LLM
- ✅ **Precisione**: Calcoli sempre corretti, nessun errore di arrotondamento
- ✅ **Velocità**: Più rapido di una chiamata API
- ✅ **Costi ridotti**: Nessuna chiamata LLM per il calcolo stesso
- ✅ **Affidabilità**: Risultati deterministici

### Esempio di utilizzo
```python
from agents.calculator_agent import run_calculator_agent

# Query di esempio
result = run_calculator_agent("quanto fa 23 * 45")
for msg in result["messages"]:
    print(msg.content)
```

### Integrazione con il Sistema
L'agente Calculator è attivato dal supervisore quando rileva richieste di calcoli matematici, conversioni o percentuali.

## Agente Translator - Dettagli Implementazione

L'agente Translator traduce testo tra oltre 40 lingue diverse utilizzando OpenAI per traduzioni di alta qualità.

### Funzionalità
1. **Estrazione intelligente**: OpenAI estrae testo da tradurre, lingua origine e destinazione
2. **Rilevamento automatico**: Identifica automaticamente la lingua di origine se non specificata
3. **Traduzioni fluenti**: Utilizza OpenAI GPT-3.5 per traduzioni naturali e contestuali
4. **Supporto multilingua**: Oltre 40 lingue supportate

### Lingue Supportate (principali)
- **Europee**: Italiano, Inglese, Francese, Spagnolo, Tedesco, Portoghese, Russo, Olandese, Polacco, Greco, Svedese, Norvegese, Danese, Finlandese, Ceco, Rumeno, Ungherese, Turco, Ucraino, Catalano, Croato, Bulgaro, Slovacco, Sloveno, Serbo, Lituano, Lettone, Estone
- **Asiatiche**: Cinese, Giapponese, Coreano, Hindi, Thai, Vietnamita, Indonesiano, Malese
- **Medio Oriente**: Arabo, Ebraico

### Pattern di Richiesta Supportati
- "traduci [testo] in [lingua]"
- "come si dice [testo] in [lingua]"
- "che significa [testo]" (traduce in italiano)
- "traduci in [lingua]: [testo]"

### Caratteristiche
- **Traduzioni accurate**: Mantiene il significato e il contesto
- **Fluenza naturale**: Non traduzioni letterali ma contestualmente appropriate
- **Formattazione elegante**: Mostra traduzione e testo originale
- **Supporto frasi lunghe**: Può tradurre da singole parole a paragrafi interi

### Esempi di utilizzo

**Query:**
```python
from agents.translator_agent import run_translator_agent

# Esempi
result = run_translator_agent("traduci hello in italiano")
# Output: "ciao"

result = run_translator_agent("come si dice buongiorno in francese")
# Output: "bonjour"

result = run_translator_agent("traduci in inglese: dove si trova la stazione?")
# Output: "where is the station?"

result = run_translator_agent("che significa thank you")
# Output: "grazie"
```

### Integrazione con il Sistema
L'agente Translator è attivato dal supervisore quando rileva richieste di traduzione linguistica.