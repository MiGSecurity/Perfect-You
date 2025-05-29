import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os
from datetime import datetime, timedelta

PROFILE_PATH = "profile.json"
SCHEDULE_PATH = "schedule.json"
TASKS_PATH = "tasks.json"
LOG_PATH = "xp_log.txt"

# ---------- Utility Functions ----------


def load_json(path, default):
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(default, f)
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def xp_for_level(level):
    return 100 * level + 200


def calculate_level(xp):
    level = 1
    total = xp_for_level(level)
    while xp >= total:
        level += 1
        total += xp_for_level(level)
    return level, xp_for_level(level) - (total - xp)


def draw_bar(current, max_val):
    width = 20
    filled = int((current / max_val) * width) if max_val else 0
    return '[' + '=' * filled + ' ' * (width - filled) + ']'

# ---------- App Core ----------


class XPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Perfect You")
        self.root.geometry("400x400")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)

        self.profile = load_json(PROFILE_PATH, {
            "username": "You",
            "xp": 0,
            "love_xp": 0,
            "level": 1,
            "xp_history": [0]*7,
            "last_active": datetime.now().strftime("%Y-%m-%d")
        })
        self.schedule = load_json(SCHEDULE_PATH, [])
        tasks_data = load_json(TASKS_PATH, {"tasks": []})
        self.tasks = tasks_data.get("tasks", [])
        self.setup_ui()
        self.refresh_loop()

    def setup_ui(self):
        self.frame = tk.Frame(self.root)
        self.frame.pack(pady=10)

        self.user_label = tk.Label(self.frame, text="")
        self.user_label.pack()

        self.love_label = tk.Label(self.frame, text="")
        self.love_label.pack()

        self.task_label = tk.Label(self.frame, text="")
        self.task_label.pack()

        self.next_label = tk.Label(self.frame, text="")
        self.next_label.pack()

        self.schedule_box = tk.Listbox(self.frame, width=50)
        self.schedule_box.pack(pady=10)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=5)

        tk.Button(btn_frame, text="Add Task", command=self.add_task_popup).pack(
            side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="View XP Log",
                  command=self.view_log).pack(side=tk.LEFT, padx=5)

    def refresh_loop(self):
        now = datetime.now()
        current_task = None
        next_task = None
        earned, lost = 0, 0
        lines = []

        for task in self.schedule:
            start = datetime.strptime(task["start"], "%Y-%m-%d %H:%M")
            end = start + timedelta(minutes=task["duration"])

            if task["status"] == "⏳":
                if start <= now < end:
                    current_task = task
                    task["status"] = "🕒"
                elif now >= end:
                    result = messagebox.askyesno(
                        "Task Complete", f"Did you complete '{task['name']}'?")
                    if result:
                        task["status"] = "✓"
                        self.profile["xp"] += task["xp"]
                        earned += task["xp"]
                        lines.append(
                            f"{now.strftime('%Y-%m-%d %H:%M')} - ✅ {task['name']} (+{task['xp']} XP)")
                    else:
                        task["status"] = "X"
                        penalty = int(task["xp"] / 2)
                        self.profile["xp"] = max(
                            0, self.profile["xp"] - penalty)
                        lost += penalty
                        lines.append(
                            f"{now.strftime('%Y-%m-%d %H:%M')} - ❌ {task['name']} (-{penalty} XP)")

            elif start > now and not next_task:
                next_task = task

        if lines:
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(f"\n=== {now.strftime('%Y-%m-%d')} ===\n")
                for l in lines:
                    f.write(l + "\n")

        level, _ = calculate_level(self.profile["xp"])
        self.profile["level"] = level
        save_json(PROFILE_PATH, self.profile)
        save_json(SCHEDULE_PATH, self.schedule)

        self.update_ui(current_task, next_task)
        self.root.after(5000, self.refresh_loop)

    def update_ui(self, current, upcoming):
        level = self.profile["level"]
        xp = self.profile["xp"]
        xp_needed = xp_for_level(level + 1)
        xp_bar = draw_bar(xp, xp_needed)
        self.user_label.config(
            text=f"👤 {self.profile['username']} | 🧬 Level {level} | XP: {xp}/{xp_needed}\n🔋 {xp_bar}")

        self.love_label.config(
            text=f"💖 Love XP: {draw_bar(self.profile['love_xp'], 200)} {self.profile['love_xp']}/200")
        self.task_label.config(
            text=f"🔴 Current: {current['name']}" if current else "🔴 Current: None")
        self.next_label.config(
            text=f"🟡 Next: {upcoming['name']} at {upcoming['start'][-5:]}" if upcoming else "🟡 Next: None")

        self.schedule_box.delete(0, tk.END)
        for task in self.schedule:
            self.schedule_box.insert(
                tk.END, f"[{task['status']}] {task['name']} at {task['start'][-5:]} for {task['duration']} min")

    def add_task_popup(self):
        if not self.tasks:
            messagebox.showinfo("No Tasks", "You have no predefined tasks.")
            return

        options = "\n".join(
            [f"{i+1}. {t['name']} ({t['duration']}min / {t['xp']} XP)" for i, t in enumerate(self.tasks)])
        task_index = simpledialog.askinteger(
            "Add Task", f"Select a task:\n{options}")
        if not task_index or task_index < 1 or task_index > len(self.tasks):
            return

        hour = simpledialog.askinteger(
            "Start Hour", "At what hour do you want to schedule it? (0-23)")
        if hour is None or hour < 0 or hour > 23:
            return

        task = self.tasks[task_index - 1]
        start = datetime.now().replace(hour=hour, minute=0, second=0, microsecond=0)
        self.schedule.append({
            "name": task["name"],
            "start": start.strftime("%Y-%m-%d %H:%M"),
            "duration": task["duration"],
            "xp": task["xp"],
            "status": "⏳"
        })
        save_json(SCHEDULE_PATH, self.schedule)

    def view_log(self):
        if not os.path.exists(LOG_PATH):
            messagebox.showinfo("XP Log", "No XP log found.")
            return
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        log_win = tk.Toplevel(self.root)
        log_win.title("XP Log")
        txt = tk.Text(log_win, wrap="word")
        txt.insert("1.0", content)
        txt.pack(expand=True, fill="both")


if __name__ == "__main__":
    root = tk.Tk()
    app = XPApp(root)
    root.mainloop()
