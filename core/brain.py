import json
import logging
import anthropic
import httpx

import config

log = logging.getLogger(__name__)


class Brain:
    """Claude API клиент с поддержкой tool-use."""

    def __init__(self):
        http_client = None
        if config.HTTPS_PROXY:
            http_client = httpx.Client(proxy=config.HTTPS_PROXY)

        self._client = anthropic.Anthropic(
            api_key=config.ANTHROPIC_API_KEY,
            http_client=http_client,
        )
        self._messages: list[dict] = []
        self._tools: list[dict] = []
        self._tool_handlers: dict[str, callable] = {}

    def register_tool(self, name: str, description: str, input_schema: dict, handler: callable):
        """Регистрирует инструмент для Claude tool-use."""
        self._tools.append({
            "name": name,
            "description": description,
            "input_schema": input_schema,
        })
        self._tool_handlers[name] = handler

    def think(self, user_text: str) -> str:
        """Отправляет текст в Claude и возвращает ответ.

        Поддерживает tool-use: если Claude запрашивает инструмент,
        выполняет его и продолжает диалог.
        """
        self._messages.append({"role": "user", "content": user_text})

        while True:
            kwargs = {
                "model": config.ANTHROPIC_MODEL,
                "max_tokens": 1024,
                "system": config.SYSTEM_PROMPT,
                "messages": self._messages,
            }
            if self._tools:
                kwargs["tools"] = self._tools

            try:
                response = self._client.messages.create(**kwargs)
            except anthropic.APIError as e:
                log.error("Claude API error: %s", e)
                self._messages.pop()
                return "Извини, не смог связаться с мозгом. Попробуй ещё раз."

            # Если Claude завершил ответ — возвращаем текст
            if response.stop_reason == "end_turn":
                self._messages.append({"role": "assistant", "content": response.content})
                text = next(
                    (b.text for b in response.content if b.type == "text"),
                    "",
                )
                return text

            # Если Claude запросил инструменты — выполняем
            tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
            if not tool_use_blocks:
                # Нет ни end_turn, ни tool_use — возвращаем что есть
                self._messages.append({"role": "assistant", "content": response.content})
                text = next(
                    (b.text for b in response.content if b.type == "text"),
                    "",
                )
                return text

            self._messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_block in tool_use_blocks:
                handler = self._tool_handlers.get(tool_block.name)
                if handler:
                    try:
                        result = handler(tool_block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result,
                        })
                    except Exception as e:
                        log.error("Tool %s error: %s", tool_block.name, e)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": tool_block.id,
                            "content": f"Ошибка: {e}",
                            "is_error": True,
                        })
                else:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_block.id,
                        "content": f"Инструмент {tool_block.name} не найден",
                        "is_error": True,
                    })

            self._messages.append({"role": "user", "content": tool_results})

    def clear_history(self):
        """Очищает историю диалога."""
        self._messages.clear()

    def trim_history(self, max_pairs: int = 20):
        """Обрезает историю до последних N пар сообщений."""
        if len(self._messages) > max_pairs * 2:
            self._messages = self._messages[-(max_pairs * 2):]
