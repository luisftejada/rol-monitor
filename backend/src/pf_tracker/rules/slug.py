"""ASCII slug derivation from Spanish canonical names.

Spanish strings are opaque canonical identifiers (``Espada larga``, ``Saber
(dungeons)``). URLs and keys need stable ASCII slugs derived from them, without
mutating the underlying data.
"""

from __future__ import annotations

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def slugify(name: str) -> str:
    """Return a lowercase ASCII slug for a Spanish canonical name.

    ``Espada larga`` -> ``espada-larga``; ``Saber (dungeons)`` -> ``saber-dungeons``;
    ``Cimitarra +1`` -> ``cimitarra-1``.
    """
    decomposed = unicodedata.normalize("NFKD", name)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    lowered = ascii_only.lower()
    return _NON_ALNUM.sub("-", lowered).strip("-")
