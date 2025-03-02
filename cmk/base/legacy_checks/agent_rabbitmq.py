#!/usr/bin/env python3
# +------------------------------------------------------------------+
# |             ____ _               _        __  __ _  __           |
# |            / ___| |__   ___  ___| | __   |  \/  | |/ /           |
# |           | |   | '_ \ / _ \/ __| |/ /   | |\/| | ' /            |
# |           | |___| | | |  __/ (__|   <    | |  | | . \            |
# |            \____|_| |_|\___|\___|_|\_\___|_|  |_|_|\_\           |
# |                                                                  |
# | Copyright Mathias Kettner 2020             mk@mathias-kettner.de |
# +------------------------------------------------------------------+
#
# This file is part of Checkmk.
# The official homepage is at http://mathias-kettner.de/check_mk.
#
# check_mk is free software;  you can redistribute it and/or modify it
# under the  terms of the  GNU General Public License  as published by
# the Free Software Foundation in version 2.  check_mk is  distributed
# in the hope that it will be useful, but WITHOUT ANY WARRANTY;  with-
# out even the implied warranty of  MERCHANTABILITY  or  FITNESS FOR A
# PARTICULAR PURPOSE. See the  GNU General Public License for more de-
# tails. You should have  received  a copy of the  GNU  General Public
# License along with GNU Make; see the file  COPYING.  If  not,  write
# to the Free Software Foundation, Inc., 51 Franklin St,  Fifth Floor,
# Boston, MA 02110-1301 USA.

# {
#     'port': 443,
#     'password': 'comein',
#     'infos': ['license_state'],
#     'user': 'itsme'
# }


from typing import Any, Mapping, Optional, Sequence, Union

from cmk.base.check_api import passwordstore_get_cmdline
from cmk.base.config import special_agent_info


def agent_rabbitmq_arguments(
    params: Mapping[str, Any], hostname: str, ipaddress: Optional[str]
) -> Sequence[Union[str, tuple[str, str, str]]]:
    args = [
        "-P",
        params["protocol"],
        "-m",
        ",".join(params["sections"]),
        "-u",
        params["user"],
        "-s",
        passwordstore_get_cmdline("%s", params["password"]),
    ]

    if "port" in params:
        args += ["-p", params["port"]]

    if "instance" in params:
        hostname = params["instance"]

    args += [
        "--hostname",
        hostname,
    ]

    return args


special_agent_info["rabbitmq"] = agent_rabbitmq_arguments
