# Perfect-You
A gamefied scheduler for those who have troubles staying consistant.
A minimalist CLI-based productivity tracker that rewards you with XP for completing scheduled tasks — and punishes you for skipping them. Think of it as a time-blocking planner mixed with an RPG.

## 🚀 Features

- 💾 Local profile with XP, level, and decay system
- 📆 Daily scheduling window (you snooze, you lose XP)
- 🧠 Predefined task types with XP rewards
- 🕒 Real-time task tracking with manual confirmation
- 📉 XP decay for inactivity
- 📈 XP bar, level-up system, and daily forecast
- 📝 Task log (`xp_log.txt`) with all completions and misses

## 📦 Files

| File           | Description                             |
|----------------|-----------------------------------------|
| `perfect_u.py` | Main application code                 |
| `tasks.json`      | Define your own tasks and XP values   |
| `profile.json`    | Auto-generated user profile           |
| `schedule.json`   | Auto-generated daily task list        |
| `xp_log.txt`      | XP tracking log for completed/missed tasks |
| `requirements.txt`| (Optional) Python dependencies        |

## 🛠 Setup

1. Install Python 3.6+
2. Clone the repo:
    ```bash
    git clone https://github.com/yourusername/xp-scheduler.git
    cd xp-scheduler
    ```
3. Run the app:
    ```bash
    python xp_scheduler.py
    ```

## 🧾 tasks.json format

```json
{
  "tasks": [
    { "name": "Work", "duration": 50, "xp": 30 },
    { "name": "Gym", "duration": 45, "xp": 25 },
    { "name": "Study", "duration": 60, "xp": 35 }
  ]
}
```
duration: in minutes

xp: XP gained on successful completion

## ❌ Miss a task?
You’ll lose half the XP you would’ve gained. Brutal but fair.

## 📈 Leveling
Stay consistent to level up. Lose XP if you ghost your own schedule.
Made for people who love time-blocking, hate guilt, and want gamified discipline.

## To do 
- A GUI version 🖥️
- ✅ A tray widget ☕
- Mobile port 📱
- Syncing it to your Google Calendar 😈
