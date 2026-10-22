 # Functional requirements

[TOC]

## Scope and Purpose

Read together with [docs/requirements/non-functional.md]. These two documents define the Server First demo. Stable FR-xxx identifiers describe observable behavior and its acceptance criteria. See also [docs/milestones], a milestone map that separates development fixtures from the completed demo.

The demo implements horizontal slice of full game functionality. All major player game loops are present: recruiting, guild management, raid organizing, loot distribution rules and two tiers of in-universe content.

## Terms

| Term | Meaning |
| --- | --- |
| MMO | Fictitious MMORPG game that Server First is simulating |
| In-Universe | Refers to terms and concepts related to MMO. This is in contrast with overlapping terms related to Server First itself. |
| Player | In-Universe NPC representing fictitious human playing MMO. |
| Role | Specialization of Player to serve in the classic model: Tank, Healer, DPS.
| Class | In-Universe RPG class with Role, strength/weakness and Item restrictions.
| Character | In-Universe instance of Class and Items that Player attends raids with |
| User | Server First player |
| Game | Single run through MMO tiers that can be saved and loaded |
| Guild | In-Universe group of Players that is User is managing |
| Item | In-Universe object that User distributes to Players to make them stronger |
| Loot | Item or collection of Items from Boss or Raid.
| Boss | In-Universe encounter that Guild has to defeat to obtain Loot
| Raid | In-Universe instance of one or more Bosses for the Guild to tackle |
| Tier | Collection of Raids available at the same time. Raid Tiers are progressively unlocked through time. Later tiers provide strong Loot. |
| Lockout | Raid time gate-ing mechanism where Bosses can be only defeated once per reset |
| Narrator | AI system that generates randomness and storytelling elements to Game |
| Morale | Player happiness indicator in the guild. Low morale can lead to moral mental breaks.
| Trait | Player behavioral pattern influencing their decision making and morale impacts |
| Server | In-Universe collection of user and AI guilds competing for first kill of the final boss |
| Rank | Hierarchical system within the Guild representing players prestige and influence |
| Gear score | Aggregating metric of Character items power level |
| Pug(s) | Players from server pool not in AI Guilds that randomly sign up for Raid events planned by User. |

Ranks are highlighted in the following chapters with *cursive*. User actions will often apply morale effects on one or more guild players, the are highlighted with `inline code` and their effects can be found [DATA-001].

## High-level game flow

### FR-001 - New game

New game shall start with  the first Tier unlocked and empty lock-out. User shall pick difficulty and narrator. User shall start with empty guild and initial "core" 15 player recruiting. 600 players for sever player pool and 10 AI guilds shall be generated.

Acceptance:

* Once user picks difficulty, narrator and core players, the game is saved
* User can immediately recruit new players and organize first raid in the first tier
* There is no lock-out for any bosses
* Game starts paused
* Server pool uses 3:6:21 - tank/healer/dps ratio for role distribution
* 10 AI guilds shall have 20 core players with 2 tanks and 4 healers grabbed from server player pool

### FR-002 - Core recruiting

User shall be presented with UI to recruit 15 players for the guild. They shall be generated randomly with per player re-roll and optional option to only roll specific role.

Acceptance:

* There is always 15 slots with one player per slot in the list
* Initial random list is always generated with 2 tanks and 4 healers and rest dps
* If user selection has less than 2 tanks and less than 4 healers, warning should appear before the game is started
* Players are randomly generated including their character class and traits
* User can lock specific slot to a role which will re-roll the player to that role if necessary and all future players in that slot will have that role until unlocked again
* Core recruiting does not incur morale changes from later requirements, overriding those requirements (see [DATA-001])
* All core recruits gain `Core recruit` immediately and `Settled core recruit` after `Core recruit` runs out
* User can assign 3 *Officers*, of different classes, during core recruiting. They gain `Core officer` in addition to `Core recruit`
* All non-*officers* players gain rank *Novice*

### FR-003 - Time progression

Game shall progress in real-time with speed controls and pause.

Acceptance:
* On normal speed an In-Universe day lasts 30 seconds
* On fast speed day lasts 15 seconds
* On fastest speed, day lasts 5 seconds
* When game is paused, In-Universe time does not progress

