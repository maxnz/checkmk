#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import OIDEnd, SNMPTree
from cmk.base.plugins.agent_based.utils.emc import DETECT_DATADOMAIN


def inventory_emc_datadomain_disks(info):
    inventory = []
    for line in info[0]:
        item = line[0] + "-" + line[1]
        inventory.append((item, None))
    return inventory


def check_emc_datadomain_disks(item, _no_params, info):
    state_table = {
        "1": ("Operational", 0),
        "2": ("Unknown", 3),
        "3": ("Absent", 1),
        "4": ("Failed", 2),
        "5": ("Spare", 0),
        "6": ("Available", 0),
        "10": ("System", 0),
    }
    for line in info[0]:
        if item == line[0] + "-" + line[1]:
            model = line[2]
            firmware = line[3]
            serial = line[4]
            capacity = line[5]
            dev_state = line[6]
            dev_state_str = state_table.get(dev_state, ("Unknown", 3))[0]
            dev_state_rc = state_table.get(dev_state, ("Unknown", 3))[1]
            yield dev_state_rc, dev_state_str
            index = int(line[7].split(".")[1]) - 1
            if len(info[1]) > index:
                busy = info[1][index][0]
                perfdata = [("busy", busy + "%")]
                yield 0, "busy %s%%" % busy, perfdata
            yield 0, "Model %s, Firmware %s, Serial %s, Capacity %s" % (
                model,
                firmware,
                serial,
                capacity,
            )


check_info["emc_datadomain_disks"] = LegacyCheckDefinition(
    detect=DETECT_DATADOMAIN,
    fetch=[
        SNMPTree(
            base=".1.3.6.1.4.1.19746.1.6.1.1.1",
            oids=["1", "2", "4", "5", "6", "7", "8", OIDEnd()],
        ),
        SNMPTree(
            base=".1.3.6.1.4.1.19746.1.6.2.1.1",
            oids=["6"],
        ),
    ],
    service_name="Hard Disk %s",
    discovery_function=inventory_emc_datadomain_disks,
    check_function=check_emc_datadomain_disks,
)
