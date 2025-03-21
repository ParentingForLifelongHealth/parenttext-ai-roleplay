from langchain_together import ChatTogether
from langchain.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    PromptTemplate,
)
from langchain_openai import ChatOpenAI
from src.conversation_tracer import ConversationTracer, TraceEntry
from src.config import Config
from src.decision_types import DecisionType
from dotenv import load_dotenv
import os
import yaml
import json
from typing import List, Optional, Tuple
from datetime import datetime

# Load environment variables from .env file
load_dotenv()


class Framework:
    def __init__(self, config, debug_mode=False):
        if not os.getenv("TOGETHER_API_KEY"):
            raise ValueError(
                "TOGETHER_API_KEY environment variable is not set. Please check your .env file."
            )

        self.config = config
        self.debug_mode = debug_mode
        self.child_llm = ChatTogether(
            model=config.get("models", "child"),
            temperature=config.get("models", "child_temperature"),
        )
        self.facilitator_llm = ChatTogether(
            model=config.get("models", "facilitator"),
            temperature=config.get("models", "facilitator_temperature"),
        )

        self.child_system_prompt = config.get("system_prompts", "child")
        self.facilitator_decision_system_prompt = config.get(
            "system_prompts", "facilitator_decision"
        )
        self.facilitator_positive_reinforcement_system_prompt = config.get(
            "system_prompts", "facilitator_positive_reinforcement"
        )
        self.facilitator_help_system_prompt = config.get(
            "system_prompts", "facilitator_help"
        )
        self.facilitator_end_coaching_system_prompt = config.get(
            "system_prompts", "facilitator_end_coaching"
        )
        self.facilitator_summary_system_prompt = config.get(
            "system_prompts", "facilitator_summary"
        )

        self.child_pipeline = (
            ChatPromptTemplate.from_messages(
                [SystemMessagePromptTemplate.from_template(self.child_system_prompt)]
            ).partial(
                scenario_description=self.config.get("scenario", "description"),
                # scenario_objectives=self.config.get("scenario", "objectives"),
            )
            | self.child_llm
        )

        self.facilitator_decision_pipeline = (
            ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(
                        self.facilitator_decision_system_prompt
                    )
                ]
            ).partial(
                scenario_description=self.config.get("scenario", "description"),
                scenario_objectives=self.config.get("scenario", "objectives"),
                end_conversation=self.config.get("conditions", "end_conversation"),
                child_only_neutral=self.config.get("conditions", "child_only_neutral"),
                child_only_positive=self.config.get(
                    "conditions", "child_only_positive"
                ),
                child_and_facilitator_positive_reinforcement=self.config.get(
                    "conditions", "child_and_facilitator_positive_reinforcement"
                ),
                child_and_facilitator_help=self.config.get(
                    "conditions", "child_and_facilitator_help"
                ),
                facilitator_only_help=self.config.get(
                    "conditions", "facilitator_only_help"
                ),
            )
            | self.facilitator_llm
        )

        self.facilitator_positive_reinforcement_pipeline = (
            ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(
                        self.facilitator_positive_reinforcement_system_prompt
                    )
                ]
            ).partial(
                scenario_description=self.config.get("scenario", "description"),
                scenario_objectives=self.config.get("scenario", "objectives"),
            )
            | self.facilitator_llm
        )

        self.facilitator_help_pipeline = (
            ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(
                        self.facilitator_help_system_prompt
                    )
                ]
            ).partial(
                scenario_description=self.config.get("scenario", "description"),
                scenario_objectives=self.config.get("scenario", "objectives"),
            )
            | self.facilitator_llm
        )

        self.facilitator_end_coaching_pipeline = (
            ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(
                        self.facilitator_end_coaching_system_prompt
                    )
                ]
            ).partial(
                scenario_description=self.config.get("scenario", "description"),
                scenario_objectives=self.config.get("scenario", "objectives"),
            )
            | self.facilitator_llm
        )

        self.facilitator_summary_pipeline = (
            ChatPromptTemplate.from_messages(
                [
                    SystemMessagePromptTemplate.from_template(
                        self.facilitator_summary_system_prompt
                    )
                ]
            ).partial(
                scenario_description=self.config.get("scenario", "description"),
                scenario_objectives=self.config.get("scenario", "objectives"),
            )
            | self.facilitator_llm
        )

        self.conversation_trace = ConversationTracer()
        self.turn_count = 1

    def _debug_print(self, prompt_name: str, prompt_content: str):
        """Helper method to print debug information if debug mode is enabled."""
        if self.debug_mode:
            print(f"\n=== {prompt_name} ===")
            print(prompt_content)
            print("===========================\n")

    def generate_child_response(self, parent_input):
        prompt_inputs = {
            "parent_response": parent_input,
            "interaction_history": self.conversation_trace.get_pretty_conversation(),
            "scenario_description": self.config.get("scenario", "description"),
            # "scenario_objectives": self.config.get("scenario", "objectives"),
            "turn_count": self.turn_count,
        }

        if self.debug_mode:
            constructed_prompt = self.child_system_prompt.format(**prompt_inputs)
            self._debug_print("Child Response Prompt", constructed_prompt)

        child_response = self.child_pipeline.invoke(prompt_inputs)
        return child_response.content

    def log_interaction(self, parent, child, decision, decision_reasoning, coaching):
        entry = TraceEntry(parent, child, decision, decision_reasoning, coaching)
        self.conversation_trace.add_entry(entry)

    def generate_decision(self, parent_input, child_response=None) -> tuple[int, str]:
        prompt_inputs = {
            "parent_response": parent_input,
            "child_response": self.conversation_trace.get_latest_child_message(),
            "interaction_history": self.conversation_trace.get_pretty_trace_full(
                exclude_latest_child=True
            ),
            "turn_count": self.turn_count,
            "scenario_description": self.config.get("scenario", "description"),
            "scenario_objectives": self.config.get("scenario", "objectives"),
            "end_conversation": self.config.get("conditions", "end_conversation"),
            "child_only_neutral": self.config.get("conditions", "child_only_neutral"),
            "child_only_positive": self.config.get("conditions", "child_only_positive"),
            "child_and_facilitator_positive_reinforcement": self.config.get(
                "conditions", "child_and_facilitator_positive_reinforcement"
            ),
            "child_and_facilitator_help": self.config.get(
                "conditions", "child_and_facilitator_help"
            ),
            "facilitator_only_help": self.config.get(
                "conditions", "facilitator_only_help"
            ),
        }

        if self.debug_mode:
            constructed_prompt = self.facilitator_decision_system_prompt.format(
                **prompt_inputs
            )
            self._debug_print("Facilitator Decision Prompt", constructed_prompt)

        max_retries = 3
        attempts = 0

        while attempts < max_retries:
            attempts += 1

            facilitator_response = self.facilitator_decision_pipeline.invoke(
                prompt_inputs
            )

            decision = None
            feedback = ""
            decision_found = False
            reasoning_found = False

            for line in facilitator_response.content.split("\n"):
                if line.startswith("DECISION:"):
                    decision_found = True
                    try:
                        decision = int(line.split(":")[1].strip())
                    except (ValueError, IndexError):
                        if self.debug_mode:
                            print(f"Invalid decision format: {line}")
                        continue
                elif line.startswith("REASONING:"):
                    reasoning_found = True
                    feedback = line.replace("REASONING:", "", 1).strip()

            try:
                if not decision_found or decision is None:
                    raise ValueError("Decision not found in the response")
                if not reasoning_found or not feedback:
                    raise ValueError("Reasoning not found in the response")

                DecisionType(decision)

                return (decision, feedback)

            except ValueError as e:
                if self.debug_mode:
                    print(f"Validation error (attempt {attempts}/{max_retries}): {e}")

                if attempts >= max_retries:
                    valid_values = [e.value for e in DecisionType]
                    raise ValueError(
                        f"Failed to get valid decision after {max_retries} attempts. "
                        f"Valid values are: {valid_values}. Last error: {str(e)}"
                    )

                continue

    def generate_positive_coaching(
        self,
        parent_input,
        child_response=None,
        reasoning=None,
        facilitator_only_response=False,
    ):
        prompt_inputs = {
            "parent_response": parent_input,
            "child_response": self.conversation_trace.get_latest_child_message(),
            # "child_response": child_response,
            "interaction_history": self.conversation_trace.get_pretty_trace_full(
                exclude_latest_child=True
            ),
            "scenario_description": self.config.get("scenario", "description"),
            "scenario_objectives": self.config.get("scenario", "objectives"),
            "previous_coaching": self.conversation_trace.get_previous_coaching(),
            "reasoning": reasoning,
        }

        if self.debug_mode:
            constructed_prompt = (
                self.facilitator_positive_reinforcement_system_prompt.format(
                    **prompt_inputs
                )
            )
            self._debug_print(
                "Facilitator Positive Reinforcement Prompt", constructed_prompt
            )

        facilitator_coaching_feedback = (
            self.facilitator_positive_reinforcement_pipeline.invoke(prompt_inputs)
        )
        if facilitator_only_response:
            return (
                self.config.get("static_messages", "retry_message")
                + " "
                + facilitator_coaching_feedback.content
            )
        return facilitator_coaching_feedback.content

    def generate_negative_coaching(
        self, parent_input, reasoning, facilitator_only_response=False
    ):
        prompt_inputs = {
            "parent_response": parent_input,
            "child_response": self.conversation_trace.get_latest_child_message(),
            # "child_response": child_response,
            "interaction_history": self.conversation_trace.get_pretty_trace_full(
                exclude_latest_child=True
            ),
            "scenario_description": self.config.get("scenario", "description"),
            "scenario_objectives": self.config.get("scenario", "objectives"),
            "reasoning": reasoning,
        }

        if self.debug_mode:
            constructed_prompt = self.facilitator_help_system_prompt.format(
                **prompt_inputs
            )
            self._debug_print("Facilitator Help Prompt", constructed_prompt)

        facilitator_coaching_feedback = self.facilitator_help_pipeline.invoke(
            prompt_inputs
        )
        if facilitator_only_response:
            return (
                self.config.get("static_messages", "retry_message")
                + " "
                + facilitator_coaching_feedback.content
            )
        return facilitator_coaching_feedback.content

    def generate_end_coaching(self, parent_input, reasoning):
        """Generate coaching feedback when the conversation is ending."""
        prompt_inputs = {
            "parent_response": parent_input,
            "child_response": self.conversation_trace.get_latest_child_message(),
            "interaction_history": self.conversation_trace.get_pretty_trace_full(
                exclude_latest_child=True
            ),
            "scenario_description": self.config.get("scenario", "description"),
            "scenario_objectives": self.config.get("scenario", "objectives"),
            "previous_coaching": self.conversation_trace.get_previous_coaching(),
            "reasoning": reasoning,
        }

        if self.debug_mode:
            constructed_prompt = self.facilitator_end_coaching_system_prompt.format(
                **prompt_inputs
            )
            self._debug_print("Facilitator End Coaching Prompt", constructed_prompt)

        # Use the pre-defined pipeline
        facilitator_coaching_feedback = self.facilitator_end_coaching_pipeline.invoke(
            prompt_inputs
        )
        return facilitator_coaching_feedback.content

    def generate_summary(self, parent_feedback_positive, parent_feedback_negative):
        prompt_inputs = {
            "interaction_history": self.conversation_trace.get_pretty_trace_full(),
            "scenario_description": self.config.get("scenario", "description"),
            "scenario_objectives": self.config.get("scenario", "objectives"),
            "parent_feedback_positive": parent_feedback_positive,
            "parent_feedback_negative": parent_feedback_negative,
        }

        if self.debug_mode:
            constructed_prompt = self.facilitator_summary_system_prompt.format(
                **prompt_inputs
            )
            self._debug_print("Facilitator Summary Prompt", constructed_prompt)

        facilitator_summary = self.facilitator_summary_pipeline.invoke(prompt_inputs)
        return facilitator_summary.content
