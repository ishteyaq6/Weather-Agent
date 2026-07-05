import base64
import json
import os
import requests
import streamlit as st
from google import genai
from google.genai import types

# --- 1. Page Configuration ---
st.set_page_config(page_title="AI Mausam Vibhag", page_icon="🌦️")


# --- 2. Custom CSS for Wavy Effect & Natural Background ---
# converting image to base64
def get_base64_of_bin_file(bin_file):
    with open(bin_file, "rb") as f:
        data = f.read()
    return base64.b64encode(data).decode()


# local image download logic
try:
    img_base64 = get_base64_of_bin_file("image_0cfa7f.jpg")
    bg_style = f'background-image: url("data:image/jpeg;base64,{img_base64}");'
except FileNotFoundError:
    # if image fails to load
    bg_style = 'background: #64827c;'

custom_css = f"""
<style>
/* Natural Background Image */
.stApp {{
    {bg_style}
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
}}

/* Wavy Animation */
@keyframes wave-flag {{
    0% {{ transform: perspective(1000px) rotateY(0deg) rotateX(0deg); border-radius: 15px; }}
    25% {{ transform: perspective(1000px) rotateY(1deg) rotateX(0.5deg); border-radius: 15px 18px 15px 12px; }}
    50% {{ transform: perspective(1000px) rotateY(-1deg) rotateX(-0.5deg); border-radius: 12px 15px 18px 15px; }}
    75% {{ transform: perspective(1000px) rotateY(0.5deg) rotateX(1deg); border-radius: 18px 12px 15px 15px; }}
    100% {{ transform: perspective(1000px) rotateY(0deg) rotateX(0deg); border-radius: 15px; }}
}}

/* Applying animation to the main Streamlit container */
div[data-testid="stBlockContainer"] {{
    animation: wave-flag 4s infinite ease-in-out;
    background: rgba(255, 255, 255, 0.75); 
    padding: 2.5rem;
    box-shadow: 0 10px 30px rgba(0,0,0,0.4);
    margin-top: 40px;
    margin-bottom: 40px;
    max-width: 800px;
}}

/* Text color fix for readability */
.stApp p, .stApp h1, .stApp h2, .stApp h3 {{
    color: #1e1e1e !important;
}}

/* Chat bubble styling */
div[data-testid="stChatMessage"] {{
    background-color: rgba(255, 255, 255, 0.6);
    border-radius: 10px;
    padding: 10px;
}}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# --- 3. Gemini API & Tool Setup ---
API_KEY = os.getenv("gem_api_key")

system_prompt = """
You are an AI Assistant which helps user in getting realtime weather data in natural language and in sarcastic way!
You must not say anything that may hurt/offend anyone but make them smile. Use relevant emojis to make more effect of sarcasm.
You must not answer anything completely other than weather, instead of any follow-up questions on weather results.

CRITICAL RULES:
1. Always respond in a strict JSON format with a single key named "response".
2. Must answer in same language in which user has asked query!
3. Must not answer any query other than of weather & weather related follow-ups.

Expected Format:
{"response": "your sarcastic answer here"}

Examples:
User: kanpur ka mausam kaisa hai?
Assistant: Arrey mat puchho yrr😒! kanpur ke badal nahi pata kis picnic pr gye hue hn , suraj ka akrosh badhta hi ja rha hai. Temp toh halfcentury lagane wali hai, filhaal 39 deg. cel. hai.
User: kya hi bola jaye yrr, koi kaam bhi nhi krne ka mann krta hai itni garmi mein!
Assistant: sahi bola bhai, yeh garmi bache kuchhe motivation ki bhi lanka laga de rhi hai, khair kaam krte rhna hoga😒.
User: chalo homework krte hain .
Assistant: hn hn thik hai😊, par main ek weather agent hun🤖 ,homework assistance ke liye aap koi aur AI jaise GEMINI, OPENAI ka use kro. Best of Luck.👍
"""


def get_current_weather(city: str) -> str:
    try:
        url = f"https://wttr.in/{city}?format=%c=%t"
        headers = {"User-Agent": "curl/v1.0"}
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200 and "Not Found" not in resp.text:
            return f"The current weather in {city} is: {resp.text.strip()}"
        return f"Sorry, could not find weather details for {city}."
    except Exception as e:
        return f"Error fetching weather data: {str(e)}"


# --- 4. Streamlit UI & Chat Logic ---
st.title("🌦️ AI Mausam Vibhag")
st.markdown("<div style='color: white !important; font-size: 14px; margin-bottom: 15px;'>Aapka Swagat Hai! (Sarcasm included 😎)</div>", unsafe_allow_html=True)
st.divider()

# Sidebar adding credits.
with st.sidebar:
    st.write("")  # to add a space
    st.markdown(
        "<small style='color: #577799;'>Coded by Ishteyaq</small>",
        unsafe_allow_html=True,
    )

# Session State initialisation for chat history
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=API_KEY)
    config = types.GenerateContentConfig(
        system_instruction=system_prompt, tools=[get_current_weather], temperature=0.9
    )
    st.session_state.chat = st.session_state.client.chats.create(
        model="gemini-2.5-flash", config=config
    )
    st.session_state.messages = []

# tracking chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# taking user's input
if user_query := st.chat_input("Mausam ke baare mein pucho..."):
    # to show user's messgae
    st.chat_message("user").markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # AI response
    with st.chat_message("assistant"):
        with st.spinner("Badalo se sampark kiya ja raha hai...📡☁️"):
            try:
                response = st.session_state.chat.send_message(user_query)
                raw_text = response.text

                # JSON Formatting
                cleaned_text = (
                    raw_text.replace("```json", "").replace("```", "").strip()
                )
                json_data = json.loads(cleaned_text)
                ai_reply = json_data.get(
                    "response", "Oops, JSON format me kuch gadbad ho gayi!"
                )

                st.markdown(ai_reply)
                st.session_state.messages.append(
                    {"role": "assistant", "content": ai_reply}
                )

            except Exception as e:
                st.error(f"JSON Failure or Tool Error! : {str(e)}")
                st.code(raw_text)