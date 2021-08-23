
import os
import math
import sys
import time

from os.path import abspath, basename, join
from subprocess import check_output
from seisflows.tools import msg
from seisflows.tools import unix
from seisflows.tools.tools import call, findpath, saveobj, timestamp
from seisflows.config import ParameterError, custom_import

PAR = sys.modules['seisflows_parameters']
PATH = sys.modules['seisflows_paths']


class localmpi(custom_import('system', 'serial')):
    """ An interface through which to submit workflows, run tasks in serial or 
      parallel, and perform other system functions.

      By hiding environment details behind a python interface layer, these 
      classes provide a consistent command set across different computing
      environments.

      Intermediate files are written to a global scratch path PATH.SCRATCH,
      which must be accessible to all compute nodes.

      Optionally, users can provide a local scratch path PATH.LOCAL if each
      compute node has its own local filesystem.

      For important additional information, please see 
      http://seisflows.readthedocs.org/en/latest/manual/manual.html#system-configuration
    """

    def check(self):
        """ Checks parameters and paths
        """
        # name of job
        if 'TITLE' not in PAR:
            setattr(PAR, 'TITLE', basename(abspath('.')))

        # time allocated for workflow in minutes
        if 'WALLTIME' not in PAR:
            setattr(PAR, 'WALLTIME', 30.)

        # time allocated for each individual task in minutes
        if 'TASKTIME' not in PAR:
            setattr(PAR, 'TASKTIME', 15.)

        # number of tasks
        if 'NTASK' not in PAR:
            raise ParameterError(PAR, 'NTASK')

        # number of cores per task
        if 'NPROC' not in PAR:
            raise ParameterError(PAR, 'NPROC')

        # limit on number of concurrent tasks
        if 'NTASKMAX' not in PAR:
            setattr(PAR, 'NTASKMAX', PAR.NTASK)

        # number of cores per node
        if 'NODESIZE' not in PAR:
            raise ParameterError(PAR, 'NODESIZE')

        # how to invoke executables
        if 'MPIEXEC' not in PAR:
            setattr(PAR, 'MPIEXEC', 'mpirun')

 

    def run(self, classname, method, *args, **kwargs):
        """ Executes task multiple times in serial
        """
        unix.mkdir(PATH.SYSTEM)

        for taskid in range(PAR.NTASK):
            os.environ['SEISFLOWS_TASKID'] = str(taskid)
            if PAR.VERBOSE > 0:
                self.progress(taskid)
            func = getattr(__import__('seisflows_'+classname), method)
            func(**kwargs)
        print ''


    def run_single(self, classname, method, *args, **kwargs):
        """ Runs task a single time
        """
        os.environ['SEISFLOWS_TASKID'] = str(0)
        func = getattr(__import__('seisflows_'+classname), method)
        func(**kwargs)



    def taskid(self):
        """ Provides a unique identifier for each running task
        """
        return int(os.environ['SEISFLOWS_TASKID'])

    def mpiexec(self):
        """ Specifies MPI executable used to invoke solver
        """
        return PAR.MPIEXEC


    def progress(self, taskid):
        """ Provides status update
        """
        if PAR.NTASK > 1:
            print ' task ' + '%02d of %02d' % (taskid+1, PAR.NTASK)