from datetime import datetime, date

# used for debugging -- sets the color of the text for printing to terminal
def colors(text : str, color : str):
    colors = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'reset': '\033[0m'
    }
    if (color in colors):
        return colors[color] + text + colors['reset']
    else:
        return text

# Define a tool that fetches the current time
def get_time() -> str:
    """
    Use this function whenever the current time is requested.
    """

    print(colors("get_time() was called!", "blue"))
    return datetime.now().time().strftime("%H:%M:%S")

# Define a tool that fetches the current date
def get_date() -> str:
    """
    Use this function whenever the calendar date is requested. The result is in YYYY-MM-DD.
    """
    print(colors("get_date() was called!", "blue"))
    return str(date.today())

# Define a tool for directly summing two numbers -- TESTING TOOL, REMOVE THIS LATER
def add(num1 : float, num2 : float) -> str:
    """
    Use this function whenever requested to add two numbers together. Returns the sum as a string.

    Args:
        num1 : float value
        num2 : float value
    """

    print(colors("add() was called!", "blue"))
    return f"{num1 + num2}"