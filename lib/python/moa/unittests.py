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
Unit tests
"""

import os
import sys
import doctest

from moa.logger import l, setSilent, setInfo, setVerbose

import moa.lock
import moa.api
import moa.info
import moa.conf
import moa.utils
import moa.job
import moa.project

MOABASE = os.environ['MOABASE']

failures = 0
tests = 0

templateFailures = 0
templateTests = 0

pluginFailures = 0
pluginTests = 0

TESTGLOB = {
    'MOABASE' : MOABASE,
    'P_TEST' : os.path.join(MOABASE, 'test', '00.base', '99.test'),
    'P_EMPTY' : os.path.join(MOABASE, 'test', '00.base', '00.empty'),
    'P_JOB' : os.path.join(MOABASE, 'test', '00.base', '10.moa.job'),
    'P_LOCKEDJOB' : os.path.join(MOABASE, 'test', '00.base', '20.moa.locked'),
    }

def testModule(m):
    global failures
    global tests
    f, t = doctest.testmod(m, extraglobs = TESTGLOB)
    failures += f
    tests += t
    
def testPlugins(args=[]):
    global pluginFailures
    global pluginTests
    testDir = os.path.join(MOABASE, 'test', '00.base', '99.test')    
        
    for plugin in moa.info.getPlugins(wd = testDir):
        if args and not plugin in args:
            continue
        l.debug("Starting a new plugin test")
        moa.utils.removeMoaFiles(testDir)
        moa.api.newJob(template = 'adhoc',
                       wd = testDir,
                       title='Testing plugin %s' % plugin)
        l.debug("start testing plugin %s" % plugin)
        rc = moa.runMake.go(wd=testDir,
                            target='moa_plugin_%s_test' % plugin,
                            background=False,
                            verbose=False,
                            captureOut=True,
                            captureErr=True,
                            makeArgs = [])
        pluginTests += 1
        if rc != 0:
            err = moa.api.getMoaErr(wd=testDir)
            print err
            if 'No rule to make target' in str(err):
                l.warning("No tests defined for plugin %s" % plugin)
            else:
                pluginFailures += 1
                l.error("Error running plugin test for %s (%s)" %
                        (plugin, rc))
                err = moa.api.getMoaErr(wd=testDir).strip()
                out = moa.api.getMoaOut(wd=testDir).strip()
                if err:
                    l.error("stderr:")
                    l.error(err)
                if out:
                    l.error("stdout:")
                    l.error(out)
        else:
            l.info("Success testing %s" % plugin)
                                     
        #result = moa.api.getMoaOut(wd=testDir).strip()
        #if result:
        #    print result

def testTemplates(which=None, verbose=False):
    global templateFailures
    global templateTests
    testDir = os.path.join(MOABASE, 'test', '00.base', '99.test')
    for template in moa.job.list():
        if which and template != which: continue
    
        l.debug("testing template %s" % template)
        templateTests  += 1
        
        moa.api.removeMoaFiles(testDir)
        moa.job.newJob(
            template = template,
            wd = testDir,
            title='Testing template %s' % template)
        
        rc = moa.runMake.go(wd=testDir,
                            target='template_test', 
                            background=False,
                            verbose = verbose,
                            makeArgs = [])
        if rc != 0:
            templateFailures += 1
            err = moa.api.getMoaErr(wd=testDir)
            l.error("Error running template test for template %s" % template)
            l.error(err)
                                     
        result = moa.api.getMoaOut(wd=testDir).strip()
        if result:
            print result

def testTemplateExtensive(template, verbose=False):
    dataDir = os.path.join(MOABASE, 'test', '10.data')
    os.putenv('MOADATA', dataDir)
    testDir = os.path.join(MOABASE, 'test', '00.base', '99.test')
    l.info("Cleaning %s" % testDir)
    moa.utils.removeFiles(testDir, recursive=True)
    l.info("Starting extensive template test for %s" % template)
    moa.api.newJob(template = template, wd=testDir,
                   title='Testing template %s' % template)
    rc = moa.api.runMoa(wd=testDir, target='%s_unittest' % template, 
                        background=False, verbose=True)    
    if verbose:
        out = moa.api.getMoaOut(wd=testDir)
        print out
    
    if rc == 0:
        l.info('Extensive test of "%s" was successfull' % template)
        return True
        
        
    err = moa.api.getMoaErr(wd=testDir)
    out = moa.api.getMoaOut(wd=testDir)

    l.error("Error running extensive template test for template %s" % template)
    l.error(out)
    l.error(err)
    
def run(options, args):

    os.putenv('MOA_UNITTESTS', "yes")
    if args:
        l.info("Testing '%s'" % " ".join(args))

    if not args:
        l.info("Start running python doctests")
        setSilent()        
        testModule(moa.utils)
        testModule(moa.lock)
        testModule(moa.api)
        testModule(moa.info)
        testModule(moa.conf)
        testModule(moa.job)
        testModule(moa.runMake)
        
        if options.verbose: setVerbose()
        else: setInfo()
        
        l.info("Finished running of python unittests")
        l.info("Ran %d test, %d failed" % (tests, failures))
        
        l.info("Start running basic template tests")
        testTemplates()
        l.info("Ran %d template test, %d failed" % (
                templateTests, templateFailures))

        l.info("Start running plugin tests")
        testPlugins()
        l.info("Ran %d plugin test, %d failed" % (
                pluginTests, pluginFailures))
        l.info("Finished running plugin tests")
        sys.exit()

    elif args[0] == 'plugins':
        l.info("Start running plugin tests")
        testPlugins(args[1:])
        l.info("Ran %d plugin test, %d failed" % (
                pluginTests, pluginFailures))
        l.info("Finished running plugin tests")
    elif args[0] == 'plugin':
        l.info("Start running plugin tests")
        testPlugins(args[1:])
    elif args[0] == 'templates':
        l.info("Start running basic template tests")
        testTemplates()
        l.info("Ran %d template test, %d failed" % (
            templateTests, templateFailures))
        l.info("Finished running basic template tests")
    elif args[0][:4] == 'moa.':            
        l.info("testing moa python module %s" % args[0])
        setSilent()
        eval("testModule(%s)" % args[0])
        if options.verbose: setVerbose()
        else: setInfo()
        l.info("Finished running unittests for %s" % args[0])
        l.info("Ran %d test, %d failed" % (tests, failures))
    else:
        #Assume it is a templat
        testTemplates(args[0], verbose=options.verbose)
        testTemplateExtensive(args[0], verbose=options.verbose)

        
    
