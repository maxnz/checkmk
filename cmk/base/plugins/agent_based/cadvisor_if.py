#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

import json
import time
from typing import Mapping

from .agent_based_api.v1 import get_value_store, Metric, register, Result, Service
from .agent_based_api.v1.type_defs import CheckResult, DiscoveryResult, StringTable
from .utils import interfaces

Section = Mapping[str, float]

_RESULTS_TO_ABANDON = {
    "Multicast in",
    "Broadcast in",
    "Unicast in",
    "Non-unicast in",
    "Multicast out",
    "Broadcast out",
    "Unicast out",
    "Non-unicast out",
}
_METRICS_TO_KEEP = {
    "in",
    "indisc",
    "inerr",
    "out",
    "outdisc",
    "outerr",
}


def parse_cadvisor_if(string_table: StringTable) -> Section:
    if_info = json.loads(string_table[0][0])
    parsed = {}
    for if_metric, entries in if_info.items():
        if len(entries) != 1:
            continue
        try:
            parsed[if_metric] = float(entries[0]["value"])
        except KeyError:
            continue

    return parsed


register.agent_section(
    name="cadvisor_if",
    parse_function=parse_cadvisor_if,
)


def discover_cadvisor_if(section: Section) -> DiscoveryResult:
    """
    >>> list(discover_cadvisor_if({"if_out_discards": 1.}))
    [Service(item='Summary')]
    """
    yield Service(item="Summary")


def check_cadvisor_if(item: str, section: Section) -> CheckResult:
    for output in interfaces.check_single_interface(
        item,
        {},
        interfaces.InterfaceWithRatesAndAverages.from_interface_with_counters_or_rates(
            interfaces.InterfaceWithCounters(
                attributes=interfaces.Attributes(
                    index="0",
                    descr=item,
                    alias=item,
                    type="1",
                    oper_status="1",
                ),
                counters=interfaces.Counters(
                    in_octets=section["if_in_total"],
                    in_disc=section["if_in_discards"],
                    in_err=section["if_in_errors"],
                    out_octets=section["if_out_total"],
                    out_disc=section["if_out_discards"],
                    out_err=section["if_out_errors"],
                ),
            ),
            timestamp=time.time(),
            value_store=get_value_store(),
            params={},
        ),
    ):
        if (
            isinstance(output, Result)
            and (
                "Speed: unknown" in output.summary
                or any(name in output.details for name in _RESULTS_TO_ABANDON)
            )
        ) or (isinstance(output, Metric) and output.name not in _METRICS_TO_KEEP):
            continue
        yield output


register.check_plugin(
    name="cadvisor_if",
    service_name="Interface %s",
    discovery_function=discover_cadvisor_if,
    check_function=check_cadvisor_if,
)
