# P0 Governance-Enforcement — G1/G2-Vorprüfung und G3-Testvertrag

**Status:** Untersuchung / keine produktive Governance-Änderung  
**Basisbranch:** `isaac-2.0/masterplan`  
**Fixierter Basiscommit:** `31a4b67ee8863e2e850f23c63ebcb1f3cfa1718d`  
**Prüfbranch:** `audit/p0-governance-g1-g3-20261029`  
**Datum:** 29.10.2026  
**Taxonomie:** B (Execution), C (Audit), E (Tests), A (nur Invariantenbeschreibung).  
**Verbindliche Projektregeln:** `AGENTS.md`; keine Änderung an `main`, Runtime, Deployments, Memory oder UI.

## 1. Sicherheitsinvariante

> Keine erreichbare effektbehaftete Aktion darf *allein wegen einer fehlenden Capability-Deklaration* durchgelassen werden. Ein tatsächlicher Effekt erfordert eine überprüfbare, zeitlich und sachlich an die konkrete Aktion gebundene Autorisierung — unabhängig vom Einstiegspunkt.

**Unterschiedliche Behauptungen strikt trennen:**

- **Policy-Korrektheit:** R/W/X verweigert einen expliziten, nicht erlaubten Zugriff.
- **Enforcement-Vollständigkeit:** jede relevante Ausführung erreicht einen verbindlichen Autorisierungspunkt.
- **Bypass-Resistenz:** auch alternative oder direkte Laufzeitpfade verweigern dieselbe nicht autorisierte Wirkung.
- **Effect-Verifikation:** ein Tool-Erfolg ist weder automatische Ausführungs- noch Wirkungsbestätigung.

Ein fehlender R/W/X-Check ist nicht notwendigerweise ein vollständiger Governance-Bypass: zusätzliche Legacy-Prüfungen können die Aktion trotzdem verweigern. Diese Ebenen sind getrennt zu testen.

## 2. G1 — Vorläufige, quellcodegestützte Effektgrenzen

Die Tabelle beschreibt **statisch gelesene Funktionspfade**, keinen vollständig bewiesenen Call-Graph. Line-Nummern beziehen sich auf den Basiscommit.

| Eingang / Effektgrenze | Beobachtete Governance | Quellort | Offene Frage |
|---|---|---|---|
| `Executor._maybe_use_tool` → `run_selected_tool` | Constitution und `_check_tool_execution_capability`; bei fehlendem `tool:*`-Eintrag wird R/W/X übersprungen | `executor.py:948-1040`, `executor.py:674-741` | Wird die konkrete Wirkung durch andere Gates zuverlässig eingeschränkt? |
| `tool_runtime.run_selected_tool` direkt | Constitution normalerweise; `skip_constitution=True` kann die dortige Prüfung auslassen | `tool_runtime.py:777-844` | Kann jeder interne Aufrufer eine gültige Vorentscheidung belegen? |
| `tool_runtime.run_tool` → `_run_registry_tool` | Im direkten Wrapper keine eigene Aktionstoken-/R/W/X-Prüfung sichtbar | `tool_runtime.py:845-847`, `tool_runtime.py:264-349` | Wo liegt die tatsächlich verbindliche Autorisierung? |
| `tool_runtime.invoke_mcp_tool` | Remote-Bridge bzw. lokale MCP-Registry; unterschiedliche Kontrollpfade | `tool_runtime.py:194-234` | Welche Garantien gelten für beide Transportvarianten? |
| `ComputerUseRuntime.execute` | Feature-/Dry-run-Gate; Verteilung auf Handler, weitere Prüfungen teils in Handlern | `computer_use.py:283-341` | Einheitliche Berechtigung für Shell, Clipboard, UI und Credentials? |
| `execute_owner_action` | Aktionsspezifische Owner- und Privilege-Regeln | `owner_action.py:1491+` | Welche Handler umgehen gemeinsame Effektgrenzen? |
| `execute_file_command` | Constitution und Pfadprüfung, explizite Audit-Entscheidungen | `file_access.py:193+` | Belegen die Events eine gültige, aktionsgebundene Autorisierung? |
| `apply_hunk` / `apply_from_model_text` | Path-Roots, optionales Constitution-Gate, Dry-run-Mechanismen | `code_edit.py:310+` | `skip_constitution` und direkte Handleraufrufe? |
| `git_commit` / Git-Operationen | Repo-/Path-Check, Constitution standardmäßig | `git_ops.py:319+` | Sind direkte oder delegierte Aufrufe gleichwertig geschützt? |
| `IsaacMCPService.invoke` | Exposure-Policy, Caller-Level, Rate-Limit; Remote-Owner-Overrides abgelehnt | `isaac_mcp.py:185-245` | Interne Trusted-Caller und lokale Registry getrennt prüfen |
| `MCPRegistry.invoke_tool` | Legacy-Privilege-Gate, Constitution für ausgewählte Tools | `mcp_registry.py:120-155` | Nicht gegatete Handler und `allow_owner_override` bei direkten Aufrufen |
| `Executor._execute_code` | Executor-Gate, Codevalidierung und isolierter Python-Prozess | `executor.py:1695-1790` | Effektumfang der Sandbox und Verbindung zum Autorisierungsnachweis |

