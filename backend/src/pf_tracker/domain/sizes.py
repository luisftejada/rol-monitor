"""Size modifier tables, embedded in the domain and guarded by a data-contract test.

The values mirror ``tamanos`` in the corpus. Note the AC/attack column and the
CMB/CMD column are different and inverse: a larger creature is easier to hit (AC
penalty) but better at combat maneuvers (CMB/CMD bonus).
"""

from __future__ import annotations

from pf_tracker.domain.enums import Size

#: Size modifier to AC and to attack rolls (``tamanos[].mod_ca_ataque``).
SIZE_AC_ATTACK_MOD: dict[Size, int] = {
    Size.FINE: 8,
    Size.DIMINUTIVE: 4,
    Size.TINY: 2,
    Size.SMALL: 1,
    Size.MEDIUM: 0,
    Size.LARGE: -1,
    Size.HUGE: -2,
    Size.GARGANTUAN: -4,
    Size.COLOSSAL: -8,
}

#: Size modifier to CMB and CMD (``tamanos[].mod_bmc_dmc``) — inverse of the above.
SIZE_CMB_CMD_MOD: dict[Size, int] = {
    Size.FINE: -8,
    Size.DIMINUTIVE: -4,
    Size.TINY: -2,
    Size.SMALL: -1,
    Size.MEDIUM: 0,
    Size.LARGE: 1,
    Size.HUGE: 2,
    Size.GARGANTUAN: 4,
    Size.COLOSSAL: 8,
}

#: Size modifier to Stealth / Sigilo (``tamanos[].mod_sigilo``).
SIZE_STEALTH_MOD: dict[Size, int] = {
    Size.FINE: 16,
    Size.DIMINUTIVE: 12,
    Size.TINY: 8,
    Size.SMALL: 4,
    Size.MEDIUM: 0,
    Size.LARGE: -4,
    Size.HUGE: -8,
    Size.GARGANTUAN: -12,
    Size.COLOSSAL: -16,
}
