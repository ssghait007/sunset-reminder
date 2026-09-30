# Sunset Reminder

Hey,

I have a confession.

Yesterday I went up to the terrace in the evening, and the sunset was magical.

Genuinely magical. Amber, rose, the whole thing.

And my very first thought was: why have I not been doing this my entire life?

It happens every single evening. It's free. It's right there, one staircase away. And I've been sitting under a ceiling staring at a terminal while the sky puts on a show nobody asked it to put on.

So I did what any reasonable software engineer would do.

I didn't set a phone alarm.

I built a system.

Obviously.

---

## The goal

Simple enough, on paper:

> Every day, 20 minutes before sunset, my Mac says something nice and tells me to go upstairs.

A sudden voice out of nowhere is scary, so every message starts with a little warning, a soft chime and then "Sunset alert!", before anything poetic happens. And the messages only talk about sunset and evening. No night. At most, the first star.

Things like:

> *"Sunset alert! The west is glowing like the inside of a seashell. Come and see."*

There are 50 of them in [`messages.txt`](messages.txt). One gets picked at random each day.

---

## Step 1: When is sunset, anyway?

Here's the thing I never really thought about. Sunset isn't at the same time every day. Obviously. But *how* not the same?

In Pune it moves around by about 80 minutes across the year. Roughly 5:56 PM in late November, roughly 7:15 PM in early July.

And here's the part that surprised me: the earliest sunset isn't on the shortest day in December. It's in late November. The Earth's orbit is an ellipse, so clock-noon and sun-noon drift apart by up to 16 minutes during the year. That drift has a name (the *equation of time*), and it's why the seasons and the sunsets don't line up neatly.

The whole thing comes down to three steps:

1. **How tilted is the sun today?** (declination, which depends only on the day of the year)
2. **How long after noon does it set?** (the hour angle)
   `cos H = cos(90.833°) / (cos φ · cos δ) − tan φ · tan δ`
   Here φ is the latitude and δ is the declination. The 90.833° is the top edge of the sun touching the horizon, plus the atmosphere bending light.
3. **Turn that into clock time:**
   `sunset = 720 − 4·(longitude − H) − EoT + 330` minutes after midnight IST
   Each degree of longitude is 4 minutes, and Pune sits about 9° west of India's clock meridian.

It came out at 18:24 for today. The published tables say about 18:26.

Close enough to go look at the sky.

---

## Step 2: Version one. It worked. It was also a bit ridiculous.

The first version ([`history/v1-sunset-reminder.py`](history/v1-sunset-reminder.py)) was a Python script, and it did everything right:

- launchd started it every day at **4:30 PM**
- it worked out today's sunset
- then it waited
- and waited
- checking the clock every 30 seconds
- for about an hour and a half
- until it was finally time to speak

It worked. I was proud of it.

Then I looked at it again and asked myself some annoying questions.

*Why 4:30?* Because the earliest reminder of the year is around 5:36 PM, so 4:30 is safe for every day.

*How does it get from 4:30 to 6:04?* It doesn't. It just sits there, awake, polling.

*Is it using CPU and memory the whole time?* Almost no CPU. But a whole Python process sits in memory for 90 minutes, probably 10 to 15 MB, doing nothing but asking "is it time yet?" about 190 times.

That's a kid in the back seat asking "are we there yet?" every 30 seconds. For an hour and a half. Every day.

*Is Python even necessary?*

No. Not even slightly.

I'd built something that computes the entire orbital mechanics of the Earth every afternoon to produce a number that changes by less than a minute from one year to the next.

I love moments like this.

No matter how much I learn, I'm still very capable of building a spaceship to cross the road.

---

## Step 3: Do the maths once, not every day

Sunset on Sep 30 this year is basically sunset on Sep 30 next year. So why calculate it daily?

The new plan: work out the whole year **once**, and let launchd just show up at the right minute. Nothing sitting in memory. No waiting.

The obvious version is one launchd entry per day, 366 entries. I didn't love it. It felt like too much.

