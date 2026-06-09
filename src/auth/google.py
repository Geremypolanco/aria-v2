import os
from authlib.integrations.starlette_client import OAuth

config = {"GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"), "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET")}
oauth = OAuth()

oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)