import os
from datetime import datetime, date


# Define a tool that fetches the current time
def get_time() -> str:
    """Use this function whenever the current time is requested."""

    # print(colors("get_time() was called!", "blue"))
    return datetime.now().strftime("%I:%M %p")

# Define a tool that fetches the current date
def get_date() -> str:
    """
    Use this function whenever the calendar date is requested. The result is in YYYY-MM-DD.
    """
    # print(colors("get_date() was called!", "blue"))
    return str(date.today())

# Define a function that the LLM can use to fetch a skill.md file.
# the skill.md file will tell the LLM (in markdown) in detail what to do to perform a specific action/skill.
# The LLM is aware of the skills it can use via the system prompt --> put a list of skills that the LLM can use with a line that says:
# 'Use this skill when the user ___' or some similar use case descriptor
def get_skill_details(skill_name : str) -> str:
    """
    Reads and returns the full instructions for a skill.
    """
    # print(colors("get_skill_details() was called", "blue"))
    # basename fetches the literal file stripping away folders/directories. We also remove the .md for now
    # this prevents directory attacks (reading undersired files)
    safe_name = os.path.basename(skill_name).replace(".md", "")

    file_path = f"./skill-files/{safe_name}.md" # assemble path to skill file

    # read and return file contents if found
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            contents = file.read()
            print(contents)
            return contents
    return f"Error: Skill '{skill_name}' not found."