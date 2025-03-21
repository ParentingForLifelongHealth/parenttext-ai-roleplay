import ConfigHelper from "./configHelper.js";
import { ChatTogetherAI } from "@langchain/community/chat_models/togetherai";
import { SystemMessagePromptTemplate, ChatPromptTemplate } from "@langchain/core/prompts";

/**
 * Framework class handling the chat interactions between child and tutor models
 */
class Framework {
  constructor(lng) {
    const configHelper = new ConfigHelper(lng);
    this.config = configHelper.getConfig();
    this.#initializeModels();
    this.#initializePipelines();
  }

  /**
   * -----------------------------------------------------------------------------
   * MODEL INITIALIZATION
   * -----------------------------------------------------------------------------
   */

  #initializeModels() {
    this.#initializeChildModel();
    this.#initializeTutorModel();
  }

  #initializeChildModel() {
    this.childLLM = new ChatTogetherAI({
      model: this.config.models.child,
      temperature: this.config.models.child_temperature,
      apiKey: process.env.TOGETHER_AI_API_KEY,
    });
  }

  #initializeTutorModel() {
    this.tutorLLM = new ChatTogetherAI({
      model: this.config.models.facilitator,
      temperature: this.config.models.facilitator_temperature,
      apiKey: process.env.TOGETHER_AI_API_KEY,
    });
  }

  /**
   * -----------------------------------------------------------------------------
   * PIPELINE INITIALIZATION
   * -----------------------------------------------------------------------------
   */

  #initializePipelines() {
    this.#initializeChildPipeline();
    this.#initializeFacilitatorDecisionPipeline();
    this.#initializeFacilitatorPositiveReinforcementPipeline();
    this.#initializeHelpPipeline();
    this.#initializeFacilitatorEndCoachingPipeline();
    this.#initializeTutorSummaryPipeline();
  }

  #initializeChildPipeline() {
    this.childSystemMessage = SystemMessagePromptTemplate.fromTemplate(
      this.config.system_prompts.child,
      ["scenario_description"]
    );

    this.childPipeline = ChatPromptTemplate.fromMessages([this.childSystemMessage]).pipe(
      this.childLLM
    );
  }

  #initializeFacilitatorDecisionPipeline() {
    this.tutorDecisionMessage = SystemMessagePromptTemplate.fromTemplate(
      this.config.system_prompts.facilitator_decision,
      [
        "scenario_description",
        "scenario_objectives",
        "end_conversation",
        "child_only_neutral",
        "child_only_positive",
        "child_and_facilitator_positive_reinforcement",
        "child_and_facilitator_help",
        "facilitator_only_help",
      ]
    );

    this.tutorDecisionPipeline = ChatPromptTemplate.fromMessages([this.tutorDecisionMessage]).pipe(
      this.tutorLLM
    );
  }

  #initializeFacilitatorPositiveReinforcementPipeline() {
    this.tutorCoachMessage = SystemMessagePromptTemplate.fromTemplate(
      this.config.system_prompts.facilitator_positive_reinforcement,
      ["scenario_description", "scenario_objectives"]
    );

    this.tutorCoachPipeline = ChatPromptTemplate.fromMessages([this.tutorCoachMessage]).pipe(
      this.tutorLLM
    );
  }

  #initializeHelpPipeline() {
    this.tutorCoachMessage = SystemMessagePromptTemplate.fromTemplate(
      this.config.system_prompts.facilitator_help,
      ["scenario_description", "scenario_objectives"]
    );

    this.facilitatorHelpPipeline = ChatPromptTemplate.fromMessages([this.tutorCoachMessage]).pipe(
      this.tutorLLM
    );
  }

  #initializeFacilitatorEndCoachingPipeline() {
    this.tutorCoachMessage = SystemMessagePromptTemplate.fromTemplate(
      this.config.system_prompts.facilitator_end_coaching,
      ["scenario_description", "scenario_objectives"]
    );

    this.facilitatorEndCoachingPipeline = ChatPromptTemplate.fromMessages([
      this.tutorCoachMessage,
    ]).pipe(this.tutorLLM);
  }

  #initializeTutorSummaryPipeline() {
    this.tutorSummaryMessage = SystemMessagePromptTemplate.fromTemplate(
      this.config.system_prompts.facilitator_summary,
      ["scenario_description", "scenario_objectives", "interaction_history"]
    );

    this.tutorSummaryPipeline = ChatPromptTemplate.fromMessages([this.tutorSummaryMessage]).pipe(
      this.tutorLLM
    );
  }

  /**
   * -----------------------------------------------------------------------------
   * CHILD MODEL INTERACTION
   * -----------------------------------------------------------------------------
   */

  /**
   * Prepare variables for child response prompt
   * @param {string} parentInput - Parent's input message
   * @param {string} interactionHistory - Previous conversation history
   * @returns {Object} Variables object for prompt template
   */
  #prepareChildVariables(parentInput, interactionHistory, turnCount) {
    return {
      parent_response: parentInput,
      scenario_description: this.config.scenario.description,
      interaction_history: interactionHistory,
      turn_count: turnCount,
      //scenario_objectives: scenario.objectives,
    };
  }

  /**
   * Get response from child model based on parent input and interaction history
   * @param {string} parentInput - Parent's input message
   * @param {string} interactionHistory - Previous conversation history
   * @returns {string} Child's response
   */
  async getChildResponse(parentInput, interactionHistory, turnCount) {
    const variables = this.#prepareChildVariables(parentInput, interactionHistory, turnCount);

    // Debug: Format the prompt to see what will be sent to the LLM
    // const formattedMessage = await this.childSystemMessage.format(variables);
    // console.log("Formatted child prompt content:", formattedMessage.content);
    console.log("----------------getChildResponse:---------------- :", variables);
    const response = await this.childPipeline.invoke(variables);
    return response.content;
  }

  /**
   * -----------------------------------------------------------------------------
   * TUTOR MODEL INTERACTIONS
   * -----------------------------------------------------------------------------
   */

  /**
   * Prepare variables for tutor decision prompt
   * @param {string} parentInput - Parent's input message
   * @param {string} childResponse - Child's response message
   * @param {string} interactionHistory - Previous conversation history
   * @param {number} turnCount - Current turn count
   * @returns {Object} Variables object for prompt template
   */
  #prepareTutorDecisionVariables(
    parentInput,
    childResponse,
    interactionHistory = "",
    turnCount = 1
  ) {
    return {
      parent_response: parentInput,
      child_response: childResponse,
      interaction_history: interactionHistory,
      turn_count: turnCount,
      scenario_description: this.config.scenario.description,
      scenario_objectives: this.config.scenario.objectives,
      end_conversation: this.config.conditions.end_conversation,
      child_only_neutral: this.config.conditions.child_only_neutral,
      child_only_positive: this.config.conditions.child_only_positive,
      child_and_facilitator_positive_reinforcement:
        this.config.conditions.child_and_facilitator_positive_reinforcement,
      child_and_facilitator_help: this.config.conditions.child_and_facilitator_help,
      facilitator_only_help: this.config.conditions.facilitator_only_help,
    };
  }

  /**
   * Get decision from tutor model based on parent and child interaction
   * @param {string} parentInput - Parent's input message
   * @param {string} childResponse - Child's response message
   * @param {string} interactionHistory - Previous conversation history
   * @param {number} turnCount - Current turn count
   * @returns {Object} Decision object with decision code and reasoning
   */
  async getDecision(parentInput, childResponse, interactionHistory, turnCount) {
    const variables = this.#prepareTutorDecisionVariables(
      parentInput,
      childResponse,
      interactionHistory,
      turnCount
    );

    // Debug: Format the prompt to see what will be sent to the LLM
    // const formattedMessage = await this.tutorDecisionMessage.format(variables);
    // console.log("Formatted decision prompt:", formattedMessage.content);
    console.log("----------------getDecision:---------------- :", variables);
    const response = await this.tutorDecisionPipeline.invoke(variables);

    return this.#parseDecisionResponse(response.content);
  }

  /**
   * Parse the decision response from the tutor model
   * @param {string} responseContent - Raw response content from model
   * @returns {Object} Parsed decision with decision code and reasoning
   * @throws {Error} If decision code is invalid
   */
  #parseDecisionResponse(responseContent) {
    let decision = null;
    let reasoning = "";

    // Extract decision and reasoning from response
    const lines = responseContent.split("\n");
    for (const line of lines) {
      if (line.startsWith("DECISION:")) {
        decision = parseInt(line.split(":")[1].trim());
      } else if (line.startsWith("REASONING:")) {
        reasoning = line.split(":")[1].trim();
      }
    }

    if (![0, 1, 2, 3, 4, 5].includes(decision)) {
      throw new Error(`Invalid decision value: ${decision}`);
    }

    return {
      decision,
      reasoning,
      raw: responseContent,
    };
  }

  /**
   * Prepare variables for tutor coaching prompt
   * @param {string} parentInput - Parent's input message
   * @param {string} childResponse - Child's response message
   * @param {string} interactionHistory - Previous conversation history
   * @returns {Object} Variables object for prompt template
   */
  #preparePositiveCoachVariables(
    parentInput,
    childResponse,
    interactionHistory = "",
    previousCoaching,
    reasoning
  ) {
    return {
      parent_response: parentInput,
      child_response: childResponse,
      interaction_history: interactionHistory,
      scenario_description: this.config.scenario.description,
      scenario_objectives: this.config.scenario.objectives,
      previous_coaching: previousCoaching,
      reasoning: reasoning,
    };
  }

  /**
   * Get coaching feedback from tutor model
   * @param {string} parentInput - Parent's input message
   * @param {string} childResponse - Child's response message
   * @param {string} interactionHistory - Previous conversation history
   * @returns {string} Coaching feedback
   */
  async getPositiveCoachingFeedback(
    parentInput,
    childResponse,
    interactionHistory,
    previousCoaching,
    reasoning,
    tutorOnlyResponse = false
  ) {
    if (!this.tutorCoachPipeline) {
      return "";
    }

    const variables = this.#preparePositiveCoachVariables(
      parentInput,
      childResponse,
      interactionHistory,
      previousCoaching,
      reasoning
    );
    console.log("----------------getPositiveCoachingFeedback:---------------- :", variables);
    const response = await this.tutorCoachPipeline.invoke(variables);
    if (tutorOnlyResponse) {
      return response.content + ` ${this.config.static_messages.retry_message}`;
    }
    return response.content;
  }

  /**
   * Prepare variables for tutor coaching prompt
   * @param {string} parentInput - Parent's input message
   * @param {string} childResponse - Child's response message
   * @param {string} interactionHistory - Previous conversation history
   * @param {string} reasoning - Previous reasoning history
   * @returns {Object} Variables object for prompt template
   */
  #prepareNegativeCoachVariables(parentInput, childResponse, interactionHistory = "", reasoning) {
    return {
      parent_response: parentInput,
      child_response: childResponse,
      interaction_history: interactionHistory,
      scenario_description: this.config.scenario.description,
      scenario_objectives: this.config.scenario.objectives,
      reasoning: reasoning,
    };
  }

  /**
   * Get coaching feedback from tutor model
   * @param {string} parentInput - Parent's input message
   * @param {string} childResponse - Child's response message
   * @param {string} interactionHistory - Previous conversation history
   * @returns {string} Coaching feedback
   */
  async getNegativeCoachingFeedback(
    parentInput,
    childResponse,
    interactionHistory,
    reasoning,
    tutorOnlyResponse = false
  ) {
    if (!this.facilitatorHelpPipeline) {
      return "";
    }

    const variables = this.#prepareNegativeCoachVariables(
      parentInput,
      childResponse,
      interactionHistory,
      reasoning
    );
    console.log("----------------getNegativeCoachingFeedback:---------------- :", variables);
    const response = await this.facilitatorHelpPipeline.invoke(variables);
    if (tutorOnlyResponse) {
      return response.content + ` ${this.config.static_messages.retry_message}`;
    }
    return response.content;
  }

  /**
   * Prepare variables for tutor coaching prompt
   * @param {string} parentInput - Parent's input message
   * @param {string} childResponse - Child's response message
   * @param {string} interactionHistory - Previous conversation history
   * @param {string} reasoning - Previous reasoning history
   * @returns {Object} Variables object for prompt template
   */
  #prepareEndCoachVariables(
    parentInput,
    childResponse,
    interactionHistory = "",
    previousCoaching,
    reasoning
  ) {
    return {
      parent_response: parentInput,
      child_response: childResponse,
      interaction_history: interactionHistory,
      scenario_description: this.config.scenario.description,
      scenario_objectives: this.config.scenario.objectives,
      previous_coaching: previousCoaching,
      reasoning: reasoning,
    };
  }

  /**
   * Get coaching feedback from tutor model
   * @param {string} parentInput - Parent's input message
   * @param {string} childResponse - Child's response message
   * @param {string} interactionHistory - Previous conversation history
   * @returns {string} Coaching feedback
   */
  async getEndCoachingFeedback(
    parentInput,
    childResponse,
    interactionHistory,
    previousCoaching,
    reasoning
  ) {
    if (!this.facilitatorHelpPipeline) {
      return "";
    }

    const variables = this.#prepareEndCoachVariables(
      parentInput,
      childResponse,
      interactionHistory,
      previousCoaching,
      reasoning
    );
    console.log("----------------getEndCoachingFeedback----------------: ", variables);
    const response = await this.facilitatorEndCoachingPipeline.invoke(variables);
    return response.content;
  }

  /**
   * Get conversation summary from tutor model
   * @param {string} interactionHistory - Complete conversation history
   * @returns {string} Conversation summary
   */
  async getConversationSummary(interactionHistory, positiveFeedback, negativeFeedback) {
    if (!this.tutorSummaryPipeline) {
      return "";
    }

    const variables = {
      interaction_history: interactionHistory,
      scenario_description: this.config.scenario.description,
      scenario_objectives: this.config.scenario.objectives,
      parent_feedback_positive: positiveFeedback,
      parent_feedback_negative: negativeFeedback,
    };
    console.log("----------------getConversationSummary:---------------- :", variables);
    const response = await this.tutorSummaryPipeline.invoke(variables);
    return response.content;
  }
}

export default Framework;
