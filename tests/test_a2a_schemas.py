from finance_green_agent.a2a_schemas import (
    DataPart,
    Message,
    Part,
    Role,
    Task,
    TaskState,
    TaskStatus,
)


def test_message_serialization():
    msg = Message(role=Role.user, content=[Part(text="hello")])
    payload = msg.model_dump(by_alias=True, exclude_none=True)
    assert payload["role"] == "ROLE_USER"
    assert payload["content"][0]["text"] == "hello"


def test_task_creation():
    msg = Message(role=Role.agent, content=[Part(data=DataPart(data={"ok": True}))])
    task = Task(
        id="t1",
        status=TaskStatus(state=TaskState.completed, message=msg),
        context_id="c1",
    )
    payload = task.model_dump(by_alias=True, exclude_none=True)
    assert payload["status"]["state"] == "TASK_STATE_COMPLETED"
