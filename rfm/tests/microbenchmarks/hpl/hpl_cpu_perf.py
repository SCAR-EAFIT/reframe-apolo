import os
import sys

import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import performance_function, run_before, run_after, sanity_function, variable
from reframe.core.backends import getlauncher

@rfm.simple_test
class HplCpuPerformanceTest(rfm.RunOnlyRegressionTest):
    descr = 'HPL CPU benchmark on a single node (pre-compiled binary)'

    valid_systems = ['apolo3:longjobs', 'apolo3:bigmem']
    valid_prog_environs = ['intel']

    hpl_dir = variable(str, value='/home/scar-test/SCC26/HPL/hpl-2.3/bin/Linux_Intel64')

    num_nodes = 1
    num_cpus_per_task = 16
    time_limit = '2h'
    exclusive_access = True
    
    @run_after('setup')
    def set_executable_and_prerun(self):
        num_cpus = self.current_partition.processor.num_cpus
        self.num_tasks = num_cpus // self.num_cpus_per_task
        self.num_tasks_per_node = self.num_tasks
        self.executable = f'{self.hpl_dir}/xhpl'

        self.prerun_cmds = [
            'source /etc/profile',
            f'export OMP_NUM_THREADS={self.num_cpus_per_task}',
            'export KMP_AFFINITY=granularity=fine,compact,1,0',
            f'cp {self.hpl_dir}/HPL.dat .',
        ]
        


    @run_before('run')
    def load_modules(self):
        self.modules = ['hpc_toolkit']  

    @sanity_function
    def assert_hpl_passed(self):
        return sn.assert_found(r'PASSED', self.stderr)

    @performance_function('Gflops')
    def hpl_gflops(self):
        return sn.extractsingle(
            r'WR\S+\s+\d+\s+\d+\s+\d+\s+\d+\s+[\d.]+\s+(?P<gflops>\S+)',
            self.stderr,
            'gflops',
            float,
        )