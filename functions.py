import json
import requests
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
from prompts import assistant_instructions

_ = load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
WEATHER_API_KEY = os.environ['WEATHER_API_KEY']

# Init OpenAI Client
client = OpenAI(api_key=OPENAI_API_KEY)

def kb_files_ids(client, kb_folder='kb'):
    # List all files in the kb folder
    files_in_kb = [f for f in os.listdir(kb_folder) if os.path.isfile(os.path.join(kb_folder, f))]

    # Initialize an empty list to store file IDs
    file_ids = []

    # Upload each file and store its ID
    for file_name in files_in_kb:
        file_path = os.path.join(kb_folder, file_name)
        with open(file_path, "rb") as file:
            uploaded_file = client.files.create(
                file=file,
                purpose='assistants'
            )
            file_ids.append(uploaded_file.id)
 
    return file_ids


def create_assistant(client):
  assistant_file_path = 'assistant.json'

  # If there is an assistant.json file already, then load that assistant
  if os.path.exists(assistant_file_path):
    with open(assistant_file_path, 'r') as file:
      assistant_data = json.load(file)
      assistant_id = assistant_data['assistant_id']
      print("Loaded existing assistant ID.")
  else:
    # If no assistant.json is present, create a new assistant using the below specifications

    files_ids = kb_files_ids(client)

    assistant = client.beta.assistants.create(
        # Getting assistant prompt from "prompts.py" file.
        instructions=assistant_instructions,
        model="gpt-4-1106-preview",
        tools=[
            {
                "type": "retrieval"  # This adds the knowledge base as a tool
            },
            {
                "type": "function",  # This adds the weather forecast as a tool
                "function": {
                    "name": "get_weather",
                    "description":
                    "Get the weather info for the selected days.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "days": {
                                "type":
                                "string",
                                "description":
                                "Days to get forecast from."
                            }
                        },
                        "required": ['days']
                    }
                }
            }
        ],
        file_ids=files_ids)

    # Create a new assistant.json file to load on future runs
    with open(assistant_file_path, 'w') as file:
      json.dump({'assistant_id': assistant.id}, file)
      print("Created a new assistant and saved the ID.")

    assistant_id = assistant.id

  return assistant_id

def get_weather(days):
    url = f"https://weatherapi-com.p.rapidapi.com/forecast.json?q=Belorado&days={days}"

    headers = {
        "X-RapidAPI-Key": WEATHER_API_KEY,
        "X-RapidAPI-Host": "weatherapi-com.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers)

    return response.json()

