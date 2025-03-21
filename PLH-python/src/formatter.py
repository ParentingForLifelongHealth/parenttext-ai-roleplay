from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.text import Text
from rich.box import ROUNDED
from rich.align import Align
from rich.padding import Padding
from rich.rule import Rule


class ConversationStyles:
    PARENT = Style(color="green", bold=True)
    CHILD = Style(color="yellow", bold=True)
    FACILITATOR = Style(color="blue", bold=True)
    ERROR = Style(color="red", bold=True)
    HEADER = Style(color="white", bold=True)
    SYSTEM = Style(color="cyan", bold=True)


class ConversationFormatter:
    @staticmethod
    def parent(message: str, label=None) -> Panel:
        text = Text()
        label_text = f"{label}: " if label is not None else ""
        text.append(label_text, style=ConversationStyles.PARENT)
        text.append(message)
        return Panel(text, box=ROUNDED, style="green", padding=(0, 2))

    @staticmethod
    def child(message: str, label=None) -> Panel:
        text = Text()
        label_text = f"{label}: " if label is not None else ""
        text.append(label_text, style=ConversationStyles.CHILD)
        text.append(message)
        return Panel(text, box=ROUNDED, style="yellow", padding=(0, 2))

    @staticmethod
    def facilitator(message: str, label=None) -> Panel:
        """Format facilitator messages as a panel"""
        text = Text()
        label_text = f"{label}: " if label is not None else ""
        text.append(label_text, style=ConversationStyles.FACILITATOR)
        text.append(message)
        return Panel(Padding(text, (1, 0)), box=ROUNDED, style="blue", padding=(0, 2))

    @staticmethod
    def system(message: str, label=None) -> Panel:
        text = Text()
        label_text = f"{label}: " if label is not None else ""
        text.append(label_text, style=ConversationStyles.SYSTEM)
        text.append(message)
        return Panel(text, box=ROUNDED, style="cyan", padding=(0, 2))

    @staticmethod
    def error(message: str, label=None) -> Panel:
        text = Text()
        label_text = f"{label}: " if label is not None else ""
        text.append(label_text, style=ConversationStyles.ERROR)
        text.append(message)
        return Panel(text, box=ROUNDED, style="red", padding=(0, 2))

    @staticmethod
    def create_header(name: str, description: str, scenario_label=None, objectives=None) -> Panel:
        header_text = Text()
        header_text.append(f"{name}\n", style=ConversationStyles.HEADER)

        if description:
            scenario_prefix = f"\n{scenario_label}: " if scenario_label is not None else "\n"
            header_text.append(scenario_prefix, style="bold")
            header_text.append(f"{description}\n")

        if objectives:
            header_text.append("\nObjectives:\n", style="bold")
            for objective in objectives:
                header_text.append(f"• {objective}\n", style="italic")

        return Panel(
            Align.center(header_text),
            box=ROUNDED,
            style="bold white on blue",
            padding=(1, 2),
        )

    @staticmethod
    def create_summary_panel(summary: str, summary_label=None) -> Panel:
        summary_text = Text()
        label_text = f"{summary_label}\n\n" if summary_label is not None else "\n\n"
        summary_text.append(label_text, style=ConversationStyles.HEADER)
        summary_text.append(summary)
        return Panel(
            summary_text, box=ROUNDED, style="bold white on blue", padding=(1, 2)
        )

    @staticmethod
    def debug_panel(message: str) -> Panel:
        text = Text()
        text.append(message)
        return Panel(
            text,
            box=ROUNDED,
            style="magenta",
            padding=(0, 2),
            title="Debug Information"
        )


class ConversationUI:
    """Handles all UI and formatting aspects of the conversation"""
    
    def __init__(self, console: Console):
        self.console = console
        # Initialize with None rather than defaults
        self.parent_label = None
        self.child_label = None
        self.facilitator_label = None
        self.scenario_label = None
        self.summary_label = None
        
    def set_labels(self, parent=None, child=None, facilitator=None, scenario=None, summary=None):
        """Set the labels for the UI components"""
        self.parent_label = parent
        self.child_label = child
        self.facilitator_label = facilitator
        self.scenario_label = scenario
        self.summary_label = summary
        
    def display_header(self, scenario_name, scenario_description):
        """Display the conversation header"""
        self.console.print(
            ConversationFormatter.create_header(scenario_name, scenario_description, self.scenario_label)
        )
        self.console.print()
        
    def display_conversation_initiator(self, message):
        """Display the initial message from the child"""
        self.console.print(ConversationFormatter.child(message, self.child_label))
        
    def display_trace(self, trace):
        """Display the conversation trace"""
        self.console.print(ConversationFormatter.debug_panel(trace))
        
    def display_save_confirmation(self, file_path):
        """Display confirmation of saved trace"""
        self.console.print(
            ConversationFormatter.system(f"Conversation trace saved to: {file_path}")
        )
        
    def display_export_confirmation(self, file_path):
        """Display confirmation of exported CSV"""
        self.console.print(
            ConversationFormatter.system(
                f"Full unfiltered conversation trace exported to CSV: {file_path}"
            )
        )
        
    def display_system_message(self, message):
        """Display a system message"""
        self.console.print(ConversationFormatter.system(message))
        
    def display_exit_message(self):
        """Display exit message"""
        self.console.print(ConversationFormatter.error("Exiting simulation..."))
        
    def display_error_message(self, message):
        """Display an error message"""
        self.console.print(ConversationFormatter.error(message))
        
    def display_child_response(self, message):
        """Display child's response"""
        self.console.print(ConversationFormatter.child(message, self.child_label))
        
    def display_facilitator_message(self, message):
        """Display facilitator's message"""
        self.console.print(ConversationFormatter.facilitator(message, self.facilitator_label))
        self.console.print()
        
    def display_end_separator(self):
        """Display a separator at the end of conversation"""
        self.console.print(Rule(style="blue"))
        
    def display_summary_panel(self, summary):
        """Display the conversation summary"""
        self.console.print(ConversationFormatter.create_summary_panel(summary, self.summary_label))
        
    def get_parent_input(self):
        """Get input from parent"""
        prompt = Text()
        label = self.parent_label if self.parent_label is not None else ""
        prompt.append(f"{label}: ", style=ConversationStyles.PARENT)
        return self.console.input(prompt)
        
    def display_facilitator_question(self, question):
        """Display a question from the facilitator"""
        self.console.print(ConversationFormatter.facilitator(question, self.facilitator_label))
        
    def display_newline(self):
        """Display a newline for spacing"""
        self.console.print()
