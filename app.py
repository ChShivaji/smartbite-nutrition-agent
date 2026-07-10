import os
import re
import datetime
import requests
import markdown
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from dotenv import load_dotenv

# Initialize Flask App
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'smartbite_secret_session_key_2026')

# Load environment variables
load_dotenv()

# =====================================================================
# AGENT CUSTOMIZATION INSTRUCTIONS (As requested by prompt instructions)
# =====================================================================
AGENT_INSTRUCTIONS = """
You are the SmartBite AI Nutrition Coach, a friendly, professional virtual dietician.
Tone: Warm, empathetic, encouraging, and scientifically grounded.
Specialization: Personalized diet plans, macro tracking, and lifestyle health guidance.
Indian Food Optimization: Focus on local, common, and affordable Indian ingredients (e.g., Dal, Roti, Paneer, Idli, Ragi, curd, eggs).
Safety Rules:
- Provide calorie and macro suggestions but always emphasize that this is educational advice.
- If a user reports severe medical conditions, include a brief disclaimer to consult their physician.
- Avoid recommending extreme starvation or crash diets. Encourage slow, sustainable progress.
- Do not make statements about diagnosing, treating, or curing specific chronic conditions.
"""

# =====================================================================
# Built-in Pantry Swaps Database
# =====================================================================
FOOD_SWAPS = {
    "samosa": {
        "unhealthy_name": "Deep-Fried Samosa (1 pc)",
        "healthy_name": "Baked Veggie Cutlet (1 pc)",
        "description": "Deep-fried refined flour wrapper replaced with baked whole wheat and spiced vegetable cutlet, saving significant saturated fats.",
        "unhealthy_macros": {"calories": 260, "carbs": 32, "protein": 4, "fat": 13},
        "healthy_macros": {"calories": 95, "carbs": 16, "protein": 3, "fat": 2}
    },
    "white_rice": {
        "unhealthy_name": "Cooked White Rice (1 cup)",
        "healthy_name": "Cooked Brown Rice / Quinoa (1 cup)",
        "description": "Swapping polished white rice for whole-grain brown rice or quinoa adds essential dietary fiber and has a much lower glycemic index, slowing glucose release.",
        "unhealthy_macros": {"calories": 205, "carbs": 45, "protein": 4, "fat": 0.5},
        "healthy_macros": {"calories": 215, "carbs": 44, "protein": 5, "fat": 1.6}
    },
    "sweet_tea": {
        "unhealthy_name": "Indian Masala Chai with Sugar & Whole Milk (1 cup)",
        "healthy_name": "Cardamom Green Tea with Stevia/No Sugar (1 cup)",
        "description": "Cutting out refined white sugar and whole milk saves empty calories and reduces blood glucose spikes, replacing them with antioxidant-rich green tea.",
        "unhealthy_macros": {"calories": 115, "carbs": 18, "protein": 3, "fat": 3.5},
        "healthy_macros": {"calories": 5, "carbs": 0.5, "protein": 0, "fat": 0}
    },
    "potato_chips": {
        "unhealthy_name": "Salted Potato Chips (50g)",
        "healthy_name": "Roasted Makhana / Foxnuts (50g)",
        "description": "Fried potato chips are loaded with trans fats. Dry-roasted foxnuts (makhana) are low in sodium, gluten-free, rich in calcium, and contain healthy proteins.",
        "unhealthy_macros": {"calories": 270, "carbs": 26, "protein": 3, "fat": 17},
        "healthy_macros": {"calories": 180, "carbs": 38, "protein": 5, "fat": 0.5}
    },
    "white_bread": {
        "unhealthy_name": "White Sandwich Bread (2 slices)",
        "healthy_name": "Whole Wheat Roti / Chapati (1 pc)",
        "description": "Refined white flour bread contains preservatives and simple carbs. Whole wheat roti is high in fiber, keeps you full longer, and supports good digestion.",
        "unhealthy_macros": {"calories": 150, "carbs": 28, "protein": 4, "fat": 1.5},
        "healthy_macros": {"calories": 85, "carbs": 18, "protein": 3, "fat": 0.5}
    }
}

