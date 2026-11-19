# Mismatched.gg Calendar Bot

### Why does this exist?

**For Players**: A tool to help you keep all your events in an easily accessible place so that you don’t have to drive 2 hours to hear a shop owner say "I had no idea *we* even ran VGC"

**For Organizers**: A tool to help you keep all your events in an easily accessable place so that players can't genuinely say "I had no idea you guys even ran VGC"

**For Judges**: A tool to help you figure out a store to talk to and help run events so that you aren't sitting there with an unused cert saying "I had no idea y'all even ran VGC"

### Why not use the official event locator??

The event locator is an amazing tool, but has a very limited search radius, and can be inaccessible at times. Plus while you're trying to see if it's back up, it can block you for too many requests. I built this tool to help players locate the events around them and be able to save events in their area to a google calendar with all the info they need  without wondering if they're missing an event just outside of the limited search radius, whether it's friendly or premier.

## How it works

You add the bot to your discord server (or use the web tool) and initialize it in a channel where everyone can read but only you and the bot can type. Then add your feeds via the [Mismatched configuration portal](https://bot.mismatched.gg), then you step back and let it do its thing!

Once every hour (or more by manual trigger) the bot checks a feed of events for all US States (and DC) and pulls it on to our server, where it is then parsed and checked against each area's "Premier" and "Friendly" calendars for changes or removals. New events are uploaded, and the others are updated or deleted.

From there, the server dispatches the bot to create an updated embedded calendar view for your configuration which updates live as changes are pulled in (no new message spam). The embed also provides links to view the calendar full calendar or add it to your account to automatically sync as the bot gets updated events.

## How to set it up

This requires you have the **admin permission flag** for the server the bot has been added to.

* [Add the bot to your discord server](https://discord.com/oauth2/authorize?client_id=1551933057852899378)
* Run `/initalize` in a channel where everyone can read but the bot can message in
* Go to [the configuration interface](https://bot.mismatched.gg) and log in with discord, set up the bot to your liking
* Run `/refresh` in the channel the bot was initialized in, and you're off to the races!

## Commands:

| Command | Description | Required flag |
|:---|:---|:---|
| `/init` | initalize the bot to the channel (limited to one instance per channel) | Bot owner or Admin |
| `/force` | calls for a new data sweep/update for all states, refreshes all configs | Bot owner or Admin |
| `/refresh` | Updates embed to use most recently configured data from the web portal (automatically occurs hourly) | Bot owner or Admin |
| `/refresh` | Updates embed to use most recently configured data from the web portal (automatically occurs hourly) | Bot owner or Admin |
| `/detatch` | Removes the configuration for the channel, allows for a new initialization (automatically occurs hourly if the bot's embed has been deleted or rendered inaccessible) | Bot owner or Admin |
| `/updatelog` | Shows git commit history for the bot with time stamps | any |
| `/calendars` | Creates a selection menu to allow a user to fetch any state's calendar synchronization link | any |
| `/clearfuture` | Wipes a calendars upcoming events, will fully repopulate the state next refresh cycle | Bot owner |


