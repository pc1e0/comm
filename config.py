from db import Weaviate
db = Weaviate()

openai_model = db.read_config(name="openai_model")
classifier_instruction = db.read_config(name="classifier_instruction")
summarizer_instruction = db.read_config(name="summarizer_instruction")