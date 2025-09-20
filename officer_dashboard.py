import streamlit as st
import sqlite3
from datetime import datetime

DB_NAME = "farmer_support.db"

# ---------------- DB Functions ----------------
def get_escalations():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM escalations ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def update_status(escalation_id, new_status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE escalations SET status = ? WHERE id = ?", (new_status, escalation_id))
    conn.commit()
    conn.close()

# ---------------- Streamlit Dashboard ----------------
st.set_page_config(page_title="Agri Officer Dashboard", layout="wide")
st.title("🌾 Digital Krishi Officer – Escalated Queries Dashboard")

st.markdown("This dashboard allows officers to **review farmer queries escalated by the AI system**, mark them as resolved, and add notes.")

# Fetch data
rows = get_escalations()

if not rows:
    st.info("✅ No escalated queries at the moment.")
else:
    for row in rows:
        esc_id, query, prediction, confidence, location, weather, image_url, status, created_at = row
        
        with st.expander(f"🚨 Query #{esc_id} | {query} | Status: {status}"):
            st.write(f"**Farmer Query:** {query}")
            st.write(f"**AI Prediction:** {prediction}")
            st.write(f"**Confidence:** {confidence:.2f}")
            st.write(f"**Location:** {location}")
            st.write(f"**Weather:** {weather}")
            st.write(f"**Image:** [View Image]({image_url})" if image_url else "No Image")
            st.write(f"**Created At:** {created_at}")

            # Update status
            col1, col2 = st.columns(2)
            with col1:
                if st.button(f"✅ Mark Resolved #{esc_id}"):
                    update_status(esc_id, "Resolved")
                    st.success(f"Query #{esc_id} marked as Resolved.")
                    st.experimental_rerun()
            with col2:
                if st.button(f"❌ Mark Pending #{esc_id}"):
                    update_status(esc_id, "Pending")
                    st.warning(f"Query #{esc_id} set back to Pending.")
                    st.experimental_rerun()
