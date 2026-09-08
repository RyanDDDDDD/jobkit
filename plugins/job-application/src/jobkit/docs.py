"""Bundled reference docs, printed by `jobkit doc <name>`."""
from jobkit._assets import resource_text

DOC_NAMES = (
    "workflow-rules",
    "render-contract",
    "output-layout",
    "ats-checklist",
    "interview-frameworks",
)


def read_doc(name: str) -> str:
    if name not in DOC_NAMES:
        raise KeyError(name)
    return resource_text(f"reference/{name}.md")
