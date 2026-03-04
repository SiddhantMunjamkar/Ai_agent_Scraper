from agents.base import BaseAgent
from state import TaskState
from ollama_client import call_ollama



class ExecutorAgent(BaseAgent):

    async def run(self, state:TaskState):

        prompt = f"""
          Your are a senior backend engineer.

          Execute the following engineering task in detail.
          Be technical and structured.

          Task:
          {state.current_subtask}
        """

        output = call_ollama(prompt)
        return output