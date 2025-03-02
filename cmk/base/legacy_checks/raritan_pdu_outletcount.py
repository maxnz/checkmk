#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import check_levels, LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import all_of, any_of, SNMPTree, startswith


def inventory_raritan_pdu_outletcount(info):
    if info and info[0]:
        yield None, None


def check_raritan_pdu_outletcount(item, params, info):
    try:
        yield check_levels(
            int(info[0][0]), "outletcount", params, human_readable_func=lambda f: "%.f" % f
        )
    except IndexError:
        pass


check_info["raritan_pdu_outletcount"] = LegacyCheckDefinition(
    detect=all_of(
        startswith(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.13742.6"),
        any_of(
            startswith(".1.3.6.1.4.1.13742.6.3.2.1.1.3.1", "PX2-2"),
            startswith(".1.3.6.1.4.1.13742.6.3.2.1.1.3.1", "PX3"),
        ),
    ),
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.13742.6.3.2.2.1.4",
        oids=["1"],
    ),
    service_name="Outlet Count",
    discovery_function=inventory_raritan_pdu_outletcount,
    check_function=check_raritan_pdu_outletcount,
    check_ruleset_name="plug_count",
)
