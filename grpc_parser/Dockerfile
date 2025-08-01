# Usa un'immagine Node.js ufficiale e leggera
FROM node:18-alpine

# Crea la directory di lavoro
WORKDIR /usr/src/app

# Copia i file di dipendenza
COPY package*.json ./

# Installa le dipendenze
RUN npm install

# Copia il resto del codice sorgente
COPY . .

# Esponi la porta che l'app usa
EXPOSE 3000

# Comando per avviare l'app
CMD [ "node", "index.js" ]