"""Configuration shared by every Apolo cluster settings file.

Only pieces that make sense site-wide live here: result storage and logging.
Environments are deliberately NOT shared — Apolo2 and Apolo3 run different
module stacks and compiler/MPI versions, so a common environment definition
would silently point one of them at modules that don't exist on it.
"""

storage = [
    {
        'enable': True,
        'backend': 'sqlite',
        'sqlite_db_file': '${HOME}/.reframe/reports/results.db',
        'sqlite_db_file_mode': '644',
        'sqlite_conn_timeout': 60,
    }
]

# handlers_perflog is logfmt (key=value), not the pipe-delimited style some
# ReFrame examples use, so Promtail/Loki can parse it with `| logfmt` and
# Grafana can graph any perf_var without a bespoke regex per field.
logging_config = [
    {
        'perflog_multiline': True,
        'handlers': [
            {
                'type': 'file',
                'name': 'reframe.log',
                'level': 'debug2',
                'format': '[%(asctime)s] %(levelname)s: %(check_info)s: %(message)s',
                'datefmt': '%FT%T%:z',
                'append': False,
            },
            {
                'type': 'stream',
                'name': 'stdout',
                'level': 'info',
                'format': '%(message)s',
            },
            {
                'type': 'file',
                'name': 'reframe.out',
                'level': 'info',
                'format': '%(message)s',
                'append': False,
            },
        ],
        'handlers_perflog': [
            {
                'type': 'filelog',
                'prefix': '%(check_system)s/%(check_partition)s',
                'level': 'info',
                'format': (
                    'time=%(asctime)s reframe_version=%(version)s '
                    'check=%(check_info)s system=%(check_system)s '
                    'partition=%(check_partition)s jobid=%(check_jobid)s '
                    'num_tasks=%(check_num_tasks)s '
                    'perf_var=%(check_perf_var)s '
                    'perf_value=%(check_perf_value)s '
                    'perf_unit=%(check_perf_unit)s '
                    'perf_ref=%(check_perf_ref)s '
                    'perf_lower_thres=%(check_perf_lower_thres)s '
                    'perf_upper_thres=%(check_perf_upper_thres)s'
                ),
                'datefmt': '%FT%T%:z',
                'append': True,
            },
        ],
    },
]
