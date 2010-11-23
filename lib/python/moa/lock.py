#!/usr/bin/env python
# 
# Copyright 2009 Mark Fiers, Plant & Food Research
# 
# This file is part of Moa - http://github.com/mfiers/Moa
# 
# Moa is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your
# option) any later version.
# 
# Moa is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
# or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public
# License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Moa.  If not, see <http://www.gnu.org/licenses/>.
# 
"""
Job locking utilities
"""

import os
from moa.exceptions import *

def lockJob(d):
    """
    Lock a moa directory

        >>> import moa.job
        >>> jobdir = moa.job.newTestJob('traverse')
        >>> lockJob(jobdir)
        >>> os.path.exists(os.path.join(jobdir, 'lock'))
        True
        >>> unlockJob(jobdir)
        >>> os.path.exists(os.path.join(jobdir, 'lock'))
        False
    """
    if not moa.info.isMoaDir(d):
        raise NotAMoaDirectory(d)

    lockFile = os.path.join(d, 'lock')
    
    if os.path.exists(lockFile):
        return True
    
    if not os.access(d, os.W_OK):
        raise MoaPermissionDenied(wd)

    with file(lockFile, 'a'):
        os.utime(lockFile, None)

def unlockJob(d):
    """
    Unlock a moa directory

        >>> import tempfile
        >>> import moa.job
        >>> emptyDir = tempfile.mkdtemp()
        >>> jobdir = moa.job.newTestJob('traverse')
        >>> lockJob(jobdir)
        >>> unlockJob(jobdir)
        >>> os.path.exists(os.path.join(jobdir, 'lock'))
        False
        >>> try:
        ...     unlockJob(emptyDir)
        ...     False
        ... except NotAMoaDirectory: True
        ... except: False
        True
        
    """
    if not moa.info.isMoaDir(d):
        raise NotAMoaDirectory(d)

    lockfile = os.path.join(d, 'lock')
    if not os.path.exists(lockfile):
        return True

    if not os.access(lockfile, os.W_OK):
        raise MoaPermissionDenied(d)
    
    os.unlink(lockfile)
