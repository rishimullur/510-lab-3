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
    if search_conditions:
        query += " WHERE " + " OR ".join(search_conditions)
        try:
            cursor.execute(query, [f"%{search_query}%"] * len(search_conditions))
        except (psycopg2.Error, Exception) as e:
            st.error(f"Error executing the search query: {e}")
    else:
        st.warning("No search conditions selected.")
else:
    try:
        cursor.execute(query)
    except (psycopg2.Error, Exception) as e:
        st.error(f"Error fetching prompts: {e}")

prompts = cursor.fetchall()

# Display prompts
for prompt_id, title, prompt_text, is_favorite in prompts:
    with st.expander(title):
        st.code(prompt_text)
        if is_favorite:
            st.write("Favorite ⭐")

        # Render template
        if st.button("Render Template", key=f"render_{prompt_id}"):
            try:
                st.code(prompt_text.format(**st.session_state), language="text")
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
            try:
                cursor.execute("SELECT title, prompt, is_favorite FROM prompts WHERE id = %s", (prompt_id,))
                title, prompt_text, is_favorite = cursor.fetchone()
                edited_prompt = prompt_form(Prompt(prompt_id, title, prompt_text, is_favorite))
                if edited_prompt:
                    cursor.execute("UPDATE prompts SET title = %s, prompt = %s, is_favorite = %s WHERE id = %s",
                                   (edited_prompt.title, edited_prompt.prompt, edited_prompt.is_favorite, edited_prompt.id))
                    conn.commit()
                    st.success("Prompt updated successfully!")
            except (psycopg2.Error, Exception) as e:
                st.error(f"Error editing the prompt: {e}")
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