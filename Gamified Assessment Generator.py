import tkinter as tk
from tkinter import font, messagebox
import random
import time
import threading
from google import genai
from google.genai import types
import json
import requests
from io import BytesIO
from PIL import Image, ImageTk
import tkinter.ttk as ttk # For progress bar

import json
import os
from dotenv import load_dotenv

# Load the secret .env file
load_dotenv()
class ScoreManager:
    FILE = "scores.json"

    @staticmethod
    def update_score(mode, current_score):
        # 1. Load existing scores
        data = {}
        if os.path.exists(ScoreManager.FILE):
            try:
                with open(ScoreManager.FILE, "r") as f:
                    data = json.load(f)
            except:
                pass # If file is corrupt, start fresh

        # 2. Check if this is a new high score
        # We store scores by mode (e.g., "SHOOTER": 25)
        best_score = data.get(mode, 0)
        is_new_record = False

        if current_score > best_score:
            best_score = current_score
            is_new_record = True
            data[mode] = best_score
            
            # 3. Save back to file
            with open(ScoreManager.FILE, "w") as f:
                json.dump(data, f)
        
        return best_score, is_new_record

#--- LOADING SCREEN ---
class LoadingScreen:
    def __init__(self, parent, theme):
        self.frame = tk.Frame(parent, bg=theme["bg"])
        self.frame.pack(expand=True, fill="both")
        
        # Pulsing Text
        self.lbl = tk.Label(self.frame, text="ANALYZING SCENARIO...", 
                            bg=theme["bg"], fg=theme["accent"], 
                            font=("Courier", 18, "bold"))
        self.lbl.pack(pady=(200, 20))
        
        # Modern Progress Bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("green.Horizontal.TProgressbar", background=theme["safe"])
        
        self.progress = ttk.Progressbar(self.frame, style="green.Horizontal.TProgressbar", 
                                        orient="horizontal", length=400, mode="indeterminate")
        self.progress.pack(pady=10)
        self.progress.start(10) # Speed of animation
        
        self.status = tk.Label(self.frame, text="Consulting Gemini AI...", 
                               bg=theme["bg"], fg="#666", font=("Segoe UI", 10))
        self.status.pack(pady=5)

    def update_status(self, text):
        self.status.config(text=text)

    def destroy(self):
        self.frame.destroy()

# --- GRAPHICS ENGINE ---
class TextureManager:
    # We cache images so we don't download the same "Zombie" 50 times
    cache = {}

    @staticmethod
    def get_image(keyword, size=(40, 40)):
        # 1. Check if we already have it
        key = f"{keyword}_{size}"
        if key in TextureManager.cache:
            return TextureManager.cache[key]
        
        # 2. If not, download from Pollinations.ai (Free AI Gen)
        # We ask for "pixel art" style with a white background for better blending
        url = f"https://image.pollinations.ai/prompt/pixel_art_{keyword}_isolated_white_background?width={size[0]}&height={size[1]}&nologo=true"
        
        try:
            print(f"Generating Graphics for: {keyword}...")
            response = requests.get(url, timeout=5) # 5s timeout so game doesn't freeze
            img_data = response.content
            
            # Convert raw bytes to a Tkinter-friendly image
            img = Image.open(BytesIO(img_data))
            img = img.resize(size) 
            tk_img = ImageTk.PhotoImage(img)
            
            # Save to cache and return
            TextureManager.cache[key] = tk_img
            return tk_img
        except Exception as e:
            print(f"Graphics Error: {e}")
            return None # If it fails, we will just draw a circle
# --- AUDIO ENGINE SETUP ---
try:
    import winsound
    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

# --- CONFIGURATION ---
THEMES = {
    "NEGATIVE": {
        "bg": "#0f172a", "fg": "#cbd5e1", "panel": "#1e293b",
        "accent": "#ef4444", "safe": "#3b82f6",
        "music_mode": "DRONE"
    },
    "POSITIVE": {
        "bg": "#fffbeb", "fg": "#44403c", "panel": "#ffffff",
        "accent": "#f59e0b", "safe": "#10b981",
        "music_mode": "ARPEGGIO"
    },
    "NEUTRAL": {
        "bg": "#262626", "fg": "#eeeeee", "panel": "#333333",
        "accent": "#00d2ff", "safe": "#00d2ff",
        "music_mode": "SILENCE"
    }
}

