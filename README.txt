What it does:

Input is the pro team you want to analyse(along with filters for patch/date/etc).

Functionality 1)

Download all the matching replays of this team.
This makes analysing teams easier for the user through being able to simply use "playdemo replays/<match-id>.dem".
No backing out and having to download next game, and then load it up.

Functionality 2)

Parse these downloaded replays for 'tick of interest'
Definition of interesting would be up to user/script writer for that particular case.
Simples examples would be teamfight starts, impressive ultimate uses (i.e chrones that catch multiple people), ganks etc
You can use "demo_gototick <tick_num>" to jump around a replay instantly, no messing with having to manually search through replays
(demo_gototime exists but has to factor in draft time and other starts. Is just plain more awkward than always correct tick number)


Possible use cases:

1) Making it easier to produce short broadcasting segments/clips for pre-game analysis.
i.e. you first do some statistical analysis to find interesting points to highlight pre-game. Such as team has 80% winrate this patch with dazzle.
You can then write a small script* to extract good** dazzle grave ticks with this tool. Then making a small highlight video to illustrate point is simple and easy.

2) Professional teams preparing for opponents (helps when breaking game down into 'sections' to analayse. i.e. easier to ask multiple
"how do they lane, how do they teamfight, what are farming patterns*** etc",
 broken down. Rather than having to analyze every aspect simultaneously



** Simple algorithm would be any grave in teamfight wins where grave applied when target under X% health and they take attacks taking them down to 0-ish health
*** (When camera angles/choices dont matter. i.e player perspective for farming patterns, could generate automated videos aggregating this info)

# TODOs:
- would be nice to have the games in a database so I can just query. dont have to wait 1-second between every api-request
- My PC thrashes cpu when downloading 5 files at once...but it seems to be avast who is the main culprit ._.

Notes:
hero_ids.json copied from https://github.com/odota/dotaconstants
The smoketimings/Main.java modified from combatlog example of https://github.com/skadistats/clarity-examples

Would not be possible without clarity or opendota projects so thanks to them :D

Housemate (https://github.com/ScoreUnder) was very helpful (File streams with generators stuff, plus java thread-pooling)
