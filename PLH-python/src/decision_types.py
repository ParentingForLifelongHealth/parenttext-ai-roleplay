from enum import Enum


class DecisionType(Enum):
    CHILD_ONLY_NEUTRAL = 0  # "child_only_neutral", continue
    CHILD_ONLY_POSITIVE = 1  # "child_only_positive", continue
    CHILD_AND_FACILITATOR_POSITIVE_REINFORCEMENT = 2  # "child_and_facilitator_positive_reinforcement", continue
    CHILD_AND_FACILITATOR_HELP = 3  # "child_and_facilitator_help", continue
    FACILITATOR_ONLY_HELP = 4  # "facilitator_only_help", re-try
    END_CONVERSATION = 5  # end_conversation, exit 