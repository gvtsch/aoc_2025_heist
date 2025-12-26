# Production Guide: MCP Memory Service

Dieser Guide baut auf dem Tag 12 Memory Service auf und beschreibt die notwendigen Schritte, um ihn von einem Prototypen in einen robusten, produktionsreifen Service zu überführen.

---

## 1. Persistenz & Datenintegrität

Das größte Manko des Prototyps ist der **In-Memory Datenspeicher**. Bei jedem Neustart des Services gehen alle Daten verloren.

### Lösung: Datenbank-Integration

- **SQLite für den Anfang:** Einfach zu integrieren, da es keine separate Server-Installation benötigt. Ideal für kleinere Anwendungen oder um die Logik zu testen.
- **PostgreSQL für Skalierung:** Die erste Wahl für produktive, skalierbare Anwendungen. Bietet Robustheit, Concurrency-Features und erweiterte Query-Möglichkeiten.

**Implementierung (Konzept mit SQLAlchemy):**

```python
# database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@postgresserver/db" # Oder "sqlite:///./memory.db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# models.py
from sqlalchemy import Column, Integer, String, DateTime
# ...
class MemoryTurn(Base):
    __tablename__ = "memory_turns"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(String, index=True)
    message = Column(String)
    # ... weitere Felder

# main.py (Ausschnitt)
from . import models
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/tools/store_memory")
async def tool_store_memory(request: StoreMemoryRequest, db: Session = Depends(get_db)):
    db_turn = models.MemoryTurn(**request.dict())
    db.add(db_turn)
    db.commit()
    db.refresh(db_turn)
    return {"memory_id": db_turn.id, "stored": True}
```

**Nächste Schritte:**
- **Datenbank-Migrationen:** Nutze **Alembic**, um Änderungen am Datenmodell (z.B. neue Spalten) versioniert und sicher in die produktive Datenbank zu bringen.

---

## 2. Fehlerbehandlung & Robustheit

Ein produktiver Service muss auf Fehler vorbereitet sein.

### Fallback-Strategien
- **LLM nicht erreichbar:** Der aktuelle Code hat einen simplen Fallback. Eine bessere Lösung wäre eine **Retry-Logik mit Exponential Backoff** (z.B. mit der `tenacity`-Bibliothek), um kurzzeitige Netzwerkausfälle zu überbrücken.
- **Circuit Breaker:** Bei wiederholten Fehlern des LLM-Services sollte ein "Circuit Breaker" den Service temporär abschalten, um eine Überlastung zu vermeiden und dem System Zeit zur Erholung zu geben.

### Standardisierte Fehler-Responses
MCP und REST-APIs im Allgemeinen profitieren von klaren Fehler-Responses.

```python
# Beispiel für eine standardisierte Fehlermeldung
{
    "error": {
        "type": "invalid_request_error",
        "message": "Agent 'unknown_agent' not found in this session.",
        "code": "agent_not_found"
    }
}
```
FastAPI's `HTTPException` kann hierfür genutzt und mit einer zentralen Exception-Handling-Middleware erweitert werden.

---

## 3. Performance & Skalierung

Unter Last wird der Service an seine Grenzen stoßen.

### Asynchrone Tasks
- **Problem:** Die LLM-Kompression ist ein blockierender I/O-Vorgang und kann mehrere Sekunden dauern. Das blockiert den ganzen Service.
- **Lösung:** Lagere langsame Tasks in einen **Background-Worker** aus (z.B. mit `FastAPI BackgroundTasks` für einfache Fälle oder **Celery** für robuste, skalierbare Systeme). Der API-Call würde dann sofort eine `task_id` zurückgeben, deren Ergebnis später abgefragt werden kann.

### Caching
- **Problem:** Häufige Anfragen für die gleiche Kompression oder die letzten Nachrichten belasten die Datenbank und das LLM unnötig.
- **Lösung:** Implementiere einen **Cache-Layer** mit **Redis**.
  - `get_recent_turns` kann für einige Sekunden gecacht werden.
  - `get_compressed_memory` kann ebenfalls gecacht werden. Der Cache wird invalidiert, sobald eine neue Nachricht für den Agenten gespeichert wird.

