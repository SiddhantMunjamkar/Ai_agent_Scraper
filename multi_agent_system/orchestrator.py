from state import TaskState , ExecutionResult
from agents.planner import PlannerAgent
from agents.executor import ExecutorAgent
from agents.reviewer import ReviewerAgent


class Orchestrator:

    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.reviewer = ReviewerAgent()

    async def run(self, task:str):
        state = TaskState(task)

        # Step 1: Planning
        state = await self.planner.run(state)

        #step 2 : Execute each subtask
        for subtask in state.subtasks:
            
            state.current_subtask = subtask
            state.retry_count = 0

            while state.retry_count<= state.max_retries:
                
                execution_output = await self.executor.run(state)
                review = await self.reviewer.run(state,execution_output)

                if review["status"] == "PASS":
                    result = ExecutionResult(
                        subtask=subtask,
                        output= execution_output,
                        review_status= review["status"],
                        review_reason= review["reason"]
                    )
                    state.results.append(result)
                    break
                else:
                    state.retry_count +=1    

                    if state.retry_count > state.max_retries:
                        result = ExecutionResult(
                            subtask=subtask,
                            output= execution_output,
                            review_status = "FAILED",
                            review_reason = "MAx retries exceeded"
                        )
                        state.results.append(result)
                        break
    
        return state



