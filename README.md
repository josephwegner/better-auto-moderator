# BetterAutoModerator

BAM is a refreshed and super-charged version of Reddit's existing auto-moderator functionality. The vision is to recreate what already exists within Reddit's Automoderator, and expand on it in useful and expected ways. The big boon behind BAM is that if you've already learned how to write Automoderator rules, there's nothing new to learn with BAM - the syntax and behavior are identical, but with more options you can use.

## Philosophy

### Let Automoderator do what Automoderator does best

To make life easy for moderators, we only want people to write moderation rules in one place - BAM. We don't want folks to have to manage a separate set of rules between Automoderator and BAM. That said, Reddit has full-time staff that support Automoderator, so we should lean on their capabilities. Where possible, BAM should integrate directly into Automoderator and let it take action. BAM should only take over on the edges where Automoderator doesn't yet have the needed functionality.

### Be familiar

Reddit moderators are smart cookies, but the vast majority of them didn't become moderators because they love writing configuration files. Automoderator has already required them to learn an exotic form of YAML. As much as possible, BAM should leverage that existing skillset. BAM rules should look exactly like Automoderator rules, and behave along the foundational behavior expectations.

### Seamless transitions

The line between an Automoderator rule and a BAM rule is very fine - so small that moderators may not even realize when their rules start running from BAM. This means that BAM needs to function _identically_ to Automoderator, and the transition should be seamless. All native Automoderator functionality should be heavily covered in tests, to ensure that BAM stays aligned.

## Install

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

## Development

To get this running locally you need to do a few things:

1. Install Python3 and Pip3
2. Clone the repo locally
3. Install the dependencies with `pipenv install`
4. [Create a Reddit App](https://www.reddit.com/prefs/apps), with the `script` type. Make note of the client ID and secret.
5. Copy `.env.sample` to `.env`, and fill in the values

You can then run the code with this command:

    pipenv run python app.py

And you can run the test suite with:

    pipenv run python -m pytest
