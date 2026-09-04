"""
ISAAC Core Ports – Unveränderliche Schnittstellen-Definitionen

Diese Datei ist die einzige autoritative Quelle für alle Domain-Interfaces.
Keine Implementierung hier – nur Protocols und ABCs.

Dependency-Richtung (unverletzbar):
  config → audit → ports → memory → executor → kernel → agents
"""

from typing import Protocol, Any, Optional, List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


# ════════════════════════════════════════════════════════════════════════════
# DATA TYPES & ENUMS
# ════════════════════════════════════════════════════════════════════════════

class PrivilegeLevel(Enum):
    """Privilege-Stufen für Constitution-Gate."""
    USER = 0
    POWER_USER = 1
    OWNER = 2
    ADMIN = 3


class Capability(Enum):
    """Fähigkeiten, die ein Agent haben kann."""
    READ_MEMORY = "read_memory"
    WRITE_MEMORY = "write_memory"
    EXECUTE_CODE = "execute_code"
    MODIFY_REPO = "modify_repo"
    ACCESS_EXTERNAL_API = "access_external_api"
    REFLECT = "reflect"
    AUDIT_LOG = "audit_log"


@dataclass
class RequestContext:
    """Kontext für jeden Request durch die Pipeline."""
    request_id: str
    user_id: str
    privilege_level: PrivilegeLevel
    timestamp: int
    atoms: List[str] = None  # Zerlegte Prompt-Atome (Decomposer)
    routing_trace: Dict[str, Any] = None
    privacy_level: str = "NORMAL"
    capabilities: List[Capability] = None


@dataclass
class AuditEntry:
    """Unveränderliche Audit-Log-Einträge (R=1 Garantie)."""
    timestamp: int
    request_id: str
    action: str
    user_id: str
    privilege_level: PrivilegeLevel
    status: str  # "approved", "denied", "error"
    details: Dict[str, Any]
    reason: Optional[str] = None


# ════════════════════════════════════════════════════════════════════════════
# CORE PORTS (Protocols)
# ════════════════════════════════════════════════════════════════════════════

