import csv
import os
from typing import List, Optional
from src.conversation_tracer import TraceEntry, ConversationTracer
from src.decision_types import DecisionType
from datetime import datetime


class TraceExporter:
    def __init__(self, conversation_tracer: ConversationTracer):
        self.conversation_tracer = conversation_tracer

    def export_to_csv(self, filename: Optional[str] = None) -> str:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"full_unfiltered_trace_{timestamp}.csv"

        os.makedirs("csv", exist_ok=True)
        file_path = os.path.join("csv", filename)

        full_trace = self.conversation_tracer.get_full_trace()

        csv_data = self._prepare_csv_data(full_trace)

        with open(file_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)

            writer.writerow(
                [
                    "Turn",
                    "Interaction",
                    "Text",
                    "Expert Score 1 (1-5)",
                    "Comment 1",
                    "Expert Score 2 (1-5)",
                    "Comment 2",
                ]
            )

            for row in csv_data:
                writer.writerow(row)

        return file_path

    def _prepare_csv_data(self, trace: List[TraceEntry]) -> List[List]:
        csv_data = []

        if self.conversation_tracer.conversation_initiator:
            csv_data.append(
                [
                    0,
                    "Child",
                    self.conversation_tracer.conversation_initiator,
                    "",
                    "",
                    "",
                    "",
                ]
            )

        current_turn = 1
        for entry in trace:
            csv_data.append([current_turn, "Parent", entry.parent, "", "", "", ""])

            # Include decision for all types
            csv_data.append(
                [current_turn, "Decision", f"{entry.decision} - {entry.get_decision_name()}", "", "", "", ""]
            )

            csv_data.append(
                [
                    current_turn,
                    "Reasoning",
                    entry.decision_reasoning if entry.decision_reasoning else "...",
                    "",
                    "",
                    "",
                    "",
                ]
            )

            # Include coaching messages for all relevant decision types
            if entry.coaching:
                csv_data.append(
                    [current_turn, "Facilitator", entry.coaching, "", "", "", ""]
                )

            # Only FACILITATOR_ONLY_HELP blocks child messages
            child_response = "[Message Blocked]" if entry.decision == DecisionType.FACILITATOR_ONLY_HELP.value else entry.child

            csv_data.append([current_turn, "Child", child_response, "", "", "", ""])

            # Only increment turn count if not FACILITATOR_ONLY_HELP
            if entry.decision != DecisionType.FACILITATOR_ONLY_HELP.value:
                current_turn += 1
        
        if self.conversation_tracer.parent_feedback_positive:
            csv_data.append(["", "", "", "", "", "", ""])  
            csv_data.append(
                ["", "Parent Reflection (Positive)", self.conversation_tracer.parent_feedback_positive, "", "", "", ""]
            )
            
        if self.conversation_tracer.parent_feedback_negative:
            csv_data.append(
                ["", "Parent Reflection (Negative)", self.conversation_tracer.parent_feedback_negative, "", "", "", ""]
            )
                
        if self.conversation_tracer.summary:
            if not self.conversation_tracer.parent_feedback_positive:
                csv_data.append(["", "", "", "", "", "", ""])  
            csv_data.append(
                ["", "Summary", self.conversation_tracer.summary, "", "", "", ""]
            )

        return csv_data
