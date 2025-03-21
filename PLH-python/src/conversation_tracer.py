from dataclasses import dataclass
from typing import List, Optional
import os
import yaml
from datetime import datetime
from src.decision_types import DecisionType


@dataclass
class TraceEntry:
    parent: str
    child: str
    decision: int
    decision_reasoning: str
    coaching: Optional[str] = None

    def get_decision_name(self) -> str:
        """Get the name of the decision from its value"""
        try:
            return DecisionType(self.decision).name
        except ValueError:
            return "UNKNOWN"


class ConversationTracer:
    def __init__(self):
        self.full_trace: List[TraceEntry] = []
        self.filtered_trace: List[TraceEntry] = []  # Used for LLM context
        self.summary: Optional[str] = None
        self.conversation_initiator: Optional[str] = None
        self.parent_feedback_positive: Optional[str] = None
        self.parent_feedback_negative: Optional[str] = None

    def add_conversation_initiator(self, initiator: str):
        self.conversation_initiator = initiator

    def get_pretty_conversation(self) -> str:
        """
        Get the conversation as a nicely formatted string. Only includes parent and child messages.
        Filters out any None messages and blocked parent messages (FACILITATOR_ONLY_HELP).
        """
        if not self.full_trace and not self.conversation_initiator:
            return ""

        conversation = []
        if self.conversation_initiator is not None:
            conversation.append(f"Child: {self.conversation_initiator}")

        for entry in self.filtered_trace:
            # Only include parent message if decision is not 2 (not blocked)
            if (
                entry.parent is not None
                and entry.decision != DecisionType.FACILITATOR_ONLY_HELP.value
            ):
                conversation.append(f"Parent: {entry.parent}")
            if entry.child is not None:
                conversation.append(f"Child: {entry.child}")

        return "\n".join(conversation)

    def add_entry(self, entry: TraceEntry):
        self.full_trace.append(entry)
        if entry.decision != DecisionType.FACILITATOR_ONLY_HELP.value:
            self.filtered_trace.append(entry)

    def set_summary(self, summary: str):
        self.summary = summary

    def get_full_trace(self) -> List[TraceEntry]:
        return self.full_trace

    def get_filtered_trace(self) -> List[TraceEntry]:
        return self.filtered_trace

    def get_pretty_trace_filtered(self, only_child_parent: bool = False) -> str:
        """
        Get the filtered trace (excluding blocked messages) as a nicely formatted string.
        Filters out any None messages.
        """
        if not self.filtered_trace and not self.conversation_initiator:
            return ""

        trace_entries = []
        if self.conversation_initiator is not None:
            trace_entries.append(f"Child: {self.conversation_initiator}")

        for entry in self.filtered_trace:
            trace_entry = []
            if entry.parent is not None:
                trace_entry.append(f"Parent: {entry.parent}")
            if not only_child_parent and entry.coaching is not None:
                trace_entry.append(f"Coaching: {entry.coaching}")
            if entry.child is not None:
                trace_entry.append(f"Child: {entry.child}")
            if not only_child_parent:
                trace_entry.append(
                    f"Decision: {entry.decision} - {entry.get_decision_name()}"
                )
                if entry.decision_reasoning is not None:
                    trace_entry.append(
                        f"Decision Reasoning: {entry.decision_reasoning}"
                    )
            trace_entries.append("\n".join(trace_entry))

        return "\n\n".join(trace_entries)

    def get_pretty_trace_full(
        self, only_child_parent: bool = False, exclude_latest_child: bool = False
    ) -> str:
        """
        Get the full trace including blocked messages as a nicely formatted string.
        Filters out any None messages.

        Parameters:
          only_child_parent: If True, only includes parent and child messages.
          exclude_latest_child: If True, excludes the latest child message from the trace.
        """
        if not self.full_trace and not self.conversation_initiator:
            return ""

        trace_entries = []
        if self.conversation_initiator is not None:
            trace_entries.append(f"Child: {self.conversation_initiator}")
        if self.summary is not None:
            trace_entries.append(f"Summary: {self.summary}")

        for i, entry in enumerate(self.full_trace):
            # Skip the last entry's child message if exclude_latest_child is True
            # and this is the last entry in the trace
            skip_child = exclude_latest_child and i == len(self.full_trace) - 1

            trace_entry = []
            if entry.parent is not None:
                trace_entry.append(f"Parent: {entry.parent}")
            if not only_child_parent and entry.coaching is not None:
                trace_entry.append(f"Coaching: {entry.coaching}")
            if entry.child is not None and not skip_child:
                trace_entry.append(f"Child: {entry.child}")
            if not only_child_parent:
                trace_entry.append(
                    f"Decision: {entry.decision} - {entry.get_decision_name()}"
                )
                if entry.decision_reasoning is not None:
                    trace_entry.append(
                        f"Decision Reasoning: {entry.decision_reasoning}"
                    )
            trace_entries.append("\n".join(trace_entry))

        return "\n\n".join(trace_entries)

    def save_trace(
        self, trace_type: str = "full", filename: Optional[str] = None
    ) -> str:
        """Save the conversation trace to a YAML file in the 'traces' folder.

        Parameters:
          trace_type: 'full' or 'filtered' trace.
          filename: Optional custom filename. If not provided, uses a timestamp.

        Returns:
          The file path of the saved trace.
        """

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trace_{timestamp}.yaml"

        if trace_type == "full":
            trace_list = self.get_full_trace()
        elif trace_type == "filtered":
            trace_list = self.get_filtered_trace()
        else:
            raise ValueError("Invalid trace_type. Use 'full' or 'filtered'.")

        os.makedirs("traces", exist_ok=True)
        file_path = os.path.join("traces", filename)

        serializable_trace = []
        for entry in trace_list:
            decision_name = entry.get_decision_name()
            ordered_entry = {
                "parent": entry.parent,
                "coaching": entry.coaching,
                "child": entry.child,
                "decision": entry.decision,
                "decision_name": decision_name,
                "decision_reasoning": entry.decision_reasoning,
            }
            serializable_trace.append(ordered_entry)

        data_to_save = {
            "conversation_initiator": self.conversation_initiator,
            "trace": serializable_trace,
            "parent_feedback_positive": self.parent_feedback_positive,
            "parent_feedback_negative": self.parent_feedback_negative,
            "summary": self.summary,
        }

        with open(file_path, "w") as f:
            yaml.safe_dump(data_to_save, f, sort_keys=False, width=10000)

        return file_path

    def set_parent_feedback(self, positive: str, negative: str):
        self.parent_feedback_positive = positive
        self.parent_feedback_negative = negative

    def get_latest_child_message(self) -> Optional[str]:
        """
        Get the latest child message from the conversation trace that wasn't filtered away.
        Iterates through the filtered trace in reverse order to find the first non-None child message.
        Returns the conversation initiator if no filtered messages exist or no non-None child message is found.
        Returns empty string if no messages or initiator exist.
        """

        for entry in reversed(self.filtered_trace):
            if entry.child is not None:
                return entry.child

        if self.conversation_initiator:
            return self.conversation_initiator

        return ""

    def get_previous_coaching(self) -> str:
        """
        Extracts all previous coaching messages from the conversation trace.
        Returns them as a formatted string.
        """
        if not self.full_trace:
            return ""

        coaching_messages = []
        for entry in self.full_trace:
            if entry.coaching and entry.coaching.strip():
                coaching_messages.append(entry.coaching)

        return "\n\n".join(coaching_messages)
