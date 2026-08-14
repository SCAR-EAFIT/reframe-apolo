site_configuration = {
    'systems': [
        {
            'name': 'apolo2',
            'descr': 'Apolo-2 Cluster',
            'hostnames': ['apolo', 'apolo.eafit.edu.co'],
            'modules_system': 'lmod',
            'partitions': [
                {
                    'name': 'bigmem',
                    'descr': 'High Memory Nodes',
                    'access': ['--partition=bigmem'],
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 10,
                    'processor': {
                        'num_cpus': 24,
                        'num_cpus_per_socket': 12,
                        'num_sockets': 2,
                        'num_cpus_per_core': 1,
                    },
                    'extras': {'cn_memory': 377},
                },
                {
                    'name': 'longjobs',
                    'descr': 'Standard CPU Nodes',
                    'access': ['--partition=longjobs', '--exclude=compute-0-35,compute-0-38'],
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 10,
                    'processor': {
                        'num_cpus': 32,
                        'num_cpus_per_socket': 16,
                        'num_sockets': 2,
                        'num_cpus_per_core': 1,
                    },
                    'extras': {'cn_memory': 62},
                },
                {
                    'name': 'accel',
                    'descr': 'GPU Accelerated Nodes',
                    'access': ['--partition=accel'],
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 10,
                    'processor': {
                        'num_cpus': 32,
                        'num_cpus_per_socket': 16,
                        'num_sockets': 2,
                        'num_cpus_per_core': 1,
                    },
                    'devices': [{'type': 'gpu', 'num_devices': 4}],
                    'extras': {'cn_memory': 62, 'min_gpus_per_node': 1},
                },
                {
                    'name': 'accel-2',
                    'descr': 'GPU Accelerated Nodes (2)',
                    'access': ['--partition=accel-2'],
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 10,
                    'processor': {
                        'num_cpus': 32,
                        'num_cpus_per_socket': 16,
                        'num_sockets': 2,
                        'num_cpus_per_core': 1,
                    },
                    'devices': [{'type': 'gpu', 'num_devices': 3}],
                    'extras': {'cn_memory': 125},
                },
                {
                    'name': 'learning',
                    'descr': 'Learning Partition',
                    'access': ['--partition=learning'],
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 10,
                    'processor': {
                        'num_cpus': 32,
                        'num_cpus_per_socket': 16,
                        'num_sockets': 2,
                        'num_cpus_per_core': 1,
                    },
                    'extras': {'cn_memory': 62},
                },
                {
                    'name': 'longjobs-smt',
                    'descr': 'Long-running jobs, SMT/hyperthreaded nodes',
                    'access': ['--partition=longjobs', '--nodelist=compute-0-35,compute-0-38'],
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 10,
                    'processor': {
                        'num_cpus': 64,
                        'num_cpus_per_socket': 32,
                        'num_sockets': 2,
                        'num_cpus_per_core': 2,
                    },
                    'extras': {'cn_memory': 62},
                },
            ]
        }
    ]
}