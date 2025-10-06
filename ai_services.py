import os
import openai
import json
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Curriculum Functions (No changes) ---
def get_chapters_for_subject(board, grade, subject):
    prompt = f"""You are a curriculum expert for Pakistan. Provide a list of all official chapter names for: Board: {board}, Class/Grade: {grade}, Subject: {subject}. Provide ONLY a valid JSON list of strings."""
    try:
        client = openai.OpenAI(); response = client.chat.completions.create(model="gpt-3.5-turbo-1106", response_format={"type": "json_object"}, messages=[{"role": "user", "content": prompt}], temperature=0.2); data = json.loads(response.choices[0].message.content)
        for key in data: return data[key]
    except Exception as e: print(f"--- DEV LOG: Error in get_chapters_for_subject ---\n{e}"); return None

def get_topics_for_chapter(board, grade, subject, chapter):
    prompt = f"""You are a curriculum expert for Pakistan. For the textbook: Board: {board}, Class/Grade: {grade}, Subject: {subject}. List all main official sub-topics within the chapter "{chapter}". Provide ONLY a valid JSON list of strings."""
    try:
        client = openai.OpenAI(); response = client.chat.completions.create(model="gpt-3.5-turbo-1106", response_format={"type": "json_object"}, messages=[{"role": "user", "content": prompt}], temperature=0.2); data = json.loads(response.choices[0].message.content)
        for key in data: return data[key]
    except Exception as e: print(f"--- DEV LOG: Error in get_topics_for_chapter ---\n{e}"); return None

# --- Learning Core & Quiz Functions (Quiz function is unchanged) ---
def generate_topic_quiz(context, topic, num_questions=10):
    prompt = f"""You are an expert high school teacher designing a quiz. Context: Student is studying for {context['grade']} under the {context['board']} for {context['subject']}. Task: Generate a {num_questions}-question MC quiz on "{topic}". The questions should test fundamental knowledge. Provide ONLY a valid JSON object with a key "questions" containing a list of objects (keys: "question", "options", "correct_answer", "explanation")."""
    try:
        client = openai.OpenAI(); response = client.chat.completions.create(model="gpt-3.5-turbo-1106", response_format={"type": "json_object"}, messages=[{"role": "system", "content": "Output JSON."}, {"role": "user", "content": prompt}], temperature=0.5); data = json.loads(response.choices[0].message.content)
        return data.get("questions")
    except Exception as e: print(f"--- DEV LOG: Error in generate_topic_quiz ---\n{e}"); return None

# --- NEW: Suite of Specialized Explanation Functions ---

def explain_topic_summary(context, topic, language):
    """Generates a concise summary."""
    lang_instruction = {"English": "Explain in simple English.", "Roman Urdu": "Explain in Roman Urdu.", "Urdu": "Explain in pure Urdu script."}.get(language)
    structure = "### 1. Simple Definition\n### 2. Core Concepts (in bullet points)\n### 3. Key Takeaway / Formula"
    prompt = f"""You are a teacher making a topic easy. Topic: {topic}. Task: Provide a concise summary. {lang_instruction} Use these exact Markdown sections:\n{structure}"""
    try:
        client = openai.OpenAI(); response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.6)
        return response.choices[0].message.content
    except Exception as e: print(f"--- DEV LOG: Error in explain_topic_summary ---\n{e}"); return "Our AI Tutor is busy."

def explain_topic_detailed(context, topic, language):
    """Generates a detailed, structured explanation."""
    lang_instruction = {"English": "Explain in-depth in academic English.", "Roman Urdu": "Explain in-depth in detailed Roman Urdu.", "Urdu": "Explain in-depth in rich Urdu script."}.get(language)
    structure = "### 1. In-Depth Analysis\n### 2. Step-by-Step Process / Key Components\n### 3. Common Misconceptions"
    prompt = f"""You are a professor preparing a study guide. Topic: {topic}. Task: Provide a detailed explanation. {lang_instruction} Use these exact Markdown sections:\n{structure}"""
    try:
        client = openai.OpenAI(); response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.6)
        return response.choices[0].message.content
    except Exception as e: print(f"--- DEV LOG: Error in explain_topic_detailed ---\n{e}"); return "Our AI Tutor is busy."

def explain_topic_deep_detail(context, topic, language):
    """Generates an exhaustive, university-level explanation."""
    lang_instruction = {"English": "Explain exhaustively in formal, academic English.", "Roman Urdu": "Explain exhaustively in advanced Roman Urdu.", "Urdu": "Explain exhaustively in formal, high-level Urdu script."}.get(language)
    structure = "### 1. Abstract\n### 2. Historical Context & Foundational Theories\n### 3. Comprehensive Theoretical Framework\n### 4. Advanced Applications & Modern Research"
    prompt = f"""You are a leading researcher writing a definitive guide. Topic: {topic}. Task: Provide an exhaustive, deep-detail explanation. {lang_instruction} Use these exact Markdown sections:\n{structure}"""
    try:
        client = openai.OpenAI(); response = client.chat.completions.create(model="gpt-3.5-turbo-16k", messages=[{"role": "user", "content": prompt}], temperature=0.6) # Using 16k model for longer responses
        return response.choices[0].message.content
    except Exception as e: print(f"--- DEV LOG: Error in explain_topic_deep_detail ---\n{e}"); return "Our AI Tutor is busy."

def generate_real_world_example(context, topic, language):
    """Generates a single, creative real-world example."""
    lang_instruction = {"English": "Explain in simple English.", "Roman Urdu": "Explain in conversational Roman Urdu.", "Urdu": "Explain in simple Urdu script."}.get(language)
    prompt = f"""You are a creative science communicator. Your task is to give one single, memorable, real-world example or analogy for the topic: "{topic}".
Make it relatable to everyday life, like cooking, sports (cricket), or technology.
Start directly with the example. Do not add any introductory phrases. {lang_instruction}"""
    try:
        client = openai.OpenAI(); response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.7)
        return response.choices[0].message.content
    except Exception as e: print(f"--- DEV LOG: Error in generate_real_world_example ---\n{e}"); return "Our AI Tutor is busy."

def answer_follow_up(context, topic, explanation_text, user_question, language):
    """Answers a user's specific follow-up question."""
    lang_instruction = {"English": "Answer in simple English.", "Roman Urdu": "Answer in Roman Urdu.", "Urdu": "Answer in pure Urdu script."}.get(language)
    prompt = f"""You are a tutor's assistant. A student has a follow-up question. Original Topic: {topic}. Student's Context: {context['grade']}. Original Explanation:\n{explanation_text}\nStudent's Question: "{user_question}"\nTask: Directly answer the question. {lang_instruction}"""
    try:
        client = openai.OpenAI(); response = client.chat.completions.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}], temperature=0.5)
        return response.choices[0].message.content
    except Exception as e: print(f"--- DEV LOG: Error in answer_follow_up ---\n{e}"); return "Sorry, I'm having trouble understanding."