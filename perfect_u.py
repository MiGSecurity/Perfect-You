import json
import os
import time
from datetime import datetime, timedelta

PROFILE_PATH = "profile.json"
SCHEDULE_PATH = "schedule.json"
TASKS_PATH = "tasks.json"
LOG_PATH = "xp_log.txt"

# -------------- Utility Functions --------------


def load_json(path, default):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump(default, f)
    with open(path, 'r') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=4)


def draw_bar(current, max_val):
    width = 20
    filled = int((current / max_val) * width) if max_val else 0
    return '[' + '=' * filled + ' ' * (width - filled) + ']'


def xp_for_level(level):
    return 100 * level + 200


def calculate_level(xp):
    level = 1
    total = xp_for_level(level)
    while xp >= total:
        level += 1
        total += xp_for_level(level)
    return level, total - (total - xp_for_level(level))


def get_days_to_next_level(profile):
    xp = profile["xp"]
    level = profile["level"]
    xp_needed = xp_for_level(level + 1)
    avg = sum(profile["xp_history"][-7:]) / max(1, len(profile["xp_history"]))
    if avg <= 0:
        return "⚠️ Negative XP trend"
    return f"{round((xp_needed - xp) / avg, 1)} days"


def format_task(task):
    if not task:
        return "None"
    return f"{task['name']} ({task['start'][-5:]})"

# -------------- Profile Management --------------


def apply_decay(profile):
    last = datetime.strptime(profile["last_active"], "%Y-%m-%d")
    today = datetime.now().date()
    days = (today - last.date()).days
    if days > 0:
        profile["xp"] = int(profile["xp"] * (0.9 ** days))
        profile["love_xp"] = int(profile["love_xp"] * (0.95 ** days))
        profile["last_active"] = today.strftime("%Y-%m-%d")
    return profile


def check_day_start(profile):
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    hour = now.hour

    if "start_hour" not in profile:
        profile["start_hour"] = int(
            input("🕒 What hour do you want to start your day every day? (0–23): "))

    if profile.get("day_started") == today_str:
        profile["can_schedule"] = True
        return profile

    if hour < profile["start_hour"] + 1:
        choice = input("☀️ Start your day? (y/n): ").strip().lower()
        if choice == "y":
            profile["day_started"] = today_str
            profile["can_schedule"] = True
        else:
            profile["can_schedule"] = False
    else:
        print("⏰ You missed your scheduling window. -10% XP penalty applied.")
        profile["xp"] = int(profile["xp"] * 0.9)
        profile["can_schedule"] = False
        profile["day_started"] = today_str
    return profile

# -------------- Task Functions --------------


def add_tasks(profile, schedule):
    if not profile.get("can_schedule"):
        print("\n🚫 You cannot schedule tasks today.")
        input("Press Enter to continue...")
        return

    tasks_data = load_json(TASKS_PATH, {"tasks": []})["tasks"]
    print("\n📋 Available Tasks:")
    for i, task in enumerate(tasks_data):
        print(f"[{i+1}] {task['name']} – {task['duration']}min, {task['xp']} XP")

    print("\n🕓 Format: task_number; start_hour[,hour2,...]")
    print("Example: 1; 09,10,11")

    while True:
        entry = input("Add tasks (or leave empty to exit): ").strip()
        if not entry:
            break
        try:
            num, times_str = entry.split(";")
            task = tasks_data[int(num.strip()) - 1]
            times = [int(t.strip()) for t in times_str.split(",")]
            for hour in times:
                start = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
                end = start + timedelta(minutes=task["duration"])

                conflict = False
                for s in schedule:
                    s_start = datetime.strptime(s["start"], "%Y-%m-%d %H:%M")
                    s_end = s_start + timedelta(minutes=s["duration"])
                    if s_start < end and start < s_end:
                        conflict = True
                        break
                if conflict:
                    print(
                        f"⚠️ Conflict: '{task['name']}' at {hour:02d}:00 overlaps.")
                    continue

                schedule.append({
                    "name": task["name"],
                    "start": start.strftime("%Y-%m-%d %H:%M"),
                    "duration": task["duration"],
                    "xp": task["xp"],
                    "status": "⏳"
                })
        except Exception as e:
            print(f"❌ Error: {e}")
    save_json(SCHEDULE_PATH, schedule)