### FR-004 - Second tier

Second tier of raids shall unlock after three months of In-Universe time passed.

Acceptance:
* Once three months pass, user is able to organize second tier raids
* Tier one raids remain accessible

### FR-004 - Game end

The game shall end when the last boss of the second raid tier is defeated by user guild. It shall be considered victory if user guild is the first guild on the server to defeat the final boss.

* User is presented with ending screen once the final boss is defeated

### FR-005 - Lock-out

All slain bosses shall reset every week.

* Bosses cannot be slain more than once per week
* All bosses receive new randomized loot from their loot tables during reset

## Guild management

### FR-006 - Weekly recruitment

User shall be presented with 5 random players from server pool to recruit every week.

Acceptance:
* Narrator can influence recruitment to give user favorable recruits
* Players in AI guilds can transfer to and from server pool

### FR-007 - Recruitment

User shall be able to reject, interview or accept players from the recruitment UI.

Acceptance:
* Rejected players are not offered again this tier in the recruitment. They are 3 times less likely to appear in the following phases.
* Accepted players immediately join the guild with *Trial* rank and gain `New recruit`. If they are promoted to *Social* they gain `Passed trial`.
* One hidden trait (if possible) and current items are revealed when player is interviewed by user
* Once trait is revealed, it is always known to user regardless of player status
* Players that user only interviews or does not interact with are returned to server pool and are eligible for next week

### FR-008 - Guild roster

User shall be able to display current guild players. Filter them by role, class and rank. Sort them by rank, class, role, gear score, morale and name.

Acceptance:
* Filters and sorting dynamically updates the displayed list.
* User can click on any player displaying their player sheet with all details

### FR-009 - Ranks

User shall be able to promote and demote players between following ranks: *Social*, *Novice*, *Senior*, *Officer*. *Trials* are automatically promoted to *Social* after two weeks.

Acceptance:
* User can only promote specific player once per week and by one rank only
* There can be only one *Officer* per class in the guild
* Demoting *Senior* or *Officer* applies `Leadership change` to guild members. Dislike and Hated relationships instead apply `Disliked leadership change` and `Hated leadership change` respectively.
* Promoting or demoting *Seniors* contributes 1 point and *Officers* 2 points towards `Unstable Leadership` debuff. If more than three points are accumulated during one week all guild players receive `Unstable Leadership`. The points reset each week.
* Promoting to *Novice*, *Senior* or *Officer* awards `Promoted to novice`, `Promoted to senior` or `Promoted to officer` respectively to the promoted player.

### FR-010 - Kick

User shall be able to remove players from the guild.

* Players kicked from guild during active raid automatically leave the raid
* Kicked players with *Trial* rank do not incur a guild morale penalty unless a Friend or Best friend relationship, in which case `Trial friend kicked` or `Trial best friend kicked` is applied to the related guild player respectively.
* Kicked players with *Social*, *Novice*, *Senior* or *Officer* rank apply `<Rank> kicked` to other guild members. Hated relationship applies `Hated player kicked` instead, irrespective of the rank. Dislike relationship applies `Disliked <rank> kicked` instead of `<Rank> kicked`. Friend relationship applies `Friend <rank> kicked` instead of `<Rank> kicked`. Best friend relationship apply `Best friend <rank> kicked` instead of `<Rank> kicked`.

## Raiding

### FR-011 - World map

User shall have world map menu option that displays available raids and capital city for guild management.

Acceptance:
* All current and past tiers' raids are visible on world map
* If at least one boss was defeated a label next to the raid displays number of killed bosses slash total number of bosses in the raid. If all bosses were defeated the label shall have green font color, red otherwise.
* Time controls UI is visible on the world map
* Capital city icon is visible on the map which when clicked opens city map
* Clicking on raid with at least one undefeated boss opens raid planning menu

### FR-012 - Plan raid event

User shall be able to organize raid events for currently opened raids that have at least one boss alive.

