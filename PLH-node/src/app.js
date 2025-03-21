import express from "express";
import ConfigHelper from "./configHelper.js";
import { getChatHistory, upsertMessage } from "./databaseHelper.js";
import Framework from "./framework.js";
import readline from "readline";
import { DECISION_TYPE } from "./decision_types.js";

const port = process.env.PORT || 3000;

const app = express();

app.use(express.json());

app.get("/", async (req, res) => {
  const configHelper = new ConfigHelper();
  const config = configHelper.getConfig();

  res.json({ model: config.models.child });
});

app.get("/scenario1", (req, res) => {
  const { lng } = req.query;
  const configHelper = new ConfigHelper(lng);
  const config = configHelper.getConfig();
  res.json({
    response: `${config.scenario.name} \n\n${config.static_messages.scenario}: ${
      config.scenario.description
    } ${
      config.scenario.conversation_initiator
        ? `\n\n${config.static_messages.child}:${config.scenario.conversation_initiator}`
        : ""
    }`,
  });
});

const stages = ["continue", "feedbackQuestion1", "feedbackQuestion2", "finish"];

app.post("/chat", async (req, res) => {
  if (!req.headers["x-api-key"] || req.headers["x-api-key"] !== process.env["API_KEY"]) {
    return res.status(403).json({ error: "Forbidden: Invalid API Key" });
  }

  let { message, chat_id, lng } = req.body;

  const configHelper = new ConfigHelper(lng);
  const config = configHelper.getConfig();

  const chatHistory = await getChatHistory(chat_id);

  const previousCoaching = chatHistory
    .filter((interaction) => interaction.coachingFeedback)
    .map((interaction) => interaction.coachingFeedback)
    .join("\n\n");

  let latestSavedChildResponse = "";

  let interactionHistoryWithoutLastChildResponse = chatHistory.map((interaction, index) => {
    let string = "";
    if (interaction.parentMessage) {
      string += `parent: ${interaction.parentMessage}\n`;
    }
    if (interaction.coachingFeedback) {
      string += `coaching: ${interaction.coachingFeedback}\n`;
    }
    if (interaction.childMessage) {
      // removes last childresponse from interactionHistory
      if (index === chatHistory.length - 1) {
        latestSavedChildResponse = interaction.childMessage;
      } else {
        string += `child: ${interaction.childMessage}\n`;
      }
    }
    if (interaction.decision) {
      string += `decision: ${interaction.decision}\n`;
    }
    if (interaction.decisionReasoning) {
      string += `decision_reasoning: ${interaction.decisionReasoning}`;
    }
    return string;
  });

  let interactionHistory = chatHistory.map((interaction, index) => {
    let string = "";
    if (interaction.parentMessage) {
      string += `parent: ${interaction.parentMessage}\n  `;
    }
    if (interaction.coachingFeedback) {
      string += `coaching: ${interaction.coachingFeedback}\n  `;
    }
    if (interaction.childMessage) {
      string += `child: ${interaction.childMessage}\n  `;
    }
    if (interaction.decision) {
      string += `decision: ${interaction.decision}\n  `;
    }
    if (interaction.decisionReasoning) {
      string += `decision_reasoning: ${interaction.decisionReasoning}`;
    }
    return string;
  });

  if (config.scenario.conversation_initiator) {
    interactionHistory.unshift(`\n\nchild:${config.scenario.conversation_initiator}`);
  }
  interactionHistory = interactionHistory.join("\n\n");

  let parentChildHistory = chatHistory.map((interaction) => {
    return `parent: ${interaction.parentMessage}\n child: ${interaction.childMessage}\n`;
  });
  if (config.scenario.conversation_initiator) {
    parentChildHistory.unshift(`\n\nchild:${config.scenario.conversation_initiator}`);
  }
  parentChildHistory = parentChildHistory.join("\n\n");

  const turnCount = chatHistory.length + 1;

  try {
    const framework = new Framework(lng);
    let result = {};
    if (chatHistory[chatHistory.length - 1]?.stage === stages[2]) {
      result = {
        message: config.static_messages.negative_question,
        positiveFeedback: message,
        endScenario: false,
        stage: stages[3],
      };
    } else if (chatHistory[chatHistory.length - 1]?.stage === stages[3]) {
      const summary = await framework.getConversationSummary(
        interactionHistory,
        chatHistory[chatHistory.length - 1].positiveFeedback,
        message
      );
      result = {
        summary,
        endScenario: false,
        negativeFeedback: message,
        stage: stages[3],
      };
    } else {
      result = await runConversation(
        framework,
        message,
        interactionHistoryWithoutLastChildResponse,
        turnCount,
        parentChildHistory,
        latestSavedChildResponse,
        previousCoaching
      );
    }

    if (result.stage === stages[1]) {
      result = {
        ...result,
        message: config.static_messages.positive_question,
        endScenario: false,
        stage: stages[2],
      };
    }

    const coachingFeedback = result.coachingFeedback
      ? `🔵 ${config.static_messages.facilitator}: ${result.coachingFeedback}`
      : "";
    const childMessage = result.childMessage
      ? `🟢 ${config.static_messages.child}: ${result.childMessage}`
      : "";
    const summary = result.summary ? `${config.static_messages.summary}: ${result.summary}` : "";
    const otherMessage = result.message ? `${result.message}` : "";

    if (result.blockedMessage) {
      return res.json({
        response: {
          coachingFeedback,
          childMessage: "",
          summary: "",
          message: "",
          endScenario: false,
        },
      });
    }

    await upsertMessage({ ...result, chat_id });
    console.log(
      "end================================================================================================================================="
    );
    res.json({
      response: {
        coachingFeedback: coachingFeedback || "",
        childMessage: childMessage || "",
        summary: summary || "",
        message: otherMessage || "",
        endScenario: !!result.summary,
      },
    });
  } catch (error) {
    console.error("Error initializing framework:", error);
    return res.status(500).json({ error: "Internal Server Error" });
  }
});

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`);
});

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

async function runConversation(
  framework,
  parentInput,
  interactionHistory,
  turnCount,
  parentChildHistory,
  latestSavedChildResponse,
  previousCoaching
) {
  let stage = stages[0];

  const { decision, reasoning } = await framework.getDecision(
    parentInput,
    latestSavedChildResponse,
    interactionHistory,
    turnCount
  );

  let coachingFeedback = undefined;
  let blockedMessage = false;
  let newChildResponse = "";
  switch (decision) {
    case DECISION_TYPE.CHILD_ONLY_NEUTRAL:
      newChildResponse = await framework.getChildResponse(
        parentInput,
        parentChildHistory,
        turnCount
      );
      break;
    case DECISION_TYPE.CHILD_ONLY_POSITIVE:
      newChildResponse = await framework.getChildResponse(
        parentInput,
        parentChildHistory,
        turnCount
      );
      break;
    case DECISION_TYPE.CHILD_AND_FACILITATOR_POSITIVE_REINFORCEMENT:
      newChildResponse = await framework.getChildResponse(
        parentInput,
        parentChildHistory,
        turnCount
      );
      coachingFeedback = await framework.getPositiveCoachingFeedback(
        parentInput,
        latestSavedChildResponse,
        interactionHistory,
        previousCoaching,
        reasoning
      );
      break;
    case DECISION_TYPE.CHILD_AND_FACILITATOR_HELP:
      newChildResponse = await framework.getChildResponse(
        parentInput,
        parentChildHistory,
        turnCount
      );
      coachingFeedback = await framework.getPositiveCoachingFeedback(
        parentInput,
        latestSavedChildResponse,
        interactionHistory,
        previousCoaching,
        reasoning
      );
      break;
    case DECISION_TYPE.FACILITATOR_ONLY_HELP: //re-try
      coachingFeedback = await framework.getNegativeCoachingFeedback(
        parentInput,
        latestSavedChildResponse,
        interactionHistory,
        reasoning,
        true
      );
      blockedMessage = true;
      break;
    case DECISION_TYPE.END_CONVERSATION:
      coachingFeedback = await framework.getEndCoachingFeedback(
        parentInput,
        latestSavedChildResponse,
        interactionHistory,
        previousCoaching,
        reasoning
      );
      stage = stages[1];
      break;
  }
  return {
    parentMessage: parentInput,
    childMessage: newChildResponse,
    decision,
    decisionReasoning: reasoning,
    coachingFeedback,
    blockedMessage,
    stage,
  };
}
