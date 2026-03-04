from fastapi import FastAPI
from pydantic import BaseModel
from orchestrator import Orchestrator


app = FastAPI()

class  TaskRequest(BaseModel):
    task:str

orchestrator = Orchestrator()

@app.post("/execute")
async def execute(request:TaskRequest):
    state = await orchestrator.run(request.task)

    return {
        "original_task":state.original_task,
        "results":[r.dict() for r in state.results]
    }