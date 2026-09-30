#!/usr/bin/python3
"""v1 (retired): speak a sunset reminder 20 minutes before today's sunset in Pune.

launchd started this every day at 16:30. It computed the sunset, then stayed
alive, polling the clock every 30 seconds until the reminder time.
Replaced by the bucketed schedule + zsh runner. Kept here for the story.
"""
import datetime as dt
import math
import os
import random
import subprocess
import sys
import time

LAT, LON, TZ_HOURS = 18.5204, 73.8567, 5.5  # Pune, IST
LEAD_MINUTES = 20
CHIME = "/System/Library/Sounds/Glass.aiff"
STATE_FILE = os.path.expanduser("~/.local/state/sunset-reminder-last")

MESSAGES = [
    'Sunset alert! The sun is slipping low, painting the sky in amber and rose.',
    'Sunset alert! The day is folding into gold. Come, let the evening hold you.',
    "Sunset alert! Soft light is spilling over the rooftops, the sky's quiet goodbye.",
    'Sunset alert! The horizon is blushing. Go and catch the last warm light.',
    'Sunset alert! The sun sinks slow, the sky turns fire and honey. Stay for the first star.',
    'Sunset alert! The sky is unrolling its silk, saffron and violet. Come and see.',
    'Sunset alert! The light is turning tender. The evening is calling you upstairs.',
    'Sunset alert! Gold is pouring over the edge of the world. Go watch it fall.',
    'Sunset alert! The clouds are catching fire, gently. A painting only this evening makes.',
    'Sunset alert! The sun is bowing out in copper and rose. Give it a standing ovation.',
    'Sunset alert! The sky is writing its evening poem. Go read it before it fades.',
    'Sunset alert! Long shadows, warm light, a slow and golden hush. Terrace time.',
    'Sunset alert! The day exhales in orange and pink. Breathe out with it.',
    'Sunset alert! The sun is melting into the hills like butter into bread. Come see.',
    'Sunset alert! The evening is lighting its lanterns in the clouds.',
    'Sunset alert! A river of amber is flowing across the sky. Go stand at its bank.',
    "Sunset alert! The sky is blushing deeper by the minute. Don't miss its best colours.",
    'Sunset alert! The sun is handing the sky over to the evening, softly, in gold.',
    'Sunset alert! Peach and lavender are gathering on the horizon. The show is starting.',
    'Sunset alert! The light has gone warm and slow, like honey. Step out into it.',
    'Sunset alert! The sun is taking its evening walk down the sky. Walk with it.',
    "Sunset alert! Every cloud is edged in gold tonight, the evening's quiet embroidery.",
    'Sunset alert! The sky is a canvas and the sun is finishing its last brushstrokes.',
    'Sunset alert! The world is glowing softly, just for a little while. Go be in it.',
    'Sunset alert! The sun sinks, the sky sings in rose and flame. Come and listen.',
    'Sunset alert! A soft gold is settling on everything. Let it settle on you too.',
    'Sunset alert! The horizon is holding the sun like a lamp. Go see its glow.',
    'Sunset alert! Crimson and coral are drifting across the sky. The evening is here.',
    'Sunset alert! The sun is dipping its toes into the horizon. Come watch it wade in.',
    'Sunset alert! The breeze is cooling and the sky is warming. The perfect evening pair.',
    'Sunset alert! The birds are flying home through golden air. Join them on the terrace.',
    'Sunset alert! The sun is writing its name in fire across the clouds.',
    'Sunset alert! The evening is pouring rosé into the sky. Go take a look.',
    "Sunset alert! Light is lingering on the rooftops like it doesn't want to leave.",
    'Sunset alert! The day is signing off in shades of flame and lilac.',
    'Sunset alert! The sky is slowly turning from gold to rose to dusk. Watch every stage.',
    "Sunset alert! The sun is a glowing ember now, settling into the horizon's hearth.",
    'Sunset alert! The evening sky is opening like a flower, petal by petal.',
    'Sunset alert! Warm light is stretching long across the city. Go stretch in it too.',
    'Sunset alert! The sun is leaving a trail of gold behind it. Follow it upstairs.',
    'Sunset alert! The clouds are dressed in pink for the evening. Go admire them.',
    'Sunset alert! Twenty minutes of golden light remain. Spend them under the open sky.',
    'Sunset alert! The sky is burning softly, beautifully. And after it, maybe a star.',
    'Sunset alert! The sun is sliding down a staircase of clouds, glowing all the way.',
    'Sunset alert! The evening is wrapping the day in a shawl of amber light.',
    'Sunset alert! The west is glowing like the inside of a seashell. Come and see.',
    'Sunset alert! The last light is the kindest light. Go and let it find you.',
    'Sunset alert! The sky is turning to watercolour, orange bleeding into violet.',
    'Sunset alert! The day is ending in gold, gently, the way good days should.',
    'Sunset alert! The sun is setting the horizon aglow. Watch it, and wait for the first star.',
]


def sunset(day):
    g = 2 * math.pi / 365 * (day.timetuple().tm_yday - 1)
    eot = 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                    - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))
    decl = (0.006918 - 0.399912 * math.cos(g) + 0.070257 * math.sin(g)
            - 0.006758 * math.cos(2 * g) + 0.000907 * math.sin(2 * g)
            - 0.002697 * math.cos(3 * g) + 0.00148 * math.sin(3 * g))
    phi = math.radians(LAT)
    hour_angle = math.degrees(math.acos(
        math.cos(math.radians(90.833)) / (math.cos(phi) * math.cos(decl))
        - math.tan(phi) * math.tan(decl)))
    minutes = 720 - 4 * (LON - hour_angle) - eot + TZ_HOURS * 60
    return dt.datetime.combine(day, dt.time()) + dt.timedelta(minutes=minutes)


def announce():
    subprocess.run(["afplay", CHIME])
    time.sleep(1)
    subprocess.run(["say", random.choice(MESSAGES)])


def main():
    today = dt.date.today()
    set_at = sunset(today)
    remind_at = set_at - dt.timedelta(minutes=LEAD_MINUTES)

    if "--dry-run" in sys.argv:
        print(f"sunset {set_at:%H:%M}, reminder {remind_at:%H:%M}")
        print(random.choice(MESSAGES))
        return
    if "--now" in sys.argv:
        announce()
        return

    try:
        with open(STATE_FILE) as f:
            if f.read().strip() == today.isoformat():
                return
    except FileNotFoundError:
        pass

    # Poll the wall clock rather than one long sleep: time.sleep stalls while the Mac sleeps.
    while dt.datetime.now() < remind_at:
        time.sleep(min(30, (remind_at - dt.datetime.now()).total_seconds() + 1))

    if dt.datetime.now() > set_at:
        return

    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        f.write(today.isoformat())
    announce()


if __name__ == "__main__":
    main()
