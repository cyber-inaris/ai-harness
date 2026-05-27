#!/usr/bin/env bash
set -euo pipefail

GUI_USER="${GUI_USER:-dima}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo $0" >&2
  exit 1
fi

mkdir -p /etc/systemd/logind.conf.d /etc/NetworkManager/conf.d

cat >/etc/systemd/logind.conf.d/ai-harness-no-sleep.conf <<'EOF'
[Login]
HandleLidSwitch=ignore
HandleLidSwitchExternalPower=ignore
HandleLidSwitchDocked=ignore
IdleAction=ignore
EOF

cat >/etc/NetworkManager/conf.d/99-ai-harness-wifi-powersave-off.conf <<'EOF'
[connection]
wifi.powersave = 2
EOF

if id "${GUI_USER}" >/dev/null 2>&1; then
  gui_uid="$(id -u "${GUI_USER}")"
  dbus_addr="unix:path=/run/user/${gui_uid}/bus"

  if [[ -S "/run/user/${gui_uid}/bus" ]]; then
    sudo -u "${GUI_USER}" DBUS_SESSION_BUS_ADDRESS="${dbus_addr}" \
      gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0 || true
    sudo -u "${GUI_USER}" DBUS_SESSION_BUS_ADDRESS="${dbus_addr}" \
      gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0 || true
    sudo -u "${GUI_USER}" DBUS_SESSION_BUS_ADDRESS="${dbus_addr}" \
      gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type "nothing" || true
    sudo -u "${GUI_USER}" DBUS_SESSION_BUS_ADDRESS="${dbus_addr}" \
      gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type "nothing" || true
    sudo -u "${GUI_USER}" DBUS_SESSION_BUS_ADDRESS="${dbus_addr}" \
      gsettings set org.gnome.settings-daemon.plugins.power lid-close-ac-action "nothing" || true
    sudo -u "${GUI_USER}" DBUS_SESSION_BUS_ADDRESS="${dbus_addr}" \
      gsettings set org.gnome.settings-daemon.plugins.power lid-close-battery-action "nothing" || true
  else
    echo "GNOME session bus for ${GUI_USER} is not available; skipped gsettings." >&2
  fi
else
  echo "GUI_USER=${GUI_USER} does not exist; skipped gsettings." >&2
fi

systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
systemctl restart systemd-logind

if command -v iw >/dev/null 2>&1; then
  iw dev 2>/dev/null | awk '/Interface/ {print $2}' | while read -r iface; do
    iw dev "${iface}" set power_save off || true
  done
fi

echo "Laptop sleep policy disabled for ai-harness host."
