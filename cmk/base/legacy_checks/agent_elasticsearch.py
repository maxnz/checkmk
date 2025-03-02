#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# {
#     'port': 443,
#     'password': 'baem',
#     'infos': ['cluster_health', 'nodestats', 'stats'],
#     'user': 'blub'
# }


from typing import Any, Mapping, Optional, Sequence, Union

from cmk.base.check_api import passwordstore_get_cmdline
from cmk.base.config import special_agent_info


def agent_elasticsearch_arguments(
    params: Mapping[str, Any], hostname: str, ipaddress: Optional[str]
) -> Sequence[Union[str, tuple[str, str, str]]]:
    args = ["-P", params["protocol"], "-m", *params["infos"]]

    if "user" in params:
        args += ["-u", params["user"]]
    if "password" in params:
        args += ["-s", passwordstore_get_cmdline("%s", params["password"])]
    if "port" in params:
        args += ["-p", str(params["port"])]  # non-str gets ignored silently
    if params.get("no-cert-check", False):
        args += ["--no-cert-check"]

    args += params["hosts"]

    return args


special_agent_info["elasticsearch"] = agent_elasticsearch_arguments
