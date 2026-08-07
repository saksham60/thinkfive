"""Dependency injection container - composes the entire application graph.

Order: Config -> DB -> Repositories -> MCP adapters -> LLM providers -> RAG
-> Memory -> HITL -> Agents -> LangGraph -> Application Services -> FastAPI.

Avoids the service-locator anti-pattern in business logic: use cases and
agents receive their dependencies via constructor injection here, not by
reaching into a global container at call time.
"""

from __future__ import annotations

import logging
from typing import Any

from app.agents.banking.agent import BankingAgent
from app.agents.case.agent import CaseAgent
from app.agents.fraud.agent import FraudAgent
from app.agents.graph.builder import build_graph
from app.agents.graph.runner import GraphRunner
from app.agents.knowledge.agent import KnowledgeAgent
from app.agents.supervisor.agent import SupervisorAgent
from app.agents.synthesis.agent import SynthesisAgent
from app.application.approvals.approve_action import ApproveActionUseCase
from app.application.approvals.reject_action import RejectActionUseCase
from app.application.approvals.resume_run import ResumeRunUseCase
from app.application.conversation.get_history import GetHistoryUseCase
from app.application.conversation.start_conversation import StartConversationUseCase
from app.application.conversation.submit_message import SubmitMessageUseCase
from app.application.customer.get_dashboard import GetDashboardUseCase
from app.application.customer.get_profile import GetProfileUseCase
from app.application.fraud.monitor_transactions import MonitorTransactionsUseCase
from app.application.fraud.process_transaction import ProcessTransactionUseCase
from app.application.supervisor.metrics import SupervisorMetricsUseCase
from app.application.supervisor.traces import GetTracesUseCase
from app.core.config import Settings
from app.evaluation.runner import EvaluationRunner
from app.evaluation.service import EvaluationService
from app.events.broker import InProcessEventBroker
from app.events.publisher import EventPublisher
from app.events.replay import EventReplayService
from app.hitl.coordinator import HITLCoordinator
from app.hitl.policy import HITLPolicyEnforcer
from app.hitl.service import HITLService
from app.infrastructure.checkpoint.postgres import CheckpointerFactory
from app.infrastructure.database.postgres import PostgresDatabase
from app.infrastructure.database.supabase import SupabaseClientFactory
from app.infrastructure.embeddings.factory import EmbeddingFactory
from app.infrastructure.repositories.agent_event import AgentEventRepository
from app.infrastructure.repositories.agent_run import AgentRunRepository
from app.infrastructure.repositories.conversation import PostgresConversationRepository
from app.infrastructure.repositories.customer import PostgresCustomerRepository
from app.infrastructure.repositories.evaluation import EvaluationRepository
from app.infrastructure.repositories.memory import PostgresMemoryRepository
from app.infrastructure.repositories.policy import PostgresHITLRepository
from app.infrastructure.repositories.processing import ProcessingStateRepository
from app.llm.factory import LLMFactory
from app.mcp.adapters.banking import BankingMCPAdapter
from app.mcp.adapters.case import CaseMCPAdapter
from app.mcp.adapters.fraud import FraudMCPAdapter
from app.mcp.manager import MCPManager
from app.memory.extractor import MemoryExtractor
from app.memory.policy import MemoryPolicyEnforcer
from app.memory.service import MemoryService
from app.memory.summarizer import ConversationSummarizer
from app.rag.chunking import DocumentChunker
from app.rag.ingestion import DocumentIngestionService
from app.rag.retrieval import HybridRetriever
from app.rag.service import RAGService
from app.security.auth import DemoAuthProvider

logger = logging.getLogger(__name__)


