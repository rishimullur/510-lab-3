import os
import psycopg2
from dataclasses import dataclass, field
from dotenv import load_dotenv
import streamlit as st

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
        is_favorite BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

# Prompt dataclass
@dataclass
class Prompt:
    id: int = None
    title: str = ""
    prompt: str = ""
    is_favorite: bool = False
    prompts: list = field(default_factory=list)

def prompt_form(prompt=Prompt()):
    """ Form to create or edit a prompt. """
    with st.form(key="prompt_form", clear_on_submit=True):
        title = st.text_input("Title", value=prompt.title, max_chars=100, key="title")
        prompt_text = st.text_area("Prompt", value=prompt.prompt, height=200, key="prompt")
        is_favorite = st.checkbox("Favorite", value=prompt.is_favorite, key="is_favorite")
        submitted = st.form_submit_button("Submit")

        if submitted:
            if not title or not prompt_text:
                st.error("Title and prompt cannot be empty.")
            else:
                return Prompt(None, title, prompt_text, is_favorite)

# Main Streamlit app
st.title("Promptbase")
st.subheader("A simple app to store and retrieve prompts")

# Search bar
search_query = st.text_input("Search prompts", key="search")
filter_options = st.multiselect("Filter by", ["Title", "Prompt", "Favorite"])

# Get prompts from the database
query = "SELECT id, title, prompt, is_favorite FROM prompts"
if search_query:
    search_conditions = []
    if "Title" in filter_options:
        search_conditions.append("title ILIKE %s")
    if "Prompt" in filter_options:
        search_conditions.append("prompt ILIKE %s")
    if "Favorite" in filter_options:
        search_conditions.append("is_favorite = true")
    query += " WHERE " + " OR ".join(search_conditions)
    cursor.execute(query, [f"%{search_query}%"] * len(search_conditions))
else:
    cursor.execute(query)
prompts = cursor.fetchall()

# Create prompt
prompt = prompt_form()
if prompt:
    query = "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s) RETURNING id"
    cursor.execute(query, (prompt.title, prompt.prompt, prompt.is_favorite))
    prompt.id = cursor.fetchone()[0]
    conn.commit()
    st.success("Prompt added successfully!")
    st.experimental_rerun()

# Display prompts
for prompt_id, title, prompt_text, is_favorite in prompts:
    with st.expander(title):
        st.code(prompt_text)
        if is_favorite:
            st.write("Favorite ⭐")

        # Render template
        if st.button("Render Template", key=f"render_{prompt_id}"):
            st.code(prompt_text.format(**st.session_state), language="text")

        # Toggle favorite
        if st.button("Toggle Favorite", key=f"favorite_{prompt_id}"):
            cursor.execute("UPDATE prompts SET is_favorite = NOT is_favorite WHERE id = %s", (prompt_id,))
            conn.commit()
            st.experimental_rerun()

        # Edit prompt
        if st.button("Edit", key=f"edit_{prompt_id}"):
            cursor.execute("SELECT title, prompt, is_favorite FROM prompts WHERE id = %s", (prompt_id,))
            title, prompt_text, is_favorite = cursor.fetchone()
            edited_prompt = prompt_form(Prompt(prompt_id, title, prompt_text, is_favorite))
            if edited_prompt:
                cursor.execute("UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s WHERE id = %s",
                               (edited_prompt.title, edited_prompt.prompt, edited_prompt.is_favorite, edited_prompt.id))
                conn.commit()
                st.success("Prompt updated successfully!")
                st.experimental_rerun()

        # Delete prompt
        if st.button("Delete", key=f"delete_{prompt_id}"):
            cursor.execute("DELETE FROM prompts WHERE id = %s", (prompt_id,))
            conn.commit()
            st.success(f"Deleted prompt '{title}'")
            st.experimental_rerun()

# Close the database connection
conn.close()