from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from xml.etree.ElementTree import Element, SubElement, tostring


@dataclass
class MarPayload:
    case_id: int
    issuer: str
    instrument: str
    suspect: str
    narrative: str
    detected_at: datetime


def render_mar_xml(payload: MarPayload) -> str:
    root = Element("MARReport")
    root.set("version", "1.0")

    header = SubElement(root, "Header")
    SubElement(header, "CaseId").text = str(payload.case_id)
    SubElement(header, "DetectedAt").text = payload.detected_at.isoformat()

    body = SubElement(root, "Body")
    SubElement(body, "Issuer").text = payload.issuer
    SubElement(body, "Instrument").text = payload.instrument
    SubElement(body, "Suspect").text = payload.suspect
    SubElement(body, "Narrative").text = payload.narrative

    return tostring(root, encoding="unicode")
