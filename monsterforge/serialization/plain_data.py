"""
Reduce arbitrary dataclass-based values into plain, literal/JSON-
comparable Python data (dict/list/str/int/float/bool/None).

Distinct from domain_to_json.py: that module encodes MonsterForge's
domain model specifically (Card/Entity-aware reference reduction) for
the API boundary. to_plain() has no domain-specific rules — it is a
generic dataclass/enum flattener, used by test tooling
(tests/tools/generate_expected_outputs.py) and by entry points that
need to serialize non-domain dataclasses (e.g.
llm.semantic_classification.attacks.AttackSemanticResult) to JSON or a
plain-data file.
"""
from dataclasses import fields, is_dataclass
from enum import Enum
from uuid import UUID


def to_plain(value: object) -> object:
    """Recursively reduce a value to plain, literal-comparable Python data
    (dict/list/str/int/float/bool/None) so the result contains no object
    references that would break across runs or require imports.

    NOTE:
    Fields named "id" are skipped. By project convention (CODE_STYLE.md
    §7), any dataclass representing an entity has
    `id: uuid.UUID = field(default_factory=uuid.uuid4)` — a fresh random
    identity assigned on construction, not deterministic content. Keeping
    it would make every generated/expected comparison fail regardless of
    whether the actual content matches.
    """
    if isinstance(value, Enum):
        return value.value

    if is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: to_plain(getattr(value, f.name))
            for f in fields(value)
            if f.name != "id"
        }

    if isinstance(value, (list, tuple)):
        return [to_plain(item) for item in value]

    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}

    if isinstance(value, UUID):
        return str(value)

    return value
