import weaviate
import os
from dotenv import load_dotenv

load_dotenv()


class Weaviate:

    def __init__(self):

        weaviate_url = os.getenv("WEAVIATE_URL")
        weaviate_key = os.getenv("WEAVIATE_KEY")
        openai_key = os.getenv("OPENAI_KEY")

        self.client = weaviate.Client(
            url=weaviate_url,
            auth_client_secret=weaviate.AuthApiKey(api_key=weaviate_key),
            additional_headers={"X-OpenAI-Api-Key": openai_key}
        )

    
    def write_config(self, name, content):

        data_object = {
            "name": name,
            "content": content
        }

        try:
            self.client.data_object.create(
                data_object=data_object,
                class_name="System"
            )
        
        except Exception as e:
            raise RuntimeError("Error when creating Weaviate data object.") from e


    def read_config(self, name):

        query = """\
        {
            Get {
                System (
                    where: {
                        path: ["name"]
                        operator: Equal
                        valueText: "%s"
                    }
                    limit: 1
                )
                {
                    content
                }
            }
        }
        """ % name
        
        try:
            result = self.client.query.raw(query)
            return result["data"]["Get"]["System"][0]["content"]

        except Exception as e:
            raise RuntimeError("Error when reading Weaviate data object.") from e


    def create_schema(self, update=False):

        if update:
            try:
                self.client.schema.delete_all()
                print("Schema deleted")
            except Exception as e:
                raise RuntimeError("Error when deleting Weaviate schema.") from e

        user_class = {
            "class": "User",
            "description": "Stores information related to individual users",
            "properties": [
                {"name": "username", "dataType": ["text"], "description": "Unique identifier for each user"},
                {"name": "num_interactions", "dataType": ["number"], "description": "Count of interactions the user has had with the assistant"}
            ],
            "vectorizer": "text2vec-openai"
        }

        factoid_class = {
            "class": "Factoid",
            "description": "Stores pieces of knowledge that the assistant can refer to",
            "properties": [
                {"name": "content", "dataType": ["text"], "description": "The actual text or information of the factoid"},
                {"name": "summary", "dataType": ["text"], "description": "Brief description or summary of the factoid"},
                {"name": "author", "dataType": ["text"], "description": "Original author or source of the content"},
                {"name": "source", "dataType": ["text"], "description": "Where the factoid was originally published (e.g., URL, book, etc.)"},
                {"name": "category", "dataType": ["text"], "description": "Categorizes the factoid (e.g., 'Finance', 'Tech', 'History')"},
                {"name": "suggested_by", "dataType": ["text"], "description": "Username who suggested the addition of this factoid (if applicable)"},
                {"name": "review_status", "dataType": ["text"], "description": "Status of review ('Pending', 'Approved', 'Rejected')"}
            ],
            "vectorizer": "text2vec-openai"
        }

        interaction_class = {
            "class": "Interaction",
            "description": "Logs interactions between the user and the assistant",
            "properties": [
                {"name": "user", "dataType": ["text"], "description": "Username of the person interacting with the assistant"},
                {"name": "inquiry", "dataType": ["text"], "description": "The question or input from the user"},
                {"name": "context", "dataType": ["text"], "description": "Context or surrounding conversation where the inquiry was made"},
                {"name": "response", "dataType": ["text"], "description": "The assistant’s reply to the user's inquiry"}
            ],
            "vectorizer": "text2vec-openai"
        }

        observation_class = {
            "class": "Observation",
            "description": "Captures and categorizes all new pieces of input (posts, comments, etc.)",
            "properties": [
                {"name": "content_id", "dataType": ["text"], "description": "Unique identifier for each piece of content"},
                {"name": "author", "dataType": ["text"], "description": "Username of the person who created the content"},
                {"name": "content", "dataType": ["text"], "description": "The actual text or information in the content"},
                {"name": "type", "dataType": ["text"], "description": "Type of content (e.g., 'Post', 'Comment', 'Reply')"},
                {"name": "category", "dataType": ["text"], "description": "Categorization based on content nature (e.g., 'Spam', 'Question')"}
            ],
            "vectorizer": "text2vec-openai"
        }

        system_class = {
            "class": "System",
            "description": "Stores standard messages, prompts, and other system-level text",
            "properties": [
                {"name": "name", "dataType": ["text"], "description": "Unique name or identifier for each system message"},
                {"name": "content", "dataType": ["text"], "description": "The actual text of the system message"},
                {"name": "version", "dataType": ["text"], "description": "Version number to track updates or changes"}
            ],
            "vectorizer": "text2vec-openai"
        }

        try:
            self.client.schema.create({"classes": [
                user_class,
                factoid_class,
                interaction_class,
                observation_class,
                system_class
            ]})
            print("Schema created")
        except Exception as e:
            raise RuntimeError("Error when creating Weaviate schema.") from e


if __name__ == "__main__":

    db = Weaviate()
    db.create_schema(update=True)