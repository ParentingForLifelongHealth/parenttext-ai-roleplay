from rich.console import Console
from rich.rule import Rule
from rich.text import Text
import argparse
import sys
from src.config import Config, ConfigValidationError
from src.framework import Framework
from src.formatter import ConversationFormatter, ConversationStyles, ConversationUI
from src.trace_csv_exporter import TraceExporter
from src.decision_types import DecisionType
import traceback

console = Console()


def log_conversation_interaction(
    framework, parent_input, child_response, decision, decision_reasoning, coaching
):
    """Log the interaction between parent and child with additional context"""
    framework.log_interaction(
        parent=parent_input,
        child=child_response,
        decision=decision,
        decision_reasoning=decision_reasoning,
        coaching=coaching,
    )


def run_conversation(framework, console: Console) -> None:
    """Run the parenting simulation conversation loop"""
    config = framework.config
    ui = ConversationUI(console)

    # Get static messages from config - no defaults
    scenario_label = config.get("static_messages", "scenario")
    facilitator_label = config.get("static_messages", "facilitator")
    child_label = config.get("static_messages", "child")
    summary_label = config.get("static_messages", "summary")
    retry_message = config.get("static_messages", "retry_message")
    positive_question = config.get("static_messages", "positive_question")
    negative_question = config.get("static_messages", "negative_question")

    # Set the UI labels - we won't set a parent label as it's not in the config
    ui.set_labels(
        parent="Parent",
        facilitator=facilitator_label,
        child=child_label,
        scenario=scenario_label,
        summary=summary_label,
    )

    ui.display_header(
        config.get("scenario", "name"), config.get("scenario", "description")
    )

    if config.get("scenario", "conversation_initiator"):
        ui.display_conversation_initiator(
            config.get("scenario", "conversation_initiator")
        )
        framework.conversation_trace.add_conversation_initiator(
            config.get("scenario", "conversation_initiator")
        )

    while True:
        parent_input = ui.get_parent_input()

        # Handle special commands
        if parent_input.lower() == "trace":
            ui.display_trace(framework.conversation_trace.get_pretty_trace_full())
            continue

        elif parent_input.lower() == "save":
            trace_file = framework.conversation_trace.save_trace("full")
            ui.display_save_confirmation(trace_file)
            continue

        elif parent_input.lower() == "export":
            exporter = TraceExporter(framework.conversation_trace)
            csv_file = exporter.export_to_csv()
            ui.display_export_confirmation(csv_file)
            continue

        elif parent_input.lower() == "exit":
            ui.display_exit_message()
            break

        # ----- Core conversation logic -----
        decision, decision_reasoning = framework.generate_decision(parent_input)
        coaching = None
        child_response = None

        ui.display_newline()

        # TODO: Duplicate stuff here
        match decision:
            case DecisionType.CHILD_ONLY_NEUTRAL.value:
                child_response = framework.generate_child_response(parent_input)
                ui.display_child_response(child_response)

            case DecisionType.CHILD_ONLY_POSITIVE.value:
                child_response = framework.generate_child_response(parent_input)
                ui.display_child_response(child_response)

            case DecisionType.CHILD_AND_FACILITATOR_POSITIVE_REINFORCEMENT.value:
                child_response = framework.generate_child_response(parent_input)
                coaching = framework.generate_positive_coaching(
                    parent_input, child_response, decision_reasoning
                )
                ui.display_facilitator_message(coaching)
                ui.display_child_response(child_response)

            case DecisionType.CHILD_AND_FACILITATOR_HELP.value:
                child_response = framework.generate_child_response(parent_input)
                coaching = framework.generate_positive_coaching(
                    parent_input, child_response, decision_reasoning
                )
                ui.display_facilitator_message(coaching)
                ui.display_child_response(child_response)

            case DecisionType.FACILITATOR_ONLY_HELP.value:
                coaching = framework.generate_negative_coaching(
                    parent_input, decision_reasoning, facilitator_only_response=True
                )
                # Only prepend the retry message if it's not already in the response
                if retry_message and not coaching.lower().startswith(
                    retry_message.lower()
                ):
                    coaching = f"{retry_message}\n\n{coaching}"
                ui.display_facilitator_message(coaching)

            case DecisionType.END_CONVERSATION.value:
                # Generate end coaching before breaking the loop
                end_coaching = framework.generate_end_coaching(
                    parent_input, decision_reasoning
                )
                # Update the coaching variable to include it in the log
                coaching = end_coaching
                ui.display_facilitator_message(end_coaching)
                # Log interaction here with the end_coaching included
                log_conversation_interaction(
                    framework,
                    parent_input,
                    child_response,
                    decision,
                    decision_reasoning,
                    coaching,
                )
                break

        ui.display_newline()

        # Only increment turn count if the message was not blocked
        if decision != DecisionType.FACILITATOR_ONLY_HELP.value:
            framework.turn_count += 1

        log_conversation_interaction(
            framework,
            parent_input,
            child_response,
            decision,
            decision_reasoning,
            coaching,
        )

    ui.display_end_separator()

    # Post-conversation feedback
    ui.display_facilitator_question(positive_question)
    parent_feedback_positive = ui.get_parent_input()

    ui.display_facilitator_question(negative_question)
    parent_feedback_negative = ui.get_parent_input()

    # Store parent feedback in the conversation trace
    framework.conversation_trace.set_parent_feedback(
        parent_feedback_positive, parent_feedback_negative
    )

    # Generate and display summary
    summary = framework.generate_summary(
        parent_feedback_positive, parent_feedback_negative
    )
    framework.conversation_trace.set_summary(summary)
    ui.display_summary_panel(summary)

    # Export the trace to both YAML and CSV formats
    trace_file = framework.conversation_trace.save_trace("full")
    ui.display_save_confirmation(trace_file)

    exporter = TraceExporter(framework.conversation_trace)
    csv_file = exporter.export_to_csv()
    ui.display_export_confirmation(csv_file)


def main() -> None:
    """Run the parenting simulation"""
    parser = argparse.ArgumentParser(
        description="Run the parenting simulation with a specified config file."
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        help="Path to the config YAML file. Defaults to config/config.yaml",
        default=None,
    )
    parser.add_argument(
        "--debug",
        "-d",
        action="store_true",
        help="Enable debug mode to print all prompts",
        default=False,
    )

    args = parser.parse_args()
    ui = ConversationUI(console)

    try:
        if args.config:
            ui.display_system_message(f"Loading config from: {args.config}")
        else:
            ui.display_system_message("No config file provided, using default config")
        config = Config(config_path=args.config)
        framework = Framework(config=config, debug_mode=args.debug)
        run_conversation(framework, console)
    except FileNotFoundError as e:
        ui.display_error_message(str(e))
        sys.exit(1)
    except ConfigValidationError as e:
        ui.display_error_message("Configuration Error:")
        ui.display_error_message(str(e))
        sys.exit(1)
    except Exception as e:
        error_text = f"Unexpected error occurred: {str(e)}\n\n"
        error_text += "Please check your configuration and try again.\n\n"
        error_text += f"Technical details:\n{traceback.format_exc()}"
        ui.display_error_message(error_text)
        sys.exit(1)


if __name__ == "__main__":
    main()
