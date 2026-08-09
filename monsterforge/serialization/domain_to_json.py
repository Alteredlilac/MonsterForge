""" 
Serialize MonsterForge domain objects into JSON for external API responses.

This module provides the serialization boundary between the domain model
and the HTTP/API layer.

Domain objects remain the canonical internal representation of MonsterForge.
They are converted to JSON only when data must cross the API boundary.
The rendering pipeline does not depend on this serialization layer and continues
to consume domain objects directly.

The encoder handles:

  - Enum values by serializing their underlying value
  - Card references using their name and UUID
  - Entity objects while exposing their derived base_form property
  - Dataclasses by serializing their declared fields
  - UUID values as strings

Public helpers provide explicit entry points for serializing cards and entities,
keeping the JSON conversion logic separate from the API routes. 
"""
from dataclasses import fields, is_dataclass
from enum import Enum
import json
import uuid
from monsterforge.domain.cards import Card
from monsterforge.domain.entity import Entity


class DomainJSONEncoder(json.JSONEncoder):
    """
    Encode MonsterForge domain objects into JSON-compatible values.

    Extends the standard JSON encoder with domain-specific serialization
    rules for Enums, Cards, Entities, dataclasses, and UUIDs.

    Card references are reduced to their name and UUID, while Entity
    objects additionally expose their derived ``base_form`` property.
    """
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value

        if isinstance(obj, Card):
            return {
                "name": obj.name,
                "id": str(obj.id),
            }

        if isinstance(obj, Entity):
            data = {
                field.name: getattr(obj, field.name)
                for field in fields(obj)
                }

            data["base_form"] = obj.base_form

            return data

        if is_dataclass(obj):  
            return {
                field.name: getattr(obj, field.name)
                for field in fields(obj)
            }

        if isinstance(obj, uuid.UUID):
            return str(obj)

        return super().default(obj)

def card_to_json(card: Card) -> str:
    """Serialize a Card domain object into a JSON string."""
    return json.dumps(card, cls=DomainJSONEncoder)

def domain_entity_to_json(domain_entity: Entity) -> str:
    """Serialize an Entity domain object into a JSON string."""
    return json.dumps(domain_entity, cls=DomainJSONEncoder)
