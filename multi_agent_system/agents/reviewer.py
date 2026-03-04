import json
from agents.base import BaseAgent
from state import TaskState
from ollama_client import call_ollama


class ReviewerAgent(BaseAgent):
    async def run(self, state:TaskState , execution_output:str):
        prompt= f""" 
You are a strict code reviewer.
Evaluate the execution result below.

Return ONLY valid JSON in this format:
{{
 "status": "PASS" or "FAIL",
 "reason": "short explanation"
}}

subtasks:
{state.current_subtask}

Execution:
{execution_output}
"""
        

        raw_output = call_ollama(prompt)

        try:
            review = json.loads(raw_output)
            if "status" not in review or "reason" not in review:
                raise ValueError()
        except Exception:
            raise Exception("Reviewer returned invalid JSON")
        
        return review