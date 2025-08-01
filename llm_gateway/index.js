// FILE: llm_gateway/index.js
const express = require('express');
const bodyParser = require('body-parser');
// CORREZIONE: Importa tutto il necessario da @google/generative-ai
const { GoogleGenerativeAI, HarmCategory, HarmBlockThreshold } = require('@google/generative-ai');

const app = express();
const port = 3001;

app.use(bodyParser.json());

// Verifica che la chiave API sia presente all'avvio
if (!process.env.GEMINI_API_KEY) {
    console.error("FATAL ERROR: La variabile d'ambiente GEMINI_API_KEY non è impostata.");
    process.exit(1); // Esce se la chiave non è configurata
}
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);

app.post('/generate', async (req, res) => {
    const { model_name, prompt, is_json_output } = req.body;

    // --- LOG 1: Richiesta Ricevuta ---
    console.log("-----------------------------------------");
    console.log(`[${new Date().toISOString()}] Ricevuta richiesta per il modello: ${model_name}`);
    console.log(`JSON Output richiesto: ${is_json_output}`);
    // Per sicurezza, non loggare l'intero prompt in produzione, ma per il debug è utilissimo
    console.log("--- PROMPT RICEVUTO ---");
    console.log(prompt);
    console.log("--- FINE PROMPT ---");
    // ------------------------------------

    if (!model_name || !prompt) {
        return res.status(400).json({ error: 'model_name and prompt are required' });
    }
    
    const maxRetries = 5;
    let lastError = null;

    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            const model = genAI.getGenerativeModel({ model: model_name });

            let finalPrompt = prompt;
            if (is_json_output) {
                finalPrompt += "\n\nIMPORTANTE: Rispondi ESCLUSIVAMENTE con un oggetto JSON valido, senza testo introduttivo o conclusivo.";
            }

            const safetySettings = [
                { category: HarmCategory.HARM_CATEGORY_HARASSMENT, threshold: HarmBlockThreshold.BLOCK_NONE },
                { category: HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold: HarmBlockThreshold.BLOCK_NONE },
                { category: HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold: HarmBlockThreshold.BLOCK_NONE },
                { category: HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold: HarmBlockThreshold.BLOCK_NONE },
            ];
            
            // --- LOG 2: Chiamata a Gemini ---
            console.log("... Chiamata all'API di Gemini in corso ...");
            // ------------------------------------

            const result = await model.generateContent({
                contents: [{ role: "user", parts: [{ text: finalPrompt }] }],
                safetySettings,
            });

            const response = await result.response;

            // --- LOG 3: Risposta da Gemini ---
            console.log("... Risposta da Gemini ricevuta ...", response);
            
            // Controlla se la risposta è stata bloccata per qualche motivo
            if (!response.candidates || response.candidates.length === 0) {
                console.error("❌ RISPOSTA BLOCCATA DA GEMINI.");
                console.error("Dettagli del blocco:", response.promptFeedback);
                return res.status(500).json({ error: "La risposta del modello è stata bloccata per motivi di sicurezza o altri filtri.", details: response.promptFeedback });
            }
            
            let text = response.text();

            console.log("--- TESTO ESTRATTO DALLA RISPOSTA ---");
            console.log(text);
            console.log("--- FINE TESTO ESTRATTO ---");

            if (is_json_output && text.includes('```')) {
                console.log("... Rilevati backtick markdown, tentativo di pulizia ...");
                // Estrae il contenuto tra il primo ```json e l'ultimo ```
                const match = text.match(/```(json)?\s*([\s\S]*?)\s*```/);
                if (match && match[2]) {
                    text = match[2].trim(); // Prende solo il contenuto JSON e rimuove spazi extra
                    console.log("--- TESTO PULITO PRONTO PER JSON.LOADS ---");
                    console.log(text);
                    console.log("--- FINE TESTO PULITO ---");
                }
            }
            // ---------------------------------------

            if (!text) {
                console.error("❌ Gemini ha restituito un testo VUOTO.");
                return res.status(500).json({ error: "Risposta vuota dal modello LLM." });
            }
            
            console.log(`[Tentativo ${attempt}] Successo! Invio risposta al client Python.`);
            
            return res.send(text); // Invia il testo puro come corpo della risposta

        } catch (error) {
            lastError = error;
            console.error(`❌ ERRORE [Tentativo ${attempt}/${maxRetries}]:`, error.message);

            // Controlliamo se l'errore è un 5xx (problema del server di Google)
            const isServerError = error.message.includes('500') || error.message.includes('503') || error.message.includes('server error');

            if (isServerError) {
                // Se il modello Pro fallisce dopo 2 tentativi, facciamo fallback a Flash
                if (model_name.includes('pro') && attempt > 2) {
                    console.log(`⚠️ ${model_name} non risponde. TENTATIVO DI FALLBACK a gemini-1.5-flash-latest.`);
                    model_name = 'gemini-2.5-flash'; // Cambia il modello per i tentativi successivi
                }

                if (attempt < maxRetries) {
                    const waitTime = Math.pow(2, attempt - 1) * 1000;
                    console.log(`... Errore del server. Riprovo tra ${waitTime / 1000} secondi...`);
                    await new Promise(resolve => setTimeout(resolve, waitTime));
                }
            } else {
                // Se l'errore non è un 5xx o siamo all'ultimo tentativo, interrompiamo
                break;
            }
        }
    }
    
    console.error("❌ Tutti i tentativi di chiamata a Gemini sono falliti.");
    res.status(500).json({ error: 'Chiamata al modello fallita dopo multipli tentativi', details: lastError ? lastError.message : 'Unknown error' });
});

app.listen(port, () => {
    console.log(`LLM Gateway in ascolto su http://localhost:${port}`);
});