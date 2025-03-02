#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


# mypy: disable-error-code="arg-type"

import time

import cmk.base.plugins.agent_based.utils.memory as memory
from cmk.base.check_api import check_levels, get_bytes_human_readable, LegacyCheckDefinition
from cmk.base.check_legacy_includes.mem import check_memory_dict, check_memory_element
from cmk.base.config import check_info
from cmk.base.plugins.agent_based.agent_based_api.v1 import get_average, get_value_store, render

#   .--mem.linux-----------------------------------------------------------.
#   |                                      _ _                             |
#   |           _ __ ___   ___ _ __ ___   | (_)_ __  _   ___  __           |
#   |          | '_ ` _ \ / _ \ '_ ` _ \  | | | '_ \| | | \ \/ /           |
#   |          | | | | | |  __/ | | | | |_| | | | | | |_| |>  <            |
#   |          |_| |_| |_|\___|_| |_| |_(_)_|_|_| |_|\__,_/_/\_\           |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   |  Specialized memory check for Linux that takes into account          |
#   |  all of its specific information in /proc/meminfo.                   |
#   '----------------------------------------------------------------------'


def inventory_mem_linux(section):
    if memory.is_linux_section(section):
        yield None, {}


def check_mem_linux(_no_item, params, section):
    if not section:
        return

    # quick fix: stop modifying parsed data in place!
    section = section.copy()

    # TODO: Currently some of these values are just set to generate the metrics later
    # See which ones we actually need.

    # SReclaimable is not available for older kernels
    # SwapCached may be missing if swap is disabled, see crash 9d22dcb4-5260-11eb-8458-0b95bfca1bb1
    # Compute memory used by caches, that can be considered "free"
    section["Caches"] = (
        section["Cached"]
        + section["Buffers"]
        + section.get("SwapCached", 0)
        + section.get("SReclaimable", 0)
    )

    section["MemUsed"] = section["MemTotal"] - section["MemFree"] - section["Caches"]
    section["SwapUsed"] = section["SwapTotal"] - section["SwapFree"]
    section["TotalTotal"] = section["MemTotal"] + section["SwapTotal"]
    section["TotalUsed"] = section["MemUsed"] + section["SwapUsed"]

    # Disk Writeback
    section["Pending"] = (
        section["Dirty"]
        + section.get("Writeback", 0)
        + section.get("NFS_Unstable", 0)
        + section.get("Bounce", 0)
        + section.get("WritebackTmp", 0)
    )

    results = check_memory_dict(section, params)

    # show this always:
    yield results.pop("virtual", (0, ""))

    details_results = []
    for state, text, metrics in results.values():
        if state:
            yield state, text, metrics
        else:
            details_results.append((state, text, metrics))
    MARK_AS_DETAILS = "\n"
    for state, text, perf in details_results:
        yield state, f"{MARK_AS_DETAILS}{text}", perf

    # Now send performance data. We simply output *all* fields of section
    # except for a few really useless values
    perfdata = []
    for name, value in sorted(section.items()):
        if name.startswith("DirectMap"):
            continue
        if (
            name.startswith("Vmalloc") and section["VmallocTotal"] > 2**40
        ):  # useless on 64 Bit system
            continue
        if name.startswith("Huge"):
            if section["HugePages_Total"] == 0:  # omit useless data
                continue
            if name == "Hugepagesize":
                continue  # not needed
            value = value * section["Hugepagesize"]  # convert number to actual memory size
        metric_name = camelcase_to_underscored(name.replace("(", "_").replace(")", ""))
        if metric_name not in {
            "mem_used",
            "mem_used_percent",
            "swap_used",
            "committed_as",
            "shmem",
            "page_tables",
        }:
            perfdata.append((metric_name, value))
    yield 0, "", perfdata


# ThisIsACamel -> this_is_a_camel
def camelcase_to_underscored(name):
    previous_lower = False
    previous_underscore = True
    result = ""
    for char in name:
        if char.isupper():
            if previous_lower and not previous_underscore:
                result += "_"
            previous_lower = False
            previous_underscore = False
            result += char.lower()
        elif char == "_":
            previous_lower = False
            previous_underscore = True
            result += char
        else:
            previous_lower = True
            previous_underscore = False
            result += char
    return result


