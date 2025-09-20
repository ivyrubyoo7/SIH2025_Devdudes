import streamlit as st
import smtplib
import sqlite3
from email.mime.text import MIMEText
from datetime import datetime

# ---------------- DB Setup ----------------
DB_NAME = "farmer_support.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS escalations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  farmer_query TEXT,
                  ai_prediction TEXT,
                  confidence REAL,
                  location TEXT,
                  weather TEXT,
                  image_url TEXT,
                  status TEXT,
                  created_at TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS feedback
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  farmer_query TEXT,
                  ai_answer TEXT,
                  feedback TEXT,
                  comment TEXT,
                  created_at TEXT)''')
    conn.commit()
    conn.close()

init_db()

# ---------------- Escalation Logic ----------------
CONFIDENCE_THRESHOLD = 0.7

def escalate_to_officer(query_data):
    """Send escalation email + store in DB"""
    # 1. Save to DB
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO escalations (farmer_query, ai_prediction, confidence, location, weather, image_url, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (query_data["query_text"],
               query_data["ai_prediction"],
               query_data["confidence"],
               query_data["location"],
               query_data["weather"],
               query_data["image_url"],
               "Pending",
               datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    # 2. Send Email (demo: change to your email & SMTP)
    try:
        msg = MIMEText(f"""
        Farmer Query: {query_data['query_text']}
        AI Prediction: {query_data['ai_prediction']}
        Confidence: {query_data['confidence']}
        Location: {query_data['location']}
        Weather: {query_data['weather']}
        Image: {query_data['image_url']}
        """)
        msg['Subject'] = "Escalated Farmer Query - Digital Krishi Officer"
        msg['From'] = "your_email@gmail.com"
        msg['To'] = "officer_email@example.com"

        # Dummy Gmail SMTP (replace credentials for real use)
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login("your_email@gmail.com", "your_app_password")
            server.send_message(msg)
        st.success("✅ Escalated to Agri Officer")
    except Exception as e:
        st.error(f"Email sending failed: {e}")

# ---------------- Feedback Logic ----------------
def save_feedback(query, answer, feedback, comment=""):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO feedback (farmer_query, ai_answer, feedback, comment, created_at) VALUES (?, ?, ?, ?, ?)",
              (query, answer, feedback, comment, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()
    st.success("✅ Feedback recorded. Thank you!")

# ---------------- Streamlit UI ----------------
st.title("🌾 Digital Krishi Officer – Escalation & Feedback")

# Simulated AI output (replace with real pipeline input later)
sample_query = "Which pesticide for banana leaf spot?"
ai_prediction = "Banana Leaf Spot"
confidence = 0.55  # Low → should escalate
ai_answer = "Use Carbendazim 0.1% solution."
location = "Thrissur"
weather = "Rain expected today"
image_url = "https://dummyimage.com/200x200/ccc/000&text=Leaf"

st.subheader("Farmer Query")
st.write(sample_query)

if confidence < CONFIDENCE_THRESHOLD:
    st.warning("⚠️ Low AI confidence. Escalating...")
    query_data = {
        "query_text": sample_query,
        "ai_prediction": ai_prediction,
        "confidence": confidence,
        "location": location,
        "weather": weather,
        "image_url": image_url
    }
    if st.button("🚨 Escalate to Officer"):
        escalate_to_officer(query_data)
else:
    st.success(f"✅ AI Answer: {ai_answer}")

# Feedback Section
st.subheader("Farmer Feedback")
col1, col2 = st.columns(2)

with col1:
    if st.button("👍 Helpful"):
        save_feedback(sample_query, ai_answer, "positive")

with col2:
    if st.button("👎 Not Helpful"):
        comment = st.text_input("Tell us what went wrong:")
        if st.button("Submit Feedback"):
            save_feedback(sample_query, ai_answer, "negative", comment)
