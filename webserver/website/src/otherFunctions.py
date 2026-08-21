# used for debugging -- sets the color of the text for printing to terminal
# NOTE: THE LLM CAN SEE THIS AS A TOOL RIGHT NOW -- REMOVE THIS LATER!
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