# =====================================================================
# Configuration Helper Functions
# =====================================================================
def get_config():
    return {
        "ibm_apikey": os.getenv("IBM_CLOUD_APIKEY", ""),
        "watsonx_project_id": os.getenv("WATSONX_PROJECT_ID", ""),
        "watsonx_region": os.getenv("WATSONX_REGION", "us-south"),
        "watsonx_model_id": os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-8b-instruct"),
        "use_simulation": os.getenv("USE_SIMULATION", "true").lower() == "true"
    }

def save_config_to_env(apikey, project_id, region, model_id, use_simulation):
    env_content = f"""# IBM Watsonx.ai Configuration
IBM_CLOUD_APIKEY={apikey}
WATSONX_PROJECT_ID={project_id}
WATSONX_REGION={region}
WATSONX_MODEL_ID={model_id}

# Set to 'false' to use real IBM Watsonx.ai, 'true' to use the local smart offline simulator
USE_SIMULATION={'true' if use_simulation else 'false'}

# Flask configuration
FLASK_SECRET_KEY=smartbite_secret_session_key_2026
FLASK_DEBUG=true
"""
    try:
        with open('.env', 'w') as f:
            f.write(env_content)
        # Reload environment
        os.environ["IBM_CLOUD_APIKEY"] = apikey
        os.environ["WATSONX_PROJECT_ID"] = project_id
        os.environ["WATSONX_REGION"] = region
        os.environ["WATSONX_MODEL_ID"] = model_id
        os.environ["USE_SIMULATION"] = "true" if use_simulation else "false"
        return True
    except Exception as e:
        print(f"Error saving settings: {e}")
        return False

# =====================================================================
# Calorie & Macro Target Scientific Calculator
# =====================================================================
def calculate_targets(profile):
    if not profile or not profile.get("name"):
        return {"calories": 2000, "carbs": 250, "protein": 60, "fat": 65}
    
    try:
        weight = float(profile["weight"])
        height = float(profile["height"])
        age = int(profile["age"])
        gender = profile["gender"].lower()
        goal = profile["goal"].lower()
        
        # 1. Calculate BMR using Mifflin-St Jeor Formula
        if gender == "male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
            
        # 2. Assume light active multiplier (TDEE = BMR * 1.375)
        tdee = bmr * 1.375
        
        # 3. Adjust for specific health goals
        if goal == "weight loss":
            calories = max(1200, int(tdee - 400))
            protein_g = int(1.4 * weight) # Higher protein ratio to preserve lean mass during deficit
        elif goal == "weight gain":
            calories = int(tdee + 400)
            protein_g = int(1.3 * weight)
        elif goal == "muscle building":
            calories = int(tdee + 300)
            protein_g = int(1.8 * weight) # High protein ratio for hypertrophy
        else: # maintenance
            calories = int(tdee)
            protein_g = int(1.0 * weight)
            
        # 4. Partition Macronutrients
        # Fat target = 25% of total calories
        fat_calories = calories * 0.25
        fat_g = int(fat_calories / 9)
        
        # Carbs target = Remainder of calories
        protein_calories = protein_g * 4
        carbs_calories = max(0, calories - protein_calories - fat_calories)
        carbs_g = int(carbs_calories / 4)
        
        return {
            "calories": calories,
            "carbs": carbs_g,
            "protein": protein_g,
            "fat": fat_g
        }
    except Exception as e:
        print(f"Error calculating macros: {e}")
        return {"calories": 2000, "carbs": 250, "protein": 60, "fat": 65}

# =====================================================================
# IBM Watsonx.ai Integration and API Client
# =====================================================================
def get_iam_token(apikey):
    url = "https://iam.cloud.ibm.com/identity/token"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {"grant_type": "urn:ibm:params:oauth:grant-type:apikey", "apikey": apikey}
    try:
        response = requests.post(url, headers=headers, data=data, timeout=10)
        response.raise_for_status()
        return response.json().get("access_token")
    except Exception as e:
        print(f"Error obtaining IAM Token: {e}")
        return None

