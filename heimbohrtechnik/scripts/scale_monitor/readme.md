# How to use
Copy or symlink the `.service` and `.timer` into `/etc/systemd/system/.`

Install with

`$ sudo systemctl daemon-reload`
`$ sudo systemctl enable --now scale_monitor.timer`

Check if the timer is enabled

`$ systemctl list-timers`

Watch it run

`$ journalctl -u scale_monitor.service -f`

Disable with 

`$ sudo systemctl disable --now scale_monitor.timer`
`$ sudo systemctl stop scale_monitor.service`

Remove the `.timer` and `.service` from `/etc/systemd/system/.`

`$ sudo systemctl daemon-reload`
