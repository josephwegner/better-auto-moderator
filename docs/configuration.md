# Global configuration

When you install BAM, you will see a file in your wiki named `better_auto_moderator` - the root file for BAM. This file holds global configurations, which will apply to _all_ of your rules. The following is a description of what each of those configurations do:

### `overwrite_automoderator`
**Default**: `false`

**NOTE: Turning this on will clear your `automoderator/config`! Read on to better understand it!**

When set to `true`, BAM will scan all of your rules and identify ones that can be run within Reddit's AutoModerator - it then copies them into your `automoderator/config` file. We recommend turning this on, to leverage the processing power of Reddit. However, doing this will cause BAM to overwrite your existing AutoModerator config - make sure that you've copied all of your rules over to `better_auto_moderator/config` before turning it on.
