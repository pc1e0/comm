import os
import praw
import threading
from ai import ChatGPT
from db import Weaviate
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


class EthTraderAI:


    def __init__(self):

        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_SECRET")
        username = os.getenv("REDDIT_USERNAME")
        password = os.getenv("REDDIT_PASSWORD")
        user_agent = os.getenv("REDDIT_USER_AGENT")
        subreddit = os.getenv("REDDIT_SUBREDDIT")

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent
        )
        self.subreddit = self.reddit.subreddit(subreddit)

        self.ai = ChatGPT()
        self.db = Weaviate()


    def extract_context(self, comment, depth=5):

        context = []
        current_comment = comment

        for _ in range(depth):

            if isinstance(current_comment, praw.models.Comment):
                context.insert(0, f"{current_comment.id}: comment | {current_comment.author.name}: {current_comment.body}")

            elif isinstance(current_comment, praw.models.Submission):
                context.insert(0, f"{current_comment.id}: post | {current_comment.author.name}: {current_comment.title}")

            try:
                current_comment = current_comment.parent()

            except AttributeError:
                break  # We reached the top

        return context
    

    def handle_learn_this(self, comment):

        # Who submitted
        suggested_by = comment.author.name if comment.author else "Unknown"
        review_status = "Approved" if suggested_by == "pc1e0" else "Pending"

        # Get the parent of the comment which contains "!learn this"
        parent = comment.parent()

        # Retrieve parent's author
        parent_author = parent.author.name if parent.author else "Unknown"

        # Retrieve parent's URL
        parent_source = f"https://www.reddit.com{parent.permalink}"
        
        # Initialize the content variable
        parent_content = ""

        # If the parent is a comment, fetch the author and body of the parent comment
        if isinstance(parent, praw.models.Comment):
            parent_content = f"A Reddit [comment]({parent_source}) by u/{parent_author}:\n\n{parent.body}"
            parent_category = "Reddit comment"
        
        # If the parent is a post, fetch the author, title, and selftext of the parent post
        elif isinstance(parent, praw.models.Submission):
            parent_content = f"A Reddit [post]({parent_source}) by u/{parent_author}:\n\n# {parent.title}\n\n{parent.selftext}"
            parent_category = "Reddit post"
        
        # Summarize parent content
        summarized_content = self.ai.summarize(parent_content)

        # Store parent content
        self.db.write_factoid(
            content=parent_content,
            summary=summarized_content,
            author=parent_author,
            source=parent_source,
            category=parent_category,
            suggested_by=suggested_by,
            review_status=review_status
        )

    
    def listen_to_comments(self):

        for comment in self.subreddit.stream.comments(skip_existing=True):

            if comment.body.startswith("!learn this"):
                self.handle_learn_this(comment)

            else:

                parent_comments = self.extract_context(comment)
                full_context = "\n".join(parent_comments)
                flagged = self.ai.moderate(full_context)

                if not flagged:

                    print("Conversation:")
                    print(full_context)

                    classification_result = self.ai.classify(comment.body, full_context)

                    print("Classification Result:")
                    print(classification_result)


    def listen_to_posts(self):

        for submission in self.subreddit.stream.submissions(skip_existing=True):
            print(f"New post: [{submission.author.name}] {submission.title}: {submission.selftext if submission.is_self else submission.url}")


    def listen_to_subreddit(self):

        comment_thread = threading.Thread(target=self.listen_to_comments)
        post_thread = threading.Thread(target=self.listen_to_posts)

        comment_thread.start()
        post_thread.start()


if __name__ == "__main__":

    # Initialize robot
    robot = EthTraderAI()

    # Start listening to the EthTrader subreddit
    robot.listen_to_subreddit()