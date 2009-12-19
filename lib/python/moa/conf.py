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
Moa script - moa.mk configuration related code
"""

import re
import os
import sys

import moa.logger
from moa.logger import exitError
import moa.utils
import moa.info
from moa.exceptions import *

l = moa.logger.l

def handler(options, args):
    """
    parse the command line and save the arguments into moa.mk
    """
    cwd = os.getcwd()    
    commandLineHandler(cwd, args)

def parseClArgs(args):
    """
    Parse the arguments defined on a commandline.

    :Parameters:
      args
        command line arguments, as passed on by sys.argv or
        optparse. It is expected to be a list of strings of the
        following format; 'param=value' or 'param+=value' No spaces
        are allowed between the parameter name, value and operator.

        >>> r = parseClArgs(['aap=1', 'noot=2', 'noot=3',
        ...                  'mies=test', 'mies+=roos'])
        >>> type(r) == type([])
        True
        >>> type(r[0]) == type({})
        True
        >>> r[0]['key'] == 'aap'
        True
        >>> r[1]['operator'] == '='
        True
        >>> r[2]['value'] == '3'
        True
        >>> r[4]['operator'] == '+='
        True
        >>> len(r) == 5
        True
        
    """
    rv = []
    for a in args:
        if not '=' in a:
            l.error("Invalid key/value pair %s" % a)
        if '+=' in a:
            k, v = [x.strip() for x in a.split('+=', 1)]
            o = '+='
        else:
            o = '='
            k, v = [x.strip() for x in a.split('=', 1)]
            
        rv.append({ 'key' : k,
                    'operator' : o,
                    'value' : v })
    return rv
    
def commandLineHandler(wd, args):
    l.debug("start parsing the commandline")
    #parse all arguments
    data = parseClArgs(args)
    writeToConf(wd, data)


def setVar(wd, key, value):
    """
    Convenience function - set the variable 'key' to a value in directory wd

        >>> import random
        >>> testTitle = 'title %d' % random.randint(0,10000)
        >>> setVar(TESTPATH, 'title', testTitle)
        >>> title = getVar(TESTPATH, 'title')
        >>> title == testTitle
        True
        >>> try: setVar(NOTMOADIR, 'title', 'test setvar in a non-moa dir')
        ... except NotAMoaDirectory:
        ...   'Fine'
        'Fine'


    """    
    writeToConf(wd, [{'key' : key,
                  'operator' : '=',
                  'value' : value}])

def appendVar(wd, key, value):
    """
    Convenience function - set the variable 'key' to a value in directory wd
    
        >>> setVar(TESTPATH, 'title', 'one')
        >>> getVar(TESTPATH, 'title')
        'one'
        >>> appendVar(TESTPATH, 'title', 'two')
        >>> appendVar(TESTPATH, 'title', 'three')
        >>> getVar(TESTPATH, 'title')
        'one two three'
        >>> try: appendVar(NOTMOADIR, 'title', 'test setvar in a non-moa dir')
        ... except NotAMoaDirectory:
        ...   'Fine'
        'Fine'

    """    
    writeToConf(wd, [{'key' : key,
                      'operator' : '+=',
                      'value' : value}])


def getVar(wd, key):
    """
    Get a single parameter from a moa directory

        >>> setVar(TESTPATH, 'title', 'test getVar')
        >>> getVar(TESTPATH, 'title')
        'test getVar'
    """    
    if not os.path.exists(wd):
        return False
    moamk = os.path.join(wd, 'moa.mk')
    if not os.path.exists(moamk):
        return False
    F = open(moamk, 'r')

    rv = []
    for line in F.readlines():
        line = line.strip()
        if not line: continue        
        if line.find(key) == 0:            
            #this also captures '+=' moa.mk lines!
            if '=' in line:
                value = line.split('=',1)[1]
                rv.append(value)
    F.close()
    return " ".join(rv)    
    
def writeToConf(wd, data):
    """
    writeToConf - actually write something to moa.mk
    
    """

    if not moa.info.isMoaDir(wd):
        raise NotAMoaDirectory(wd)

    
    moamk = os.path.join(wd, 'moa.mk')
    moamktmp = os.path.join(wd, 'moa.mk.tmp')
    moamklock = os.path.join(wd, 'moa.mk.lock')

    
    
    #refd is a refactoring of data - allows easy checking
    refd = dict([(x['key'],x) for x in data])
    l.debug("Changing variable: %s" % ", ".join(refd.keys()))
    l.debug("starting to write a new moa.mk in %s" % wd)

    #get a lock on moa.mk
    with moa.utils.flock(moamklock):
        l.debug("got a lock on moa.mk in %s" % wd)
        if os.path.exists(moamktmp):
            l.debug("removing an older?? moa.mk.tmp")
            os.unlink(moamktmp)

        #move moa.mk to a new location
        if os.path.exists(moamk):
            os.rename(moamk, moamktmp)
        else:
            #create an empty dummy file
            open(moamktmp, 'w').close()
        
        #open filehandles to both files:
        F = open(moamktmp, 'r')
        G = open(moamk, 'w')
        
        #parse through the old file
        for line in F.readlines():
            k,o,v = re.split(r'\s*(\+?=)\s*', line.strip())
            l.debug("read %s %s %s" % (k,o,v))
            if refd.get(k, {}).get('operator') == '=':
                #do not rewrite this line - it is being replaced
                l.debug("ignoring %s" % k)
            else:
                #if the mode is not 'set', write 
                G.write(line)
                
        for v in data:
            if v['value']:
                G.write("%(key)s%(operator)s%(value)s\n" % v)
                l.info("%(key)s%(operator)s%(value)s\n" % v)
            else:
                l.info("removing %s" % k)

        F.close()
        G.close()
        os.unlink(moamktmp)
    
