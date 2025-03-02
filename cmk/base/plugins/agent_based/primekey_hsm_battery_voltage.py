#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from dataclasses import dataclass
from typing import Mapping, Tuple

from .agent_based_api.v1 import check_levels, register, Result, Service, SNMPTree, State
from .agent_based_api.v1.type_defs import CheckResult, DiscoveryResult, StringTable
from .utils.primekey import DETECT_PRIMEKEY


@dataclass(frozen=True)
class HSMBattery:
    voltage: float
    state_fail: bool


_Section = Mapping[str, HSMBattery]


def _parse_voltage(voltage_entry: str) -> float:
    return float(voltage_entry.removesuffix(" V"))


def parse(string_table: StringTable) -> _Section | None:
    if not string_table:
        return None

    parsed = {
        "1": HSMBattery(
            voltage=_parse_voltage(string_table[0][0]), state_fail=bool(int(string_table[0][1]))
        ),
        "2": HSMBattery(
            voltage=_parse_voltage(string_table[0][2]), state_fail=bool(int(string_table[0][3]))
        ),
    }
    return parsed


register.snmp_section(
    name="primekey_hsm_battery_voltage",
    parse_function=parse,
    detect=DETECT_PRIMEKEY,
    fetch=SNMPTree(
        ".1.3.6.1.4.1.22408.1.1.2.2.4.104.115.109",
        [
            "52.1",  # voltage
            "53.1",  # status
            "55.1",  # voltage2
            "56.1",  # status2
        ],
    ),
)


def discover(section: _Section) -> DiscoveryResult:
    for item in section.keys():
        yield Service(item=item)


def check(
    item: str,
    params: Mapping[str, Tuple[float, float]],
    section: _Section,
) -> CheckResult:
    if not (battery := section.get(item)):
        return

    yield Result(
        state=State.CRIT, summary=f"PrimeKey HSM battery {item} status not OK"
    ) if battery.state_fail else Result(
        state=State.OK, summary=f"PrimeKey HSM battery {item} status OK"
    )

    yield from check_levels(
        levels_upper=params.get("levels"),
        levels_lower=params.get("levels_lower"),
        value=battery.voltage,
        render_func=lambda v: f"{v} V",
        metric_name="voltage",
    )


register.check_plugin(
    name="primekey_hsm_battery_voltage",
    service_name="PrimeKey HSM Battery %s",
    discovery_function=discover,
    check_function=check,
    check_default_parameters={},
    check_ruleset_name="voltage",
)
