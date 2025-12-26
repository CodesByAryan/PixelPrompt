# 👾 PixelPrompt: AI-Powered Generative Game Engine

> **Turn any text into a playable video game instantly.**

PixelPrompt is an experimental "Text-to-Game" engine built with Python. It uses **Google Gemini 2.5 Flash** to analyze educational scenarios and **Pollinations.ai** to generate pixel-art graphics in real-time.

Simply type a sentence like *"The firewall blocks the hackers"* or *"The white blood cells hunt the virus,"* and the engine constructs a unique game mechanism, rules, and visuals on the fly.

## 🎮 Features
* **Generative Gameplay:** The AI selects the best game mode (Shooter, Dodger, Sorter, Connector, etc.) based on the verb in your sentence.
* **Real-Time Pixel Art:** Entities are generated instantly using AI image diffusion.
* **Psychometric Profiling:** Analyzes player reflexes and decision-making styles.
* **Persistent High Scores:** Saves your best runs locally.
* **Dynamic Audio:** Adaptive sound engine that changes mood based on the game sentiment.

## 🕹️ Game Modes
1.  **SHOOTER:** Destroy falling enemies (e.g., *"Antibiotics kill bacteria"*).
2.  **DODGER:** Survive against chasing threats (e.g., *"Avoid the meteors"*).
3.  **SORTER:** Categorize items into left/right bins (e.g., *"Separate trash vs recycling"*).
4.  **RESOURCE:** Maintain balance/stability (e.g., *"Keep the economy stable"*).
5.  **CONNECTOR:** Draw a path between two concepts without touching walls.
6.  **COLLECTOR:** Gather specific items before time runs out.

## 🛠️ Tech Stack
* **Core:** Python 3.13+
* **AI Brain:** Google Gemini 2.5 Flash (via `google-genai` SDK)
* **Graphics:** Tkinter (Canvas) + PIL + Pollinations.ai API
* **Build:** PyInstaller (for EXE generation)

## 🚀 How to Run

### Option 1: Run from Source (Recommended for Devs)
1.  Clone this repository.
2.  Install dependencies:
    ```bash
    pip install google-genai requests pillow python-dotenv
    ```
3.  **Setup API Key (Secure Method):**
    * Create a file named `.env` in the project folder.
    * Add your Google Gemini API key inside it like this:
      ```ini
      GEMINI_API_KEY=AIzaSyYourKeyHere...
      ```
    * *Note: The `.env` file is ignored by Git to keep your key safe.*
4.  Run the script:
    ```bash
    python "Gamified Assessment Generator.py"
    ```

### Option 2: Run the Executable
1.  Download `PixelPrompt.exe` from the Releases tab (if available).
2.  Run the file. No Python installation required.

## ⚠️ Important Note on API Usage
This application requires a **Google Gemini API Key**.
* It uses the free tier of Gemini.
* If you fork this project, **DO NOT** commit your API key to GitHub. Always use a `.env` file.

## 👨‍💻 About the Developer
**Aryan Biswas**
* B.Tech Computer Science & Business Systems (CSBS)
* 2nd Year Student @ Asansol Engineering College
* Passionate about Generative AI, Python, and Game Development.

---
*Created as a Generative AI experiment.*