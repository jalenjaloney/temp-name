# Stamper

### Table of Contents
- [General Info](#general-info)
- [Features](#features)
- [Technologies](#technologies)
- [Setup](#setup)
- [Usage](#usage)
- [Workflows](#workflows)

### General Info
**Stamper** is a social platform that allows users to post timestamped comments while watching a show or movie, offering a 
space to share reactions at specific moments. Whether it is shock at a plot twist or laughter at a punch line, these 
moment-specific reactions create a shared experience that enhances rather than interrupts what you're watching.

### Features
- Timestamped commenting synced to movie/show runtime
- Gemini-powered emoji summaries based on viewer comments
- Custom playback that simulates progress for syncing comments
- User authentication for adding comments
- Button to show/hide comments

### Technologies
This project is created with:
- Python (Flask)
- HTML
- CSS
- Jinja2
- TMDb API
- Google GenAI
- SQLite
- dotenv


### Setup
In the terminal:
``` bash
# Clone the repository
git clone https://github.com/jalenjaloney/temp-name.git
cd temp-name/

# Install Python dependencies
pip install -r requirements.txt
```

Create a .env file and add your API keys
```env
# Example .env file
TMDB_API_KEY=your_tmdb_key
GENAI_KEY=your_genai_key
```

### Usage
The project is deployed on PythonAnywhere: https://jalenseotechdev.pythonanywhere.com/

### Workflows