# --- ADVANCED AUDIO ENGINE ---
class AudioEngine(threading.Thread):
    def __init__(self):
        super().__init__()
        self.mode = "SILENCE"
        self.running = True
        self.daemon = True
        self.sfx_queue = [] # List to hold sound effects

    def set_mode(self, mode):
        self.mode = mode

    def play_sfx(self, name):
        """Queue a sound effect to play immediately."""
        self.sfx_queue.append(name)

    def run(self):
        while self.running:
            if not HAS_AUDIO:
                time.sleep(1)
                continue

            # 1. PRIORITY: Play Sound Effects (SFX) if any exist
            if self.sfx_queue:
                sfx = self.sfx_queue.pop(0)
                if sfx == "START":
                    # Rising "Power Up" Sound
                    winsound.Beep(440, 100)
                    winsound.Beep(554, 100)
                    winsound.Beep(659, 200)
                elif sfx == "GAMEOVER":
                    # Falling "Failure" Sound
                    winsound.Beep(400, 150)
                    winsound.Beep(300, 150)
                    winsound.Beep(200, 400)
                elif sfx == "WIN":
                    # High "Victory" Sound
                    winsound.Beep(523, 100)
                    winsound.Beep(659, 100)
                    winsound.Beep(783, 100)
                    winsound.Beep(1046, 300)
                continue # Skip BGM this loop so SFX is instant

            # 2. BACKGROUND MUSIC (BGM)
            if self.mode == "DRONE": 
                # Creepy/Dark (Long, low notes)
                freq = random.choice([100, 110, 120, 130])
                winsound.Beep(freq, 600) 
            elif self.mode == "ARPEGGIO": 
                # Happy/Calm (C Major Chord)
                notes = [523, 659, 783, 1046]
                winsound.Beep(random.choice(notes), 200)
                time.sleep(0.1)
            elif self.mode == "ACTION": 
                # Fast/Tense (Short, random low beeps for Shooter/Dodger)
                winsound.Beep(random.choice([200, 250, 300]), 100)
            else:
                # Silence
                time.sleep(0.2)

    def stop(self):
        self.running = False
        
