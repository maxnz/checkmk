#!/usr/bin/env python3
# Copyright (C) 2019 Checkmk GmbH - License: GNU General Public License v2
# This file is part of Checkmk (https://checkmk.com). It is subject to the terms and
# conditions defined in the file COPYING, which is part of this source code package.
"""This is an unsorted collection of small unrelated helper functions which are
usable in all components of Check_MK

Please try to find a better place for the things you want to put here."""

import itertools
import sys
import time
from collections.abc import Callable, Iterator, Mapping, MutableMapping
from pathlib import Path
from typing import Any


# TODO: Change to better name like: quote_pnp_string()
def pnp_cleanup(s: str) -> str:
    """Quote a string (host name or service description) in PNP4Nagios format

    Because it is used as path element, this needs to be handled as "str" in Python 2 and 3
    """
    return s.replace(" ", "_").replace(":", "_").replace("/", "_").replace("\\", "_")


def key_config_paths(a: Path) -> tuple[tuple[str, ...], int, tuple[str, ...]]:
    """Key function for Check_MK configuration file paths

    Helper functions that determines the sort order of the
    configuration files. The following two rules are implemented:

    1. *.mk files in the same directory will be read
       according to their lexical order.
    2. subdirectories in the same directory will be
       scanned according to their lexical order.
    3. subdirectories of a directory will always be read *after*
       the *.mk files in that directory.
    """
    pa = a.parts
    return pa[:-1], len(pa), pa


def total_size(
    o: Any, handlers: dict[type[Any], Callable[[Any], Iterator[object]]] | None = None
) -> int:
    """Returns the approximate memory footprint an object and all of its contents.

    Automatically finds the contents of the following builtin containers and
    their subclasses:  tuple, list, dict, set and frozenset.
    To search other containers, add handlers to iterate over their contents:

        handlers = {SomeContainerClass: iter,
                    OtherContainerClass: OtherContainerClass.get_elements}

    """
    if handlers is None:
        handlers = {}

    all_handlers: dict[type[Any], Callable[[Any], Iterator[object]]] = {
        tuple: iter,
        list: iter,
        dict: lambda d: itertools.chain.from_iterable(d.items()),
        set: iter,
        frozenset: iter,
    }
    all_handlers.update(handlers)  # user handlers take precedence
    seen: set[int] = set()
    default_size = sys.getsizeof(0)  # estimate sizeof object without __sizeof__

    def sizeof(o: Any) -> int:
        if id(o) in seen:  # do not double count the same object
            return 0
        seen.add(id(o))
        s = sys.getsizeof(o, default_size)

        for typ, handler in all_handlers.items():
            if isinstance(o, typ):
                s += sum(map(sizeof, handler(o)))
                break
        return s

    return sizeof(o)


def cachefile_age(path: Path | str) -> float:
    """Return the time difference between the last modification and now.

    Raises:
        FileNotFoundError if `path` does not exist.

    """
    if not isinstance(path, Path):
        path = Path(path)

    return time.time() - path.stat().st_mtime


def typeshed_issue_7724(x: Mapping[str, str] | None) -> MutableMapping[str, str] | None:
    """Temporary workaround for https://github.com/python/typeshed/issues/7724
    TODO: Remove this when the issue a above is fixed!"""
    return None if x is None else dict(x)
