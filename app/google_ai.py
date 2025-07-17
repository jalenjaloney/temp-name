import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
import sqlite3

load_dotenv()
# Set environment variables
my_api_key = os.getenv('GENAI_KEY')
genai.api_key = my_api_key

# Create an genAI client using the key from our environment variable
client = genai.Client(api_key=my_api_key)

def get_comments(media_id, db_path=None):
    if not db_path:
        db_path = os.path.join(os.path.dirname(__file__), "..", "instance", "site.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT timestamp, content
        FROM comment
        WHERE episode_id = ?
        ORDER BY timestamp ASC
    """, (media_id,))

    comments = cursor.fetchall()
    conn.close()

    if not comments:
        return ""

    formatted = []
    for seconds, content in comments:
        seconds = int(seconds)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        timestamp = f"{hours:02}:{minutes:02}:{secs:02}" if hours else f"{minutes:02}:{secs:02}"
        formatted.append(f"[{timestamp}] {content}")

    return "\n".join(formatted)

def summarize_comments(comment_block):

    prompt = f"""
    Analyze timestamped viewer comments on a movie or episode.

    Each comment starts with a timestamp (e.g. [13:10]).
    Provide 4 emojis that represent the overall sentiment and general viewer reaction based on the following timestamped comments from a movie or episode.

    Here are the comments:
    {comment_block}
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=("You are a helpful assistant.")
        ),
        contents=prompt
    )
    
    return response.text.strip()



#test
# if __name__ == "__main__":
#     episode_or_movie_id = 1922715
#     comment_text = get_comments(episode_or_movie_id)

#     if not comment_text:
#         print("No comments found.")
#     else:
#         print("Comment Summary:\n")
#         summary = summarize_comments(comment_text)
#         print(summary)