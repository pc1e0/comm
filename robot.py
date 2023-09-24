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

    
    def listen_to_comments(self):

        for comment in self.subreddit.stream.comments(skip_existing=True):

            parent_comments = self.extract_context(comment)
            full_context = "\n".join(parent_comments)
            flagged = self.ai.moderate(full_context)

            if not flagged:

                print("Conversation:")
                print(full_context)

                classification_result = self.ai.classify(comment, full_context)

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