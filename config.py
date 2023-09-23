from db import Database
db = Database()

openai_model = db.read_config(name="openai_model")
classifier_instruction = db.read_config(name="classifier_instruction")