from langchain.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from pydantic import BaseModel
from langchain.chains import ConversationChain
from langchain.chat_models import ChatOpenAI, AzureChatOpenAI
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationTokenBufferMemory,
)
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import AsyncCallbackManager, AsyncCallbackHandler
from dotenv import load_dotenv
from starlette.types import Send
from typing import Any, Optional, Awaitable, Callable, Iterator, Union
from fastapi.responses import StreamingResponse

load_dotenv()

Sender = Callable[[Union[str, bytes]], Awaitable[None]]


class EmptyIterator(Iterator[Union[str, bytes]]):
    def __iter__(self):
        return self

    def __next__(self):
        raise StopIteration


class AsyncStreamCallbackHandler(AsyncCallbackHandler):
    """Callback handler for streaming, inheritance from AsyncCallbackHandler."""

    def __init__(self, send: Sender):
        super().__init__()
        self.send = send

    async def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Rewrite on_llm_new_token to send token to client."""
        print(repr(token), len(token))
        await self.send(f"data: {repr(token)}\n\n")


class ChatOpenAIStreamingResponse(StreamingResponse):
    """Streaming response for openai chat model, inheritance from StreamingResponse."""

    def __init__(
        self,
        generate: Callable[[Sender], Awaitable[None]],
        status_code: int = 200,
        media_type: Optional[str] = None,
    ) -> None:
        super().__init__(
            content=EmptyIterator(), status_code=status_code, media_type=media_type
        )
        self.generate = generate

    async def stream_response(self, send: Send) -> None:
        """Rewrite stream_response to send response to client."""
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )

        async def send_chunk(chunk: Union[str, bytes]):
            if not isinstance(chunk, bytes):
                chunk = chunk.encode(self.charset)
            print(chunk, len(chunk))
            await send({"type": "http.response.body", "body": chunk, "more_body": True})

        # send body to client
        await self.generate(send_chunk)

        # send empty body to client to close connection
        await send({"type": "http.response.body", "body": b"", "more_body": False})


def send_message(message: str) -> Callable[[Sender], Awaitable[None]]:
    async def generate(send: Sender):
        # model = AzureChatOpenAI(
        #     deployment_name="gpt35",
        #     openai_api_version="2023-03-15-preview",
        #     streaming=True,
        #     verbose=True,
        #     callback_manager=AsyncCallbackManager([AsyncStreamCallbackHandler(send)]),
        # )
        # await model.agenerate(messages=[[HumanMessage(content=message)]])
        prompt = ChatPromptTemplate.from_messages(
            [
                SystemMessagePromptTemplate.from_template(
                    "The following is a friendly conversation between a human and an AI. The AI is talkative and provides lots of specific details from its context. If the AI does not know the answer to a question, it truthfully says it does not know."
                ),
                MessagesPlaceholder(variable_name="history"),
                HumanMessagePromptTemplate.from_template("{input}"),
            ]
        )

        llm = AzureChatOpenAI(
            deployment_name="gpt35",
            openai_api_version="2023-03-15-preview",
            callback_manager=AsyncCallbackManager([AsyncStreamCallbackHandler(send)]),
            verbose=True,
            streaming=True,
        )

        # memory = ConversationTokenBufferMemory(
        #     llm=llm, max_token_limit=3000, return_messages=True
        # )
        memory = ConversationBufferWindowMemory(k=3, return_messages=True)

        conversation = ConversationChain(
            llm=llm,
            prompt=prompt,
            memory=memory,
        )

        await conversation.apredict(input=message)

    return generate


class StreamRequest(BaseModel):
    """Request body for streaming."""

    message: str
