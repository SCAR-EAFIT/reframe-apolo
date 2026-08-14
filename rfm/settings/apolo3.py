site_configuration = {
    'systems': [
        {
            'name': 'apolo3',
            'descr': 'Apolo-3 Cluster',
            'hostnames': ['apolo-3', 'apolo-3.eafit.edu.co'],
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
                        'num_cpus': 64,
                        'num_cpus_per_socket': 32,
                        'num_sockets': 2,
                        'num_cpus_per_core': 1,
                    },
                    'extras': {'cn_memory': 503},
                },
                {
                    'name': 'longjobs',
                    'descr': 'Standard CPU Nodes',
                    'access': ['--partition=longjobs'],
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 10,
                    'processor': {
                        'num_cpus': 64,
                        'num_cpus_per_socket': 32,
                        'num_sockets': 2,
                        'num_cpus_per_core': 1,
                    },
                    'extras': {'cn_memory': 377},
                },
                {
                    'name': 'accel',
                    'descr': 'GPU Accelerated Nodes',
                    'access': ['--partition=accel'],
                    'scheduler': 'slurm',
                    'launcher': 'srun',
                    'max_jobs': 10,
                    'processor': {
                        'num_cpus': 64,
                        'num_cpus_per_socket': 32,
                        'num_sockets': 2,
                        'num_cpus_per_core': 1,
                    },
                    'devices': [{'type': 'gpu', 'num_devices': 2}],
                    'extras': {'cn_memory': 251, 'min_gpus_per_node': 1},
                },                        
            ]
        }
    ]
}