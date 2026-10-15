# Portal Pokémon Roster

This list is copied from the portal’s `engine/roster_data.js` database. The
portal is the source of truth; use `/api/pokemon-roster` and `/api/pokemon-options`
for the live JSON data.

The portal currently provides 24 selectable Pokémon for Gen 9 3v3 Singles.
Each entry uses the portal’s default ability, item, nature, EV preset, and
moves unless the user customizes them in the UI.

| Pokémon | Types | BST | Abilities | Default moves |
|---|---|---:|---|---|
| Garchomp | Dragon / Ground | 600 | Rough Skin; Sand Veil | Earthquake; Outrage; Stone Edge; Swords Dance |
| Dragonite | Dragon / Flying | 600 | Multiscale; Inner Focus | Extreme Speed; Outrage; Earthquake; Fire Punch |
| Tyranitar | Rock / Dark | 600 | Sand Stream; Unnerve | Stone Edge; Crunch; Earthquake; Ice Punch |
| Metagross | Steel / Psychic | 600 | Clear Body; Light Metal | Meteor Mash; Bullet Punch; Earthquake; Zen Headbutt |
| Salamence | Dragon / Flying | 600 | Intimidate; Moxie | Draco Meteor; Flamethrower; Earthquake; Roost |
| Hydreigon | Dark / Dragon | 600 | Levitate | Dark Pulse; Draco Meteor; Flamethrower; Flash Cannon |
| Dragapult | Dragon / Ghost | 600 | Infiltrator; Clear Body | Dragon Darts; Phantom Force; Flamethrower; U-turn |
| Volcarona | Bug / Fire | 550 | Flame Body; Swarm | Fiery Dance; Bug Buzz; Giga Drain; Quiver Dance |
| Lucario | Fighting / Steel | 525 | Inner Focus; Steadfast; Justified | Close Combat; Meteor Mash; Extreme Speed; Flash Cannon |
| Scizor | Bug / Steel | 500 | Technician; Swarm | Bullet Punch; Close Combat; Swords Dance; U-turn |
| Gengar | Ghost / Poison | 500 | Cursed Body | Shadow Ball; Sludge Bomb; Focus Blast; Thunderbolt |
| Gyarados | Water / Flying | 540 | Intimidate; Moxie | Waterfall; Earthquake; Ice Fang; Dragon Dance |
| Charizard | Fire / Flying | 534 | Blaze; Solar Power | Flamethrower; Air Slash; Focus Blast; Dragon Pulse |
| Blastoise | Water | 530 | Torrent; Rain Dish | Hydro Pump; Ice Beam; Flash Cannon; Protect |
| Venusaur | Grass / Poison | 525 | Overgrow; Chlorophyll | Giga Drain; Sludge Bomb; Earth Power; Sleep Powder |
| Arcanine | Fire | 555 | Intimidate; Flash Fire; Justified | Flare Blitz; Extreme Speed; Wild Charge; Will-O-Wisp |
| Excadrill | Ground / Steel | 508 | Mold Breaker; Sand Rush; Sand Force | Earthquake; Iron Head; Rock Slide; Swords Dance |
| Togekiss | Fairy / Flying | 545 | Serene Grace; Super Luck | Air Slash; Dazzling Gleam; Aura Sphere; Roost |
| Snorlax | Normal | 540 | Thick Fat; Immunity | Body Slam; Earthquake; Crunch; Rest |
| Alakazam | Psychic | 500 | Magic Guard; Synchronize; Inner Focus | Psychic; Shadow Ball; Focus Blast; Energy Ball |
| Lapras | Water / Ice | 535 | Water Absorb; Shell Armor | Freeze-Dry; Hydro Pump; Thunderbolt; Ice Beam |
| Corviknight | Flying / Steel | 495 | Mirror Armor; Pressure | Brave Bird; Body Press; Roost; Iron Defense |
| Ferrothorn | Grass / Steel | 489 | Iron Barbs | Power Whip; Gyro Ball; Leech Seed; Protect |
| Greninja | Water / Dark | 530 | Protean; Torrent | Hydro Pump; Dark Pulse; Ice Beam; U-turn |

## Important training note

The portal runs the final `PokemonAgent.decide(observation)` policy during a
match. It does not provide a public RL `reset()`/`step()` training API. Train
locally using Pokémon Showdown or another compatible battle-data environment,
then submit the resulting Python agent through the portal.
