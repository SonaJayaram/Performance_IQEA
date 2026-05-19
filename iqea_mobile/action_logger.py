import json

actions = []

def log_action(action, locator=None, value=None):
    step = len(actions) + 1
    actions.append({
        "step": step,
        "action": action,
        "locator": locator,
        "value": value
    })

def save_actions(file="actions.json"):
    with open(file, "w") as f:
        json.dump(actions, f, indent=4)