class MemoryPort(Protocol):
    """
    Memory-Schnittstelle – hybride Speicherung (FTS5 + ChromaDB).
    
    Pre-Conditions:
      - Alle retrieve-Queries sind non-empty strings
      - Alle store-Operationen haben unique keys
    
    Post-Conditions:
      - retrieve() gibt sortierte Liste nach Relevanz zurück
      - store() garantiert Persistierung in beide Stores
    """

    def retrieve(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve ähnliche Memories zu Query.
        
        Args:
            query: Natural language query oder semantisches Embedding
            limit: Max Anzahl Results
            
        Returns:
            Liste von {id, content, relevance_score, source} dicts
        """
        ...

    def store(self, key: str, value: Any, metadata: Dict = None) -> None:
        """
        Store Memory in FTS5 + ChromaDB.
        
        Args:
            key: Eindeutiger Identifier
            value: Beliebiger Python-Objekt
            metadata: Optionale Metadaten (tags, source, etc.)
            
        Raises:
            ValueError wenn key bereits existiert
        """
        ...

    def checkpoint(self, checkpoint_id: str) -> None:
        """Speichere aktuellen State als Checkpoint."""
        ...

    def restore(self, checkpoint_id: str) -> None:
        """Restore State aus Checkpoint."""
        ...


class ExecutorPort(Protocol):
    """
    Execution-Engine für Tasks, Code, Tools.
    
    Pre-Conditions:
      - Task muss gültig sein (validated gegen Constitution)
      - Context darf nicht None sein
      
    Post-Conditions:
      - run_task() gibt ExecutionResult zurück (auch bei Fehler)
      - Alle Executions werden auditiert
    """

    def run_task(self, task: str, context: RequestContext) -> Dict[str, Any]:
        """
        Führe Task aus.
        
        Args:
            task: Task-Beschreibung oder Code
            context: RequestContext mit User/Privilege-Info
            
        Returns:
            {status: "success"|"error", result: ..., error: ...}
        """
        ...

    def run_code_edit(self, file_path: str, edits: List[Dict]) -> Dict[str, Any]:
        """Aider-style Code Editing."""
        ...

    def run_git_ops(self, operation: str, args: Dict) -> Dict[str, Any]:
        """Git-Operationen (commit, push, etc.)."""
        ...


class ConstitutionPort(Protocol):
    """
    Constitution-Gate – zentrale Sicherheits-Policy.
    
    Pre-Conditions:
      - Context muss vollständig und gültig sein
      - Capability muss definiert sein
      
    Post-Conditions:
      - evaluate() gibt immer Decision (approve/deny/escalate) zurück
      - Alle Decisions werden auditiert
    """

    def evaluate(
        self,
        context: RequestContext,
        action: str,
        required_capabilities: List[Capability]
    ) -> Tuple[bool, str]:
        """
        Evaluate ob Action unter Constitution erlaubt ist.
        
        Args:
            context: RequestContext
            action: Was soll passieren
            required_capabilities: Welche Fähigkeiten nötig
            
        Returns:
            (approved: bool, reason: str)
        """
        ...

    def get_privilege_level(self, user_id: str) -> PrivilegeLevel:
        """Hole Privilege-Level für User."""
        ...

    def require_privilege(
        self,
        current: PrivilegeLevel,
        required: PrivilegeLevel
    ) -> bool:
        """Check ob current >= required."""
        ...


class AuditPort(Protocol):
    """
    Append-Only Audit Log (R=1 Garantie).
    
    Pre-Conditions:
      - Entries sind unveränderlich
      - Timestamp muss monoton wachsend sein
      
    Post-Conditions:
      - log() garantiert atomares Schreiben
      - query() gibt konsistente Snapshots zurück
    """

    def log(self, entry: AuditEntry) -> None:
        """
        Log eine Audit-Entry (append-only).
        
        Args:
            entry: AuditEntry
            
        Raises:
            IOError falls Write fehlschlägt
        """
        ...

    def query(
        self,
        start_timestamp: int,
        end_timestamp: int,
        filters: Dict = None
    ) -> List[AuditEntry]:
        """
        Query Audit-Log mit Zeitbereich und Filtern.
        
        Returns:
            Sortierte Liste von AuditEntries (temporal order)
        """
        ...

    def verify_integrity(self) -> bool:
        """Verify dass Log nicht manipuliert wurde (Hashes, etc.)."""
        ...


class DecomposerPort(Protocol):
    """
    Privacy Decomposer – zerteilt Prompts in unabhängige Atome.
    
    Pre-Conditions:
      - Prompt ist non-empty string
      - Sensitivity-Klassifikation muss lokal laufen
      
    Post-Conditions:
      - atomize() garantiert dass kein Atom die volle Identität + Inhalt enthält
      - Keine Atome sind rekonstruierbar (synthetische PII-Tests)
    """

    def atomize(self, prompt: str) -> List[str]:
        """
        Zerlege Prompt in Privacy-respektierende Atome.
        
        Returns:
            Liste von Atom-Strings (unabhängig + sicher)
        """
        ...

    def reassemble(self, atom_results: List[Any]) -> Any:
        """
        Reassemble Ergebnisse von Atomen in finale Antwort.
        
        Pre: Alle Atome wurden verarbeitet
        """
        ...

    def classify_sensitivity(self, text: str) -> str:
        """
        Klassifiziere Sensitivität (LOCAL, kein externes Modell).
        
        Returns:
            "PUBLIC" | "INTERNAL" | "SENSITIVE" | "PII"
        """
        ...


class IntentRouterPort(Protocol):
    """
    Hybrid Intent Router – intelligentes Request-Routing.
    
    Pre-Conditions:
      - Intent-Embeddings müssen in ChromaDB geseed sein
      - Confidence-Thresholds müssen konfiguriert sein
      
    Post-Conditions:
      - route() gibt immer IntentResult mit Confidence zurück
      - Fallback-Chain: low_complexity → semantic → llm → unknown
    """

    @dataclass
    class IntentResult:
        intent: str
        confidence: float  # 0.0-1.0
        layer_used: str  # "regex" | "semantic" | "llm" | "unknown"
        latency_ms: int
        raw_scores: Dict = None

    def route(self, query: str) -> IntentResult:
        """
        Route Query zu Intent-Handler.
        
        Returns:
            IntentResult mit Confidence und welcher Layer verwendet wurde
        """
        ...

    def seed_embeddings(self, intent_class: str, examples: List[str]) -> None:
        """Seed ChromaDB mit Intent-Beispielen."""
        ...


class ReflectionPort(Protocol):
    """
    Reflection Engine – Isaac lernt aus eigenen Runs.
    
    Pre-Conditions:
      - Audit-Log muss vorhanden sein
      - Proposals müssen durch Constitution gehen
      
    Post-Conditions:
      - reflect() gibt ReflectionProposals zurück (nie Execution!)
      - Proposals sind immer versioniert und rollback-fähig
    """

    @dataclass
    class ReflectionProposal:
        change: str
        confidence: float
        evidence: List[str]
        risk_score: float
        proposed_by: str  # "task_reflection" | "deep_reflection" | "human"

    def reflect_on_task(self, task_id: str) -> Optional[ReflectionProposal]:
        """Short reflection nach Task."""
        ...

    def deep_reflect(self, time_window_hours: int = 24) -> List[ReflectionProposal]:
        """Deep reflection über Audit-Log in Zeitfenster."""
        ...


# ════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ════════════════════════════════════════════════════════════════════════════

__all__ = [
    "PrivilegeLevel",
    "Capability",
    "RequestContext",
    "AuditEntry",
    "MemoryPort",
    "ExecutorPort",
    "ConstitutionPort",
    "AuditPort",
    "DecomposerPort",
    "IntentRouterPort",
    "ReflectionPort",
]
