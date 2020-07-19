from os import environ

if environ.get('DYNO') is not None:
    from dotenv import load_dotenv
    load_dotenv()
