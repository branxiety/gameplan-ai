import os
import random

import streamlit as st
import openai
from dotenv import load_dotenv

# ---------- SETUP ----------
load_dotenv()  # loads .env if present (optional but nice)
openai.api_key = os.getenv("OPENAI_API_KEY")

if not openai.api_key:
    st.error("OPENAI_API_KEY not found. Please set it as an environment variable or in a .env file.")
    st.stop()

# ---------- SIMPLE "DATASET" FOR EXERCISES ----------
EXERCISE_LIBRARY = {
    "legs": [
        "Bodyweight Squats",
        "Walking Lunges",
        "Glute Bridges",
        "Romanian Deadlifts (dumbbells or barbell)",
        "Calf Raises"
    ],
    "upper body": [
        "Push-Ups",
        "Dumbbell Rows",
        "Shoulder Press",
        "Bench Press",
        "Lat Pulldown or Assisted Pull-Up"
    ],
    "core": [
        "Plank",
        "Dead Bug",
        "Side Plank",
        "Russian Twists",
        "Bird Dogs"
    ],
    "full body": [
        "Burpees",
        "Kettlebell Swings",
        "Thrusters",
        "Mountain Climbers",
        "Farmer’s Carry"
    ]
}


def sample_exercises(focus_area: str, n: int = 3):
    """Sample a few exercises from the small local library."""
    focus_area = focus_area.lower()
    if focus_area not in EXERCISE_LIBRARY:
        focus_area = "full body"
    exercises = EXERCISE_LIBRARY[focus_area]
    n = min(n, len(exercises))
    return random.sample(exercises, n)


# ---------- LLM CALL ----------
SYSTEM_PROMPT = """
You are GamePlan, an AI training companion and coach.

Your job:
- Ask brief clarifying questions only when necessary.
- Create structured, safe workout plans based on the user's time, level, mood, and goals.
- Use encouraging, human-like, but not cringey language.
- Assume the user has basic health clearance; if not sure, remind them to consult a professional.
- Always organize output using clear headings and bullet points.

IMPORTANT:
- Keep it within the user's requested time.
- Include sets, reps, and rest suggestions.
- Add 1-2 short motivational lines that feel like a friendly coach.
"""


def generate_workout_plan(user_message: str,
                          level: str,
                          goal: str,
                          minutes: int,
                          mood: str,
                          focus: str):
    """Call OpenAI ChatCompletion to generate a workout plan."""
    # Use a small, cheap model name that you can update if needed.
    model_name = "gpt-4o-mini"  # change if your account uses a different model

    # Add a tiny "data" layer: recommended exercises from our library
    suggested_exercises = sample_exercises(focus_area=focus, n=3)
    exercise_hint = (
        f"For this user, you might want to include some of these exercises when relevant: "
        f"{', '.join(suggested_exercises)}."
    )

    full_user_message = f"""
User profile:
- Experience level: {level}
- Goal: {goal}
- Session length: {minutes} minutes
- Mood: {mood}
- Focus area: {focus}

User request:
\"\"\"{user_message}\"\"\"

Additional hint from a small exercise dataset:
{exercise_hint}

Please respond with:

1. Short summary (1–2 sentences) of today's plan.
2. Warm-up (5 minutes max).
3. Main workout (clearly numbered exercises with sets/reps/rest).
4. Optional finisher (if time allows).
5. Cool-down or stretching ideas.
6. 1–2 motivational lines that feel like a supportive coach.
"""

    response = openai.ChatCompletion.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_user_message},
        ],
        temperature=0.8,
        max_tokens=900,
    )

    return response["choices"][0]["message"]["content"]


# ---------- STREAMLIT UI ----------
st.set_page_config(page_title="GamePlan – AI Training Companion", page_icon="💪", layout="centered")

st.title("GamePlan 💪")
st.subheader("An AI-powered training companion for students and amateur athletes")

st.markdown(
    """
GamePlan creates **quick, personalized workouts** and **motivational coaching**
based on your time, experience level, and mood.

Try prompts like:
- *“Make me a 20-minute leg workout for basketball.”*
- *“I only have 10 minutes and I feel tired. Give me something light.”*
- *“Design a 30-minute upper body workout for a beginner.”*
"""
)

with st.sidebar:
    st.header("Your Training Profile")

    level = st.selectbox(
        "Experience level",
        ["Beginner", "Intermediate", "Advanced"],
        index=0
    )

    goal = st.selectbox(
        "Main goal",
        ["General fitness", "Strength", "Hypertrophy / muscle gain", "Endurance", "Sport-specific (e.g., basketball)"],
        index=0
    )

    minutes = st.slider("Session length (minutes)", min_value=10, max_value=90, value=30, step=5)

    mood = st.selectbox(
        "How are you feeling today?",
        ["Tired / low energy", "Neutral", "Motivated", "Very motivated"],
        index=1
    )

    focus = st.selectbox(
        "Focus area",
        ["Full body", "Legs", "Upper body", "Core"],
        index=0
    )

st.markdown("---")

user_message = st.text_area(
    "What kind of workout do you want today? 🧠",
    placeholder="Example: I play intramural basketball and want a 20-minute leg workout to improve my explosiveness.",
    height=120,
)

generate = st.button("Generate GamePlan")

if generate:
    if not user_message.strip():
        st.warning("Please type something about the workout you want.")
    else:
        with st.spinner("Designing your GamePlan..."):
            try:
                plan = generate_workout_plan(
                    user_message=user_message,
                    level=level,
                    goal=goal,
                    minutes=minutes,
                    mood=mood,
                    focus=focus
                )
                st.markdown("### 📝 Your GamePlan")
                st.markdown(plan)

            except Exception as e:
                st.error(f"Something went wrong while generating your plan: {e}")
