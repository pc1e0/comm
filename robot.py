import os
import praw
import openai
import threading
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()


class EthTraderAI:


    def __init__(self, client_id, client_secret, username, password, user_agent, subreddit):

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            username=username,
            password=password,
            user_agent=user_agent
        )
        self.subreddit = self.reddit.subreddit(subreddit)


    def check_content_moderation(self, content):
        response = openai.Moderation.create(input=content)
        return response["results"][0]['flagged']


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
            full_context = '\n'.join(parent_comments)
            flagged = self.check_content_moderation(full_context)
            if not flagged:
                print(full_context)


    def listen_to_posts(self):
        for submission in self.subreddit.stream.submissions(skip_existing=True):
            print(f"New post: [{submission.author.name}] {submission.title}: {submission.selftext if submission.is_self else submission.url}")


    def listen_to_subreddit(self):
        comment_thread = threading.Thread(target=self.listen_to_comments)
        post_thread = threading.Thread(target=self.listen_to_posts)

        comment_thread.start()
        post_thread.start()


if __name__ == '__main__':

    # Load OpenAI key
    openai.api_key = os.getenv("OPENAI_KEY")

    # Load Reddit keys
    CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
    CLIENT_SECRET = os.getenv("REDDIT_SECRET")
    USERNAME = os.getenv('REDDIT_USERNAME')
    PASSWORD = os.getenv('REDDIT_PASSWORD')
    USER_AGENT = os.getenv('REDDIT_USER_AGENT')
    SUBREDDIT = os.getenv('REDDIT_SUBREDDIT')

    # Initialize robot
    robot = EthTraderAI(CLIENT_ID, CLIENT_SECRET, USERNAME, PASSWORD, USER_AGENT, SUBREDDIT)

    # Start listening to the EthTrader subreddit
    robot.listen_to_subreddit()