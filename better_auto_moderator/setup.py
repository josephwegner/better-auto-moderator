from os import environ

# Don't load dotenv on Heroku dynos
if environ.get('DYNO') is not None:
    from dotenv import load_dotenv
    load_dotenv()
