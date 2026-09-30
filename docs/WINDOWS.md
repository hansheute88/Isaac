# Isaac unter Windows 10/11 (natives Python)

Isaac läuft lokal mit **nativem Python** — kein Docker, kein WSL. Lokal-first:
`ACTIVE_PROVIDER=ollama` ist bevorzugt; ist Ollama nicht erreichbar, fällt Isaac
automatisch auf die API-Modelle zurück (groq → gemini → openrouter, siehe
`relay.py::ask_with_fallback` — Fast-Fail + Cooldown für offline Backends).

## Voraussetzungen

1. **Python 3.11/3.12** — von [python.org](https://www.python.org/downloads/),
   bei der Installation **"Add python.exe to PATH"** anhaken.
2. **Ollama (optional, für lokale Modelle)** — von [ollama.ai](https://ollama.ai),
   danach in der Eingabeaufforderung: `ollama pull qwen2.5:1.5b`

## Setup (einmal)

`install_windows.bat` doppelklicken. Das Skript:

1. Erstellt `.venv` und installiert die schlanke Dependency-Liste
   (`requirements-free.txt` — kein Playwright, kein ChromaDB).
2. Erstellt `.env` aus `.env.example` und setzt `ACTIVE_PROVIDER=ollama`.

## API-Fallback-Key hinterlegen (einmal)

`.env` öffnen (Editor) und deinen Groq-Key eintragen:

```
GROQ_API_KEY=gsk_...
```

Der Key ist der Fallback, wenn Ollama nicht läuft. Alternative Provider:
`OPENROUTER_API_KEY` / `GOOGLE_API_KEY` (siehe `.env.example`).

## Starten

`run_isaac_windows.bat` doppelklicken. Es startet den Kernel:

- **Dashboard:** http://localhost:8766
- **WebSocket:** ws://localhost:8765
- Beenden mit **Ctrl+C** im Konsolenfenster.

Beim ersten Start fragt Windows ggf. die Firewall — Zugriff zulassen
(auf localhost beschränkt, keine externen Ports offen).

## Verhalten

| Ollama läuft? | Key in .env? | Isaac nutzt |
|---------------|--------------|-------------|
| ✅            | egal         | Ollama (lokal) |
| ❌            | ✅           | Groq/Gemini/OpenRouter (Fallback) |
| ❌            | ❌           | nur lokale Antworten (Greetings/Status), kein LLM-Chat |

## Validierung

```bat
.venv\Scripts\python.exe -m py_compile isaac_core.py executor.py low_complexity.py memory.py relay.py logic.py
.venv\Scripts\python.exe sanity_check.py
set ISAAC_DISABLE_VECTOR_MEMORY=1 && .venv\Scripts\python.exe -m unittest tests_phase_a_stabilization tests_state_io tests_provider_configuration
```

## Hinweise

- Ports belegt (z. B. 8765/8766 durch andere Software)? In `.env` setzen:
  `MONITOR_PORT=8767` und `MONITOR_HTTP_PORT=8768`.
- Browser-Automatisierung (Playwright) ist unter Windows nicht vorinstalliert —
  nach Bedarf: `.venv\Scripts\pip install -r requirements.txt`.
