"""
langchain schemas for defining state and response format.
"""
from langgraph.graph import  MessagesState

from pydantic import BaseModel, Field
from typing import List
from pydantic import BaseModel

class Turn(BaseModel):
    start: float = Field(..., description="Start time of the turn in seconds")
    end: float = Field(..., description="End time of the turn in seconds")
    speaker: str = Field(..., description="Speaker label or name")
    text: str = Field(..., description="Transcribed text of the turn")

class Conversation(BaseModel):
    turns: List[Turn] = Field(..., description="List of turns in the transcript")

class SummarizationState(MessagesState):
    summary: str
    topics: List[str]
    decisions: List[str]
    actions: List[str]

class ItemFormatter(BaseModel):
    """Structure of the extracted items."""
    text: str = Field(description="The key text of interest")
    start: float = Field(description="Moment when this item is mentioned")
    end: float = Field(description="Moment when it's no longer discussed")

class SummarizationResponseFormatter(BaseModel):
    """Always structure and format the response to the user."""
    summary: str = Field(description="The summary of the provided text")
    topics: List[ItemFormatter] = Field(description="The topics discussed in the text")
    decisions: List[ItemFormatter] = Field(description="The decisions taken in the text")
    actions: List[ItemFormatter] = Field(description="The action plan discussed in the text")

class GradeSummarizationFormatter(BaseModel):
    """Grade summarization using a binary score for relevance check."""

    binary_score: str = Field(
        description="Relevance score: 'yes' if relevant, or 'no' if not relevant"
    )
