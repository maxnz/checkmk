#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# Check has been developed using a Emerson Network Power Rack PDU Card
# Agent App Firmware Version  4.840.0
# Agent Boot Firmware Version 4.540.3
# FDM Version 1209
# GDD Version 45585

# Example info data:
# [[['Rack PDU Card', '4.840.0', '535055G103T2010JUN240295']], [['1', '1', '.1.3.6.1.4.1.476.1.42.4.8.2.2', 'Emerson Network Power', '1']]]


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree
from cmk.base.plugins.agent_based.utils.lgp import DETECT_LGP

lgp_info_devices = {
    ".1.3.6.1.4.1.476.1.42.4.8.2.1": "lgpMPX",
    ".1.3.6.1.4.1.476.1.42.4.8.2.2": "lgpMPH",
}


def inventory_lgp_info(info):
    if info and info[0] and info[0][0]:
        return [(None, None)]
    return []


def check_lgp_info(item, params, info):
    if info and info[0] and info[0][0]:
        agent_info = info[0][0]

        device_output = ""
        if len(info) > 1:
            devices = []
            for id_, manufacturer, unit_number in info[1]:
                id_ = lgp_info_devices.get(id_, id_)
                devices.append(
                    "ID: %s, Manufacturer: %s, Unit-Number: %s" % (id_, manufacturer, unit_number)
                )
            device_output = "\n".join(devices)

        return (0, "Model: %s, Firmware: %s, S/N: %s\n%s" % tuple(agent_info + [device_output]))
    return None


check_info["lgp_info"] = LegacyCheckDefinition(
    detect=DETECT_LGP,
    fetch=[
        SNMPTree(
            base=".1.3.6.1.4.1.476.1.42.2.1",
            oids=["2.0", "3.0", "4.0"],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.476.1.42.2.4.2.1",
            oids=["2", "3", "6"],
        ),
    ],
    service_name="Liebert Info",
    discovery_function=inventory_lgp_info,
    check_function=check_lgp_info,
)