So instead: **buckets**.

Group consecutive days whose reminder times are within 5 minutes of each other, and give each group one time. Use the *earliest* time in the group, so the warning is always between 20 and 25 minutes before sunset, never less.

[`generate.py`](generate.py) does it once and writes [`schedule.tsv`](schedule.tsv):

```
from  to    remind  sunset_floor
0101  0108  17:48   18:08
0109  0116  17:53   18:13
...
0928  1003  18:01   18:21
...
1104  1215  17:36   17:56
```

31 buckets. Most are 5 to 10 days long. One is 42 days, from November to mid-December, because the sunset there barely moves. It's just sitting at the bottom of the curve, taking a break.

---

## Step 4: And then launchd said no

Here's the funny part.

My plan was "Oct 3 to Oct 10, fire at 18:01." Clean. Elegant.

launchd doesn't do date ranges.

It can do "on this exact date", or "every day of this month at this time". That's it.

So I couldn't hand it my beautiful buckets. The instructions were right there in bold, and I'd designed around something that didn't exist.

What launchd *can* do is "every day in September at 18:01, 18:06, 18:11…". So each month gets an entry for every bucket time it touches. That's **42 entries** for the whole year, in [`com.sachin.sunset-reminder.plist`](com.sachin.sunset-reminder.plist).

That means on any given day, launchd starts the script 4 to 6 times.

And the script, now a tiny zsh file ([`sunset-reminder`](sunset-reminder)), just says:

- Is it before *today's* time? Not me. Exit.
- Has the sun already set? (Say the Mac was asleep and just woke up.) Too late. Exit.
- Did I already speak today? Exit.
- Otherwise: chime, pause, one line of poetry.

Each extra run takes about 10 to 20 milliseconds. One `awk` lookup and it's gone.

---

## Step 5: Is it perfectly efficient?

No.

It runs 4 to 6 times to speak once.

I could make it exactly once a day. Either 366 launchd entries (about 40 KB, which honestly is fine), or the script rewriting its own schedule every evening (more moving parts, more ways to break).

I looked at both and chose neither.

Going from **90 minutes of an idle Python process** to **about a tenth of a second of CPU a day** is the win. Chasing the last few milliseconds would just be building the spaceship again, only smaller.

It's not perfect, but it's simple, and it's almost free.

---

## What I actually learned

Not really about launchd.

Version one was fine. It worked. The only reason there's a version two is that I went back and asked "why?" about my own decisions, and it turned out a few of them didn't have very good answers.

That's not embarrassing. That's the whole job.

The people I worry about aren't the ones who ship the heavy version first. They're the ones who get so attached to it that they never look at it again.

So this week's reminder is simple.

Read the docs, especially the part that says what launchd *can't* do.

But don't wait for the perfect design before you build the first one.

And go watch the sunset.

It's on every evening, and it doesn't need anything installed.

---

## Using it

```sh
./install.sh                         # copies files, generates schedule + plist, loads the agent
~/.local/bin/sunset-reminder --now   # hear it right now
launchctl bootout gui/$(id -u)/com.sachin.sunset-reminder   # turn it off
```

| File | What it is |
|---|---|
| `sunset-reminder` | The zsh runner that launchd starts. Decides whether today is the moment, then chimes and speaks. |
| `generate.py` | Run once. Computes the year, builds the buckets, writes `schedule.tsv` and the plist. Change `LAT`/`LON`/`LEAD` here for another city or lead time. |
| `schedule.tsv` | The 31 buckets: date range, reminder time, earliest sunset in the range. |
| `messages.txt` | The 50 "Sunset alert!" lines. Edit freely. |
| `com.sachin.sunset-reminder.plist` | The generated launchd schedule (42 month and time entries). |
| `history/v1-sunset-reminder.py` | The original Python version, kept for the story. |

Location is Pune (18.52°N, 73.86°E, IST). Times use the NOAA approximation and match published tables to within a couple of minutes.
