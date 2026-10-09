from pydantic import BaseModel, ConfigDict, Field


class Message(BaseModel):
    model_config = ConfigDict(strict=True)
    content: str = Field(max_length=8192)


class Choice(BaseModel):
    model_config = ConfigDict(strict=True)
    message: Message
    finish_reason: str


class Completion(BaseModel):
    model_config = ConfigDict(strict=True)
    choices: list[Choice] = Field(min_length=1, max_length=1)
