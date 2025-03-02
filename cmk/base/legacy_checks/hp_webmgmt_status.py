#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import all_of, exists, SNMPTree, startswith


def inventory_hp_webmgmt_status(info):
    for index, _health in info[0]:
        yield index, None


def check_hp_webmgmt_status(item, _no_params, info):
    status_map = {
        "1": (3, "unknown"),
        "2": (3, "unused"),
        "3": (0, "ok"),
        "4": (1, "warning"),
        "5": (2, "critical"),
        "6": (2, "non-recoverable"),
    }

    device_model = info[1][0][0]
    serial_number = info[2][0][0]
    for index, health in info[0]:
        if index == item:
            status, status_msg = status_map[health]
            infotext = "Device status: %s" % status_msg
            if device_model and serial_number:
                infotext += " [Model: %s, Serial Number: %s]" % (device_model, serial_number)
            return status, infotext
    return None


check_info["hp_webmgmt_status"] = LegacyCheckDefinition(
    detect=all_of(
        startswith(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.11"),
        exists(".1.3.6.1.4.1.11.2.36.1.1.5.1.1.*"),
    ),
    fetch=[
        SNMPTree(
            base=".1.3.6.1.4.1.11.2.36.1.1.5.1.1",
            oids=["1", "3"],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.11.2.36.1.1.5.1.1.9",
            oids=["1"],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.11.2.36.1.1.5.1.1.10",
            oids=["1"],
        ),
    ],
    service_name="Status %s",
    discovery_function=inventory_hp_webmgmt_status,
    check_function=check_hp_webmgmt_status,
)
