from capstone import models
import json

def add_history(user_name, query):
    user = models.User.get(user_name=user_name)
    history = json.loads(user.history)
    
    history.append(query)
    user.history = json.dumps(history)
    user.save()

def get_history(user_name)
    user = models.User.get(user_name=user_name)
    return json.loads(user.history)
