import openai
import config
import json
import os
from dotenv import load_dotenv

load_dotenv()


class ChatGPT:

    def __init__(self):

        openai.api_key = os.getenv("OPENAI_KEY")

    
    def moderate(self, content):

        try:
            response = openai.Moderation.create(input=content)
            return response["results"][0]["flagged"]
        
        except Exception as e:
            raise RuntimeError("Error when moderating content for ChatGPT.") from e
    

    def submit(self, chat=None, system=None, prompt=None, max_tokens=512, temperature=1):

        if not chat:
            chat = [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ]

        try:
            response = openai.ChatCompletion.create(
                model=config.openai_model,
                messages=chat,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response["choices"][0]["message"]["content"]
        
        except Exception as e:
            raise RuntimeError("Error when getting chat response from ChatGPT.") from e
    

    def classify(self, inquiry, context):

        setup = [
            {"role": "system", "content": config.classifier_instruction},
            {"role": "user", "content": f"Context:\n\n{context}"},
            {"role": "user", "content": f"User inquiry:\n\n{inquiry}"}
        ]

        response = self.submit(
            chat=setup,
            max_tokens=64,
            temperature=0
        )

        # The required structure of the response
        required_keys = {"seeks_help", "category"}

        # Load the response string as JSON
        try:
            response_dict = json.loads(response)
        except json.JSONDecodeError:
            raise ValueError("The ChatGPT response is not a valid JSON.")
        
        # Check if all required keys are present
        if not required_keys.issubset(response_dict.keys()):
            raise ValueError("The ChatGPT JSON response doesn't have expected keys.")
        
        # Check if 'need_assistance' is of boolean type
        if not isinstance(response_dict["seeks_help"], bool):
            raise ValueError("The ChatGPT JSON's 'seeks_help' is not boolean.")
        
        # Check if 'category' is of string type
        if not isinstance(response_dict["category"], str):
            raise ValueError("The ChatGPT JSON's 'category' is not string.")

        return response_dict
    

    def summarize(self, content):
        
        setup = [
            {"role": "system", "content": config.summarizer_instruction},
            {"role": "user", "content": f"Content:\n\n{content}"}
        ]

        response = self.submit(
            chat=setup,
            max_tokens=512
        )

        return response