**Bisheriger Evidenzgrad:** direktes Lesen dieser Funktionen; noch keine systematische dynamische Reachability-Analyse, keine vollständige Imports-/Aliasauflösung, keine Runtime-/Fault-Injection-Läufe. Die Liste darf nicht als „G1 abgeschlossen“ markiert werden.

### Automatische G1-Kandidatenliste

```bash
python3 scripts/g1_execution_surface_inventory.py \
  --root . --output /tmp/isaac-g1-candidates.json
python3 -m unittest -v tests_isaac_p0_g1_inventory
```

Der AST-Scanner importiert keine Isaac-Module, meldet potentielle Ausführungsaufrufe, Guard-Referenzen, Definitionsorte und Syntaxprobleme. Sein Resultat ist **Kandidateninventur, kein vollständiger Aufrufgraph**. Fehlende dynamische Calls, `getattr`, Aliase, Callback- und Dependency-Injection-Kanten müssen manuell/dynamisch vervollständigt werden. Jeder Kandidat braucht eine bestätigte `entry → guard → sink`-Trajektorie.

## 3. G2 — Vorläufige Autorisierungs-Matrix

| Aktionsklasse | Erforderliche Operation | Kontextbindung | Besondere Anforderung |
|---|---|---|---|
| Tool-/MCP-Aufruf | `execute` | Principal, Task, Tool-ID, kanonisierte Argumente | Auch direkter Runtime-Aufruf |
| Datei lesen | `read` | Aufgelöster kanonischer Pfad | Pfadänderung, Symlink-TOCTOU, Scope |
| Datei ändern/löschen | `write` | Pfad, Operation, Inhaltshash oder Zielidentität | Revalidation unmittelbar vor Write |
| Shell-/Code-Ausführung | `execute` | Executable, argv, cwd, Environment-Policy | Prozess-/Child-Prozess-Effekte prüfen |
| Computer-Use | Operation je Handler | Aktion, Ziel, Parameter und Owner-Kontext | Nicht nur Runtime-Feature-Flag |
| Git-Operation | `write` (Repository) | Repo-Root, Ref, Pfade, Aktion | Keine implizite Übertragung auf Push |
| Externer Netzwerkzugriff | `execute` / `write` (Egress) | Ziel-Host, Request/Redaction-Policy | Privacy-Kontrolle vor Egress |

**Dies ist ein Prüfvertrag, keine Behauptung, dass diese zentrale Schnittstelle bereits existiert.** G2 wird erst geschlossen, wenn jede erreichbare Wirkung nach einem geprüften Policy-Vertrag eingeordnet und abgedeckt ist.

### Angestrebte Ausführungsberechtigung

`principal, task_id, action_id, resource, operation, canonical_arguments_hash, policy_version, issued_at, expires_at, single_use`.

- Kein Caller darf sich selbst eine gültige Autorisierung ausstellen.
- Überprüfung und Verbrauch derselben Berechtigung müssen **atomar** sein (keine doppelte Nutzung zwischen parallelen Workern).
- Geänderte Argumente, Ressource oder Policy-Version invalidieren die Autorisierung.
- Crash/Timeout: „verbrauchte Autorisierung“ ist **nicht** gleich „einmaliger externer Effekt“. Für Wiederholungen sind Idempotency-Keys, Effekt-Reconciliation oder ein expliziter UNKNOWN-Zustand erforderlich.
- Der tatsächliche Sink muss die Autorisierung validieren; Vorprüfungen an API/UI/MCP allein sind nicht ausreichend.
- Legacy-Policies erst migrieren, bevor bestehende Kompatibilitätspfade entfallen.