check_info["mem.linux"] = LegacyCheckDefinition(
    service_name="Memory",
    sections=["mem"],
    discovery_function=inventory_mem_linux,
    check_function=check_mem_linux,
    check_ruleset_name="memory_linux",
    check_default_parameters={
        "levels_virtual": ("perc_used", (80.0, 90.0)),
        "levels_total": ("perc_used", (120.0, 150.0)),
        "levels_shm": ("perc_used", (20.0, 30.0)),
        "levels_pagetables": ("perc_used", (8.0, 16.0)),
        "levels_committed": ("perc_used", (100.0, 150.0)),
        "levels_commitlimit": ("perc_free", (20.0, 10.0)),
        "levels_vmalloc": ("abs_free", (50 * 1024 * 1024, 30 * 1024 * 1024)),
        "levels_hardwarecorrupted": ("abs_used", (1, 1)),
    },
)

# .
#   .--mem.used------------------------------------------------------------.
#   |                                                        _             |
#   |           _ __ ___   ___ _ __ ___   _   _ ___  ___  __| |            |
#   |          | '_ ` _ \ / _ \ '_ ` _ \ | | | / __|/ _ \/ _` |            |
#   |          | | | | | |  __/ | | | | || |_| \__ \  __/ (_| |            |
#   |          |_| |_| |_|\___|_| |_| |_(_)__,_|___/\___|\__,_|            |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   | Memory check that takes into account the swap space. This check is   |
#   | used for unixoide operating systems.                                 |
#   '----------------------------------------------------------------------'


# .
#   .--mem.win-------------------------------------------------------------.
#   |                                                _                     |
#   |              _ __ ___   ___ _ __ ___ __      _(_)_ __                |
#   |             | '_ ` _ \ / _ \ '_ ` _ \\ \ /\ / / | '_ \               |
#   |             | | | | | |  __/ | | | | |\ V  V /| | | | |              |
#   |             |_| |_| |_|\___|_| |_| |_(_)_/\_/ |_|_| |_|              |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   | Windows now has a dedicated memory check that reflect the special    |
#   | nature of the page file.                                             |
#   '----------------------------------------------------------------------'

_MB = 1024**2

# Special memory and page file check for Windows


def inventory_mem_win(section):
    if "MemTotal" in section and "PageTotal" in section:
        yield None, {}


def _get_levels_type(levels):
    if levels is None:
        return None
    if not isinstance(levels, tuple):
        return "predictive"
    if isinstance(levels[0], float):
        return "perc_used"
    return "abs_free"


def _get_levels_type_and_value(levels_value):
    levels_type = _get_levels_type(levels_value)
    if levels_type is None or levels_type == "predictive":
        return (
            levels_type,
            None,
        )
    return (
        levels_type,
        (
            levels_type,
            levels_value
            if levels_type == "perc_used"
            else (
                # absolute levels on free space come in MB, which cannot be changed easily
                levels_value[0] * _MB,
                levels_value[1] * _MB,
            ),
        ),
    )


def _do_averaging(
    timestamp,
    average_horizon_min,
    paramname,
    used,
    total,
):
    used_avg = (
        get_average(
            get_value_store(),
            "mem.win.%s" % paramname,
            timestamp,
            used / 1024.0,  # use kB for compatibility
            average_horizon_min,
        )
        * 1024
    )
    return (
        used_avg,
        "%d min average: %s (%s)"
        % (
            average_horizon_min,
            render.percent(100.0 * used_avg / total),
            get_bytes_human_readable(used_avg),
        ),
    )


def _apply_predictive_levels(
    params,
    paramname,
    title,
    used,
):
    if "average" in params:
        titleinfo = title
        dsname = "%s_avg" % paramname
    else:
        titleinfo = title
        dsname = paramname

    return check_levels(
        used / _MB,  # Current value stored in MB in RRDs
        dsname,
        params[paramname],
        unit="GiB",  # Levels are specified in GiB...
        scale=1024,  # ... in WATO ValueSpec
        infoname=titleinfo,
    )


def check_mem_windows(_no_item, params, section):
    now = time.time()

    for title, prefix, paramname, metric_name in [
        ("RAM", "Mem", "memory", "mem_used"),
        ("Commit charge", "Page", "pagefile", "pagefile_used"),
    ]:
        total = section.get("%sTotal" % prefix)
        free = section.get("%sFree" % prefix)
        if None in (total, free):
            continue
        used = total - free

        levels_type, levels_memory_element = _get_levels_type_and_value(params.get(paramname))
        do_averaging = "average" in params

        state, infotext, perfdata = check_memory_element(
            title,
            used,
            total,
            None if do_averaging else levels_memory_element,
            metric_name=metric_name,
            create_percent_metric=title == "RAM",
        )

        # Metrics for total mem and pagefile are expected in MB
        if prefix == "Mem":
            perfdata.append(("mem_total", total / _MB))
        elif prefix == "Page":
            perfdata.append(("pagefile_total", total / _MB))

        # Do averaging, if configured, just for matching the levels
        if do_averaging:
            used, infoadd = _do_averaging(
                now,
                params["average"],
                paramname,
                used,
                total,
            )
            infotext += f", {infoadd}"

            if levels_type != "predictive":
                state, _infotext, perfadd = check_memory_element(
                    title,
                    used,
                    total,
                    levels_memory_element,
                    metric_name=paramname + "_avg",
                )

                perfdata.append(
                    (
                        (averaged_metric := perfadd[0])[0],
                        # the averaged metrics are expected to be in MB
                        *(v / _MB if v is not None else None for v in averaged_metric[1:]),
                    )
                )

        if levels_type == "predictive":
            state, infoadd, perfadd = _apply_predictive_levels(
                params,
                paramname,
                title,
                used,
            )
            if infoadd:
                infotext += ", " + infoadd
            perfdata += perfadd

        yield state, infotext, perfdata


