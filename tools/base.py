"""Реестр инструментов для Claude tool-use."""

_TOOL_REGISTRY: list[dict] = []


def tool(name: str, description: str, parameters: dict):
    """Декоратор для регистрации инструмента.

    Использование:
        @tool("get_events", "Получить события из календаря", {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Дата в формате YYYY-MM-DD"}
            },
            "required": ["date"]
        })
        def get_events(params):
            return [{"title": "Встреча", "time": "14:00"}]
    """
    def decorator(func):
        _TOOL_REGISTRY.append({
            "name": name,
            "description": description,
            "input_schema": parameters,
            "handler": func,
        })
        return func
    return decorator


def get_all_tools() -> list[dict]:
    """Возвращает все зарегистрированные инструменты."""
    return _TOOL_REGISTRY


def register_tools_to_brain(brain):
    """Регистрирует все инструменты в Brain."""
    for t in _TOOL_REGISTRY:
        brain.register_tool(
            name=t["name"],
            description=t["description"],
            input_schema=t["input_schema"],
            handler=t["handler"],
        )
