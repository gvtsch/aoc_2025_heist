Tag 8. Die zweite Woche. Heute geht es um Token-basierte Authentifizierung. 

Wir bauen heute einen einfachen OAuth 2.0 Token-Service mit FastAPI, der einen Client Credential Flow implementiert. Das ist ein gängiges Authentifizierungsverafhren, um Maschinen (oder wie bei uns (Mikro-)Services, Bots, ...) sicher den Zugriff auf eine API zu geben. 

Gehen wir darauf doch erstmal genauer ein, bevor wir es implementieren. Als erstes sendet der Client seine Client-ID, sein Secret und den gewünschten Scope an den Token-Endpunkt des Auth-Servers. Anschließend prüft der Auth-Server die Daten und stellt ein JWT-Token aus. Dabei handelt es sich um eine JSON Web Token. Das ist ein kompaktes, URL-sicheres Token-Format. Es enthält nur Zeichen, die in einer URL problemlos übertragen werden können, ohne kodiert oder verändert werden zu müssen: Buchstaben, Zahlen, Bindestriche, Unterstriche und Punkte. Das JWT-Token enthält Informationen, die als JSON-Objekt zwischen zwei Parteien übertragen werden. Schließlich kann der der Client mit dem Token auf geschützte Resourcen zugreifen. 

Wichtig: Das Token ist nicht unbegrenzt gültig! Es läuft nach einer bestimmten Zeit ab (bei uns nach einer Stunde). Ist das Token abgelaufen, muss der Client ein neues anfordern. So bleibt der Zugang immer aktuell und sicher – und gestohlene oder veraltete Tokens verlieren automatisch ihre Gültigkeit.

Und warum ist das für unser Projekt wichtig? Nicht jeder "Agent" soll Zugriff auf alle Informationen haben! Ganz wie im realen, professionellen Leben eben auch.

**Kurzer Exkurs: Warum ist das überhaupt sicher?**
Das Prinzip ist simpel. Nur wer die richtige Client-ID und das passende Secret kennt, bekommt ein Token. Und nur mit diesem Token kommt man an die geschützten Endpunkte. Das Token selbst ist ein signiertes JWT – das kann nicht einfach gefälscht werden. Die Rechte (Scopes) werden beim Ausstellen geprüft und im Token festgehalten. Ohne gültiges Token kein Zugriff.

Wer das Secret kennt, kann sich natürlich als dieser Client ausgeben. Deshalb gilt auch hier wie überall – Secrets gehören nicht ins Repo, sondern in Umgebungsvariablen oder ein Secret-Management. In echten Systemen werden sie regelmäßig rotiert und gut geschützt. Aber das Prinzip bleibt... Ohne Secret kein Token, ohne Token kein Zugriff. Und genau so wollen wir das für unsere Agenten und Services haben!

Zur Implementierung... Weil wir einiges davon schon kennen, werde ich nicht mehr alles zeigen oder ansprechen. Das komplette File gibt es wieder im Repository: https://github.com/gvtsch/aoc_2025_heist/blob/main/day_08


## Die FastAPI-App und die Clients

```python
app = FastAPI(title="OAuth Service", version="1.0")

CLIENTS = {
    "hacker-client": {
        "secret": "hacker-secret-123",
        "scopes": ["simulation:read", "simulation:write"]
    },
    "planner-client": {
        "secret": "planner-secret-456",
        "scopes": ["memory:read"]
    }
}
```

Hier definieren wir unsere API und die erlaubten Clients. Jeder Client hat ein Secret und eine Liste von Scopes, also Berechtigungen. In der Realität würde das natürlich in einer Datenbank liegen. Für unsere Zwecke reicht aber im Moment ein Dictionary.

## TokenRequest und TokenResponse

```python
class TokenRequest(BaseModel):
    client_id: str
    client_secret: str
    scope: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    scope: str
```

