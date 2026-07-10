# SmartBite: Personalized AI Nutrition Agent

An AI-powered, personalized Nutrition Assistant web application built using **Python Flask**, modern responsive **CSS Glassmorphism**, and **IBM Watsonx.ai** using **IBM Granite models**. 

Designed and optimized for the **IBM SkillsBuild AICTE-2026 University Engagements** (Problem Statement #8: Nutrition Agent).

---

## 🚀 Key Features

* **AI Nutrition Coach Chat:** Conversational agent powered by IBM Granite models (`ibm/granite-3-8b-instruct`), custom-tailored with specific guidelines to offer warm, encourage, and scientifically backed diet plans.
* **Calorie & Macro Calculator:** Built-in scientific calculator that computes Basal Metabolic Rate (BMR) using the **Mifflin-St Jeor Equation** and adjusts targets based on the user's specific goals (Weight Loss, Muscle Gain, or Maintenance).
* **Interactive BMI Visualizer:** Dynamic real-time calculation and visualization of Body Mass Index on a color-spectrum scale.
* **Hydration Tracker:** Visual daily water logger with animated glassmorphic progress waves.
* **Smart Food Swaps:** Fully searchable database of common Indian cuisines showing macro and calorie comparisons between unhealthy foods and healthy alternatives.
* **Family Profiles:** Support for tracking and switching between multiple household member profiles.
* **Watsonx Credentials Portal:** Integrated settings dashboard allowing users to input their IBM Cloud API Key, Project ID, Region, and switch between live Watsonx access and a smart local simulation mode.

---

## 🛠️ Technology Stack

1. **Backend:** Python 3.10+, Flask Web Server, `python-dotenv`, `requests`, `markdown`.
2. **AI Engine:** IBM Watsonx.ai with IBM Granite 3.0 Instruct models.
3. **Frontend:** HTML5, Vanilla CSS3 (Custom design tokens, Glassmorphism, responsive sidebar layout), JavaScript, FontAwesome Icons.
4. **Environment Management:** Virtual environment configured with `requirements.txt` and a Windows `run.bat` launcher.

---

## 📐 Scientific Formulation

The application calculates energy requirements dynamically using standard dietetic equations:

### Mifflin-St Jeor Equation (BMR)
* **Men:** $BMR = 10 \times \text{weight (kg)} + 6.25 \times \text{height (cm)} - 5 \times \text{age (years)} + 5$
* **Women:** $BMR = 10 \times \text{weight (kg)} + 6.25 \times \text{height (cm)} - 5 \times \text{age (years)} - 161$

### Daily Calorie Target (TDEE)
Adjusted for light daily activity:
$$\text{TDEE} = \text{BMR} \times 1.375$$

* **Weight Loss:** Target Calorie Intake = $\text{TDEE} - 400 \text{ kcal}$ (capped at a minimum of $1200 \text{ kcal}$)
* **Weight Gain / Muscle Building:** Target Calorie Intake = $\text{TDEE} + 300\text{-}400 \text{ kcal}$

---

## ⚙️ Installation & Running Guide

### One-Click Launch (Windows)
Simply double-click the `run.bat` file in the project folder. The script will automatically:
1. Create a Python virtual environment (`.venv`).
2. Upgrade `pip` and install all required libraries.
3. Launch the local web server on [http://localhost:5000](http://localhost:5000).

### Manual Installation
If you prefer running manual commands in the terminal:

1. Clone or download this repository.
2. Initialize virtual environment:
   ```bash
   python -m venv .venv
   ```
3. Activate the virtual environment:
   * **Windows:** `.venv\Scripts\activate`
   * **macOS/Linux:** `source .venv/bin/activate`
4. Install requirements:
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Run the application:
   ```bash
   python app.py
   ```
6. Open your web browser and navigate to [http://localhost:5000](http://localhost:5000).

---

## 🔌 Connecting to IBM Watsonx.ai

By default, the application runs in **Local Offline Simulation Mode** to allow instant testing. To connect to the live IBM Watsonx.ai cloud model:

1. Log in to [cloud.ibm.com](https://cloud.ibm.com/) and create a free **watsonx.ai** catalog service (Sydney/Dallas/Frankfurt region).
2. Open Watsonx.ai Studio and create a New Project.
3. Under the project's **Manage** tab > **General** section, copy your **Project ID**.
4. Go to **Manage** (top menu) > **Access (IAM)** > **API Keys** and generate a new secret API key.
5. In the web app, navigate to **Settings**, turn **OFF** the simulation toggle, paste your credentials, select your region, and click **Save**. The `.env` file will automatically update!

---

## 🏆 Project Novelty & AICTE Evaluation Alignment

* **Usage of IBM Cloud-Platform:** Direct REST token authentication and inference API requests to Watsonx.ai Granite 3.0 models.
* **Genuinity & Innovativeness:** Offers visual macro tracking, Indian cuisine optimized recommendations, family profile grouping, and interactive pantry food swaps.
* **Readiness for Deployment:** Clean codebase, modular structure, secure key management via `.env`, and Heroku/IBM Cloud-ready `app.json` manifest.
* **Future Scope:** Ready for wearable telemetry sync (e.g. sync Apple Health / Fitbit steps to auto-adjust TDEE) and multi-lingual voice search capability.
