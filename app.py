import os
import psycopg2
from dataclasses import dataclass
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# Connect to the PostgreSQL database
conn = psycopg2.connect(os.getenv("DATABASE_URL"))
cursor = conn.cursor()

# Create the prompts table if it doesn't exist
cursor.execute("""
   CREATE TABLE IF NOT EXISTS prompts (
       id SERIAL PRIMARY KEY,
       title TEXT NOT NULL,
       prompt TEXT NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   )
""")

# Prompt dataclass
@dataclass
class Prompt:
   title: str
   prompt: str

def prompt_form(prompt=Prompt("", "")):
   """
   Form to create or edit a prompt.
   """
   with st.form(key="prompt_form", clear_on_submit=True):
       title = st.text_input("Title", value=prompt.title, max_chars=100, key="title")
       prompt_text = st.text_area("Prompt", value=prompt.prompt, height=200, key="prompt")
       submitted = st.form_submit_button("Submit")

       if submitted:
           if not title or not prompt_text:
               st.error("Title and prompt cannot be empty.")
           else:
               return Prompt(title, prompt_text)

# Main Streamlit app
st.title("Promptbase")
st.subheader("A simple app to store and retrieve prompts")

# Prompt form
prompt = prompt_form()

if prompt:
   # Insert the prompt into the database
   cursor.execute("INSERT INTO prompts (title, prompt) VALUES (%s, %s)", (prompt.title, prompt.prompt))
   conn.commit()
   st.success("Prompt added successfully!")

# Search bar
search_query = st.text_input("Search prompts", key="search")

# Get prompts from the database
cursor.execute("SELECT id, title, prompt FROM prompts WHERE title ILIKE %s OR prompt ILIKE %s", (f"%{search_query}%", f"%{search_query}%"))
prompts = cursor.fetchall()

# Display prompts
for prompt_id, title, prompt_text in prompts:
   with st.expander(title):
       st.code(prompt_text)

       # Favorite button
       if st.button("Favorite", key=f"favorite_{prompt_id}"):
           st.info(f"Marked '{title}' as favorite!")

       # Delete button
       if st.button("Delete", key=f"delete_{prompt_id}"):
           cursor.execute("DELETE FROM prompts WHERE id = %s", (prompt_id,))
           conn.commit()
           st.success(f"Deleted prompt '{title}'")
           st.experimental_rerun()

# Close the database connection
conn.close()
