"""Memória de conversação entre sessões.

Mantém histórico por session_id em memória (padrão) ou em qualquer
backend compatível com BaseChatMessageHistory.

Exemplo:
    memory = ConversationMemory()
    history = memory.get_history("session-123")
"""
from __future__ import annotations

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain_community.chat_message_histories import ChatMessageHistory


class ConversationMemory:
    """Gerencia históricos de conversação por session_id."""

    def __init__(self, max_messages: int = 20) -> None:
        self._sessions: dict[str, ChatMessageHistory] = {}
        self._max_messages = max_messages

    def get_history(self, session_id: str) -> BaseChatMessageHistory:
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatMessageHistory()
        return self._sessions[session_id]

    def get_messages(self, session_id: str) -> list[BaseMessage]:
        messages = self.get_history(session_id).messages
        return messages[-self._max_messages:] if len(messages) > self._max_messages else messages

    def add_user_message(self, session_id: str, content: str) -> None:
        self.get_history(session_id).add_user_message(content)

    def add_ai_message(self, session_id: str, content: str) -> None:
        self.get_history(session_id).add_ai_message(content)

    def clear(self, session_id: str) -> None:
        if session_id in self._sessions:
            self._sessions[session_id].clear()

    def list_sessions(self) -> list[str]:
        return list(self._sessions.keys())
