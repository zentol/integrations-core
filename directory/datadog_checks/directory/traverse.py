# (C) Datadog, Inc. 2018-present
# All rights reserved
# Licensed under a 3-clause BSD style license (see LICENSE)
import platform
import sys

import six
from scandir import scandir


def _walk(top, follow_symlinks):
    """Modified version of https://docs.python.org/3/library/os.html#os.scandir
    that returns https://docs.python.org/3/library/os.html#os.DirEntry for files
    directly to take advantage of possible cached os.stat calls.
    """
    dirs = []
    nondirs = []

    scandir_iter = scandir(top)

    # Avoid repeated global lookups.
    get_next = next

    while True:
        try:
            entry = get_next(scandir_iter)
        except StopIteration:
            break

        try:
            is_dir = entry.is_dir(follow_symlinks=follow_symlinks)
        except OSError:
            is_dir = False

        if is_dir:
            dirs.append(entry)
        else:
            nondirs.append(entry)

    yield top, dirs, nondirs

    for dir_entry in dirs:
        for entry in walk(dir_entry.path, follow_symlinks=follow_symlinks):
            yield entry


if six.PY3 or platform.system() != 'Windows':
    walk = _walk
else:
    # Fix for broken unicode handling on Windows on Python 2.x, see:
    # https://github.com/benhoyt/scandir/issues/54
    file_system_encoding = sys.getfilesystemencoding()

    def walk(top, follow_symlinks):
        if isinstance(top, bytes):
            top = top.decode(file_system_encoding)
        return _walk(top, follow_symlinks)
