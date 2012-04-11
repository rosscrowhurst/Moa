# Copyright 2009-2011 Mark Fiers
# The New Zealand Institute for Plant & Food Research
# 
# This file is part of Moa - http://github.com/mfiers/Moa
# 
# Licensed under the GPL license (see 'COPYING')
# 
"""
**sgeActor** - Run jobs through SGE
-----------------------------------------------------------

"""
import os
import sys
import time
import optparse
import subprocess as sp

from moa.sysConf import sysConf
import moa.logger as l
import moa.ui

def hook_defineCommandOptions(job, parser):
    parser.add_argument( '--ol', action='store_const', const='openlava',
                               dest='actorId', help='Use OpenLava as actor' )

def openlavaRunner(wd, cl, conf={}, **kwargs):
    """
    Run the job using OPENLAVA

    what does this function do?
    - put env in the environment
    - Execute the commandline (in cl)
    - store stdout & stderr in log files
    - return the rc
    """

    #see if we can get a command
    command = kwargs.get('command', 'unknown')
    if command == 'unknown':
        l.error("runner should be called with a command")

    outDir = os.path.join(wd, '.moa', 'log.latest')
    if not os.path.exists(outDir):
        try:
            os.makedirs(outDir)
        except OSError:
            pass

    #expect the cl to be nothing more than a single script to execute
    outfile = os.path.join(outDir, 'stdout')
    errfile = os.path.join(outDir, 'stderr')

    sc = []
    def s(*cl):
        sc.append(" ".join(map(str, cl)))

    s("#!/bin/bash")
    s("cd", wd)
    s("#BSUB -o", outfile)
    s("#BSUB -e", errfile)


    lastJids = []
    #if len(sysConf.job.data.openlava.get('jidlist', [])) > 1:
    #    lastJids = sysConf.job.data.openlava.get('jidlist')[-1]
    

    #if command == 'run':
    #    prep_jids = sysConf.job.data.openlava.jids.get('prepare', [])
        #hold until the 'prepare' jobs are done
        #if prep_jids: 
        #    qcl.append("-w '")
        #    qcl.append('&&'.join(['exit(%s)' % x for x in prep_jids])

    #elif command == 'finish':
    #    run_jids = sysConf.job.data.openlava.jids.get('run', [])
        #hold until the 'prepare' jobs are done
        #if run_jids: 
        #    qcl.append('-hold_jid')
        #    qcl.append(','.join(map(str, run_jids)))

    #give it a reasonable name
    #if conf.get('runid', None):
    #    qcl.append('-N')
    #    qcl.append(str(conf['runid']))

    # make sure the environment is copied
    #qcl.append('-V')
    #qcl.extend(cl)

    #print " ".join(qcl)
    #dump the configuration in the environment
    s("")
    s("## Defining moa specific environment variables")
    s("")
      
    for k in conf:
        # to prevent collusion, prepend all env variables
        # with 'moa_'
        if k[0] == '_' or k[:3] == 'moa':
            outk = k
        else:
            outk = 'moa_' + k
        v = conf[k]
        if isinstance(v, list):
            s("%s='%s'" % (outk, " ".join(v)))
        elif isinstance(v, dict):
            continue
        else:
            s("%s='%s'" % (outk, v))
         
    s("")
    s("## Run the command")
    s("")
    s(*(['/bin/bash'] + cl))

    l.debug("executing bsub")
    moa.ui.message("Submitting job to openlava")
    p = sp.Popen('bsub', cwd = wd, stdout=sp.PIPE, stdin=sp.PIPE)
    o,e = p.communicate("\n".join(sc))
    jid = int(o.strip().split()[2])
    sysConf.actor.openlava.jids.append(jid)
    moa.ui.message("submitted job with openlava job id %s " % jid)

    #store the job id submitted
    if not sysConf.job.data.openlava.jids.has_key(command):
            sysConf.job.data.openlava.jids[command] = []
    sysConf.job.data.openlava.jids[command].append(jid)
    return p.returncode

def hook_postRun():
    """
    Need to exit here, and reconvene once all jobs have executed
    """
    #print sysConf.actor.openlava.jids

#ergister this actor globally
sysConf.actor.actors['openlava'] = openlavaRunner
sysConf.actor.openlava.jids = []