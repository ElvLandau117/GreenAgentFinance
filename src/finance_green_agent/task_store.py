from __future__ import annotations

from typing import Dict
from uuid import uuid4

from .a2a_schemas import Artifact, Message, Task, TaskState, TaskStatus


class InMemoryTaskStore:
    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    def create_task(
        self,
        context_id: str | None = None,
        history: list[Message] | None = None,
    ) -> Task:
        task_id = uuid4().hex
        task = Task(
            id=task_id,
            context_id=context_id,
            status=TaskStatus(state=TaskState.submitted),
            history=history or [],
        )
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def update_status(
        self, task_id: str, state: TaskState, message: Message | None = None
    ) -> Task:
        task = self._tasks[task_id]
        task.status = TaskStatus(state=state, message=message)
        return task

    def add_artifact(self, task_id: str, artifact: Artifact) -> Task:
        task = self._tasks[task_id]
        task.artifacts.append(artifact)
        return task

    def add_history(self, task_id: str, message: Message) -> Task:
        task = self._tasks[task_id]
        task.history.append(message)
        return task