Das sind die Datenmodelle für die Anfrage und die Antwort beim Token-Endpunkt. Der Client schickt seine Daten als JSON, und wir antworten mit dem Token und ein paar Metadaten.

## Token generieren
Irgendwann muss auch das JWT gebaut werden.

```python
def create_token(client_id: str, scope: str) -> str:
    payload = {
        "sub": client_id,
        "scope": scope,
        "exp": datetime.utcnow() + timedelta(hours=1),
        "iat": datetime.utcnow(),
        "iss": "heist-oauth-service"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

Das sogenannte Payload enthält:
- sub: Wer ist der Client?
- scope: Was darf er?
- exp: Wann läuft das Token ab?
- iat: Wann wurde es erstellt?
- iss: Wer hat das Token ausgestellt?

Und dieses Token wird dann mit unserem Secrect-Key signiert. 

## Token prüfen

```python
def verify_token(authorization: str) -> dict:
    try:
        token = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")
```

Hier wird das Token aus dem Header extrahiert und geprüft. Wenn alles passt, bekommen wir das Payload zurück - sonst gibt es einen Fehler.

## Token Endpunkt
Und wir kommen mal wieder zu einem Endpunkt. Und hier passiert dann auch die "Magie".

```python
@app.post("/oauth/token", response_model=TokenResponse)
def get_token(request: TokenRequest):
    if request.client_id not in CLIENTS:
        raise HTTPException(status_code=401, detail="Unknown client")
    client = CLIENTS[request.client_id]
    if client["secret"] != request.client_secret:
        raise HTTPException(status_code=401, detail="Invalid secret")
    if request.scope not in client["scopes"]:
        raise HTTPException(status_code=403, detail="Scope not allowed")
    token = create_token(request.client_id, request.scope)
    return TokenResponse(
        access_token=token,
        token_type="Bearer",
        expires_in=3600,
        scope=request.scope
    )
