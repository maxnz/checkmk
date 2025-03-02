#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import SNMPTree
from cmk.base.plugins.agent_based.utils.ibm import DETECT_IBM_IMM


def inventory_ibm_imm_fan(info):
    for descr, speed_text in info:
        if speed_text.lower() != "offline":
            yield descr, {}


def check_ibm_imm_fan(item, params, info):  # pylint: disable=too-many-branches
    for descr, speed_text in info:
        if descr == item:
            if speed_text.lower() in ["offline", "unavailable"]:
                yield 2, "is %s" % speed_text.lower()
                return

            # speed_text can be "34 %", or "34%", or "34 % of maximum"
            # or simply a text without quotes..
            rpm_perc = int(speed_text.strip().replace('["%]', " ").replace("%", " ").split(" ")[0])
            yield 0, "%d%% of max RPM" % rpm_perc

            warn_lower, crit_lower = params["levels_lower"]
            warn, crit = params.get("levels", (None, None))

            if warn_lower:
                if rpm_perc < crit_lower:
                    state = 2
                elif rpm_perc < warn_lower:
                    state = 1
                else:
                    state = 0
                if state > 0:
                    yield state, "too low (warn/crit below %d%%/%d%%)" % (warn_lower, crit_lower)

            if warn:
                if rpm_perc >= crit:
                    state = 2
                elif rpm_perc >= warn:
                    state = 1
                else:
                    state = 0
                if state > 0:
                    yield state, "too high (warn/crit at %d%%/%d%%)" % (warn, crit)


check_info["ibm_imm_fan"] = LegacyCheckDefinition(
    detect=DETECT_IBM_IMM,
    fetch=SNMPTree(
        base=".1.3.6.1.4.1.2.3.51.3.1.3.2.1",
        oids=["2", "3"],
    ),
    service_name="Fan %s",
    discovery_function=inventory_ibm_imm_fan,
    check_function=check_ibm_imm_fan,
    check_ruleset_name="hw_fans_perc",
    check_default_parameters={
        "levels_lower": (28, 25),  # Just a guess. Please give feedback.
    },
)
