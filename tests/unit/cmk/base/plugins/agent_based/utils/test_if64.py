#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

from cmk.base.plugins.agent_based.utils import interfaces
from cmk.base.plugins.agent_based.utils.if64 import generic_parse_if64


def test_generic_parse_if64() -> None:
    assert generic_parse_if64(
        [
            [
                "2",
                "GigabitEthernet1/1",
                "6",
                "1000000000",
                "1",
                "615170130480",
                "468482397",
                "1439303",
                "3279788",
                "0",
                "0",
                "163344362761",
                "394389414",
                "54227",
                "36274",
                "0",
                "0",
                "0",
                "** Trunk to main switch **",
                [0, 12, 206, 149, 55, 128],
            ],
            [
                "3",
                "Primary Internet connection\\nVLAN 10\\nContact data ISP:\\n",
                "6",
                "1000000000",
                "1",
                "44357143434",
                "57785953",
                "3644158",
                "0",
                "0",
                "0",
                "43529803172",
                "51011741",
                "0",
                "0",
                "0",
                "0",
                "0",
                "",
                [220, 166, 50, 183, 252, 79],
            ],
        ]
    ) == [
        interfaces.InterfaceWithCounters(
            interfaces.Attributes(
                index="2",
                descr="GigabitEthernet1/1",
                alias="** Trunk to main switch **",
                type="6",
                speed=1000000000,
                oper_status="1",
                out_qlen=0,
                phys_address=[0, 12, 206, 149, 55, 128],
                oper_status_name="up",
            ),
            interfaces.Counters(
                in_octets=615170130480,
                in_ucast=468482397,
                in_mcast=1439303,
                in_bcast=3279788,
                in_disc=0,
                in_err=0,
                out_octets=163344362761,
                out_ucast=394389414,
                out_mcast=54227,
                out_bcast=36274,
                out_disc=0,
                out_err=0,
            ),
        ),
        interfaces.InterfaceWithCounters(
            interfaces.Attributes(
                index="3",
                descr="Primary Internet connection\\nVLAN 10\\nContact data ISP:\\n",
                alias="",
                type="6",
                speed=1000000000,
                oper_status="1",
                out_qlen=0,
                phys_address=[220, 166, 50, 183, 252, 79],
                oper_status_name="up",
            ),
            interfaces.Counters(
                in_octets=44357143434,
                in_ucast=57785953,
                in_mcast=3644158,
                in_bcast=0,
                in_disc=0,
                in_err=0,
                out_octets=43529803172,
                out_ucast=51011741,
                out_mcast=0,
                out_bcast=0,
                out_disc=0,
                out_err=0,
            ),
        ),
    ]