```

Der Client schickt seine Zugangsdaten und den gewünschten Scope an den Endpunkt. Der Server prüft, ob der Client bekannt ist, ob das Secret stimmt und ob der Scope erlaubt ist. Nur wenn alle Bedingungen erfüllt sind, wird ein Token generiert und zurückgegeben. Dieses Token ist der Schlüssel für den weiteren Zugriff auf geschützte Ressourcen – und genau so funktioniert der Client Credentials Flow in OAuth 2.0: Maschinen authentifizieren sich, bekommen ein zeitlich begrenztes Zugangs-Token und können damit gezielt auf APIs zugreifen, ohne dass ein Benutzer beteiligt ist.

## Geschützte Resource
Um das alles zu testen, brauchen wir noch etwas, das geschützt werden soll.

```python
@app.get("/protected-resource")
def protected_resource(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No authorization header")
    payload = verify_token(authorization)
    return {
        "message": "Access granted!",
        "client": payload["sub"],
        "scope": payload["scope"]
    }
```

Hier muss der Client sein Token vorzeigen. Das Token wird geprüft und wir erlauben den Zugriff, wenn alles passt. So schützen wir unsere Resource, bzw. unsere API vor unberechtigtem Zugriff und können steuern, wer was darf und wer nicht. 

Und um das alles automatisch zu testen, habe ich noch eine Testdatei.

```python
import requests

BASE_URL = "http://localhost:8001"

def get_token(client_id, client_secret, scope):
    resp = requests.post(
        f"{BASE_URL}/oauth/token",
        json={
            "client_id": client_id,
            "client_secret": client_secret,
            "scope": scope
        }
    )
    print(f"Token request status: {resp.status_code}")
    print(f"Response: {resp.text}\n")
    return resp.json().get("access_token") if resp.ok else None

def test_protected(token):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    resp = requests.get(f"{BASE_URL}/protected-resource", headers=headers)
    print(f"Protected resource status: {resp.status_code}")
    print(f"Response: {resp.text}\n")

def main():
    print("== Successful access ==")
    token = get_token("hacker-client", "hacker-secret-123", "simulation:read")
    test_protected(token)

    print("== Wrong secret ==")
    token = get_token("hacker-client", "wrong", "simulation:read")
    test_protected(token)

    print("== Wrong scope ==")
    token = get_token("hacker-client", "hacker-secret-123", "memory:read")
    test_protected(token)

    print("== No token ==")
    test_protected(None)

if __name__ == "__main__":
    main()
```

Diese Datei arbeitet vier Fälle ab.
1. Erfolgreicher Zugriff: Wir holen uns mit korrekten Daten ein Token und greifen damit auf die geschützte Resource zu. Ergebnis: Zugriff erlaubt, alles läuft wie geplant.
2. Falsches Secret: Wir geben absichtlich ein falsches Secret an. Der Server lehnt das ab – kein Token, kein Zugriff. So soll es sein!
3. Falscher Scope: Wir fragen einen Scope an, den der Client gar nicht haben darf. Auch hier gibt es kein Token und damit keinen Zugang zur Resource. Rechte werden sauber geprüft.
4. Kein Token: Wir versuchen ganz ohne Token auf die Resource zuzugreifen. Der Server blockt sofort ab – ohne gültigen Ausweis kommt hier niemand rein.

```bash
== Successful access ==
Token request status: 200
Response: {"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoYWNrZXItY2xpZW50Iiwic2NvcGUiOiJzaW11bGF0aW9uOnJlYWQiLCJleHAiOjE3NjUyMDE5MDUsImlhdCI6MTc2NTE5ODMwNSwiaXNzIjoiaGVpc3Qtb2F1dGgtc2VydmljZSJ9.qtwiY-u3r1VfAKeCM7oRMEBrl7UwYDhUPzT4y2K_o9I","token_type":"Bearer","expires_in":3600,"scope":"simulation:read"}

Protected resource status: 200
Response: {"message":"Access granted!","client":"hacker-client","scope":"simulation:read"}

== Wrong secret ==
Token request status: 401
Response: {"detail":"Invalid secret"}

Protected resource status: 401
Response: {"detail":"No authorization header"}

== Wrong scope ==
Token request status: 403
Response: {"detail":"Scope not allowed"}

Protected resource status: 401
Response: {"detail":"No authorization header"}

== No token ==
Protected resource status: 401
Response: {"detail":"No authorization header"}
```

Jeder dieser Fälle zeigt, wie der Service auf typische Fehler oder fehlende Berechtigungen reagiert. Nur wer sich korrekt ausweist und die richtigen Rechte hat, kommt durch. Genau so wollen wir das für unsere Agenten und Services haben!


## Was wäre in Produktion anders?

In echten Anwendungen gibt es noch ein paar Dinge, die du beachten solltest:
- **Clients und Secrets** werden nicht im Code, sondern in einer Datenbank oder einem Secret-Management-System gespeichert und verwaltet.
- **Secrets** sollten nie im Repository liegen, sondern als Umgebungsvariablen oder über spezielle Tools bereitgestellt werden.
- **HTTPS** ist Pflicht! Nur so sind die Daten und Tokens wirklich sicher übertragen.
- **Token-Lifetime und Rotation**: Tokens sollten regelmäßig erneuert und abgelaufene Tokens ungültig gemacht werden.
- **Monitoring und Logging**: Verdächtige Zugriffe und Fehler sollten überwacht werden.
- **Rate-Limits und IP-Whitelist**: Schützen vor Missbrauch und Angriffen.

Das Beispiel hier ist bewusst einfach gehalten, damit wir das Prinzip verstehen und direkt nachbauen können. Für produktive Systeme gibt es viele weitere Best Practices. Aber da stecke ich nicht besonders tief drin.

## Zusammenfassung

Heute haben wir erfolgreich einen OAuth 2.0 Service implementiert. Auf diese Weise werden wir regeln, wer worauf Zugriff hat und wer nicht.
