**What it does:**

Input is json results file of https://www.opendota.com/explorer query

*Functionality 1)*

Download all the matching replays for this query.
This makes analysing teams/games easier for the user through being able to simply use "playdemo replays/<match-id>.dem".
No backing out and having to download next game, and then load it up.

*Functionality 2)*

Parse these downloaded replays for 'tick of interest'
Definition of interesting would be up to user/script writer for that particular case.
Simples examples would be teamfight starts, impressive ultimate uses (i.e chrones that catch multiple people), ganks etc
You can use "demo_gototick <tick_num>" to jump around a replay instantly, no messing with having to manually search through replays
(demo_gototime exists but has to factor in draft time and other starts. Is just plain more awkward than always correct tick number)


**Possible use cases:**

1) Making it easier to produce short broadcasting segments/clips for pre-game analysis.
i.e. you first do some statistical analysis to find interesting points to highlight pre-game. Such as team has 80% winrate this patch with void.
You can then write a simple script to extract ticks where > x enemies were chronoed. Then making a small highlight video to illustrate point is simple and easy.

2) Professional teams preparing for opponents (helps when breaking game down into 'sections' to analayse. i.e. easier to ask multiple
questions, "how do they lane, how do they teamfight, what are farming patterns* etc",
 broken down. Rather than having to analyze every aspect simultaneously.


* (When camera angles/choices dont matter. i.e player perspective for farming patterns, could generate automated videos aggregating this info)

**How to Use**
- Clone https://github.com/skadistats/clarity-examples
- Add the folder inside clarity-examples in this repo to the examples
- add 
        ```<profile>
            <id>smoketimings</id>
            <activation><activeByDefault>true</activeByDefault></activation>
            <properties>
                <exampleName>smoketimings</exampleName>
            </properties>
        </profile>```
  to pom.xml
- mvn -P smoketimings package
- run ```python main.py "download_path"``` (python 3)

# TODOs:
- Move the analysis parts to a server, not local

Notes:
hero_ids.json copied from https://github.com/odota/dotaconstants
The smoketimings/Main.java modified from combatlog example of https://github.com/skadistats/clarity-examples

Would not be possible without clarity or opendota projects so thanks to them :D

Housemate (https://github.com/ScoreUnder) was very helpful (File streams with generators stuff, plus java thread-pooling)
