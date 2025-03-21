# Parenting Simulation Chatbot

This project is a Python-based parenting simulation chatbot that uses the Rich library for terminal formatting and LangChain with Together.ai for interfacing with language models.

## Features

- Interactive conversation with a simulated child
- Decision-making and coaching feedback
- Conversation trace export to YAML and CSV formats
- Annotation-ready CSV export for expert scoring

## Commands

During a conversation, you can use the following special commands:

- `trace` - Display the current conversation trace
- `save` - Save the conversation trace to a YAML file
- `export` - Export the conversation trace to a CSV file for annotation
- `exit` - End the conversation

## Decision Types

The chatbot uses the following decision types to determine the flow of conversation:

- **0 - CHILD_ONLY_NEUTRAL**: Continue conversation normally with a neutral child response
- **1 - CHILD_ONLY_POSITIVE**: Continue conversation with a positive child response
- **2 - CHILD_AND_FACILITATOR_POSITIVE_REINFORCEMENT**: Provide positive reinforcement coaching along with the child response
- **3 - CHILD_AND_FACILITATOR_HELP**: Provide helpful coaching along with the child response
- **4 - FACILITATOR_ONLY_HELP**: Block inappropriate responses and provide coaching for improvement
- **5 - END_CONVERSATION**: End the conversation when objectives are achieved

## CSV Export Format

The CSV export is designed for annotation and includes the following columns:

- **Turn**: The turn number in the conversation
- **Interaction**: The type of interaction (Child, Parent, Decision, Reasoning, Facilitator, Parent Reflection, Summary)
- **Text**: The content of the interaction
- **Expert Score 1 (1-5)**: Column for the first expert to provide a score
- **Comment 1**: Column for the first expert to provide comments
- **Expert Score 2 (1-5)**: Column for the second expert to provide a score
- **Comment 2**: Column for the second expert to provide comments

The CSV export includes:
- The full conversation trace with all turns
- Decision codes (0-5) with their corresponding names
- Reasoning for each decision
- Coaching feedback when provided
- Parent reflections (positive and negative) at the end of the conversation
- A summary of the conversation

The CSV file will be saved in the `csv` directory with a timestamp in the filename.

## Prerequisites

- Python 3.7 or above installed on your system.
- (Optional) Git, if you want to clone the repository.

## Setup Instructions

### 1. Cloning the Repository

If you haven't already, clone the repository:

```
git clone <repository_url>
cd <repository_directory>
```

### 2. Creating a Virtual Environment

It is highly recommended to run the project in a virtual environment to avoid dependency conflicts.

**On Windows:**

```
python -m venv venv
venv\Scripts\activate
```

**On macOS/Linux:**

```
python3 -m venv venv
source venv/bin/activate
```

### 3. Installing Dependencies

Install the required packages with:

```
pip install -r requirements.txt
```

### 4. Configuration

The project expects a configuration file named `config.yaml` in the same directory as `config.py`. The configuration is structured into the following sections:

#### Models Configuration
- `child`: Specify the language model to use for generating child responses
- `child_temperature`: Set the creativity level for child responses (higher values = more creative/variable responses)
- `facilitator`: Specify the language model for coaching and decision-making
- `facilitator_temperature`: Set the consistency level for facilitator responses (lower values = more consistent/focused responses)

#### Static Messages Configuration
- `retry_message`: Message to display when asking parent to try again
- `facilitator`: Label for the facilitator in the conversation
- `child`: Label for the child in the conversation
- `summary`: Label for conversation summary
- `scenario`: Label for scenario description
- `positive_question`: Question asking what went well
- `negative_question`: Question asking what could be improved

#### Scenario Configuration
- `name`: A descriptive name for the parenting scenario
- `description`: Brief context about the current situation
- `objectives`: List of specific parenting skills or goals to practice in this scenario
- `conversation_initiator`: The opening message from the child that starts the conversation

#### Conditions Configuration
Defines the rules for conversation flow:
- `child_only_neutral`: When to continue with neutral child response
- `child_only_positive`: When to continue with positive child response
- `child_and_facilitator_positive_reinforcement`: When to provide positive reinforcement with child response
- `child_and_facilitator_help`: When to provide helpful coaching with child response
- `facilitator_only_help`: When to block inappropriate responses
- `end_conversation`: Conditions for successfully completing the scenario

#### System Prompts
Define the behavior and personality for each AI role:
- `child`: Instructions for generating child responses
- `facilitator_decision`: Rules for determining conversation flow
- `facilitator_positive_reinforcement`: Guidelines for providing positive reinforcement
- `facilitator_help`: Guidelines for providing constructive coaching
- `facilitator_end_coaching`: Rules for ending the conversation
- `facilitator_summary`: Format for session summaries

Placeholders in the .yaml file wrapped in {} (e.g., {interaction_history}) will be replaced with dynamic values.

**Note:** When creating your own scenario, focus on defining clear objectives and appropriate responses that align with your parenting goals.

### 5. Environment Variables

Create a `.env` file in the root directory with your environment variables:

```
TOGETHER_API_KEY=your_api_key_here
```

Required environment variables:
- `TOGETHER_API_KEY`: Your Together API key for accessing the language models

**Note:** Never commit your `.env` file to version control. The repository includes a `.gitignore` file that excludes it.

### 6. Running the Application

To run the parenting simulation, execute the following command in your terminal:

```
python -m src.main
```

By default, the application uses the configuration file at `config/config.yaml`. To use a different configuration file, use the `--config` or `-c` flag:

```
python -m src.main --config path/to/your/config.yaml
```

To run in debug mode, which will print all input prompts being sent to the language models, use the `--debug` or `-d` flag:

```
python -m src.main --debug
```

You can combine both flags:

```
python -m src.main --config path/to/your/config.yaml --debug
```

This allows you to maintain multiple configuration files for different scenarios or testing purposes, and inspect the exact prompts being sent to the models when needed.

Special commands:
  - `trace` to view the conversation trace.
  - `save` to save the conversation trace.
  - `exit` to quit the simulation.

### 7. Exiting the Virtual Environment

Once you're done, you can exit the virtual environment with:

- On Windows: `venv\Scripts\deactivate.bat`
- On macOS/Linux: `deactivate`

## Project Structure

The repository is organized as follows:

    ├── config
    │   └── config.yaml
    ├── src
    │   ├── main.py
    │   ├── config.py
    │   ├── decision_types.py
    │   ├── formatter.py
    │   ├── conversation_tracer.py
    │   ├── framework.py
    │   └── trace_csv_exporter.py
    ├── traces
    ├── csv
    ├── requirements.txt
    └── README.md

## Troubleshooting

- **Dependency Issues:** Ensure your virtual environment is activated and all dependencies from requirements.txt are installed.
- **Python Version:** Make sure you are running Python 3.7 or above.

## License

This project is open source and available under the MIT License.

## Annotation Process

1. Run a conversation with the simulated child
2. Complete the conversation to generate a CSV file
3. Open the CSV file in Excel or another spreadsheet program
4. Experts can fill in the score and comment columns
5. Save the annotated CSV file for analysis