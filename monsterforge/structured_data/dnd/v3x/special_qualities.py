"""
qualità speciali

"""

from enum import Enum
from dataclasses import dataclass, field

@dataclass(kw_only=True)
class SpecialQuality(str, Enum):
    ...