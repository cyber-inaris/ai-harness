#!/usr/bin/env bash
set -euo pipefail

WARN_TEMP_C="${AI_HARNESS_HEAT_WARN_TEMP_C:-80}"
CRIT_TEMP_C="${AI_HARNESS_HEAT_CRIT_TEMP_C:-88}"
FIREFOX_USER="${AI_HARNESS_HEAT_FIREFOX_USER:-dima}"
RESTART_FIREFOX="${AI_HARNESS_HEAT_RESTART_FIREFOX:-0}"
START_THERMALD="${AI_HARNESS_HEAT_START_THERMALD:-1}"
LOG_DIR="${AI_HARNESS_HEAT_LOG_DIR:-/var/log/ai-harness}"
LOG_FILE="${LOG_DIR}/heat-guard.log"

log() {
  printf '%s %s\n' "$(date --iso-8601=seconds)" "$*" | tee -a "${LOG_FILE}"
}

require_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root or with sudo: sudo $0" >&2
    exit 1
  fi
}

sensor_temp() {
  sensors 2>/dev/null | awk '
    /Tctl:/ {
      v=$2
      gsub(/[^0-9.]/, "", v)
      if (v != "") {
        print v
        found=1
        exit
      }
    }
    /temp[0-9]+:/ || /Composite:/ || /edge:/ {
      v=$2
      gsub(/[^0-9.]/, "", v)
      if (v != "" && v > max) {
        max=v
      }
    }
    END {
      if (!found && max != "") {
        print max
      }
    }
  '
}

temp_ge() {
  awk -v a="$1" -v b="$2" 'BEGIN { exit !(a >= b) }'
}

set_power_saver() {
  if command -v powerprofilesctl >/dev/null 2>&1; then
    powerprofilesctl set power-saver || true
  fi
}

start_thermald() {
  if [[ "${START_THERMALD}" != "1" ]]; then
    log "thermald=skipped reason=disabled"
    return
  fi

  if systemctl list-unit-files thermald.service >/dev/null 2>&1; then
    systemctl start thermald || true
  fi
}

clean_safe_caches() {
  apt-get clean || true
  find /tmp /var/tmp -xdev -type f -mtime +1 -delete 2>/dev/null || true

  if [[ -d "/home/${FIREFOX_USER}/snap/firefox/common/.cache/mozilla/firefox" ]]; then
    find "/home/${FIREFOX_USER}/snap/firefox/common/.cache/mozilla/firefox" \
      -xdev -type f -mtime +1 -delete 2>/dev/null || true
  fi

  if command -v snap >/dev/null 2>&1; then
    snap list --all 2>/dev/null |
      awk '/disabled/{print $1, $3}' |
      while read -r snap_name snap_rev; do
        snap remove "${snap_name}" --revision="${snap_rev}" >/dev/null 2>&1 || true
      done
  fi

  if command -v docker >/dev/null 2>&1; then
    docker system prune -f >/dev/null 2>&1 || true
  fi
}

log_top_cpu() {
  {
    echo "top cpu:"
    ps -eo pid,user,pcpu,pmem,etime,comm --sort=-pcpu | head -12
  } >>"${LOG_FILE}" 2>&1 || true
}

restart_firefox_if_allowed() {
  if [[ "${RESTART_FIREFOX}" != "1" ]]; then
    log "firefox_restart=skipped reason=AI_HARNESS_HEAT_RESTART_FIREFOX_not_enabled"
    return
  fi

  if pgrep -u "${FIREFOX_USER}" -x firefox >/dev/null 2>&1; then
    log "firefox_restart=term user=${FIREFOX_USER}"
    pkill -TERM -u "${FIREFOX_USER}" -x firefox || true
  fi
}

main() {
  require_root
  install -d -m 0755 "${LOG_DIR}"

  if ! command -v sensors >/dev/null 2>&1; then
    log "status=missing_sensors action=none"
    exit 0
  fi

  current_temp="$(sensor_temp)"
  if [[ -z "${current_temp}" ]]; then
    log "status=no_temperature action=none"
    exit 0
  fi

  log "temp_c=${current_temp} warn_c=${WARN_TEMP_C} crit_c=${CRIT_TEMP_C}"

  if temp_ge "${current_temp}" "${WARN_TEMP_C}"; then
    log "action=heat_warn set_power_saver=true start_thermald=${START_THERMALD} clean_safe_caches=true"
    set_power_saver
    start_thermald
    clean_safe_caches
    log_top_cpu
  fi

  if temp_ge "${current_temp}" "${CRIT_TEMP_C}"; then
    log "action=heat_critical"
    restart_firefox_if_allowed
  fi
}

main "$@"
