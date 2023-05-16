"""This is an example of how to use async langchain with fastapi and return a streaming response."""
import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse, HTMLResponse, Response
from dotenv import load_dotenv
from chain import ChatOpenAIStreamingResponse, send_message, StreamRequest
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()
# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return HTMLResponse(content=open("static/index.html").read(), status_code=200)


@app.post("/stream")
def stream(body: StreamRequest):
    return ChatOpenAIStreamingResponse(
        send_message(body.message), media_type="text/event-stream"
    )


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()
    uvicorn.run(host="0.0.0.0", port=8000, app=app)
