**What it does:**

Input is json results file of https://www.opendota.com/explorer query

*Functionality 1)*

Download all the matching replays for this query.
This makes analysing teams/games easier for the user through being able to simply use "playdemo replays/match-id.dem" console cmd.
No backing out and having to download next game, and then load it up.

*Functionality 2)*

Parse these downloaded replays for 'tick of interest'
Definition of interesting would be up to user/script writer for that particular case.
Simples examples would be teamfight starts, impressive ultimate uses (i.e chrones that catch multiple people), ganks etc
You can use "demo_gototick tick_number" console cmd to jump around a replay instantly, no messing with having to manually search through replays
(demo_gototime exists but has to factor in draft time and other starts. Is just plain more awkward than always correct tick number)

**Instructions**
requirements:
python3, java 1.8

- Clone this repo (https://github.com/ThePianoDentist/dotaHighlightHelper)
- Clone https://github.com/ThePianoDentist/clarity-examples repo
- cd/move to clarity-examples directory
- `mvn -P modified_odota package`
- Set ODOTA_REPLAY_PARSER_FILE in config.ini to the one-jar file produced
- Set REPLAY_FOLDER in config.ini
- make a query on https://www.opendota.com/explorer and click JSON to save result

example usage:
cd to hightlightHelper directory
python main.py "C:\Users\Johnny\Downloads\data (4).json" teamfights

(if just testing, filtering tournament: Kiev major, Player: Boboka, Hero: Riki....and searching for courierkills is a nice short example e.g. https://www.youtube.com/watch?v=jmhubgQrh9E&feature=youtu.be)

you can set a limit on numnber of parallel replay downloads with MAX_PARALLEL_DOWNLOADS in config file.



**Possible use cases:**

1) Making it easier to produce short broadcasting segments/clips for pre-game analysis.
i.e. you first do some statistical analysis to find interesting points to highlight pre-game. Such as team has 80% winrate this patch with void.
You can then write a simple script to extract ticks where > x enemies were chronoed. Then making a small highlight video to illustrate point is simple and easy.

2) Making montages of players/teams/tournaments. I.e. could extract every rampage in a tournament, every flawless teamwipe, every courier kill etc.

3) Professional teams preparing for opponents (helps when breaking game down into 'sections' to analayse. i.e. easier to ask multiple
questions, "how do they lane, how do they teamfight, what are farming patterns* etc",
 broken down. Rather than having to analyze every aspect simultaneously.


* (When camera angles/choices dont matter. i.e player perspective for farming patterns, could generate automated videos aggregating this info)

**Known Bugs:**
- For chronospheres, when specifying minimum enemies caught it will include friendlies

**TODOs:**
- Move the analysis parts to a server, not local
- Let parts that can be asyn, be async. (I.e. dont need to wait for all match_its found to start downloading replays, same for parsing)
- The output from parallel java tasks mixes lines. Solved by putting matchID into entries, but is this poor solution?

**Notes:**
Would not be possible/so easy without clarity or opendota projects so thanks to them :D
