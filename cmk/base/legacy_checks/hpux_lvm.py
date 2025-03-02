#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.

# <<<hpux_lvm:sep(58)>>>
# vg_name=/dev/vg00:vg_write_access=read,write:vg_status=available:max_lv=255:\
# cur_lv=8:open_lv=8:max_pv=16:cur_pv=4:act_pv=4:max_pe_per_pv=4384:vgda=8:pe_size=16:to
# tal_pe=17388:alloc_pe=13920:free_pe=3468:total_pvg=0:total_spare_pvs=0:total_spare_pvs_in_use=0:vg_version=1.0.0
# lv_name=/dev/vg00/lvol1:lv_status=available,syncd:lv_size=1792:current_le=112:allocated_pe=224:used_pv=2
# lv_name=/dev/vg00/lvol2:lv_status=available,syncd:lv_size=32768:current_le=2048:allocated_pe=4096:used_pv=2
# lv_name=/dev/vg00/lvol3:lv_status=available,syncd:lv_size=2048:current_le=128:allocated_pe=256:used_pv=2
# lv_name=/dev/vg00/lvol4:lv_status=available,syncd:lv_size=32768:current_le=2048:allocated_pe=4096:used_pv=2
# lv_name=/dev/vg00/lvol5:lv_status=available,syncd:lv_size=12288:current_le=768:allocated_pe=1536:used_pv=2
# lv_name=/dev/vg00/lvol6:lv_status=available,syncd:lv_size=5120:current_le=320:allocated_pe=640:used_pv=2
# lv_name=/dev/vg00/lvol7:lv_status=available,syncd:lv_size=12288:current_le=768:allocated_pe=1536:used_pv=2
# lv_name=/dev/vg00/lvol8:lv_status=available,syncd:lv_size=12288:current_le=768:allocated_pe=1536:used_pv=3
# pv_name=/dev/disk/disk7_p2:pv_status=available:total_pe=4319:free_pe=0:autoswitch=On:proactive_polling=On
# pv_name=/dev/disk/disk9:pv_status=available:total_pe=4375:free_pe=1734:autoswitch=On:proactive_polling=On
# pv_name=/dev/disk/disk11_p2:pv_status=available:total_pe=4319:free_pe=175:autoswitch=On:proactive_polling=On
# pv_name=/dev/disk/disk10:pv_status=available:total_pe=4375:free_pe=1559:autoswitch=On:proactive_polling=On


from cmk.base.check_api import LegacyCheckDefinition
from cmk.base.config import check_info


def inventory_hpux_lvm(info):
    inventory = []
    for line in info:
        if line[0].startswith("lv_name="):
            lv_name = line[0].split("=")[1]
            inventory.append((lv_name, None))
    return inventory


def check_hpux_lvm(item, params, info):
    for line in info:
        if line[0].startswith("vg_name"):
            vg_name = line[0].split("=")[1]
        elif line[0].startswith("lv_name"):
            lv_name = line[0].split("=")[1]
            if lv_name == item:
                status = line[1].split("=")[1]
                infotext = "status is %s (VG = %s)" % (status, vg_name)
                if status == "available,syncd":
                    return (0, infotext)
                return (2, infotext)

    return (3, "no such volume found")


check_info["hpux_lvm"] = LegacyCheckDefinition(
    service_name="Logical Volume %s",
    discovery_function=inventory_hpux_lvm,
    check_function=check_hpux_lvm,
)
