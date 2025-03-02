#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.


from cmk.base.check_api import passwordstore_get_cmdline
from cmk.base.config import active_check_info


def check_bi_aggr_arguments(params):
    # Convert legacy format
    if isinstance(params, tuple):
        converted_params = {}
        converted_params["base_url"] = params[0]
        converted_params["aggregation_name"] = params[1]
        converted_params["credentials"] = ("configured", (params[2], params[3]))
        converted_params["optional"] = params[4]
        params = converted_params

    args = ["-b", params["base_url"], "-a", params["aggregation_name"]]

    if params["credentials"] == "automation":
        args.append("--use-automation-user")
    else:
        # configured
        args += [
            "-u",
            params["credentials"][1][0],
            "-s",
            passwordstore_get_cmdline("%s", params["credentials"][1][1]),
        ]

    opt_params = params["optional"]
    if "auth_mode" in opt_params:
        args += ["-m", opt_params["auth_mode"]]

    if "timeout" in opt_params:
        args += ["-t", opt_params["timeout"]]

    if opt_params.get("in_downtime"):
        args += ["--in-downtime", opt_params["in_downtime"]]

    if opt_params.get("acknowledged"):
        args += ["--acknowledged", opt_params["acknowledged"]]

    if opt_params.get("track_downtimes"):
        args += ["-r", "-n", "$HOSTNAME$"]

    return args


active_check_info["bi_aggr"] = {
    "command_line": "check_bi_aggr $ARG1$",
    "argument_function": check_bi_aggr_arguments,
    "service_description": lambda params: "Aggr %s" % params[1]
    if isinstance(params, tuple)
    else params["aggregation_name"],
    "has_perfdata": True,
}
