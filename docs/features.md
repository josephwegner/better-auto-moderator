# BetterAutoModerator features

Beyond just recreating AutoModerator features and enhancing them, BAM has a few additional features for making your rules more powerful and easy to manage.

## Variables

Often times AutoModerator rules can be repetitive - repeating the same lists of flairs, users, keywords, etc. all over the place. Variables make it easier to write these settings in one place and use them in any of your rules.

In your config file (`better_auto_moderator` in wiki), you can add a `variables` object like follows:

```
variables:
    - shadowbanned_users: ['joker', 'meanieface', 'badguy']
    - approved_user_flairs: ['Top performer', 'Nice guy', 'Thoughtful individual']
```

These variables are then available in your rules, to be used as [YAML anchors](https://support.atlassian.com/bitbucket-cloud/docs/yaml-anchors/). That goes something like this:

```
type: any
author:
    name: *shadowbanned_users
action: remove
```

**Protip:** If you only allow some members of your mod team to edit AutoModerator rules, but want people to be able to edit these variables, you can change your file permissions. If you set the `better_auto_moderator/rules` file to only be editable by approved editors, that will mean the rules are locked down but the variables can be changed!
