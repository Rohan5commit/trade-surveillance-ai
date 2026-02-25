from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from src.ingestion.communications import CommunicationEvent


@dataclass
class ConnectorWindow:
    start: datetime
    end: datetime


class O365Connector:
    def fetch(self, window: ConnectorWindow) -> list[CommunicationEvent]:
        # Implement via Microsoft Graph in deployment-specific integration layer.
        return []


class GmailConnector:
    def fetch(self, window: ConnectorWindow) -> list[CommunicationEvent]:
        # Implement via Gmail API in deployment-specific integration layer.
        return []


class SlackConnector:
    def fetch(self, window: ConnectorWindow) -> list[CommunicationEvent]:
        # Implement via Slack API token scopes in deployment-specific integration layer.
        return []


class VoiceTranscriptionConnector:
    def fetch(self, window: ConnectorWindow) -> list[CommunicationEvent]:
        # Integrate with transcription service (Whisper/API) as needed.
        return []