## 4. G3 — Tests, kein Produktiv-Fix

```bash
# Charakterisierung des gegenwärtigen Verhaltens (soll auf Basiscommit grün sein):
ISAAC_DISABLE_VECTOR_MEMORY=1 python3 -m unittest -v \
  tests_isaac_p0_governance_characterization

# Absichtlich ROT; ausschließlich separat in einer isolierten Testumgebung:
ISAAC_DISABLE_VECTOR_MEMORY=1 python3 -m unittest -v \
  tests_isaac_p0_governance_red

# Prüfung des reinen Inventarisierungswerkzeugs:
python3 -m unittest -v tests_isaac_p0_g1_inventory
```

Der RED-Test verwendet `AsyncMock` an der **Effekt-Senke**, um zu prüfen, ob ein direkter Aufruf diese ohne aktionsgebundene Freigabe erreicht. Es findet kein realer Shell-, Netzwerk- oder Dateieffekt statt. Die Constitution wird in einem Test bewusst als „allow“ simuliert, um fehlende zusätzliche Durchsetzung zu isolieren. Das ist **kein Nachweis eines vollständigen Umgehungsangriffs gegen alle Legacy-Gates**.

**Ausstehende negative Tests nach vollständigem G1:** geänderte Argumente/Zielressource, abgelaufene Grants, Double-Consume parallel, Cross-Task-Reuse, Retry nach Crash zwischen Remote-Effekt und Evidence, manipulierte Events, Symlink-/Pfadwechsel, direkte Internal-Caller und MCP-Transporte.

**Wichtig:** Die vier Tests in `tests_isaac_p0_governance_red.py` sind absichtlich fehlschlagende Spezifikationen. Sie dürfen den verpflichtenden grünen CI-Status nicht ersetzen und werden ausschließlich explizit gestartet, bis die Effektgrenze tatsächlich gehärtet ist.

## 5. G4 — Evidence und Recovery

Verfügbare Bausteine: `isaac_runtime_audit.py` mit `action_id`, `parent_action_id`, Autorisierungs- und Ausführungsereignissen sowie `isaac_30day_evidence.py` mit Hash-Kette/Dateisynchronisation. Diese Mechanismen sollen **erweitert statt ersetzt** werden.

Nachweis pro Aktion getrennt führen:

1. Auth-Decision `DENY / ALLOW` samt Policy-, Task-, Principal- und Argumentbindung
2. Auth-Consume `RESERVED / CONSUMED / EXPIRED` mit atomarem Zustandswechsel
3. Invocation `NOT_STARTED / STARTED / COMPLETED / UNKNOWN`
4. Tool-Rückmeldung `SUCCESS / FAILURE / TIMEOUT`
5. Effektprüfung `CONFIRMED / ABSENT / UNKNOWN`
6. Verknüpfte Evidence-IDs und gegen vollständige Neuberechnung geschützter externer Integritätsanker

**Crash-Fall:** Wenn der externe Effekt eingetreten ist, der Evidence-Schreibvorgang aber scheitert, darf ein Retry nicht blind denselben Effekt wiederholen. UNKNOWN und anschließende Reconciliation sind erforderlich.

## 6. Validierungs- und Scope-Status

- [x] Basiscommit festgehalten; separater Prüfbranch verwendet
- [x] Charakterisierung, isolierte Negativ-Spezifikationen, read-only AST-Inventarisierer hinzugefügt
- [ ] AST-Inventur auf *vollständigem* Repository ausgeführt und dynamisch validiert
- [ ] Jeder produktive, erreichbare Aufrufpfad mit Guard und Sink vollständig verifiziert
- [ ] Neue Tests im echten Isaac-Python-Environment ausgeführt (aktuell nicht behauptet)
- [ ] Atomare Autorisierung implementiert (bewusst **nicht** Teil dieses Prüfbranches)
- [ ] 30-Tage-Proof / G4-Fault-Injection belegt

**Keine Änderungen an:** `executor.py`, `tool_runtime.py`, `constitution.py`, `isaac_capabilities.py`, `isaac_30day_evidence.py` oder produktiven MCP-/Computer-Use-Implementierungen. Kein Merge, kein Deploy, keine produktive Freigabe.

**Stop-Bedingung:** Bei neuen unaufgeklärten Effektpfaden darf G1/G2 nicht als abgeschlossen gelten. Erst danach Minimalpatch und eigenständiger Hardening-PR.
