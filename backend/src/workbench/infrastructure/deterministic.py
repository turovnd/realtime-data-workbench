from typing import Literal

from workbench.schemas.common import Config, Topic
from workbench.schemas.enrichment import Enrichment


async def generate_demo(text: str, config: Config) -> str:
    lowered = text.lower()
    topic: Topic = "other"
    rules: tuple[tuple[Topic, tuple[str, ...]], ...] = (
        ("billing", ("billing", "invoice", "charged")),
        ("performance", ("slow", "seconds", "times out")),
        ("reliability", ("stop", "empty", "loses")),
        ("usability", ("shortcut", "pin", "filters", "panel")),
    )
    for candidate, keywords in rules:
        if any(word in lowered for word in keywords):
            topic = candidate
            break
    intent: Literal["issue", "request", "praise", "unclear"] = "issue"
    if lowered.startswith("please"):
        intent = "request"
    elif any(word in lowered for word in ("thank you", "easy to", "easier")):
        intent = "praise"
    elif topic == "other":
        intent = "unclear"
    summary = text[:200] if config == "v1" else f"{intent.title()} · {topic}: {text[:190]}"
    return Enrichment(
        topic=topic, intent=intent, summary=summary, evidence=[text[:180]]
    ).model_dump_json()
