"""
Tool call tracer for Agent Breaker.
Captures tool calls from LangGraph graph.stream() output.
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any, List

from langchain_core.messages import AIMessage, ToolMessage


@dataclass
class ToolCallRecord:
    """Record of a single tool call during graph execution."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Optional[str]
    was_executed: bool  # True if ToolMessage found (tool ran), False if only AIMessage intent


class ToolCallTracer:
    """
    Captures tool calls from LangGraph graph.stream() chunks.
    
    Usage:
        tracer = ToolCallTracer()
        for chunk in graph.stream(state):
            tracer.capture(chunk)
        
        if tracer.has_tool_executions():
            print(tracer.get_executed_tools())
    """

    def __init__(self):
        self.records: List[ToolCallRecord] = []
        self._pending: Dict[str, ToolCallRecord] = {}  # tool_call_id → record

    def capture(self, chunk: Dict) -> None:
        """
        Process one chunk from graph.stream() and extract tool calls.

        Args:
            chunk: One output from `for chunk in graph.stream()`
                   Format: {node_name: {state_key: value, ...}}
        """
        for node_name, state_update in chunk.items():
            messages = state_update.get("messages", [])

            for msg in messages:

                # Case 1: LLM decided to call a tool (intent)
                if isinstance(msg, AIMessage) and msg.tool_calls:
                    for tc in msg.tool_calls:
                        record = ToolCallRecord(
                            tool_name=tc["name"],
                            arguments=tc["args"],
                            result=None,
                            was_executed=False
                        )
                        self._pending[tc["id"]] = record
                        self.records.append(record)

                # Case 2: Tool actually executed and returned a result
                if isinstance(msg, ToolMessage):
                    if msg.tool_call_id in self._pending:
                        record = self._pending[msg.tool_call_id]
                        record.result = str(msg.content)[:300]
                        record.was_executed = True

    def has_tool_executions(self) -> bool:
        """Return True if any tools were actually executed (ToolMessage confirmed)."""
        return any(record.was_executed for record in self.records)

    def get_executed_tools(self) -> List[str]:
        """Return list of tool names that were actually executed."""
        return [record.tool_name for record in self.records if record.was_executed]
