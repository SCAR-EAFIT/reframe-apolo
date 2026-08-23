import math
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

    hpl_dir = variable(str, value='/home/scar-test/reframe/reframe-apolo/rfm/bin/hpl/hpl-2.3/Linux_Intel64')

    # HPL.dat problem parameters. P and Q are NOT listed here: they are
    # derived from num_tasks at runtime (P * Q must equal the number of
    # MPI ranks or xhpl aborts), so they always match the actual resources.
    problem_size = variable(int, value=20000)
    block_size = variable(int, value=256)

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
            'module use /opt/ohpc/pub/moduledeps/oneapi',
            'module load hpc_toolkit',
            f'export OMP_NUM_THREADS={self.num_cpus_per_task}',
            f'export MKL_NUM_THREADS={self.num_cpus_per_task}',
            'export I_MPI_PIN=1',
            'export I_MPI_PIN_DOMAIN=socket',
            'export OMP_PLACES=cores',
            'export OMP_PROC_BIND=close',
            'export KMP_AFFINITY=granularity=fine,compact,1,0',
        ]

    @staticmethod
    def _process_grid(num_tasks):
        '''Split num_tasks into a (P, Q) grid, P <= Q, as square as possible.'''
        p = int(math.isqrt(num_tasks))
        while p > 1 and num_tasks % p != 0:
            p -= 1
        return p, num_tasks // p

    @run_before('run')
    def write_hpl_dat(self):
        p, q = self._process_grid(self.num_tasks)
        dat_path = os.path.join(self.stagedir, 'HPL.dat')
        with open(dat_path, 'w') as fp:
            fp.write(f'''HPLinpack benchmark input file
Innovative Computing Laboratory, University of Tennessee
HPL.out      output file name (if any)
6            device out (6=stdout,7=stderr,file)
1            # of problems sizes (N)
{self.problem_size}          Ns
1            # of NBs
{self.block_size}           NBs
0            PMAP process mapping (0=Row-,1=Column-major)
1            # of process grids (P x Q)
{p}            Ps
{q}            Qs
16.0         threshold
1            # of panel fact
2            PFACTs (0=left, 1=Crout, 2=Right)
1            # of recursive stopping criterium
4            NBMINs (>= 1)
1            # of panels in recursion
2            NDIVs
1            # of recursive panel fact.
1            RFACTs (0=left, 1=Crout, 2=Right)
1            # of broadcast
1            BCASTs (0=1rg,1=1rM,2=2rg,3=2rM,4=Lng,5=LnM)
1            # of lookahead depth
1            DEPTHs (>=0)
2            SWAP (0=bin-exch,1=long,2=mix)
64           swapping threshold
0            L1 in (0=transposed,1=no-transposed) form
0            U  in (0=transposed,1=no-transposed) form
1            Equilibration (0=no,1=yes)
8            memory alignment in double (> 0)
##### This line (no. 32) is ignored (it serves as a separator). ######
0                               Number of additional problem sizes for PTRANS
1200 10000 30000                values of N
0                               number of additional blocking sizes for PTRANS
40 9 8 13 13 20 16 32 64        values of NB
''')

    @sanity_function
    def assert_hpl_passed(self):
        return sn.assert_found(r'PASSED', self.stdout)

    @performance_function('Gflops')
    def hpl_gflops(self):
        return sn.extractsingle(
            r'WR\S+\s+\d+\s+\d+\s+\d+\s+\d+\s+[\d.]+\s+(?P<gflops>\S+)',
            self.stdout,
            'gflops',
            float,
        )