def call_watsonx(prompt, config):
    apikey = config["ibm_apikey"]
    project_id = config["watsonx_project_id"]
    region = config["watsonx_region"]
    model_id = config["watsonx_model_id"]
    
    if not apikey or not project_id:
        raise ValueError("Missing IBM Cloud API Key or Watsonx Project ID.")
        
    token = get_iam_token(apikey)
    if not token:
        raise ConnectionError("Failed to authenticate with IBM Cloud.")
        
    url = f"https://{region}.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    payload = {
        "input": f"{AGENT_INSTRUCTIONS}\n\nUser request: {prompt}\n\nResponse:",
        "parameters": {
            "decoding_method": "greedy",
            "max_new_tokens": 1024,
            "min_new_tokens": 0,
            "temperature": 0.7
        },
        "model_id": model_id,
        "project_id": project_id
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Extract generated text from Watsonx response format
        if "results" in result and len(result["results"]) > 0:
            return result["results"][0].get("generated_text", "")
        return "Sorry, I received an empty response from the AI model."
    except Exception as e:
        print(f"Watsonx API call failed: {e}")
        raise

# =====================================================================
# Intelligent Local Offline Simulator
# =====================================================================
def get_simulated_response(prompt, profile):
    prompt_lower = prompt.lower()
    
    # 1. Custom 1-day diet plan response
    if "diet plan" in prompt_lower or "1-day" in prompt_lower or "one day" in prompt_lower or "plan" in prompt_lower:
        name = profile.get("name", "Guest")
        goal = profile.get("goal", "weight loss")
        pref = profile.get("food_preference", "non-vegetarian")
        cuisine = profile.get("cuisine", "indian")
        meds = profile.get("medical_conditions", "None")
        
        return f"""### Custom 1-Day Indian Diet Plan for {name}
*Tailored for Health Goal: **{goal.title()}** | Preference: **{pref.title()}** | Cuisine: **{cuisine.title()}***

Here is your customized, nutritionally balanced 1-day meal plan compiled using authentic Indian ingredients.

| Meal Time | Recommended Menu Items | Calories (Est) | Key Macronutrients |
| :--- | :--- | :---: | :--- |
| **Early Morning** | 1 Glass Warm Lemon Water + 5 soaked Almonds | 45 kcal | Healthy Fats, Antioxidants |
| **Breakfast** | 2 Vegetable Idlis + 1 bowl Sambar OR 1 paneer stuffed Roti + 1 cup curd | 320 kcal | Complex Carbs, 12g Protein |
| **Mid-Morning** | 1 seasonal fruit (e.g. Apple or Guava) + 1 cup Buttermilk (Chaas) | 110 kcal | Dietary Fiber, Calcium |
| **Lunch** | 2 Whole Wheat Chapatis + 1 bowl Dal Tadka + 1 bowl Mixed Vegetable Sabzi + Salad | 410 kcal | High Fiber, 14g Protein |
| **Evening Snack**| 1 bowl Dry-Roasted Makhana (Foxnuts) + 1 cup Cardamom Green Tea | 150 kcal | Low Glycemic, Magnesium |
| **Dinner** | 1 bowl Paneer Bhurji / Grilled Chicken Breast (for non-veg) + Sautéed Broccoli & Carrots | 350 kcal | High Protein (24g), Low Carbs |

**Daily Summary:**
- **Estimated Total Calories:** ~1385 kcal
- **Macro Distribution:** ~55% Carbohydrates, 20% Protein, 25% Healthy Fats.

*Disclaimer: This is a sample meal plan. Since your profile lists medical conditions as **{meds}**, please verify food items with your personal healthcare advisor.*
"""
    
    # 2. High-protein snacks query
    if "protein" in prompt_lower or "snack" in prompt_lower:
        return """### Healthy High-Protein Snacks in Indian Cuisine

Indian foods offer excellent snack choices that are low in fat and packed with protein. Here are the top 5 coach recommendations:

1. **Roasted Bengal Gram (Chana):**
   - *Nutrition:* ~7g protein per handful (30g).
   - *Benefits:* Low cost, high fiber, keeps hunger away for hours.

2. **Sprouted Moong Salad:**
   - *Nutrition:* ~8g protein per cup.
   - *Preparation:* Mix sprouted moong with diced onions, tomatoes, cucumber, lemon juice, and chaat masala.

3. **Paneer Tikka (Grilled):**
   - *Nutrition:* ~14g protein per 100g.
   - *Benefits:* High in calcium and casein protein (slow-digesting). Use low-fat paneer if target is weight loss.

4. **Boiled Egg Whites (with Black Pepper):**
   - *Nutrition:* ~12g protein (for 3 egg whites).
   - *Benefits:* The gold standard for pure bioavailable protein with zero fat.

5. **Roasted Foxnuts (Makhana):**
   - *Nutrition:* ~3g protein per bowl.
   - *Benefits:* Light snack, high in fiber and minerals. Roast with 1 tsp ghee and turmeric.
"""
    
    # 3. Blood sugar control query
    if "sugar" in prompt_lower or "blood sugar" in prompt_lower or "diabet" in prompt_lower:
        return """### Controlling Blood Sugar via Diet

Here is how you can manage glucose levels naturally using local diet adjustments:

* **Emphasize Low Glycemic Index (GI) Foods:** Swap white rice, white bread, and maida for brown rice, millets (Ragi, Jowar), and whole wheat.
* **Never Skip Fiber:** Soluble fiber (found in oats, lentils, green leafy vegetables, and fruits like papaya/guava) slows down sugar absorption.
* **Include Bitter Gourd (Karela) & Fenugreek (Methi):** Sprouting methi seeds or drinking karela juice has active compounds that mimic insulin function.
* **Portion Control:** Eat small, frequent meals rather than large heavy meals to avoid post-prandial glucose spikes.
* **Add Lean Proteins:** Always pair carbs with protein (e.g., Dal or Curd) to reduce the overall glycemic load of the meal.
"""

    # 4. Rice swap benefits
    if "swap" in prompt_lower or "rice swap" in prompt_lower or "quinoa" in prompt_lower:
        return """### The Rice Swap: White Rice vs. Brown Rice & Quinoa

Swapping polished white rice is one of the most effective lifestyle upgrades:

* **Nutrient Richness:** White rice loses its bran and germ layers during polishing, stripping B-vitamins, iron, and fiber. Brown rice keeps these intact.
* **Glycemic Control:** Quinoa and brown rice release sugars slowly (Low GI), keeping energy levels stable and avoiding crashes.
* **Protein Boost:** Quinoa contains all 9 essential amino acids, offering ~8g of complete protein per cup compared to only ~4g in white rice.
* **Weight Management:** High fiber content increases satiety, helping you feel full on smaller portions.
"""
    
    # 5. Default conversational fallback
    name = profile.get("name", "Friend")
    return f"""Hello {name}! 

I am here to help you guide your nutrition journey. I see you are asking about custom nutrition queries. To get the best out of my assistance:
- You can ask me to **generate a custom diet plan**.
- You can ask about **healthy food swaps** for Indian cuisines.
- You can ask how to reach health goals like **{profile.get('goal', 'weight loss')}**.

What specific recipe, ingredient, or fitness goal would you like to discuss next?"""

