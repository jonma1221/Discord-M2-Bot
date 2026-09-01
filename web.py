import uvicorn
import os
from fastapi import FastAPI
from threading import Thread

app = FastAPI()
@app.get("/")
def pingBot():
    return {"message": "Bot is online"}

def run_server():
    # Render automatically injects the PORT environment variable
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True  # Allows the thread to exit when the main program stops
    t.start()