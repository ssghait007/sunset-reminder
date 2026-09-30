#!/usr/bin/python3
"""One-off generator: buckets the year's sunset-reminder times and writes
schedule.tsv plus the launchd plist. Re-run only to change location or lead time."""
import datetime as dt, math, os

LAT, LON, TZ_HOURS = 18.5204, 73.8567, 5.5   # Pune, IST
LEAD, TOLERANCE = 20, 5                       # minutes
HERE = os.path.dirname(os.path.abspath(__file__))
PLIST = os.path.expanduser("~/Library/LaunchAgents/com.sachin.sunset-reminder.plist")

def sunset_minutes(day):
    g = 2 * math.pi / 365 * (day.timetuple().tm_yday - 1)
    eot = 229.18 * (0.000075 + 0.001868*math.cos(g) - 0.032077*math.sin(g)
                    - 0.014615*math.cos(2*g) - 0.040849*math.sin(2*g))
    decl = (0.006918 - 0.399912*math.cos(g) + 0.070257*math.sin(g) - 0.006758*math.cos(2*g)
            + 0.000907*math.sin(2*g) - 0.002697*math.cos(3*g) + 0.00148*math.sin(3*g))
    phi = math.radians(LAT)
    h = math.degrees(math.acos(math.cos(math.radians(90.833)) / (math.cos(phi)*math.cos(decl))
                               - math.tan(phi)*math.tan(decl)))
    return 720 - 4*(LON - h) - eot + TZ_HOURS*60

# 2028 is a leap year, so Feb 29 gets a slot; sunsets shift < 1 min between years.
days = [dt.date(2028, 1, 1) + dt.timedelta(i) for i in range(366)]
remind = [int(sunset_minutes(d) - LEAD) for d in days]   # floor: never later than LEAD

# Greedy buckets of consecutive days whose reminder times stay within TOLERANCE.
# The bucket fires at its earliest time, so the lead is LEAD..LEAD+TOLERANCE minutes.
buckets, start = [], 0
for i in range(1, len(days) + 1):
    if i == len(days) or max(remind[start:i+1]) - min(remind[start:i+1]) >= TOLERANCE:
        buckets.append((days[start], days[i-1], min(remind[start:i])))
        start = i

with open(os.path.join(HERE, "schedule.tsv"), "w") as f:
    f.write("# from\tto\tremind\tsunset_floor   (MMDD, HH:MM)\n")
    for a, b, m in buckets:
        f.write(f"{a:%m%d}\t{b:%m%d}\t{m//60:02d}:{m%60:02d}\t{(m+LEAD)//60:02d}:{(m+LEAD)%60:02d}\n")

slots = sorted({(d.month, m) for a, b, m in buckets
                for d in days if a <= d <= b})
entries = "\n".join(
    f"        <dict><key>Month</key><integer>{mo}</integer>"
    f"<key>Hour</key><integer>{m//60}</integer><key>Minute</key><integer>{m%60}</integer></dict>"
    for mo, m in slots)
with open(PLIST, "w") as f:
    f.write(f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sachin.sunset-reminder</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/zsh</string>
        <string>{os.path.expanduser('~/.local/bin/sunset-reminder')}</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
{entries}
    </array>
</dict>
</plist>
""")
lens = [(b - a).days + 1 for a, b, _ in buckets]
print(f"{len(buckets)} buckets, {min(lens)}-{max(lens)} days (median {sorted(lens)[len(lens)//2]}), {len(slots)} launchd entries")
