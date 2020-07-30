# Rule Documentation
## Glossary, and a quick note

Not to cast shade, but sometimes the Reddit AutoModerator documentation can be a bit unclear on what all is available and usable where. BAM recreates all of the functionality, and in effort to make using BAM clear these docs will reiterate all of the pre-existing AutoModerator functionality. They won't be described in detail, but they'll be there.

To that end, here's a glossary of what things are and how they map to Reddit's AutoModerator:

**Checks**: Line items in a rule that are used as _filters_ to decide if a rule should run. These would be things like `body` and `flair`. Checks are the first thing that happen when a rule is applied.

**Actions**: Line items in a rule that _make changes to Reddit_. These would be things like `comment` or `set_locked`. Actions run after all of the checks have passed.

**Sub-Groups**: These are items that are _related_ to the base item, and can be used for either checks or actions - for instance, you may want to check the flair of a submission's _author_. Notably, these can be nested a few levels deep, like `comment -> parent_submission -> author`. Sub-Groups are used like:
```
type: submission
author:
    flair: 'Cool'
```

**Comparators**: The method used when checking a value against your check. Most checks use the `includes-word` comparator by default, but there's also `full-exact`, `includes-word`, `starts-with`, etc. Comparators are set in the check name like `body (starts-with): "PSA: "`.

**Options**: An optional configuration that changes how a check is run. AutoModerator uses pretty consistent defaults across the board, but you can modify things like case sensitivty, or comparisons via RegExp. These are set along-side the comparator, like `body (starts-with case-sensitive): "PSA: "`.

## Globally Available (type: any)
### Comparators
_* available in Reddit's AutoModerator_

- **contains**: Checks if a list contains the value
- **only**: Checks if a list contains _only_ the value. Lists with the same value multiple times will pass.
- _ends-with*_
- _full-exact*_
- _full-text*_
- _includes*_
- _includes-word*_
- _starts-with*_
- _bool*_: Compares True/False values. See AutoModerator's `is_edited` for an example.
- _numeric*_: Compares numeric values, with modifiers such as `> 5` or `< 200`. See AutoModerator's `comment_karma` for details.
- _time*_: Compares a timestamp to a value, such as `> 90 days` or `< 60 hours`. See AutoModerator's `account_age` for details.

### Sub-Groups
_* available in Reddit's AutoModerator_

- _author*_: uses a [Author](#author) type

### Checks
_* available in Reddit's AutoModerator_

- **report_reasons**: A list of reasons that an item has been reported
- _body*_
- _body_longer_than*_
- _body_shorter_than*_
- _id*_
- _is_edited*_
- _reports*_
- _url*_

### Actions
_* available in Reddit's AutoModerator_

- **ignore_reports**: Ignores any active reports on an item
- **log**: Creates a log message in BAM's server logs
- _comment*_
- _message*_
- _modmail*_
- _setsticky*_
- _set_locked*_

## Author (available in sub-groups)
### Checks
_* available in Reddit's AutoModerator_

- **is_banned**: Whether or not the Author is a moderator of parent item's subreddit. Defaults to `bool` comparator.
- _account_age*_
- _combined_karma*_
- _comment_karma*_
- _flair_template_id*_
- _flair_text*_
- _id*_
- _is_contributor*_
- _is_submitted*_: Only available on [Comments](#comment)
- _is_gold*_
- _is_moderator*_
- _name*_
- _post_karma*_

### Actions
_* available in Reddit's AutoModerator_

- _set_flair*_

## Submission
### Sub-Groups
_* available in Reddit's AutoModerator_

- _crosspost_author*_: Uses an [Author](#author) type.
- _crosspost_subreddit*_: Uses a [Subreddit](#subreddit) type.

### Comparators
_* available in Reddit's AutoModerator_

- _domain*_

### Checks
_* available in Reddit's AutoModerator_

- _crosspost_id*_
- _crosspost_title*_
- _domain*_
- _flair_css_class*_
- _flair_template_id*_
- _flair_css_class*_
- _is_gallery*_
- _is_original_content*_
- _is_poll*_
- _media_author*_
- _media_author_url*_
- _media_description*_
- _media_title*_
- _poll_option_count*_
- _poll_option_text*_
- _title*_

### Actions
_* available in Reddit's AutoModerator_

- _set_contest_mode*_
- _set_flair*_
- _set_nsfw*_
- _set_original_content*_
- _set_spoiler*_
- _set_suggested_sort*_

## Comment
### Sub-Groups
_* available in Reddit's AutoModerator_

- **parent_comment**: The comment this comment is replying to. If this is a top-level comment, this sub-group is skipped. Uses a [Comment](#comment) type.
- _author*_: uses a [Author](#author) type.
- _parent_submission*_: uses a [Submission](#submission) type.

### Checks
_* available in Reddit's AutoModerator_

- _is_top_level*_

## Modqueue
Modqueue items will either be of type [Comment](#comment) or [Submission](#submission), and will use the same checks/actions/etc. as those.

## Subreddit
### Checks
_* available in Reddit's AutoModerator_

- _name*_
- _is_nsfw*_

## Placeholders

Placeholders can be used in rule strings, like `set_flair: "Discuss {{title}}"`

_* available in Reddit's AutoModerator_

- _author*_
- _author_flair_css_class*_
- _author_flair_template_id*_
- _author_flair_text*_
- _body*_
- _domain*_
- _kind*_
- _media_author*_
- _media_author_url*_
- _media_description*_
- _media_title*_
- _permalink*_
- _subreddit*_
- _title*_
- _url*_
