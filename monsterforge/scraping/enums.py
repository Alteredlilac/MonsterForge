"""
Defines the categories of page scraped from a source site.

Lives here rather than in db/scraping.py so it follows the same pattern
as every other enum-owning package in this project (structured_data/dnd/
v3x/enums.py, domain/enums.py, validation/enums.py): a local enums.py per
package, never accumulated in a shared module.
"""
from enum import Enum


# =====================
# PAGE TYPE
# =====================
class PageType(str, Enum):
    # Index pages themselves (monsters/classes/feats/items/spells) are
    # tracked too when downloaded, not only used to discover links.
    INDEX = "index"
    MONSTER = "monster"
    CLASS = "class"
    FEAT = "feat"
    ITEM = "item"
    SPELL = "spell"


# NOTE:
# This member list is a placeholder, not a verified content taxonomy —
# it's a guess at the categories a scraped source site will actually
# have, made before any real scraping has happened. Expect it to change
# once the scraping stage is implemented and run against the real site,
# not to be treated as settled just because it compiles today.
