from abc import ABC , abstractmethod
from state import TaskState


class BaseAgent(ABC):

    @abstractmethod
    async def run(self, state:TaskState):
        pass