class Container:
    """Composed application dependencies, attached to app.state.container."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        # Infrastructure: database
        self.db = PostgresDatabase(settings)
        self.supabase_factory = SupabaseClientFactory(settings)
        self.checkpointer_factory = CheckpointerFactory(settings)

        # Repositories
        self.customer_repo = PostgresCustomerRepository(self.db)
        self.conversation_repo = PostgresConversationRepository(self.db)
        self.memory_repo = PostgresMemoryRepository(self.db)
        self.agent_run_repo = AgentRunRepository(self.db)
        self.agent_event_repo = AgentEventRepository(self.db)
        self.hitl_repo = PostgresHITLRepository(self.db)
        self.processing_repo = ProcessingStateRepository(self.db)
        self.evaluation_repo = EvaluationRepository(self.db)

        # MCP
        self.mcp_manager = MCPManager(settings)
        self.banking_adapter = BankingMCPAdapter(self.mcp_manager.get_banking_client())
        self.fraud_adapter = FraudMCPAdapter(self.mcp_manager.get_fraud_client())
        self.case_adapter = CaseMCPAdapter(self.mcp_manager.get_case_client())

        # LLM
        self.llm_factory = LLMFactory(settings)

        # RAG
        self.embedding_factory = EmbeddingFactory(settings)
        self.embedding_provider = self.embedding_factory.create()
        self.chunker = DocumentChunker(settings.rag_chunk_size, settings.rag_chunk_overlap)
        self.retriever = HybridRetriever(self.db, self.embedding_provider, settings.rag_similarity_threshold)
        self.rag_service = RAGService(self.retriever)
        self.ingestion_service = DocumentIngestionService(self.db, self.chunker, self.embedding_provider)

        # Memory
        self.memory_extractor = MemoryExtractor()
        self.memory_policy_enforcer = MemoryPolicyEnforcer()
        self.memory_summarizer = ConversationSummarizer(self.llm_factory.create())
        self.memory_service = MemoryService(
            self.memory_repo,
            self.memory_extractor,
            self.memory_policy_enforcer,
            self.memory_summarizer,
            settings.customer_memory_ttl_days,
        )

        # Events
        self.event_broker = InProcessEventBroker()
        self.event_publisher = EventPublisher(self.agent_event_repo, self.event_broker)
        self.event_replay_service = EventReplayService(self.agent_event_repo)

        # HITL
        self.hitl_coordinator = HITLCoordinator(self.hitl_repo)
        self.hitl_policy_enforcer = HITLPolicyEnforcer()

        # Auth
        self.auth_provider = DemoAuthProvider(settings, None)

        # Evaluation
        self.evaluation_runner = EvaluationRunner(self.evaluation_repo, None)
        self.evaluation_service = EvaluationService(self.evaluation_runner)

        # Application use cases (customer/conversation, independent of graph)
        self.start_conversation_use_case = StartConversationUseCase(self.conversation_repo)
        self.get_history_use_case = GetHistoryUseCase(self.conversation_repo)
        self.get_dashboard_use_case = GetDashboardUseCase(
            self.customer_repo, self.banking_adapter, self.fraud_adapter, self.case_adapter
        )
        self.get_profile_use_case = GetProfileUseCase(self.customer_repo)
        self.process_transaction_use_case = ProcessTransactionUseCase(
            self.fraud_adapter, self.processing_repo, self.event_publisher
        )
        self.monitor_transactions_use_case = MonitorTransactionsUseCase(
            self.banking_adapter, self.processing_repo, self.process_transaction_use_case
        )
        self.supervisor_metrics_use_case = SupervisorMetricsUseCase(
            self.agent_run_repo, self.agent_event_repo, self.hitl_coordinator
        )
        self.get_traces_use_case = GetTracesUseCase(self.agent_event_repo)

        # Graph, runner, HITL service, submit-message use case are wired in `wire_graph()`
        # after the checkpointer is asynchronously initialized during lifespan startup.
        self.graph: Any = None
        self.graph_runner: GraphRunner | None = None
        self.hitl_service: HITLService | None = None
        self.submit_message_use_case: SubmitMessageUseCase | None = None
        self.approve_action_use_case: ApproveActionUseCase | None = None
        self.reject_action_use_case: RejectActionUseCase | None = None
        self.resume_run_use_case: ResumeRunUseCase | None = None

    def build_agents_for_customer(self, customer_id: str) -> dict[str, Any]:
        """Construct per-request agent instances (agents are cheap, stateless wrappers)."""
        return {
            "supervisor_agent": SupervisorAgent(self.llm_factory.create()),
            "banking_agent": BankingAgent(self.llm_factory.create(), self.banking_adapter, customer_id),
            "fraud_agent": FraudAgent(self.llm_factory.create(), self.fraud_adapter, customer_id),
            "knowledge_agent": KnowledgeAgent(self.llm_factory.create(), self.rag_service),
            "case_agent": CaseAgent(self.llm_factory.create(), self.case_adapter, customer_id),
            "synthesis_agent": SynthesisAgent(self.llm_factory.create()),
        }

    def build_runtime_context(self, customer_id: str) -> dict[str, Any]:
        """Build the `configurable` dict passed into every graph invocation."""
        return {**self.build_agents_for_customer(customer_id), "event_publisher": self.event_publisher}

    def build_runtime_context_for_resume(self, customer_id: str) -> dict[str, Any]:
        """Rebuild resumed specialists with the persisted trusted customer identity."""
        return {**self.build_agents_for_customer(customer_id=customer_id), "event_publisher": self.event_publisher}

    async def wire_graph(self) -> None:
        """Finish wiring the components that require an async-initialized checkpointer."""
        checkpointer = await self.checkpointer_factory.setup()
        self.graph = build_graph(checkpointer)
        self.evaluation_runner.graph_runner_factory = self._execute_evaluation_case

        self.graph_runner = GraphRunner(
            self.graph,
            self.agent_run_repo,
            self.agent_event_repo,
            self.event_publisher,
            self.hitl_coordinator,
            self.conversation_repo,
            self.memory_service,
            max_iterations=self.settings.graph_max_iterations,
            recent_message_limit=self.settings.memory_recent_messages,
            summary_threshold=self.settings.memory_summary_threshold,
        )

        self.hitl_service = HITLService(
            self.hitl_coordinator,
            self.hitl_policy_enforcer,
            self.case_adapter,
            self.agent_run_repo,
            self.graph_runner,
            self.event_publisher,
        )

        self.submit_message_use_case = SubmitMessageUseCase(
            self.conversation_repo,
            self.agent_run_repo,
            self.graph_runner,
            self.event_publisher,
            self.memory_service,
            self.build_runtime_context,
        )
        self.approve_action_use_case = ApproveActionUseCase(self.hitl_service)
        self.reject_action_use_case = RejectActionUseCase(self.hitl_service)
        self.resume_run_use_case = ResumeRunUseCase(self.hitl_coordinator, self.graph_runner)

    async def _execute_evaluation_case(self, case: dict[str, Any]) -> dict[str, Any]:
        """Execute one isolated golden case against the compiled graph."""
        from uuid import uuid4

        from langchain_core.messages import HumanMessage

        from app.agents.case.toolset import FORBIDDEN_TOOLS

        if case.get("category") == "authorization":
            definitions = CaseAgent(
                self.llm_factory.create(), self.case_adapter, "demo_customer_001"
            ).toolset.get_tool_definitions()
            names = {item["function"]["name"] for item in definitions}
            return {"authorization_safe": names.isdisjoint(FORBIDDEN_TOOLS)}

        thread_id = f"evaluation-{uuid4()}"
        metadata = case.get("metadata") or {}
        if isinstance(metadata, str):
            import json
            metadata = json.loads(metadata)
        customer_id = str(metadata.get("customer_id") or "demo_customer_001")
        config = {
            "configurable": {
                "thread_id": thread_id, "customer_id": customer_id,
                "max_iterations": self.settings.graph_max_iterations,
                **self.build_agents_for_customer(customer_id),
            },
            "recursion_limit": self.settings.graph_recursion_limit,
        }
        result = await self.graph.ainvoke(
            {
                "messages": [HumanMessage(content=case["input_message"])],
                "conversation_id": str(uuid4()), "run_id": str(uuid4()),
                "thread_id": thread_id, "customer_id": customer_id,
                "iteration_count": 0, "warnings": [], "errors": [], "memory_context": {},
            },
            config=config,
        )
        snapshot = await self.graph.aget_state(config)
        evidence_to_agent = {
            "banking_evidence": "banking", "fraud_evidence": "fraud",
            "policy_evidence": "knowledge", "case_evidence": "case",
        }
        actual_agent = next((agent for key, agent in evidence_to_agent.items() if result.get(key)), None)
        actual_tools = [
            item.get("tool")
            for key in evidence_to_agent
            for item in (result.get(key, {}).get("evidence", []) if isinstance(result.get(key), dict) else [])
            if isinstance(item, dict) and item.get("tool")
        ]
        pending = (snapshot.values or {}).get("pending_human_action") or {}
        return {
            **result, "actual_agent": actual_agent, "actual_tools": actual_tools,
            "interrupted": bool(snapshot.next), "approval_id": pending.get("approval_id"),
        }

    async def startup(self) -> None:
        """Startup sequence: connect DB, wire graph, recover stale runs."""
        await self.db.connect()
        try:
            await self.mcp_manager.initialize()
            await self.wire_graph()
            await self._recover_stale_runs()
        except Exception:
            await self.mcp_manager.close_all()
            await self.checkpointer_factory.close()
            await self.db.disconnect()
            raise
        logger.info("Container startup complete")

    async def _recover_stale_runs(self) -> None:
        """Mark stale QUEUED/RUNNING runs as INTERRUPTED; WAITING_FOR_HUMAN untouched."""
        stale = await self.agent_run_repo.find_stale_runs()
        for run in stale:
            await self.agent_run_repo.mark_interrupted(run["run_id"])
        if stale:
            logger.info(f"Recovered {len(stale)} stale runs -> INTERRUPTED")

    async def shutdown(self) -> None:
        """Shutdown sequence: close MCP clients, checkpointer, database pool."""
        await self.mcp_manager.close_all()
        await self.checkpointer_factory.close()
        await self.db.disconnect()
        logger.info("Container shutdown complete")


def create_container(settings: Settings) -> Container:
    """Factory function for the DI container."""
    return Container(settings)