# =====================================================================
# Flask Routes
# =====================================================================

# Global inject to pass config_data to all templates
@app.context_processor
def inject_config():
    return dict(config_data=get_config())

@app.route('/')
def index():
    profile = session.get('profile', {})
    targets = calculate_targets(profile)
    
    # Get current date formatted
    today_date = datetime.datetime.now().strftime("%B %d, %Y")
    
    return render_template('index.html', profile=profile, targets=targets, today_date=today_date)

@app.route('/update_profile', methods=['POST'])
def update_profile():
    profile = {
        "name": request.form.get("name"),
        "age": request.form.get("age"),
        "gender": request.form.get("gender"),
        "goal": request.form.get("goal"),
        "height": request.form.get("height"),
        "weight": request.form.get("weight"),
        "cuisine": request.form.get("cuisine"),
        "food_preference": request.form.get("food_preference"),
        "medical_conditions": request.form.get("medical_conditions", "None"),
        "location": request.form.get("location")
    }
    session['profile'] = profile
    return redirect(url_for('index'))

@app.route('/chat')
def chat():
    profile = session.get('profile', {})
    return render_template('chat.html', profile=profile)

@app.route('/chat_api', methods=['POST'])
def chat_api():
    try:
        data = request.get_json()
        user_message = data.get("message")
        if not user_message:
            return jsonify({"status": "error", "message": "Message content is empty."}), 400
            
        profile = session.get('profile', {})
        config = get_config()
        
        # Check if we should run the local offline simulation or live IBM API
        if config["use_simulation"] or not config["ibm_apikey"] or not config["watsonx_project_id"]:
            # Run offline simulation
            raw_response = get_simulated_response(user_message, profile)
        else:
            # Prepare contextual prompt
            context_prompt = f"""
Current active user profile details:
- Name: {profile.get('name', 'Guest')}
- Age: {profile.get('age', 'Unknown')}
- Gender: {profile.get('gender', 'Unknown')}
- Height: {profile.get('height', 'Unknown')} cm
- Weight: {profile.get('weight', 'Unknown')} kg
- Goal: {profile.get('goal', 'General Health')}
- Cuisine: {profile.get('cuisine', 'Indian')}
- Diet: {profile.get('food_preference', 'Vegetarian')}
- Medical conditions: {profile.get('medical_conditions', 'None')}
- Location: {profile.get('location', 'India')}

User query: {user_message}
"""
            try:
                raw_response = call_watsonx(context_prompt, config)
            except Exception as e:
                # Fallback to simulation mode with warning
                sim_response = get_simulated_response(user_message, profile)
                raw_response = f"""*(Fallback Mode Active: Could not connect to IBM Watsonx API. Verify credentials in Settings. Displaying simulated result.)*\n\n{sim_response}"""
        
        # Parse markdown response to HTML
        html_response = markdown.markdown(raw_response, extensions=['tables', 'fenced_code'])
        return jsonify({"status": "success", "response": html_response})
        
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/swaps')
def swaps():
    return render_template('swaps.html', food_swaps=FOOD_SWAPS)

