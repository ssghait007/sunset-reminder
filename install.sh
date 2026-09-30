#!/bin/zsh
# Put the files where the runner and launchd expect them, then (re)load the agent.
set -e
cd ${0:A:h}
mkdir -p ~/.local/bin ~/.local/share/sunset-reminder ~/.local/state
cp sunset-reminder ~/.local/bin/ && chmod +x ~/.local/bin/sunset-reminder
cp generate.py messages.txt ~/.local/share/sunset-reminder/
/usr/bin/python3 ~/.local/share/sunset-reminder/generate.py   # writes schedule.tsv + plist
launchctl bootout gui/$(id -u)/com.sachin.sunset-reminder 2>/dev/null || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.sachin.sunset-reminder.plist
echo "Installed. Test it with: ~/.local/bin/sunset-reminder --now"
