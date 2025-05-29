import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os
from datetime import datetime, timedelta

PROFILE_PATH = "profile.json"
SCHEDULE_PATH = "schedule.json"
TASKS_PATH = "tasks.json"
LOG_PATH = "xp_log.txt"

QUOTES = [
    "You can do it. Keep going.",
    "Discipline beats motivation.",
    "Consistency is key.",
    "Progress, not perfection.",
    "Small steps every day.",
    "Push yourself. No one else will.",
    "Don’t break the chain.",
    "Win the morning, win the day.",
    "You’re stronger than you think.",
    "Keep showing up.",
    "Make it count today.",
    "You’re building something real.",
    "Your future self will thank you."
]

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
    lvl = 1
    total = xp_for_level(lvl)
    while xp >= total:
        lvl += 1
        total += xp_for_level(lvl)
    return lvl, xp_for_level(lvl)


def draw_bar(current, maximum):
    width = 20
    filled = int((current / maximum) * width) if maximum else 0
    return '[' + '=' * filled + ' ' * (width - filled) + ']'

# ---------- Main Application ----------


class XPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Perfect You")
        self.root.geometry("400x460")
        self.root.resizable(False, False)
        self.root.attributes("-topmost", True)
        self.root.configure(bg="#1e1e1e")

        # Load or initialize data
        self.profile = load_json(PROFILE_PATH, {
            "username": "You", "xp": 0, "love_xp": 0,
            "level": 1, "xp_history": [0] * 7,
            "last_active": datetime.now().strftime("%Y-%m-%d"),
            "earned_xp_display": 0, "lost_xp_display": 0
        })
        self.schedule = load_json(SCHEDULE_PATH, [])
        self.tasks = load_json(TASKS_PATH, {"tasks": []}).get("tasks", [])

        # Quote rotation
        self.quote_index = 0
        self.last_quote_time = datetime.now()

        self.build_ui()
        self.refresh_loop()

    def build_ui(self):
        frm = tk.Frame(self.root, bg="#1e1e1e")
        frm.pack(pady=10)

        # User & XP
        self.user_label = tk.Label(
            frm, fg="white", bg="#1e1e1e", font=("Segoe UI", 10))
        self.user_label.pack()
        self.love_label = tk.Label(
            frm, fg="white", bg="#1e1e1e", font=("Segoe UI", 10))
        self.love_label.pack()

        # Current / Next
        self.task_label = tk.Label(
            frm, fg="white", bg="#1e1e1e", font=("Segoe UI", 10, "bold"))
        self.task_label.pack()
        self.next_label = tk.Label(
            frm, fg="white", bg="#1e1e1e", font=("Segoe UI", 10, "bold"))
        self.next_label.pack()

        # Schedule list
        self.schedule_box = tk.Listbox(frm, width=50, bg="#2e2e2e", fg="white")
        self.schedule_box.pack(pady=10)

        # Stats & gains/losses
        self.xp_stats = tk.Label(frm, fg="#dddddd", bg="#1e1e1e")
        self.xp_stats.pack()
        self.gain_label = tk.Label(frm, fg="#00ff55", bg="#1e1e1e")
        self.gain_label.pack()
        self.loss_label = tk.Label(frm, fg="#ff5555", bg="#1e1e1e")
        self.loss_label.pack()
        self.legend_label = tk.Label(
            frm, text="📈 Gained XP   💀 Lost XP", fg="grey", bg="#1e1e1e", font=("Segoe UI", 8))
        self.legend_label.pack()

        # Motivational quote
        self.quote_label = tk.Label(
            self.root, fg="#bbbbbb", bg="#1e1e1e", wraplength=380, justify="center")
        self.quote_label.pack(pady=(5, 10))

        # Action buttons
        btns = tk.Frame(self.root, bg="#1e1e1e")
        btns.pack(pady=5)
        tk.Button(btns, text="Add Task", command=self.add_task).pack(
            side=tk.LEFT, padx=5)
        tk.Button(btns, text="View XP Log", command=self.view_log).pack(
            side=tk.LEFT, padx=5)

    def refresh_loop(self):
        now = datetime.now()
        current_task = None
        next_task = None
        earned = lost = 0
        lines = []

        # Process each scheduled task
        for t in self.schedule:
            start = datetime.strptime(t["start"], "%Y-%m-%d %H:%M")
            end = start + timedelta(minutes=t["duration"])
            if t["status"] == "⏳":
                if start <= now < end:
                    current_task = t
                    t["status"] = "🕒"
                elif now >= end:
                    done = messagebox.askyesno(
                        "Task Complete", f"Did you complete '{t['name']}'?")
                    if done:
                        t["status"] = "✓"
                        self.profile["xp"] += t["xp"]
                        earned += t["xp"]
                        lines.append(
                            f"{now.strftime('%Y-%m-%d %H:%M')} - ✅ {t['name']} (+{t['xp']} XP)")
                    else:
                        t["status"] = "X"
                        penalty = t["xp"] // 2
                        self.profile["xp"] = max(
                            0, self.profile["xp"] - penalty)
                        lost += penalty
                        lines.append(
                            f"{now.strftime('%Y-%m-%d %H:%M')} - ❌ {t['name']} (-{penalty} XP)")
                elif not next_task:
                    next_task = t

        # Append to log
        if lines:
            with open(LOG_PATH, 'a', encoding='utf-8') as logf:
                logf.write(f"\n=== {now.strftime('%Y-%m-%d')} ===\n")
                for entry in lines:
                    logf.write(entry + "\n")

        # Update profile stats
        lvl, _ = calculate_level(self.profile["xp"])
        self.profile["level"] = lvl
        self.profile.setdefault("earned_xp_display", 0)
        self.profile.setdefault("lost_xp_display", 0)
        self.profile["earned_xp_display"] += earned
        self.profile["lost_xp_display"] += lost
        save_json(PROFILE_PATH, self.profile)
        save_json(SCHEDULE_PATH, self.schedule)

        # Refresh UI and schedule next update
        self.update_ui(current_task, next_task)
        self.root.after(1000, self.refresh_loop)

    def update_ui(self, current, upcoming):
        # XP and Level display
        lvl = self.profile["level"]
        xp = self.profile["xp"]
        need = xp_for_level(lvl + 1)
        bar = draw_bar(xp, need)
        avg = sum(self.profile.get("xp_history", [])[-7:]) / \
            max(1, len(self.profile.get("xp_history", [])))
        rem = need - xp
        eta = f"{round(rem/avg,1)} days" if avg > 0 else "⚠️ Negative XP trend"
        self.user_label.config(
            text=f"👤 {self.profile['username']} | 🧬 L{lvl} | XP:{xp}/{need}\n"
                 f"📅 {datetime.now():%Y-%m-%d} 🕒 {datetime.now():%H:%M:%S}  🔋 {bar}"
        )

        # Love XP bar
        love_xp = self.profile.get("love_xp", 0)
        self.love_label.config(
            text=f"💖 Love XP: {draw_bar(love_xp,200)} {love_xp}/200"
        )

        # Current and Next tasks
        self.task_label.config(
            text=f"🔴 Current: {current['name']}" if current else "🔴 Current: None")
        if upcoming:
            name = upcoming.get("name", "?")
            time = upcoming.get("start", "")[-5:]
            self.next_label.config(text=f"🟡 Next: {name} at {time}")
        else:
            self.next_label.config(text="🟡 Next: None")

        # XP stats and gains/losses
        self.xp_stats.config(text=f"📈 Avg/day:{int(avg)} | ETA:{eta}")
        self.gain_label.config(text=f"📈 +{self.profile['earned_xp_display']}")
        self.loss_label.config(text=f"💀 -{self.profile['lost_xp_display']}")

        # Schedule list
        self.schedule_box.delete(0, tk.END)
        for t in self.schedule:
            self.schedule_box.insert(
                tk.END,
                f"[{t['status']}] {t['name']} at {t['start'][-5:]} for {t['duration']}m"
            )

        # Rotate motivational quote
        if (datetime.now() - self.last_quote_time).total_seconds() > 1800:
            self.quote_index = (self.quote_index + 1) % len(QUOTES)
            self.last_quote_time = datetime.now()
        self.quote_label.config(text=QUOTES[self.quote_index])

    def add_task(self):
        if not self.tasks:
            messagebox.showinfo("No Tasks", "You have no predefined tasks.")
            return
        opts = "\n".join(
            [f"{i+1}. {t['name']}({t['duration']}m/{t['xp']}XP)" for i, t in enumerate(self.tasks)])
        idx = simpledialog.askinteger("Add Task", f"Select task:\n{opts}")
        if not idx or idx < 1 or idx > len(self.tasks):
            return
        hr = simpledialog.askinteger("Start Hour", "Hour? (0-23)")
        if hr is None or hr < 0 or hr > 23:
            return
        sel = self.tasks[idx-1]
        st = datetime.now().replace(hour=hr, minute=0, second=0, microsecond=0)
        self.schedule.append({
            "name": sel['name'],
            "start": st.strftime("%Y-%m-%d %H:%M"),
            "duration": sel['duration'],
            "xp": sel['xp'],
            "status": "⏳"
        })
        save_json(SCHEDULE_PATH, self.schedule)

    def view_log(self):
        if not os.path.exists(LOG_PATH):
            messagebox.showinfo("XP Log", "No log.")
            return
        content = open(LOG_PATH, 'r', encoding='utf-8').read()
        w = tk.Toplevel(self.root)
        w.title("XP Log")
        txt = tk.Text(w, wrap='word')
        txt.insert('1.0', content)
        txt.pack(expand=True, fill='both')


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = XPApp(root)
        root.mainloop()
    except Exception:
        import traceback
        traceback.print_exc()
