Heute wage ich mich wieder auf mir bekannte Gewässer... Mehr oder weniger. 
Es geht um Docker. Der Teil ist das Mehr, der andere, die FastAPI, das Weniger.

Docker ermöglicht uns eine einfache Isolation von Services und Projekte lassen sich sehr einfach auch auf unterschiedlichen Betriebssystemen bzw. in anderen Umgebungen deployen oder nachbauen. 

Heute geht es erstmal um einen einzelnen Container. Aber man kann auch viele oder mehrere Container orchestrieren. Dazu kommen wir nächste Woche. Wir hosten wieder einen kleinen FastAPI Service.

Apropos... Man benötigt ein sogenanntes docker-compose.yml und ein Dockerfile.
Im yml-File definiert man, welche Container-Dienste mit welchen Einstellungen gemeinsam gestartet und verwaltet werden sollen. 

```yml
version: '3.8'

services:
  agent-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_BASE_URL=http://host.docker.internal:1234/v1
      - LLM_MODEL=google/gemma-3n-e4b
    volumes:
      - ./data:/app/data

```

In diesem docker-compose.yml wird ein Dienst namens "agent-api" definiert, der aus dem lokalen Dockerfile gebaut wird, den Port 8000 nach außen freigibt, zwei Umgebungsvariablen für das LLM setzt und das lokale Verzeichnis ./data ins Containerverzeichnis /app/data einbindet.
Die beiden besagten Umgebungsvariablen LLM_BASE_URL und LLM_MODEL weisen den Container an, auf den Dienst auf dem Host-Rechner unter Port 1234 zuzugreifen. Das ist unser lokal gehostetes LLM in LM-Studio! Und damit ist auch klar, wofür LLM_MODEL gedacht ist ;)

Im Dockerfile definiert man, wie ein einzelnes Container-Image gebaut wird - also die Basis, installierte Software, Konfigurationen und Startbefehl für genau einen Container. 

```Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY day_05_fastapi.py .

# Expose port
EXPOSE 8000

# Run agent
CMD ["python", "day_05_fastapi.py"]
```

Unser Dockerfile sorgt dafür, dass ein Python-Image (3.11-slim) als Basis verwendet wird. Dann wird das Arbeitsverzeichnis definiert und anschließend werden die Pakete aus der requirements.txt installiert. Das Python-Skript wird kopiert, der Port 8000 freigegeben und schließlich wird eben dieses Skript beim Starten des Containers ausgeführt.

Wenn man nun die Grundlagen geschaffen hat, also wenn alle Dateien existieren und funktionieren, kann man das Ganze starten, indem man docker-compose up im Terminal ausführt. Wichtig: Docker muss vorher gestartet sein! Im Hintergrund wird dann der Container gebaut und das oben Beschriebene ausgeführt. 
In diesem Fall wird dann eine FastAPI App gestartet, die man im Browser aufrufen kann. Damit kann man dann wiederum mit dem lokal gehosteten LLM kommunizieren.

Wir können nun mehrere unterschiedliche URLs aufrufen.
z.B. http://localhost:8000/: Aber die URL führt ins Leere, wenn man nichts für die Root-Route definiert hat.
Anders bei http://localhost:8000/docs. Diese URL führt zur automatisch generierten Dokumentation von FastAPI.
http://localhost:8000/health führt zu einem Health Status, sofern der Endpunkt im Code definiert ist. 
Man kann auch über die Dokumentation in den Bereich Chat gelangen und die Kommunikation mit LM-Studio testen. Oder aber über die Kommandozeile.

```bash 
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hallo, wie geht es dir?"}'
```

Dieser Aufruf führt zu folgender Ausgabe.

```Bash
{"response":"Hallo! Mir geht es gut, danke der Nachfrage! 😊 \n\n(Hello! I'm doing well, thank you for asking! 😊)\n\nIt's nice to be able to communicate in German. How can I help you today? \n","container_id":"186177f2a75e"}% 
```

Und so weiter und so weiter. Damit kann man sich mal in Ruhe auseinander setzen. 

## Zusammenfassung
Wir haben also jetzt einen Service im Docker-Container am Laufen – und können sogar mit ihm quatschen. Das bringt uns echt ein paar Vorteile:

- Egal ob Windows, Mac oder Linux – das Ding läuft überall gleich. Kein „bei mir geht’s, bei dir nicht“ mehr.
- Alles, was die App braucht, steckt im Container. Keine Abhängigkeits-Hölle, keine Versionskonflikte.
- Wenn’s mal woanders laufen soll: Einfach Container starten, fertig. Reproduzierbar und stressfrei.
- Mehrere Instanzen? Kein Problem – einfach skalieren, wie man lustig ist.
- Und: Die Schnittstellen sind klar – HTTP rein, Antwort raus. Übersichtlich und sauber.

Damit haben wir nun das Docker-Basislager aufgebaut. Nächste Woche geht’s dann ans Eingemachte: Mehrere Container, die zusammenarbeiten. 
Wenn du noch mehr zu Docker wissen möchtest, und meine Erklärungen dir gefallen, dann schau doch mal hier nach: [Mein Docker Setup](https://gvtsch.github.io/Blog/Docker,-Compose--and--Codespaces)