### Load Balancing
- Führe mehrere Instanzen des Services (z.B. als Docker-Container) aus und verteile die Last mit einem **Load Balancer** wie Nginx oder einem Cloud-Load-Balancer (AWS ALB, etc.). Dies erfordert einen zustandslosen Service (Daten in DB/Redis, nicht im Speicher).

---

## 4. Security

Der Service ist aktuell komplett ungeschützt.

### Authentifizierung & Autorisierung
- **API Keys:** Eine einfache Methode, bei der jeder Client einen einzigartigen Schlüssel im `Authorization`-Header mitsendet.
- **OAuth 2.0:** Die robustere Methode, die du bereits in Tag 8/9 erkundet hast. Ein zentraler Auth-Service stellt Tokens aus, die der Memory-Service validiert.

**Implementierung (Konzept mit API Key):**
```python
# security.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

API_KEY_NAME = "Authorization"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key: str = Security(api_key_header)):
    # Hier API-Key gegen eine DB prüfen
    if api_key == "SECRET_API_KEY": # Beispiel
        return api_key
    else:
        raise HTTPException(status_code=403, detail="Could not validate credentials")

# main.py
@app.get("/secure-endpoint", dependencies=[Depends(get_api_key)])
async def secure_endpoint():
    return {"message": "This is a secure endpoint"}
```

### Rate Limiting
- Schütze den Service vor Missbrauch (absichtlich oder unabsichtlich), indem du die Anzahl der Anfragen pro Client und Zeitfenster beschränkst (z.B. mit `slowapi`).

---

## 5. Monitoring & Observability

Ohne Einblick in den Zustand des Services fliegst du blind.

### Structured Logging
- Verwende eine Bibliothek wie `structlog`, um Logs im **JSON-Format** auszugeben. Diese sind maschinenlesbar und können von Log-Management-Systemen (ELK-Stack, Datadog, Grafana Loki) einfach verarbeitet und durchsucht werden.

### Metrics
- Integriere `prometheus-fastapi-instrumentator`, um automatisch **Prometheus-Metriken** für jeden Endpunkt bereitzustellen (z.B. `requests_total`, `requests_latency_seconds`).
- Füge **Custom Metrics** hinzu:
  - `memory_compression_duration_seconds`: Wie lange dauert die LLM-Kompression?
  - `memory_turns_stored_total`: Wie viele Nachrichten werden gespeichert?
  - `llm_errors_total`: Wie oft schlägt die LLM-Anfrage fehl?

---

## 6. Deployment & CI/CD

Automatisiere den Weg von Code zu Produktion.

### Containerisierung
- Nutze die `Dockerfile` aus Tag 6 als Basis. Stelle sicher, dass alle Konfigurationen über **Environment-Variablen** gesteuert werden (z.B. `DATABASE_URL`, `SECRET_KEY`).

### CI/CD Pipeline (z.B. mit GitHub Actions)
1.  **Lint & Test:** Bei jedem Push automatisch Code-Qualität prüfen (`black`, `flake8`) und Unit-Tests (`pytest`) ausführen.
2.  **Build:** Ein Docker-Image bauen und mit einem Git-Commit-SHA taggen.
3.  **Push:** Das Image in eine Container Registry (Docker Hub, AWS ECR, etc.) hochladen.
4.  **Deploy:** Automatisch die neue Version des Services in der Zielumgebung (z.B. Kubernetes, AWS ECS) ausrollen.

---

Dieser Guide ist eine Roadmap. Jeder dieser Punkte ist ein eigenes, tiefes Thema, aber er gibt dir eine klare Vorstellung davon, was nötig ist, um aus einem coolen Prototypen einen verlässlichen, skalierbaren und sicheren Microservice zu machen.
