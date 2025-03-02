#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# Author: Lars Michelsen <lm@mathias-kettner.de>

# General Status:
# '.1.3.6.1.4.1.232.22.2.3.1.1.1.5'  => 'cpqRackCommonEnclosurePartNumber',
# '.1.3.6.1.4.1.232.22.2.3.1.1.1.6'  => 'cpqRackCommonEnclosureSparePartNumber',
# '.1.3.6.1.4.1.232.22.2.3.1.1.1.7'  => 'cpqRackCommonEnclosureSerialNum',
# '.1.3.6.1.4.1.232.22.2.3.1.1.1.8'  => 'cpqRackCommonEnclosureFWRev',
# '.1.3.6.1.4.1.232.22.2.3.1.1.1.16' => 'cpqRackCommonEnclosureCondition',


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree
from cmk.base.plugins.agent_based.utils.hp import DETECT_HP_BLADE

# GENERAL MAPS:

hp_blade_status_map = {1: "Other", 2: "Ok", 3: "Degraded", 4: "Failed"}
hp_blade_status2nagios_map = {
    "Other": 2,
    "Ok": 0,
    "Degraded": 1,
    "Failed": 2,
}


def inventory_hp_blade_general(info):
    if len(info) > 0 and len(info[0]) > 1:
        return [(None, None)]
    return []


def check_hp_blade_general(item, params, info):
    snmp_state = hp_blade_status_map[int(info[0][1])]
    status = hp_blade_status2nagios_map[snmp_state]
    return (
        status,
        "General Status is %s (Firmware: %s, S/N: %s)" % (snmp_state, info[0][0], info[0][2]),
    )


check_info["hp_blade"] = LegacyCheckDefinition(
    detect=DETECT_HP_BLADE,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.232.22.2.3.1.1.1",
        oids=["8", "16", "7"],
    ),
    service_name="General Status",
    discovery_function=inventory_hp_blade_general,
    check_function=check_hp_blade_general,
)