Acceptance:
* User can pick time and date for the raid anytime from now on. Raids can only be scheduled between 5pm to 1am.
* User can set raid as recurring which will automatically schedule it every week, the same week day and time
* Recurring planned events for the selected raid are visible in the raid planning screen showing summary of the next two events
* When adjusting recurring event, user is asked to select whether they want to modify only this event or all future events for this raid
* Event planning shows 10/25 slots for players depending on the raid divided into groups of 5
* User can drag guild players to and between the slots assuming the are available
* Raid event planning shall show raid-wide and group-wide buffs as icons dynamically based on the roster
* User can advertize the raid events for pugs to sign up to. Pugs randomly appear in an available list once advertised at a rate 3-8 players per day. There is 30% chance 1-2 pugs that signed up but were to picked will disappear from the list daily starting from day 2 of being signed up. Narrator can influence pug selection.
* Once advertised, available pugs are displayed with name, class and gear score. They can be dragged to slots same as guild members.

### FR-013 - Cancel raid

User can cancel raid up the time it is scheduled to start.

Acceptance:
* Cancelling raid event more than a week before it starts does not incur any morale loss.
* Cancelling raid less than a week but more than 1 day before it starts applies `Raid canceled` to available guild players unless stated otherwise.
* Cancelling raid event less than 2 days before it starts applies `Raid canceled last-minute` to available guild players unless stated otherwise.

### FR-012 - Raid start

Planned raids automatically start at the time they are scheduled.

Acceptance:
* If less than 80% raid slots are filled user is given option and recommendation to last-minute cancel the raid
* If pugs were taken over guild players with rank *Novice* and above for the specific role, all non-taken guild players gain `Passed over for a pug`
* Guild players traits related to attendance are evaluated at the raid start

## Players


## DATA-001 - Morale effects

The following table defines the named morale effects used by the requirements.

| Name | Morale effect | Duration (In-Universe time) |
| --- | --- | --- |
| Core recruit | +15 | 4 weeks |
| Settled core recruit | +5 | 3 weeks |
| Core officer | +5 | 3 weeks |
| New recruit | +10 | 3 weeks |
| Passed trial | +5 | 3 weeks |
| Leadership change | -1 | 2 weeks |
| Disliked leadership change | 0 | 2 weeks |
| Hated leadership change | 0 | 2 weeks |
| Unstable Leadership | -5 | 3 weeks |
| Promoted to novice | +3 | 3 weeks |
| Promoted to senior | +5 | 5 weeks |
| Promoted to officer | +7 | 6 weeks |
| Trial friend kicked | -3 | 3 weeks |
| Trial best friend kicked | -5 | 5 weeks |
| Social kicked | -1 | 2 weeks |
| Novice kicked | -3 | 2 weeks |
| Senior kicked | -5 | 3 weeks |
| Officer kicked | -7 | 4 weeks |
| Disliked social kicked | 0 | 2 weeks |
| Disliked novice kicked | -1 | 2 weeks |
| Disliked senior kicked | -2 | 2 weeks |
| Disliked officer kicked | -3 | 3 weeks |
| Hated player kicked | +3 | 2 weeks |
| Friend social kicked | -3 | 4 weeks |
| Friend novice kicked | -5 | 4 weeks |
| Friend senior kicked | -7 | 5 weeks |
| Friend officer kicked | -13 | 6 weeks |
| Best friend social kicked | -5 | 8 weeks |
| Best friend novice kicked | -6 | 8 weeks |
| Best friend senior kicked | -10 | 9 weeks |
| Best friend officer kicked | -15 | 10 weeks |
| Raid canceled | -3 | 2 weeks |
| Raid canceled last-minute | -5 | 3 weeks |
| Passed over for a pug | -8 | 4 weeks |

## DATA-002 - Classes

The following tables defines all In-Universe classes that Character can have.

### Tanks

| Name | Avoidance | Migitation | EHP | CDs | AOE threat | Cleave threat | Single-target threat | Mobility | Initial gearing | Gear scaling | Buffs | Damage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |  --- |
| Dookh |       ++ |          + |   - |   + |          + |             0 |                    0 |        - |               + |            0 |     - |      - |
| ???   |        + |          0 |  ++ |   - |          0 |             0 |                    + |        0 |               - |            0 |     + |      + |
| ???   |        - |         ++ |   + |   0 |          - |             + |                    + |        + |               0 |            + |     0 |      0 |