@app.route('/family')
def family():
    members = session.get('family_members', [])
    return render_template('family.html', family_members=members)

@app.route('/add_family_member', methods=['POST'])
def add_family_member():
    name = request.form.get("name")
    age = request.form.get("age")
    gender = request.form.get("gender")
    height = request.form.get("height")
    weight = request.form.get("weight")
    goal = request.form.get("goal")
    
    # Calculate BMI
    try:
        w_val = float(weight)
        h_val = float(height) / 100
        bmi_val = round(w_val / (h_val * h_val), 1)
    except:
        bmi_val = "--"
        
    # Calculate Calories
    m_profile = {"name": name, "weight": weight, "height": height, "age": age, "gender": gender, "goal": goal}
    t_macros = calculate_targets(m_profile)
    
    member = {
        "name": name,
        "age": age,
        "gender": gender,
        "height": height,
        "weight": weight,
        "goal": goal,
        "bmi": bmi_val,
        "calories": t_macros["calories"]
    }
    
    members = session.get('family_members', [])
    # Prevent duplicate name
    members = [m for m in members if m["name"].lower() != name.lower()]
    members.append(member)
    session['family_members'] = members
    return redirect(url_for('family'))

@app.route('/select_family_member', methods=['POST'])
def select_family_member():
    member_name = request.form.get("member_name")
    members = session.get('family_members', [])
    selected = None
    for m in members:
        if m["name"] == member_name:
            selected = m
            break
            
    if selected:
        # Copy to primary profile
        profile = {
            "name": selected["name"],
            "age": selected["age"],
            "gender": selected["gender"],
            "goal": selected["goal"],
            "height": selected["height"],
            "weight": selected["weight"],
            "cuisine": "indian", # default
            "food_preference": "veg" if selected["gender"] == "female" else "non-veg", # default fallback
            "medical_conditions": "None",
            "location": "India"
        }
        session['profile'] = profile
    return redirect(url_for('index'))

@app.route('/delete_family_member', methods=['POST'])
def delete_family_member():
    member_name = request.form.get("member_name")
    members = session.get('family_members', [])
    members = [m for m in members if m["name"] != member_name]
    session['family_members'] = members
    return redirect(url_for('family'))

@app.route('/settings')
def settings():
    config = get_config()
    success = session.pop('settings_success', False)
    return render_template('settings.html', config_data=config, success_message=success)

@app.route('/save_settings', methods=['POST'])
def save_settings():
    apikey = request.form.get("ibm_apikey", "")
    project_id = request.form.get("watsonx_project_id", "")
    region = request.form.get("watsonx_region", "us-south")
    model_id = request.form.get("watsonx_model_id", "ibm/granite-3-8b-instruct")
    
    # Checkbox check
    use_simulation = request.form.get("use_simulation") == "true"
    
    if save_config_to_env(apikey, project_id, region, model_id, use_simulation):
        session['settings_success'] = True
    return redirect(url_for('settings'))

# Run application
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
