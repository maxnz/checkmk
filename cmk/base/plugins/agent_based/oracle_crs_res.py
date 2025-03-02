#!/usr/bin/env python3
# Copyright (C) 2022 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Optional

from .agent_based_api.v1 import check_levels, IgnoreResultsError, register, Result, Service, State
from .agent_based_api.v1.type_defs import CheckResult, DiscoveryResult, StringTable

# <<<oracle_crs_res:sep(124)>>>
# oracle_host|NAME=ora.DG_CLUSTER.dg
# oracle_host|TYPE=ora.diskgroup.type
# oracle_host|STATE=ONLINE on oracle_host
# oracle_host|TARGET=ONLINE
# oracle_host|NAME=ora.I31_ARCH.dg
# oracle_host|TYPE=ora.diskgroup.type
# oracle_host|STATE=ONLINE on oracle_host
# oracle_host|TARGET=ONLINE
# oracle_host|NAME=ora.I31_DATA.dg
# oracle_host|TYPE=ora.diskgroup.type
# oracle_host|STATE=ONLINE on oracle_host
# oracle_host|TARGET=ONLINE
# oracle_host|NAME=ora.I31_MLOG.dg
# oracle_host|TYPE=ora.diskgroup.type
# oracle_host|STATE=ONLINE on oracle_host
# oracle_host|TARGET=ONLINE
# ...usw...


@dataclass(frozen=True)
class Resource:
    type: str
    state: str
    target: str


@dataclass(frozen=True)
class Section:
    crs_nodename: Optional[str]
    resources: Mapping[str, Mapping[Optional[str], Resource]]


def parse_oracle_crs_res(string_table: StringTable) -> Section:
    crs_nodename = None
    raw_ressources: dict[str, Any] = defaultdict(dict)
    entry: dict[str, str] = {}

    for line in string_table:
        if len(line) == 1:
            # Seems to be an old version where first column is missing:
            # <<<oracle_crs_res>>>
            # NAME=foo
            # TYPE=bar
            # STATE=baz
            nodename, varsetting = None, line[0]
        else:
            nodename, varsetting = line

        if nodename == "nodename":
            crs_nodename = varsetting
            continue

        key, value = varsetting.split("=", 1)
        if key == "NAME":
            res_name = value
            entry = {}
            raw_ressources.setdefault(res_name, {})
            raw_ressources[res_name][nodename] = entry
        else:
            entry[key.lower()] = value

    resources: dict[str, Mapping[Optional[str], Resource]] = {}
    for resname, values in raw_ressources.items():
        resources[resname] = {node: Resource(**entry) for node, entry in values.items()}
    return Section(crs_nodename, resources)


register.agent_section(
    name="oracle_crs_res",
    parse_function=parse_oracle_crs_res,
)


def discover_oracle_crs_res(section: Section) -> DiscoveryResult:
    for item in section.resources:
        yield Service(item=item)


def check_oracle_crs_res(
    item: str, params: Mapping[str, tuple[int, int]], section: Section
) -> CheckResult:
    if item not in section.resources:
        if item == "ora.cssd":
            yield Result(state=State.CRIT, summary="Clusterware not running")
        elif item == "ora.crsd":
            yield Result(state=State.CRIT, summary="Cluster resource service daemon not running")
        else:
            raise IgnoreResultsError(
                f"No resource details found for {item}, Maybe cssd/crsd is not running"
            )
        return

    if (nodes_info := section.resources.get(item)) is None:
        return

    number_of_nodes_not_in_target_state = 0
    summary = ""
    for nodename, entry in nodes_info.items():
        resstate = entry.state.split(" ", 1)[0]
        restarget = entry.target

        if nodename == "csslocal":
            infotext = "local: "
        elif nodename:
            infotext = "on " + nodename + ": "
        else:
            infotext = ""
        infotext += resstate.lower()

        if resstate != restarget:
            number_of_nodes_not_in_target_state += 1
            infotext += f", target state {restarget.lower()}"

        summary += f"; {infotext}" if summary else infotext

    yield from check_levels(
        value=number_of_nodes_not_in_target_state,
        levels_upper=params["number_of_nodes_not_in_target_state"],
        metric_name="oracle_number_of_nodes_not_in_target_state",
        label="Number of nodes not in target state",
        render_func=lambda x: str(int(x)),
    )

    yield Result(
        state=State.OK,
        summary=summary,
    )


register.check_plugin(
    name="oracle_crs_res",
    service_name="ORA-GI %s Resource",
    discovery_function=discover_oracle_crs_res,
    check_function=check_oracle_crs_res,
    check_ruleset_name="oracle_crs_res",
    check_default_parameters={"number_of_nodes_not_in_target_state": (1, 2)},
)