# --- NLP ENGINE WITH GEMINI INTEGRATION (FIXED) ---
class GeminiBrain:
    def __init__(self):
        # OLD LINE (DELETE THIS):
        # self.API_KEY = "AIzaSy..." 

        # NEW LINE (SECURE):
        self.API_KEY = os.getenv("GEMINI_API_KEY")

        if not self.API_KEY:
            print("CRITICAL ERROR: API Key not found. Check your .env file!")
            self.active = False
            return

    def analyze(self, text):
        if not self.active:
            print("AI is inactive. Check API Key.")
            return None

        prompt = f"""
        Analyze this educational scenario for a game engine: "{text}"
        
        Return ONLY a raw JSON object (no markdown) with these keys:
        - mode: One of [SHOOTER, RESOURCE, SORTER, DODGER, COLLECTOR, CONNECTOR] based on the action.
        - verb: The main action verb (uppercase).
        - ent_a: The subject entity (e.g. Player/Hero).
        - ent_b: The target entity (e.g. Enemy/Apple).
        - sentiment: POSITIVE or NEGATIVE based on the mood.
        
        Example JSON: {{"mode": "SHOOTER", "verb": "FIGHT", "ent_a": "Hero", "ent_b": "Monster", "sentiment": "NEGATIVE"}}
        """
        
        try:
            # 1. Use the new 'gemini-2.5-flash' model you found
            # 2. Force JSON response for perfect game data
            response = self.client.models.generate_content(
                model="gemini-2.5-flash", 
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            # The new SDK returns a rich object, we want the text
            if response.text:
                return json.loads(response.text)
            return None
            
        except Exception as e:
            print(f"Parsing Error: {e}")
            return None
# --- RESULTS SCREEN ---
class ResultsScreen:
    def __init__(self, parent, theme, score, mode, high_score, is_new_record, on_replay, on_menu):
        self.parent = parent
        self.frame = tk.Frame(parent, bg=theme["bg"])
        self.frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Header
        tk.Label(self.frame, text="ASSESSMENT COMPLETE", bg=theme["bg"], fg=theme["fg"], font=("Courier", 20, "bold")).pack(pady=(20, 10))
        
        # Grade Logic
        self.grade = "C"
        if mode == "SHOOTER":
            if score > 20: self.grade = "S"
            elif score > 15: self.grade = "A"
            elif score > 10: self.grade = "B"
        # (Simplified logic for brevity, you can keep your old complex logic if you want)
        
        # Big Grade Display
        grade_color = theme["safe"] if self.grade in ["S", "A"] else theme["accent"]
        tk.Label(self.frame, text=self.grade, bg=theme["bg"], fg=grade_color, font=("Segoe UI", 72, "bold")).pack()
        
        # --- NEW: HIGH SCORE DISPLAY ---
        score_color = theme["fg"]
        if is_new_record:
            score_color = "#00ff00" # Bright Green for new record
            tk.Label(self.frame, text="★ NEW RECORD! ★", bg=theme["bg"], fg=score_color, font=("Segoe UI", 12, "bold")).pack()
            
        score_text = f"Score: {score:.1f}  |  Best: {high_score:.1f}"
        tk.Label(self.frame, text=score_text, bg=theme["bg"], fg=score_color, font=("Segoe UI", 16)).pack(pady=5)
        # -------------------------------

        # Buttons
        btn_frame = tk.Frame(self.frame, bg=theme["bg"])
        btn_frame.pack(pady=40)
        tk.Button(btn_frame, text="REPLAY", command=on_replay, bg=theme["panel"], fg=theme["fg"], width=15).pack(side="left", padx=10)
        tk.Button(btn_frame, text="NEW SCENARIO", command=on_menu, bg=theme["accent"], fg="white", width=15).pack(side="left", padx=10)

    def destroy(self):
        self.frame.destroy()
# --- PARTICLE SYSTEM ---
class Particle:
    def __init__(self, canvas, x, y, color):
        self.canvas = canvas
        self.life = 15 # How many frames it lives
        # Create a tiny 4x4 pixel chunk
        self.id = canvas.create_rectangle(x, y, x+4, y+4, fill=color, outline="")
        # Random explosion velocity
        self.vx = random.choice([-5, -3, 3, 5])
        self.vy = random.choice([-5, -3, 3, 5])

    def update(self):
        self.life -= 1
        # Move the particle
        self.canvas.move(self.id, self.vx, self.vy)
        # Gravity effect
        self.vy += 1 
        
        if self.life <= 0:
            self.canvas.delete(self.id)
            return False # Dead
        return True # Alive
# --- GAME CLASSES ---

#--- ResourceGame (unchanged) ---
class ResourceGame:
    def __init__(self, parent, theme, data, on_game_over):
        self.parent = parent
        self.theme = theme
        self.on_game_over = on_game_over
        self.data = data
        self.running = True
        self.val = 50
        self.score = 0.0
        self.time_left = 30
        
        self.frame = tk.Frame(parent, bg=theme["bg"])
        self.frame.pack(expand=True, fill="both")
        
        verb = data.get('verb', 'BALANCE')
        ent = data.get('ent_b', 'SYSTEM').upper()
        tk.Label(self.frame, text=f"GOAL: {verb} {ent}", bg=theme["bg"], fg=theme["safe"], font=("Courier", 16, "bold")).pack(pady=10)
        self.lbl_stats = tk.Label(self.frame, text=f"Stability: 0.0s | Time: 30", bg=theme["bg"], fg=theme["fg"], font=("Segoe UI", 12))
        self.lbl_stats.pack()

        self.canvas = tk.Canvas(self.frame, width=50, height=200, bg=theme["panel"], highlightthickness=0)
        self.canvas.pack(pady=20)
        self.canvas.create_rectangle(0, 80, 50, 120, fill="#222", outline=theme["safe"], dash=(2,2))
        self.bar = self.canvas.create_rectangle(0, 100, 50, 200, fill=theme["safe"])

        btn_frame = tk.Frame(self.frame, bg=theme["bg"])
        btn_frame.pack()
        tk.Button(btn_frame, text="GROW", command=lambda: self.mod(10), bg=theme["panel"], fg="white", width=10).pack(side="left", padx=10)
        tk.Button(btn_frame, text="REDUCE", command=lambda: self.mod(-10), bg=theme["panel"], fg="white", width=10).pack(side="left", padx=10)

        self.loop()
        self.timer_loop()

    def mod(self, d): self.val = max(0, min(100, self.val + d)); self.update_ui()
    def update_stats(self): self.lbl_stats.config(text=f"Stability: {self.score:.1f}s | Time: {self.time_left}")

    def timer_loop(self):
        if not self.running: return
        self.time_left -= 1
        self.update_stats()
        if self.time_left <= 0:
            self.running = False
            self.on_game_over(self.score, "RESOURCE")
        else:
            self.parent.after(1000, self.timer_loop)

    def loop(self):
        if not self.running: return
        self.val = max(0, min(100, self.val + random.choice([-1, 0, 1])))
        if 40 <= self.val <= 60: self.score += 0.2
        self.update_ui()
        self.parent.after(200, self.loop)

    def update_ui(self):
        h = 200 - (self.val * 2)
        self.canvas.coords(self.bar, 0, h, 50, 200)
        self.canvas.itemconfig(self.bar, fill=self.theme["safe"] if 40 <= self.val <= 60 else self.theme["accent"])
        self.update_stats()

    def destroy(self): 
        self.running = False
        self.frame.destroy()

#--- SORTER GAME ---
class SorterGame:
    def __init__(self, parent, theme, data, on_game_over):
        self.parent = parent
        self.root = parent.winfo_toplevel() # <--- GET THE MAIN WINDOW
        self.theme = theme
        self.data = data
        self.on_game_over = on_game_over
        self.running = True
        self.score = 0
        self.time_left = 30
        self.items = []
        
        self.frame = tk.Frame(parent, bg=theme["bg"])
        self.frame.pack(expand=True, fill="both")
        
        # UI Setup
        ea = data.get('ent_a', 'A')
        eb = data.get('ent_b', 'B')
        tk.Label(self.frame, text=f"SORT: {ea} (LEFT) vs {eb} (RIGHT)", bg=theme["bg"], fg=theme["fg"], font=("Courier", 14, "bold")).pack(pady=10)
        self.lbl_stats = tk.Label(self.frame, text="Score: 0 | Time: 30", bg=theme["bg"], fg=theme["fg"], font=("Segoe UI", 12))
        self.lbl_stats.pack()

        self.canvas = tk.Canvas(self.frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_line(300, 0, 300, 1000, fill="#555") 

        # --- KEY BINDING FIX ---
        # Bind to the ROOT window so it works even if focus is elsewhere
        self.root.bind("<Left>", lambda e: self.sort("LEFT"))
        self.root.bind("<Right>", lambda e: self.sort("RIGHT"))
        self.frame.focus_set() # Force focus to this game
        # -----------------------
        
        self.spawn_loop()
        self.move_loop()
        self.timer_loop()

    def update_stats(self): self.lbl_stats.config(text=f"Score: {self.score} | Time: {self.time_left}")

    def timer_loop(self):
        if not self.running: return
        self.time_left -= 1
        self.update_stats()
        if self.time_left <= 0:
            self.running = False
            self.on_game_over(self.score, "SORTER")
        else:
            self.parent.after(1000, self.timer_loop)

    def spawn_loop(self):
        if not self.running: return
        w = self.canvas.winfo_width() or 600
        ea = self.data.get('ent_a', 'Category A')
        eb = self.data.get('ent_b', 'Category B')
        cat = random.choice([ea, eb])
        color = self.theme["safe"] if cat == ea else self.theme["accent"]
        t_id = self.canvas.create_text(w/2, 0, text=cat, fill=color, font=("Courier", 12, "bold"))
        self.items.append({"id": t_id, "cat": cat, "y": 0, "active": True})
        self.parent.after(1500, self.spawn_loop)

    def move_loop(self):
        if not self.running: return
        h = self.canvas.winfo_height()
        for i in self.items:
            if i["active"]:
                self.canvas.move(i["id"], 0, 3)
                i["y"] += 3
                if i["y"] > h: 
                    self.canvas.delete(i["id"])
                    i["active"] = False
        self.items = [i for i in self.items if i["active"]]
        self.parent.after(50, self.move_loop)

    def sort(self, direction):
        if not self.items: return
        active = [i for i in self.items if i["active"]]
        if not active: return
        target = max(active, key=lambda x: x["y"])
        
        w = self.canvas.winfo_width()
        is_correct = False
        
        ea = self.data.get('ent_a', 'Category A')
        eb = self.data.get('ent_b', 'Category B')

        if direction == "LEFT" and target["cat"] == ea: is_correct = True
        if direction == "RIGHT" and target["cat"] == eb: is_correct = True
        
        target_x = w/4 if direction == "LEFT" else w*3/4
        self.canvas.coords(target["id"], target_x, target["y"])
        
        if is_correct:
            self.score += 1
            self.canvas.itemconfig(target["id"], fill="#0f0")
        else:
            self.canvas.itemconfig(target["id"], fill="#f00")
            
        target["active"] = False
        self.parent.after(200, lambda: self.canvas.delete(target["id"]))
        self.update_stats()

    def destroy(self):
        self.running = False
        # Unbind from ROOT so keys don't break the menu later
        self.root.unbind("<Left>")
        self.root.unbind("<Right>")
        self.frame.destroy()

#--- COLLECTOR GAME ---
class CollectorGame:
    def __init__(self, parent, theme, data, on_game_over):
        self.parent = parent
        self.theme = theme
        self.on_game_over = on_game_over
        self.data = data
        self.running = True
        self.score = 0
        self.time_left = 30
        self.frame = tk.Frame(parent, bg=theme["bg"])
        self.frame.pack(expand=True, fill="both")
        
        ent = data.get('ent_a', 'ITEM').upper()
        tk.Label(self.frame, text=f"COLLECT: {ent}", bg=theme["bg"], fg=theme["safe"], font=("Courier", 16, "bold")).pack(pady=10)
        self.lbl_stats = tk.Label(self.frame, text=f"Score: 0 | Time: {self.time_left}", bg=theme["bg"], fg=theme["fg"], font=("Segoe UI", 12))
        self.lbl_stats.pack()

        self.canvas = tk.Canvas(self.frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_click)

        self.spawn_loop()
        self.timer_loop()

    def timer_loop(self):
        if not self.running: return
        self.time_left -= 1
        self.lbl_stats.config(text=f"Score: {self.score} | Time: {self.time_left}")
        if self.time_left <= 0:
            self.running = False
            self.on_game_over(self.score, "COLLECTOR")
        else:
            self.parent.after(1000, self.timer_loop)

    def spawn_loop(self):
        if not self.running: return
        w = self.canvas.winfo_width()
        if w < 50: w = 600
        h = self.canvas.winfo_height()
        if h < 50: h = 400
        x = random.randint(20, w-20)
        y = random.randint(20, h-20)
        item = self.canvas.create_oval(x-15, y-15, x+15, y+15, fill=self.theme["safe"], outline="white")
        # Auto remove after 1.5s
        self.parent.after(1500, lambda: self.canvas.delete(item) if self.running else None)
        self.parent.after(800, self.spawn_loop)

    def on_click(self, event):
        x, y = event.x, event.y
        closest = self.canvas.find_closest(x, y)
        if closest:
            self.canvas.delete(closest[0])
            self.score += 1
            self.lbl_stats.config(text=f"Score: {self.score} | Time: {self.time_left}")

    def destroy(self): 
        self.running = False
        self.frame.destroy()

#--- NEW GAME: SHOOTER WITH PARTICLES ---
class ShooterGame:
    def __init__(self, parent, theme, data, on_game_over):
        self.parent = parent
        self.theme = theme
        self.on_game_over = on_game_over
        self.data = data 
        
        self.running = True
        self.score = 0
        self.targets = []
        self.particles = [] # <--- LIST TO STORE PARTICLES
        self.time_left = 30
        
        self.frame = tk.Frame(parent, bg=theme["bg"])
        self.frame.pack(expand=True, fill="both")
        
        self.setup_ui(data)
        
        self.canvas = tk.Canvas(self.frame, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_click)
        
        self.spawn_loop()
        self.move_loop()
        self.particle_loop() # <--- START PARTICLE PHYSICS
        self.timer_loop()

    def setup_ui(self, data):
        verb = data.get('verb', 'ELIMINATE')
        ent = data.get('ent_b', 'TARGET').upper()
        tk.Label(self.frame, text=f"MISSION: {verb} THE {ent}S", 
                 bg=self.theme["bg"], fg=self.theme["accent"], 
                 font=("Courier", 16, "bold")).pack(pady=10)
        self.lbl_stats = tk.Label(self.frame, text=f"Kills: 0 | Time: {self.time_left}", 
                                  bg=self.theme["bg"], fg=self.theme["fg"], font=("Segoe UI", 12))
        self.lbl_stats.pack()

    def update_stats(self):
        self.lbl_stats.config(text=f"Kills: {self.score} | Time: {self.time_left}")

    def timer_loop(self):
        if not self.running: return
        self.time_left -= 1
        self.update_stats()
        if self.time_left <= 0:
            self.running = False
            self.on_game_over(self.score, "SHOOTER")
        else:
            self.parent.after(1000, self.timer_loop)

    def spawn_loop(self):
        if not self.running: return
        w = self.canvas.winfo_width()
        if w < 50: w = 600
        x = random.randint(30, w-30)
        
        enemy_name = self.data.get('ent_b', 'Enemy') 
        img = TextureManager.get_image(enemy_name)
        
        if img:
            t_id = self.canvas.create_image(x, 0, image=img, anchor="n")
            if not hasattr(self.canvas, "refs"): self.canvas.refs = {}
            self.canvas.refs[t_id] = img 
        else:
            t_id = self.canvas.create_oval(x-20, 0, x+20, 40, fill=self.theme["accent"], outline="white")

        self.targets.append(t_id)
        self.parent.after(1000, self.spawn_loop)

    def move_loop(self):
        if not self.running: return
        h = self.canvas.winfo_height()
        for t in self.targets[:]:
            self.canvas.move(t, 0, 5)
            bbox = self.canvas.bbox(t)
            if bbox and bbox[3] > h:
                self.canvas.delete(t)
                self.targets.remove(t)
                if hasattr(self.canvas, "refs") and t in self.canvas.refs:
                    del self.canvas.refs[t]
        self.parent.after(50, self.move_loop)

    # --- NEW: PARTICLE UPDATE LOOP ---
    def particle_loop(self):
        if not self.running: return
        # Update all particles and keep only the living ones
        self.particles = [p for p in self.particles if p.update()]
        self.parent.after(30, self.particle_loop)
    # ---------------------------------

    def on_click(self, event):
        x, y = event.x, event.y
        closest = self.canvas.find_closest(x, y)
        if closest:
            t = closest[0]
            c = self.canvas.bbox(t) 
            if c and c[0] <= x <= c[2] and c[1] <= y <= c[3]:
                # --- EXPLOSION EFFECT ---
                # Spawn 8 particles at the click location
                for _ in range(8):
                    p = Particle(self.canvas, x, y, self.theme["accent"])
                    self.particles.append(p)
                # ------------------------

                self.canvas.delete(t)
                if t in self.targets: self.targets.remove(t)
                self.score += 1
                self.update_stats()

    def destroy(self):
        self.running = False
        self.frame.destroy()

# --- NEW GAME: DODGER ---
class DodgerGame:
    def __init__(self, parent, theme, data, on_game_over):
        self.parent = parent
        self.theme = theme
        self.on_game_over = on_game_over
        self.running = True
        self.time_left = 30
        self.enemies = []
        
        self.frame = tk.Frame(parent, bg=theme["bg"])
        self.frame.pack(expand=True, fill="both")
        
        tk.Label(self.frame, text=f"SURVIVE: AVOID {data['ent_b'].upper()}", bg=theme["bg"], fg=theme["accent"], font=("Courier", 16, "bold")).pack(pady=10)
        self.lbl_timer = tk.Label(self.frame, text=f"Time: {self.time_left}", bg=theme["bg"], fg=theme["fg"], font=("Segoe UI", 12))
        self.lbl_timer.pack()

        self.canvas = tk.Canvas(self.frame, bg="black", highlightthickness=0, cursor="none")
        self.canvas.pack(fill="both", expand=True)
        
        # Player Dot
        self.player_id = self.canvas.create_oval(0, 0, 20, 20, fill="#3b82f6", outline="white")
        
        self.canvas.bind("<Motion>", self.update_player)
        self.spawn_enemies()
        self.move_loop()
        self.timer_loop()

    def update_player(self, event):
        x, y = event.x, event.y
        self.canvas.coords(self.player_id, x-10, y-10, x+10, y+10)

    def spawn_enemies(self):
        # Create 5 enemies
        for _ in range(5):
            x, y = random.randint(50, 500), random.randint(50, 300)
            eid = self.canvas.create_rectangle(x, y, x+30, y+30, fill=self.theme["accent"], outline="white")
            self.enemies.append({"id": eid, "vx": random.choice([-4, 4]), "vy": random.choice([-4, 4])})

    def move_loop(self):
        if not self.running: return
        w = self.canvas.winfo_width()
        if w < 50: w = 600
        
        h = self.canvas.winfo_height()
        if h < 50: h = 400
        
        px1, py1, px2, py2 = self.canvas.coords(self.player_id)
        
        for e in self.enemies:
            self.canvas.move(e["id"], e["vx"], e["vy"])
            ex1, ey1, ex2, ey2 = self.canvas.coords(e["id"])
            
            # Wall Bounce
            if ex1 <= 0 or ex2 >= w: e["vx"] *= -1
            if ey1 <= 0 or ey2 >= h: e["vy"] *= -1
            
            # Collision Check
            if not (px2 < ex1 or px1 > ex2 or py2 < ey1 or py1 > ey2):
                self.game_over()
                return

        self.parent.after(30, self.move_loop)

    def timer_loop(self):
        if not self.running: return
        self.time_left -= 1
        self.lbl_timer.config(text=f"Time: {self.time_left}")
        if self.time_left <= 0:
            self.running = False
            self.on_game_over(30, "DODGER") # Survived full duration
        else:
            self.parent.after(1000, self.timer_loop)

    def game_over(self):
        self.running = False
        score = 30 - self.time_left
        self.on_game_over(score, "DODGER")

    def destroy(self):
        self.running = False
        self.frame.destroy()

# --- NEW GAME: CONNECTOR (FIXED) ---
class ConnectorGame:
    def __init__(self, parent, theme, data, on_game_over):
        self.parent = parent
        self.theme = theme
        self.on_game_over = on_game_over
        self.running = True
        self.time_left = 30
        self.is_active = False # <--- NEW: Game doesn't count until you touch Start
        
        self.frame = tk.Frame(parent, bg=theme["bg"])
        self.frame.pack(expand=True, fill="both")
        
        tk.Label(self.frame, text=f"CONNECT: {data['ent_a']} -> {data['ent_b']}", bg=theme["bg"], fg=theme["safe"], font=("Courier", 14, "bold")).pack(pady=10)
        self.lbl_timer = tk.Label(self.frame, text=f"Time: {self.time_left} (HOVER START TO BEGIN)", bg=theme["bg"], fg=theme["fg"], font=("Segoe UI", 12))
        self.lbl_timer.pack()

        # Canvas: bg is danger, line is safe
        self.canvas = tk.Canvas(self.frame, bg=theme["accent"], highlightthickness=0) 
        self.canvas.pack(fill="both", expand=True, padx=20, pady=20)
        
        self.canvas.bind("<Configure>", self.draw_level)
        self.canvas.bind("<Motion>", self.check_pos)
        
        self.timer_loop()

    def draw_level(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        # FIX: Prevent drawing on tiny canvas (prevents crash)
        if w < 100: return 

        # Draw Start
        self.canvas.create_rectangle(0, h/2-30, 60, h/2+30, fill=self.theme["safe"], tags="start")
        self.canvas.create_text(30, h/2, text="START", fill="white", font=("Arial", 10, "bold"))
        
        # Draw Goal
        self.canvas.create_rectangle(w-60, h/2-30, w, h/2+30, fill=self.theme["safe"], tags="goal")
        self.canvas.create_text(w-30, h/2, text="GOAL", fill="white", font=("Arial", 10, "bold"))

        # Draw Path (Thick Line)
        points = [60, h/2]
        seg_len = (w - 120) / 5
        for i in range(1, 6):
            x = 60 + i * seg_len
            y = h/2 + random.randint(-100, 100)
            y = max(50, min(h-50, y))
            points.append(x)
            points.append(y)
        points.append(w-60)
        points.append(h/2)
        
        self.canvas.create_line(points, width=40, capstyle=tk.ROUND, joinstyle=tk.ROUND, fill="#444", tags="path")

    def check_pos(self, event):
        if not self.running: return
        x, y = event.x, event.y
        
        items = self.canvas.find_overlapping(x, y, x+1, y+1)
        tags = []
        for i in items:
            tags += self.canvas.gettags(i)
        
        # LOGIC FIX:
        # 1. If game hasn't started, ONLY check for START zone
        if not self.is_active:
            if "start" in tags:
                self.is_active = True
                self.canvas.itemconfig("start", fill="#fff") # Visual cue
                self.lbl_timer.config(text=f"Time: {self.time_left} (GO!)")
            return

        # 2. If game IS active, check for Win/Fail
        if "goal" in tags:
            self.running = False
            self.on_game_over(self.time_left, "CONNECTOR")
            return

        in_safe_zone = "path" in tags or "start" in tags
        
        if not in_safe_zone:
            self.reset_to_start()

    def reset_to_start(self):
        # Penalty Logic
        self.is_active = False # Stop checking until they go back to start
        self.canvas.config(bg="#ff0000")
        self.parent.after(200, lambda: self.canvas.config(bg=self.theme["accent"]))
        self.canvas.itemconfig("start", fill=self.theme["safe"]) # Reset start color
        
        self.time_left = max(0, self.time_left - 3)
        self.lbl_timer.config(text=f"Time: {self.time_left} (PENALTY! RETURN TO START)")

    def timer_loop(self):
        if not self.running: return
        # Only drain time if game is active
        if self.is_active:
            self.time_left -= 1
            self.lbl_timer.config(text=f"Time: {self.time_left}")
        
        if self.time_left <= 0:
            self.running = False
            self.on_game_over(0, "CONNECTOR")
        else:
            self.parent.after(1000, self.timer_loop)

    def destroy(self):
        self.running = False
        self.frame.destroy()
# --- MAIN APP ---
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Generative Game Engine")
        self.root.geometry("800x650")
        
        self.nlp = GeminiBrain()
        self.audio = AudioEngine()
        self.audio.start()
        
        self.current_screen = None
        self.game_instance = None # Track active game to call .destroy() on it
        self.current_theme = THEMES["NEUTRAL"]
        self.last_input_data = None 
        
        self.setup_menu()

    def clear_current_context(self):
        """Safely stops game loops and destroys UI elements."""
        if self.game_instance:
            self.game_instance.destroy() # Sets running=False
            self.game_instance = None
        
        if self.current_screen:
            self.current_screen.destroy()
            self.current_screen = None

    def setup_menu(self):
        self.clear_current_context()
        
        self.menu_frame = tk.Frame(self.root, bg=self.current_theme["bg"])
        self.menu_frame.pack(fill="both", expand=True)
        self.current_screen = self.menu_frame
        
        # Header
        tk.Label(self.menu_frame, text="TEXT-TO-GAME ENGINE", bg=self.current_theme["bg"], 
                 fg=self.current_theme["fg"], font=("Courier", 24, "bold")).pack(pady=40)
        
        # Input
        tk.Label(self.menu_frame, text="Enter Educational Scenario:", 
                 bg=self.current_theme["bg"], fg="#888", font=("Segoe UI", 12)).pack()
        
        self.entry = tk.Entry(self.menu_frame, font=("Segoe UI", 14), width=40)
        self.entry.pack(pady=10)
        self.entry.insert(0, "The hero escaped the collapsing dungeon.") 
        
        tk.Button(self.menu_frame, text="GENERATE GAME", command=self.generate, 
                  bg=self.current_theme["accent"], fg="white", font=("Segoe UI", 12, "bold"), padx=20, pady=10).pack(pady=20)

    def apply_theme(self, sentiment):
        t = THEMES[sentiment]
        self.current_theme = t
        self.root.configure(bg=t["bg"])
        self.audio.set_mode(t["music_mode"])
        return t

    # --- REPLACE YOUR OLD generate() METHOD WITH THIS ---
    def generate(self):
        text = self.entry.get()
        if not text: return
        
        # 1. Clear Menu & Show Loading Screen
        self.clear_current_context()
        self.current_screen = LoadingScreen(self.root, self.current_theme)
        
        # 2. Start the Heavy Work in a Background Thread
        # This prevents the window from freezing saying "Not Responding"
        t = threading.Thread(target=self.run_async_generation, args=(text,))
        t.start()

    # --- NEW METHOD: RUNS IN BACKGROUND ---
    def run_async_generation(self, text):
        # Step A: Get Game Data from Gemini
        data = self.nlp.analyze(text)
        
        if not data:
            # If failed, go back to menu (scheduled on main thread)
            self.root.after(0, self.setup_menu)
            return

        # Step B: Pre-load the Image (So it doesn't pop in later)
        if "ent_b" in data:
            enemy = data["ent_b"]
            # Tell UI we are downloading
            self.root.after(0, lambda: self.current_screen.update_status(f"Generating Graphics for '{enemy}'..."))
            # Fetch image (TextureManager caches it automatically)
            TextureManager.get_image(enemy)

        # Step C: Start Game (Must be called on Main Thread)
        self.last_input_data = data
        self.root.after(0, lambda: self.start_game(data))
    def start_game(self, data):
        self.clear_current_context()
        
        # 1. Play Start Sound
        self.audio.play_sfx("START") # <--- NEW LINE
        
        # 2. Set Music Mode based on Game Type
        # (This fixes "Same sound always playing")
        mode = data["mode"]
        theme_sentiment = data["sentiment"]
        
        if mode in ["SHOOTER", "DODGER"]:
            self.audio.set_mode("ACTION") # Fast music for action games
        elif theme_sentiment == "NEGATIVE":
            self.audio.set_mode("DRONE")  # Scary music for sad themes
        else:
            self.audio.set_mode("ARPEGGIO") # Happy music for others
          
        # Apply Theme
        theme = self.apply_theme(data["sentiment"])
        
        # Create Container
        container = tk.Frame(self.root, bg=theme["bg"])
        container.pack(fill="both", expand=True)
        self.current_screen = container

        # Instantiate specific Game Class based on Mode
        mode = data["mode"]
        
        if mode == "SHOOTER":
            self.game_instance = ShooterGame(container, theme, data, self.show_results)
        elif mode == "RESOURCE":
            self.game_instance = ResourceGame(container, theme, data, self.show_results)
        elif mode == "SORTER":
            self.game_instance = SorterGame(container, theme, data, self.show_results)
        elif mode == "DODGER":
            self.game_instance = DodgerGame(container, theme, data, self.show_results)
        elif mode == "COLLECTOR":
            self.game_instance = CollectorGame(container, theme, data, self.show_results)
        elif mode == "CONNECTOR":
            self.game_instance = ConnectorGame(container, theme, data, self.show_results)
        else:
            # Fallback
            self.game_instance = ResourceGame(container, theme, data, self.show_results)

    def show_results(self, score, mode):
        self.clear_current_context()

        # 1. Stop Audio
        self.audio.set_mode("SILENCE")

        # 2. Save/Load High Score
        high_score, is_new_record = ScoreManager.update_score(mode, score)

        # 3. Play Appropriate Sound
        if is_new_record:
            self.audio.play_sfx("WIN") # Victory sound for new record
        elif score > 5:
             # Basic win sound if score is okay but not a record
            self.audio.play_sfx("WIN") 
        else:
            self.audio.play_sfx("GAMEOVER")

        # 4. Show Screen (Passing new arguments)
        self.current_screen = ResultsScreen(
            self.root, 
            self.current_theme, 
            score, 
            mode, 
            high_score,     # <--- Passed here
            is_new_record,  # <--- Passed here
            self.replay_game, 
            self.setup_menu
        )

    def replay_game(self):
        if self.last_input_data:
            self.start_game(self.last_input_data)

    def on_close(self):
        self.audio.stop()
        if self.game_instance:
            self.game_instance.destroy()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.protocol("WM_DELETE_WINDOW", app.on_close)
    root.mainloop()
