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
Moa utilities
"""

import os
import re
import sys
import shutil
import optparse
import moa.logger as l
import moa.info

def defineCommands(data):
    data['commands']['cp'] = {
        'desc' : 'Copy a moa job (only the configuration, not the data), '+
        'use moa cp DIR_FROM DIR_TO',
        'call' : moacp }
        
    data['commands']['kill'] = {
        'desc' : 'Kill a running moa job',
        'call' : moakill }

def moakill(data):
    """
    kill a running job
    """
    cwd = data['cwd']

    if not moa.info.status(cwd) == 'running': 
        l.warning("Moa does not seem to be running!")
        sys.exit(-1)

    pid = int(open(os.path.join(cwd, 'moa.runlock')).read())
    l.critical("killing job %d" % pid)
    os.kill(pid)

        
def moacp(data):
    """
    Copy a moa job - 
      0 create a new directory
      1 copy the configuration

    TODO: adapt file & dir links
    """
    wd = data['cwd']
    options = data['options']
    args = data['newargs']

    if len(args) > 1: dirto = args[1]
    else: dirto = '.'

    dirfrom = args[0]

    #remove trailing slash & determine basename
    if dirfrom[-1] == '/': dirfrom = dirfrom[:-1]
    fromBase = os.path.basename(dirfrom)

    # trick - the second argument is a number
    # renumber the target directory
    if re.match("^[0-9]+$", dirto):
        dirto = re.sub("^[0-9]*\.", dirto + '.', fromBase)
    
    if not os.path.exists(dirto):
        l.info("creating directory %s" % dirto)
        os.makedirs(dirto)
    else:
        dirto = os.path.join(dirto, fromBase)
        os.makedirs(dirto)

        
    l.info("Copying from %s to %s" % (dirfrom, dirto))

    for f in ['Makefile', 'moa.mk']:
        cfr = os.path.join(dirfrom, f)
        cto = os.path.join(dirto, f)

        l.info("copy %s to %s" % (cfr, cto))

        shutil.copyfile(cfr, cto)