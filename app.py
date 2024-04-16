import os
import psycopg2
from dataclasses import dataclass
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# Connect to the PostgreSQL database
try:
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    cursor = conn.cursor()
except (psycopg2.Error, Exception) as e:
    st.error(f"Error connecting to the database: {e}")
    st.stop()

# Create the prompts table if it doesn't exist
try:
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
except (psycopg2.Error, Exception) as e:
    st.error(f"Error creating the prompts table: {e}")
    st.stop()

# Prompt dataclass
@dataclass
class Prompt:
    id: int = None
    title: str = ""
    prompt: str = ""
    is_favorite: bool = False

# Main Streamlit app
st.title("Promptbase")
st.subheader("A simple app to store and retrieve prompts")

# Search, Filter, and View Existing Prompts
st.markdown("### Search, Filter, and View Existing Prompts")

# Search bar
search_query = st.text_input("Search prompts", key="search")
st.markdown("###### Filter")
filter_favorite = st.checkbox("Show Only Favorites", value=False, key="filter_favorite")

# Get prompts from the database
query = "SELECT id, title, prompt, is_favorite FROM prompts"
if search_query:
    search_conditions = ["title ILIKE %s OR prompt ILIKE %s"]
    if filter_favorite:
        search_conditions.append("is_favorite = true")
    query += " WHERE " + " AND ".join(search_conditions)
    try:
        cursor.execute(query, [f"%{search_query}%"] * 2)
    except (psycopg2.Error, Exception) as e:
        st.error(f"Error executing the search query: {e}")
else:
    if filter_favorite:
        query += " WHERE is_favorite = true"
    try:
        cursor.execute(query)
    except (psycopg2.Error, Exception) as e:
        st.error(f"Error fetching prompts: {e}")

try:
    prompts = cursor.fetchall()
except (psycopg2.Error, Exception) as e:
    st.error(f"Error fetching prompts: {e}")
    prompts = []

# Display prompts
for prompt_id, title, prompt_text, is_favorite in prompts:
    with st.expander(title):
        if "edit_mode" not in st.session_state:
            st.session_state.edit_mode = {}

        if not st.session_state.edit_mode.get(prompt_id, False):
            st.text_area("Prompt", value=prompt_text, height=200, key=f"prompt_{prompt_id}", disabled=True)
            if is_favorite:
                st.write("Favorite ⭐")

            # Render template
            additional_input = st.text_area("Use as template by adding additional text below", key=f"additional_input_{prompt_id}", height=100)
            if st.button("Render Template", key=f"render_{prompt_id}"):
                try:
                    rendered_prompt = prompt_text + " " + additional_input
                    st.code(rendered_prompt, language="text")
                except Exception as e:
                    st.error(f"Error rendering the template: {e}")

            # Toggle favorite
            if st.button("Toggle Favorite", key=f"favorite_{prompt_id}"):
                try:
                    cursor.execute("UPDATE prompts SET is_favorite = NOT is_favorite WHERE id = %s", (prompt_id,))
                    conn.commit()
                except (psycopg2.Error, Exception) as e:
                    st.error(f"Error toggling the favorite status: {e}")
                st.experimental_rerun()

            # Edit prompt
            if st.button("Edit", key=f"edit_{prompt_id}"):
                st.session_state.edit_mode[prompt_id] = True
        else:
            edited_prompt_text = st.text_area("Edit Prompt", value=prompt_text, height=200, key=f"edit_prompt_{prompt_id}")
            if st.button("Save", key=f"save_{prompt_id}"):
                try:
                    cursor.execute("UPDATE prompts SET prompt = %s WHERE id = %s", (edited_prompt_text, prompt_id))
                    conn.commit()
                    st.success("Prompt updated successfully!")
                    st.session_state.edit_mode[prompt_id] = False
                except (psycopg2.Error, Exception) as e:
                    st.error(f"Error updating the prompt: {e}")
                st.experimental_rerun()

        # Delete prompt
        if st.button("Delete", key=f"delete_{prompt_id}"):
            try:
                cursor.execute("DELETE FROM prompts WHERE id = %s", (prompt_id,))
                conn.commit()
                st.success(f"Deleted prompt '{title}'")
            except (psycopg2.Error, Exception) as e:
                st.error(f"Error deleting the prompt: {e}")
            st.experimental_rerun()

# Add a New Prompt
st.markdown("### Add a New Prompt")

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

# Create prompt
prompt = prompt_form()
if prompt:
    query = "INSERT INTO prompts (title, prompt, is_favorite) VALUES (%s, %s, %s) RETURNING id"
    try:
        cursor.execute(query, (prompt.title, prompt.prompt, prompt.is_favorite))
        prompt.id = cursor.fetchone()[0]
        conn.commit()
        st.success("Prompt added successfully!")
    except (psycopg2.Error, Exception) as e:
        st.error(f"Error inserting a new prompt: {e}")
    st.experimental_rerun()

# Close the database connection
conn.close()