#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import any_of, equals, SNMPTree


def inventory_docsis_channels_downstream(info):
    for line in info:
        if line[1] != "0":
            yield line[0], {}


def check_docsis_channels_downstream(item, params, info):
    for channel_id, frequency, power in info:
        if channel_id == item:
            # Power
            warn, crit = params["power"]
            power_dbmv = float(int(power)) / 10
            infotext = "Power is %.1f dBmV" % power_dbmv
            levels = " (Levels Warn/Crit at %d dBmV/ %d dBmV)" % (warn, crit)
            state = 0
            if power_dbmv <= crit:
                state = 2
                infotext += levels
            elif power_dbmv <= warn:
                state = 1
                infotext += levels
            yield state, infotext, [("power", power_dbmv, warn, crit)]

            # Check Frequency
            frequency_mhz = float(frequency) / 1000000
            infotext = "Frequency is %.1f MHz" % frequency_mhz
            perfdata = [("frequency", frequency_mhz, warn, crit)]
            state = 0
            if "frequency" in params:
                warn, crit = params["frequency"]
                levels = " (warn/crit at %d MHz/ %d MHz)" % (warn, crit)
                if frequency_mhz >= crit:
                    state = 2
                    infotext += levels
                elif frequency_mhz >= warn:
                    state = 1
                    infotext += levels
            # Change this to yield in case of future extension of the check
            yield state, infotext, perfdata
            return

    yield 3, "Channel information not found in SNMP data"


# This Check is a subcheck because there is also a upstream version possible
check_info["docsis_channels_downstream"] = LegacyCheckDefinition(
    detect=any_of(
        equals(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.4115.820.1.0.0.0.0.0"),
        equals(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.4115.900.2.0.0.0.0.0"),
        equals(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.9.1.827"),
        equals(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.4998.2.1"),
        equals(".1.3.6.1.2.1.1.2.0", ".1.3.6.1.4.1.20858.2.600"),
    ),
    fetch=SNMPTree(
        base=".1.3.6.1.2.1.10.127.1.1.1.1",
        oids=["1", "2", "6"],
    ),
    service_name="Downstream Channel %s",
    discovery_function=inventory_docsis_channels_downstream,
    check_function=check_docsis_channels_downstream,
    check_ruleset_name="docsis_channels_downstream",
    check_default_parameters={
        "power": (5.0, 1.0),
    },
)

# Information for future extensions of the check:
# docsIfDownChannelId             1.3.6.1.2.1.10.127.1.1.1.1.1
# docsIfDownChannelFrequency      1.3.6.1.2.1.10.127.1.1.1.1.2
# docsIfDownChannelWidth          1.3.6.1.2.1.10.127.1.1.1.1.3
# docsIfDownChannelModulation     1.3.6.1.2.1.10.127.1.1.1.1.4
# docsIfDownChannelInterleave     1.3.6.1.2.1.10.127.1.1.1.1.5
# docsIfDownChannelPower          1.3.6.1.2.1.10.127.1.1.1.1.6
# docsIfDownChannelAnnex          1.3.6.1.2.1.10.127.1.1.1.1.7
