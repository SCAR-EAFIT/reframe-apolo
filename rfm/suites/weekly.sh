#!/bin/bash
# =============================================================================
# weekly.sh
# Weekly ReFrame test runner for the Apolo clusters (apolo2 / apolo3).
# Designed to be called by cron, once per week, per cluster.
#
# Runs everything tagged 'weekly': tests too expensive (multi-hour, exclusive
# node, GPU) to justify running every night — e.g. full HPL and the MLPerf
# CosmoFlow benchmark. Lighter checks belong in the 'production' tag and run
# from nightly.sh instead.
#
# Parameterized via env vars (override per invocation, e.g. from crontab):
#   RFM_SYSTEM         system name passed to --system: apolo2 or apolo3.
#                       No default — set explicitly so a forgotten env var
#                       can never silently run the wrong cluster's benchmarks.
#   RFM_TESTS_ROOT      path to tests dir or single .py file
#                       (default: <repo>/rfm/tests)
#   RFM_CONFIG_FILES    path to ReFrame config
#                       (default: <repo>/rfm/settings/${RFM_SYSTEM}.py)
#   RFM_PREFIX          output prefix for ReFrame (default: $HOME/reframe)
#   RFM_MAX_RETRIES     retries on failure (default: 1 — weekly jobs run for
#                       hours, so retrying a genuine failure is expensive)
# =============================================================================

set -u

# ---------------------------------------------------------------------------
# 0. Bootstrap the module system
#    Cron runs with a minimal environment — source Lmod's init script so
#    the 'module' command is available, then load the reframe module.
#    Lmod's own scripts (e.g. reading $SLURM_NODELIST) aren't nounset-safe,
#    so relax -u just for this block.
# ---------------------------------------------------------------------------
set +u
for init in /etc/profile.d/lmod.sh /etc/profile.d/modules.sh \
            "${LMOD_PKG:-/opt/lmod/lmod}/init/bash"; do
    [[ -r "$init" ]] && source "$init"
done

if ! command -v module &>/dev/null; then
    echo "[ERROR] 'module' command not found after sourcing Lmod init scripts. Aborting." >&2
    exit 1
fi

module purge
module load reframe
set -u

if ! command -v reframe &>/dev/null; then
    echo "[ERROR] 'reframe' not found in PATH after 'module load reframe'. Aborting." >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 1. Configuration — overridable via environment variables
# ---------------------------------------------------------------------------
if [[ -z "${RFM_SYSTEM:-}" ]]; then
    echo "[ERROR] RFM_SYSTEM is not set. Pass it explicitly, e.g.:" >&2
    echo "        RFM_SYSTEM=apolo2 $0" >&2
    exit 1
fi

# Resolve paths relative to this script's location so the suite works
# regardless of where the repo is cloned on the login node.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

RFM_TESTS_ROOT="${RFM_TESTS_ROOT:-${REPO_ROOT}/rfm/tests}"
RFM_TESTS_DIRS=("${RFM_TESTS_ROOT}")

RFM_CONFIG="${RFM_CONFIG_FILES:-${REPO_ROOT}/rfm/settings/${RFM_SYSTEM}.py}"

RFM_OUT="${RFM_PREFIX:-$HOME/reframe}"
RFM_MAX_RETRIES="${RFM_MAX_RETRIES:-1}"

# Log directory for this script's own logs
LOG_DIR="${RFM_OUT}/logs/weekly"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="${LOG_DIR}/reframe_${RFM_SYSTEM}_weekly_${TIMESTAMP}.log"

# ---------------------------------------------------------------------------
# 2. Prepare log directory
# ---------------------------------------------------------------------------
mkdir -p "$LOG_DIR"
{
    echo "===== ReFrame Weekly Run (${RFM_SYSTEM}) — $(date) ====="
    echo "System     : $RFM_SYSTEM"
    echo "Tests dirs : ${RFM_TESTS_DIRS[*]}"
    echo "Config     : $RFM_CONFIG"
    echo "Output     : $RFM_OUT"
    echo "Max retries: $RFM_MAX_RETRIES"
    echo "========================================"
} | tee "$LOG_FILE"

# ---------------------------------------------------------------------------
# 3. Run ReFrame
#    -c  : check path (discovers all tests recursively)
#    -R  : recursive discovery within the check path
#    -r  : run the tests (not just list)
#    --tag weekly : only tests explicitly opted into the weekly suite
# ---------------------------------------------------------------------------
CHECK_ARGS=()
for d in "${RFM_TESTS_DIRS[@]}"; do
    CHECK_ARGS+=(-c "$d")
done

reframe \
    -C "$RFM_CONFIG" \
    "${CHECK_ARGS[@]}" \
    -R \
    --tag weekly \
    --system "$RFM_SYSTEM" \
    --timestamp \
    --max-retries "$RFM_MAX_RETRIES" \
    -r \
    2>&1 | tee -a "$LOG_FILE"

RFM_EXIT=${PIPESTATUS[0]}

echo "===== Weekly run finished with exit code ${RFM_EXIT} — $(date) =====" | tee -a "$LOG_FILE"

exit "$RFM_EXIT"