def update_status(profile, schedule):
    now = datetime.now()
    earned, lost = 0, 0
    lines = []

    for task in schedule:
        start = datetime.strptime(task["start"], "%Y-%m-%d %H:%M")
        end = start + timedelta(minutes=task["duration"])

        if task["status"] == "⏳":
            if start <= now < end:
                task["status"] = "🕒"
            elif now >= end:
                print(
                    f"\n⏳ Task '{task['name']}' ended at {end.strftime('%H:%M')}")
                result = input("Did you complete it? (y/n): ").strip().lower()
                if result == "y":
                    task["status"] = "✓"
                    profile["xp"] += task["xp"]
                    earned += task["xp"]
                    lines.append(
                        f"{now.strftime('%Y-%m-%d %H:%M')} - ✅ {task['name']} (+{task['xp']} XP)")
                else:
                    task["status"] = "X"
                    penalty = int(task["xp"] / 2)
                    profile["xp"] = max(0, profile["xp"] - penalty)
                    lost += penalty
                    lines.append(
                        f"{now.strftime('%Y-%m-%d %H:%M')} - ❌ {task['name']} (-{penalty} XP)")

    if lines:
        with open(LOG_PATH, "a") as f:
            f.write(f"\n=== {now.strftime('%Y-%m-%d')} ===\n")
            for l in lines:
                f.write(l + "\n")

    profile["xp_history"].append(earned)
    if len(profile["xp_history"]) > 7:
        profile["xp_history"] = profile["xp_history"][-7:]
    profile["earned_xp_display"] = earned
    profile["lost_xp_display"] = lost

    return profile, schedule

# -------------- UI --------------


def draw_ui(profile, schedule):
    os.system("cls" if os.name == "nt" else "clear")
    now = datetime.now()
    current = None
    upcoming = None

    for task in schedule:
        start = datetime.strptime(task["start"], "%Y-%m-%d %H:%M")
        end = start + timedelta(minutes=task["duration"])
        if start <= now < end:
            current = task
        elif start > now and not upcoming:
            upcoming = task

    level = profile["level"]
    xp = profile["xp"]
    love = profile["love_xp"]
    next_xp = xp_for_level(level + 1)
    xp_bar = draw_bar(xp, next_xp)
    love_bar = draw_bar(love, 200)

    print("=" * 50)
    print(f"👤 {profile['username']} | 🧬 Level {level} | XP: {xp}")
    print(f"💖 Love XP: {love_bar} {love}/200")
    print(
        f"📅 Date: {now.strftime('%Y-%m-%d')} | 🕒 Time: {now.strftime('%H:%M')}")
    print("-" * 50)
    print(f"🔴 Current Task: {format_task(current)}")
    print(f"🟡 Next Task   : {format_task(upcoming)}")
    print("-" * 50)
    print("📅 Schedule for Today:")
    for task in schedule:
        start = datetime.strptime(task["start"], "%Y-%m-%d %H:%M")
        end = start + timedelta(minutes=task["duration"])
        print(f"[{task['status']}] {task['name']:<12} {start.strftime('%H:%M')}–{end.strftime('%H:%M')}  XP: {task['xp']}")
    print("-" * 50)
    print(
        f"📈 Avg XP/day: {int(sum(profile['xp_history'][-7:]) / max(1,len(profile['xp_history'][-7:])))} | ETA to next level: {get_days_to_next_level(profile)}")
    print(
        f"📈 Gained XP: +{profile['earned_xp_display']} | 💀 Lost XP: -{profile['lost_xp_display']}")
    print("=" * 50)

# -------------- Main Loop --------------


def main():
    if not os.path.exists(PROFILE_PATH):
        profile = {
            "username": input("Enter your name: "),
            "xp": 0,
            "love_xp": 0,
            "level": 1,
            "last_active": datetime.now().strftime("%Y-%m-%d"),
            "xp_history": [0]*7,
            "day_started": "",
            "can_schedule": True
        }
        save_json(PROFILE_PATH, profile)
    profile = load_json(PROFILE_PATH, {})
    schedule = load_json(SCHEDULE_PATH, [])
    profile = apply_decay(profile)
    profile = check_day_start(profile)

    while True:
        profile, schedule = update_status(profile, schedule)
        profile["level"], _ = calculate_level(profile["xp"])
        draw_ui(profile, schedule)
        print("[1] Add Task  [2] View XP Log  [Enter] Refresh")
        choice = input("> ").strip()
        if choice == "1":
            add_tasks(profile, schedule)
        elif choice == "2":
            if os.path.exists(LOG_PATH):
                os.system("cls" if os.name == "nt" else "clear")
                with open(LOG_PATH, "r") as f:
                    print(f.read())
                input("\n[Enter] to return...")
        save_json(PROFILE_PATH, profile)
        save_json(SCHEDULE_PATH, schedule)
        time.sleep(1)  # Manual refresh every second


if __name__ == "__main__":
    main()
