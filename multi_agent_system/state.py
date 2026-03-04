from typing import List ,Dict
from pydantic import BaseModel


class ExecutionResult(BaseModel):
    subtask: str
    output: str
    review_status: str
    review_reason: str


class TaskState:
    def __init__(self, original_task:str):
        self.original_task:str= original_task
        self.subtasks: List[str] = []
        self.results: List[ExecutionResult] = []
        self.current_subtask: str| None = None
        self.retry_count:int =0
        self.max_retry_count:int = 0
        self.max_retries:int = 1