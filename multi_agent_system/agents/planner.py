import json 
import re
from agents.base import BaseAgent
from state import TaskState
from ollama_client import call_ollama




def extract_json_array(text:str):
    """ 
     Safely extract a JSON array from model output.
    """

    # try direct parse
    try:
         return json.loads(text)
    except :
         pass
    
    # search for  array in text
    match = re.search(r"\[[\s\S]*?\]",text)

    if match:
         return json.loads(match.group())

    return None

class PlannerAgent(BaseAgent):

    async def run(self, state:TaskState):
        prompt = f""" Your are a senior software achitect.
         Break the following task into 3-5 concrete enginering substasks.
         
         CRITICAL RULES:
         - output MUST be JSON
         - Only output JSON array
         - No explanation

        Example:
        ["design system architecture","define kafka topics","implement producer service"]


         Task:
         {state.original_task}
           """
        raw_output = call_ollama(prompt)
        print("\n===== PLANNER RAW OUTPUT =====")
        print(raw_output)
        print("================================\n")

        subtasks= extract_json_array(raw_output)

        # retry once if parsing fails
        if subtasks is None:

            print("Planner output invalid. Retrying once...")

            raw_output = call_ollama(prompt)

            print("\n===== PLANNER RETRY OUTPUT =====")
            print(raw_output)
            print("===============================\n")

            subtasks = extract_json_array(raw_output)

        if subtasks is None:
            raise Exception("Planner could not produce valid JSON after retry")

        state.subtasks = subtasks

        return state