check_info["mem.win"] = LegacyCheckDefinition(
    service_name="Memory",
    sections=["mem"],
    discovery_function=inventory_mem_win,
    check_function=check_mem_windows,
    check_ruleset_name="memory_pagefile_win",
    check_default_parameters={
        "memory": (80.0, 90.0),
        "pagefile": (80.0, 90.0),
    },
)

# .
#   .--mem.vmalloc---------------------------------------------------------.
#   |                                                   _ _                |
#   |    _ __ ___   ___ _ __ ___ __   ___ __ ___   __ _| | | ___   ___     |
#   |   | '_ ` _ \ / _ \ '_ ` _ \\ \ / / '_ ` _ \ / _` | | |/ _ \ / __|    |
#   |   | | | | | |  __/ | | | | |\ V /| | | | | | (_| | | | (_) | (__     |
#   |   |_| |_| |_|\___|_| |_| |_(_)_/ |_| |_| |_|\__,_|_|_|\___/ \___|    |
#   |                                                                      |
#   +----------------------------------------------------------------------+
#   | This very specific check checks the usage and fragmentation of the   |
#   | address space 'vmalloc' that can be problematic on 32-Bit systems.   |
#   | It is superseeded by the new check mem.linux and will be removed     |
#   | soon.                                                                |
#   '----------------------------------------------------------------------'

# warn, crit, warn_chunk, crit_chunk. Integers are in MB, floats are in percent
mem_vmalloc_default_levels = (80.0, 90.0, 64, 32)


def inventory_mem_vmalloc(section):
    if memory.is_linux_section(section):
        return  # handled by new Linux memory check

    # newer kernel version report wrong data,
    # i.d. both VmallocUsed and Chunk equal zero
    if "VmallocTotal" in section and not (
        section["VmallocUsed"] == 0 and section["VmallocChunk"] == 0
    ):
        # Do not checks this on 64 Bit systems. They have almost
        # infinitive vmalloc
        if section["VmallocTotal"] < 4 * 1024**2:
            yield None, mem_vmalloc_default_levels


def check_mem_vmalloc(_item, params, section):
    total_mb = section["VmallocTotal"] / 1024.0**2
    used_mb = section["VmallocUsed"] / 1024.0**2
    chunk_mb = section["VmallocChunk"] / 1024.0**2
    warn, crit, warn_chunk, crit_chunk = params

    state = 0
    infotxts = []
    perfdata = []
    for var, loop_warn, loop_crit, loop_val, neg, what in [
        ("used", warn, crit, used_mb, False, "used"),
        ("chunk", warn_chunk, crit_chunk, chunk_mb, True, "largest chunk"),
    ]:
        # convert levels from percentage to MB values
        if isinstance(loop_warn, float):
            w_mb = total_mb * loop_warn / 100
        else:
            w_mb = float(loop_warn)

        if isinstance(loop_crit, float):
            c_mb = total_mb * loop_crit / 100
        else:
            c_mb = float(loop_crit)

        loop_state = 0
        infotxt = "%s %.1f MB" % (what, loop_val)
        if (loop_val >= c_mb) != neg:
            loop_state = 2
            infotxt += " (critical at %.1f MB!!)" % c_mb
        elif (loop_val >= w_mb) != neg:
            loop_state = 1
            infotxt += " (warning at %.1f MB!)" % w_mb
        state = max(state, loop_state)
        infotxts.append(infotxt)
        perfdata.append((var, loop_val, w_mb, c_mb, 0, total_mb))
    return (state, ("total %.1f MB, " % total_mb) + ", ".join(infotxts), perfdata)


check_info["mem.vmalloc"] = LegacyCheckDefinition(
    service_name="Vmalloc address space",
    sections=["mem"],
    discovery_function=inventory_mem_vmalloc,
    check_function=check_mem_vmalloc,
)
