import reframe as rfm
import reframe.utility.sanity as sn
from reframe.core.builtins import (
    parameter, performance_function, run_after, run_before, sanity_function
)


@rfm.simple_test
class StreamBenchmark(rfm.RegressionTest):
    descr = 'STREAM memory bandwidth benchmark'
    tags = {'production', 'performance', 'memory'}

    # 200M double-precision elements per array (~4.8 GB total working set)
    # comfortably exceeds any per-socket L3 cache on Apolo's nodes, keeping
    # the benchmark memory-bound rather than cache-bound.
    stream_array_size = parameter([200_000_000])

    valid_systems = ['apolo2:longjobs', 'apolo3:longjobs']
    valid_prog_environs = ['gnu']

    build_system = 'SingleSource'
    sourcesdir = 'src'
    sourcepath = 'stream.c'
    build_locally = False

    exclusive_access = True
    num_tasks = 1
    num_tasks_per_node = 1

    # Rough placeholders (MB/s), not calibrated against real runs yet.
    # Replace once the test has actually been run on each cluster and the
    # output reviewed.
    _triad_references = {
        'apolo2:longjobs': {
            200_000_000: 50_000,
        },
        'apolo3:longjobs': {
            200_000_000: 314_961,
        },
    }

    @run_after('init')
    def set_description(self):
        size_mb = 3 * 8 * self.stream_array_size / 1e6
        self.descr = (
            f'STREAM memory bandwidth benchmark '
            f'(array_size={self.stream_array_size:_}, '
            f'~{size_mb:.0f} MB working set)'
        )

    @run_before('compile')
    def set_compiler_flags(self):
        self.build_system.cflags = [
            '-O3',
            '-fopenmp',
            '-march=native',
            '-mcmodel=medium',
            f'-DSTREAM_ARRAY_SIZE={self.stream_array_size}',
            '-DNTIMES=20',
        ]

    @run_before('run')
    def configure_runtime(self):
        num_cpus = self.current_partition.processor.num_cpus
        self.num_cpus_per_task = num_cpus
        self.env_vars['OMP_NUM_THREADS'] = str(num_cpus)
        self.env_vars['OMP_PLACES'] = 'cores'
        self.env_vars['OMP_PROC_BIND'] = 'spread'

    @sanity_function
    def validate(self):
        return sn.assert_found(r'Solution Validates', self.stdout)

    @performance_function('MB/s')
    def triad_bw(self):
        return sn.extractsingle(r'Triad:\s+(\S+)', self.stdout, 1, float)

    @run_before('performance')
    def set_reference(self):
        partition = self.current_partition.fullname
        value = self._triad_references.get(partition, {}).get(
            self.stream_array_size
        )
        if value is not None:
            self.reference = {partition: {'triad_bw': (value, -0.15, 0.15, 'MB/s')}}
