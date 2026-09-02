"""Seed dataset for the launch corpus: Classroom of the Elite, Code Geass, Attack on
Titan, and One Piece.

Run with: python -m app.db.seed (requires migrations applied via `alembic upgrade head`).

mal_id/anilist_id are real, verified IDs (cross-checked live against both APIs) — they drive
external metadata ingestion (app/db/ingest_sources.py, SPEC.md D6).
"""

import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import Anime, Character, Faction, Franchise, FranchiseEntry, TemporalFact

logger = logging.getLogger(__name__)

SEED_ANIME: list[dict] = [
    {
        "slug": "classroom-of-the-elite",
        "title": "Classroom of the Elite",
        # Seasons 1-4 (12 + 13 + 12 + 16). Season 4 aired Apr 1 - Jun 24, 2026 and is
        # complete, verified against Wikipedia's episode listing.
        "total_episodes": 53,
        "season_episode_counts": [12, 13, 12, 16],
        "mal_id": 35507,
        "anilist_id": 98659,
        "cover_image_url": "https://s4.anilist.co/file/anilistcdn/media/anime/cover/large/bx98659-WNyPLIZDpGGY.jpg",
        "genres": ["Drama", "Suspense"],
        "score": 7.82,
        "synopsis": (
            "At a prestigious high school that grades its students far more harshly "
            "than it appears, an outwardly average transfer student is placed in the "
            "lowest-ranked class — and turns out to be anything but ordinary."
        ),
        # The school's four-class ranking (D lowest, A highest) is explained to the
        # audience in Episode 1 via the point system — it's public setting lore, not a
        # narrative reveal — so all four classes are given a `first_revealed_at` of
        # S1E1 and render as visible faction cards immediately, filling in with named
        # rival-class students as each of them individually debuts.
        "factions": [
            {
                "name": "Class D",
                "description": "The lowest-ranked class at the Advanced Nurturing High School.",
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Class C",
                "description": "The third-ranked class at the Advanced Nurturing High School.",
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Class B",
                "description": "The second-ranked class at the Advanced Nurturing High School.",
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Class A",
                "description": "The top-ranked class at the Advanced Nurturing High School.",
                "first_revealed_at": "S1E1",
            },
        ],
        "characters": [
            {
                "name": "Kiyotaka Ayanokoji",
                "faction": "Class D",
                "role": "Class D Student",
                "height": "176 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b123212-ewZgUQr9vvEM.png",
                "backstory": (
                    "An inconspicuous and unobtrusive student who keeps a low profile. "
                    "He shows a calm, observant nature and a sharp insight into the "
                    "people around him. Almost nothing about his life prior to the "
                    "entrance exam is known."
                ),
            },
            {
                "name": "Suzune Horikita",
                "faction": "Class D",
                "role": "Class D Student",
                "height": "156 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b123213-jUfrGBXfW7BL.png",
                "backstory": (
                    "A cold, aloof girl who sits near Ayanokoji. Unlike him, she "
                    "disregards friendship and rarely goes out of her way to talk to "
                    "her classmates. Unconvinced she belongs in Class D, she is "
                    "determined to climb her way up to Class A."
                ),
            },
            {
                "name": "Kikyo Kushida",
                "faction": "Class D",
                "role": "Class D Idol",
                "height": "155 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b123214-Ym9cldopi3yR.png",
                "backstory": (
                    "Tremendously popular with both boys and girls, Kushida is "
                    "considered Class D's idol. She makes a point of trying to "
                    "befriend everyone, not just her own classmates, and gets along "
                    "particularly well with Horikita."
                ),
            },
            {
                "name": "Kakeru Ryuen",
                "faction": "Class C",
                "role": "Class C Leader",
                "first_revealed_at": "S1E4",
                "backstory": (
                    "A physically imposing, openly aggressive leader who controls his "
                    "classmates through intimidation and treats every inter-class "
                    "exam as a fight to be won by any means necessary."
                ),
            },
            {
                "name": "Honami Ichinose",
                "faction": "Class B",
                "role": "Class B Representative",
                "first_revealed_at": "S1E4",
                "backstory": (
                    "A warm, well-liked student widely seen as the ideal class "
                    "representative, known for keeping Class B cooperative and "
                    "friendly even under exam pressure."
                ),
            },
            {
                "name": "Kohei Katsuragi",
                "faction": "Class A",
                "role": "Class A Leader",
                "first_revealed_at": "S1E4",
                "backstory": (
                    "A serious, methodical strategist who leads Class A with strict "
                    "discipline, treating every special exam as a calculation to be "
                    "solved rather than a game to be enjoyed."
                ),
            },
            {
                "name": "Ken Sudo",
                "faction": "Class D",
                "role": "Class D Student",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b207025-gpnIy6ewtfVu.png",
                "backstory": (
                    "A hot-blooded, athletically gifted Class D student who reacts "
                    "to insults about his class with his fists first and his head "
                    "second."
                ),
            },
            {
                "name": "Kei Karuizawa",
                "faction": "Class D",
                "role": "Class D Student",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b141122-6Zk52eU3VK3O.png",
                # Public-facing description only — her real circumstances are a
                # much later story reveal, not something this dataset gates a
                # fact for yet, so the backstory stops at what Class D itself
                # sees of her.
                "backstory": (
                    "A popular, fashion-conscious Class D student at the center "
                    "of her own tight social circle, well known throughout the "
                    "class though rarely seen without her group of friends."
                ),
            },
            {
                "name": "Airi Sakura",
                "faction": "Class D",
                "role": "Class D Student",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b123215-sMQJk35TqQv4.jpg",
                "backstory": (
                    "A quiet, camera-shy Class D student with a passion for "
                    "photography, more comfortable observing from behind a lens "
                    "than speaking up in a crowd."
                ),
            },
            {
                "name": "Rokusuke Kouenji",
                "faction": "Class D",
                "role": "Class D Student",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b158988-P28e8SU3WpGK.png",
                "backstory": (
                    "An eccentric, supremely self-assured Class D student who "
                    "answers to no one and involves himself in class affairs "
                    "strictly on his own terms."
                ),
            },
            {
                "name": "Ryuuji Kanzaki",
                "faction": "Class C",
                "role": "Class C Student",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b207022-dfXyWDXyBVKC.png",
                "first_revealed_at": "S1E4",
                "backstory": (
                    "A composed, well-liked Class C student who acts as a "
                    "steady counterbalance to his class's more aggressive "
                    "leader, respected by classmates across multiple classes."
                ),
            },
        ],
        "franchise_entries": [
            {
                "title": "Classroom of the Elite",
                "entry_type": "tv",
                "release_order": 1,
                "chronological_order": 1,
                "note": (
                    "No movies or OVAs exist for this series. Season 5 has since "
                    "been announced (June 2026) but has no episode count or air "
                    "date yet, so it isn't reflected in the watch progress range "
                    "above — check back once it airs."
                ),
            },
        ],
        "facts": [
            {
                "subject": "Class D",
                "predicate": "point_system",
                "object": "Students accumulate class points that convert into personal spending points, and a class's points can drop to zero.",
                "source_citation": "Season 1, Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": None,
                "confidence": 0.99,
            },
            {
                "subject": "Kikyo Kushida",
                "predicate": "true_personality",
                "object": "Conceals a manipulative, ruthless personality behind a friendly public facade.",
                "source_citation": "Season 1, Episode 11",
                "first_revealed_at": "S1E11",
                "first_hinted_at": "S1E4",
                "confidence": 0.92,
            },
            {
                "subject": "Kiyotaka Ayanokoji",
                "predicate": "hidden_ability",
                "object": "Trained under an elite program with exceptional analytical and combat skills, deliberately suppressed to appear average.",
                "source_citation": "Season 1, Episode 12",
                "first_revealed_at": "S1E12",
                "first_hinted_at": "S1E2",
                "confidence": 0.9,
            },
        ],
    },
    {
        "slug": "code-geass",
        "title": "Code Geass",
        "total_episodes": 50,
        "season_episode_counts": [25, 25],
        "mal_id": 1575,
        "anilist_id": 1575,
        "cover_image_url": "https://cdn.myanimelist.net/images/anime/1032/135088l.jpg",
        "genres": ["Award Winning", "Drama", "Sci-Fi"],
        "score": 8.71,
        "synopsis": (
            "After Britannia conquers Japan and renames it Area 11, an exiled prince "
            "gains a mysterious power of absolute command and turns it against the "
            "empire that took everything from him."
        ),
        "factions": [
            {
                "name": "Holy Britannian Empire",
                "description": "The ruling imperial power occupying Area 11.",
            },
            {
                "name": "Black Knights",
                "description": "A resistance organization opposing Britannian rule.",
            },
        ],
        "characters": [
            {
                "name": "Lelouch Lamperouge",
                "faction": "Holy Britannian Empire",
                "role": "Ashford Academy Student Council",
                "height": "178-183 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b417-gVLmIJu9phcK.png",
                "power": "Geass: the Power of Absolute Obedience",
                "backstory": (
                    "A brilliant, calculating Ashford Academy student and the exiled "
                    "eleventh prince of Britannia, who gains the Geass power of "
                    "absolute obedience from a mysterious girl named C.C."
                ),
            },
            {
                "name": "Suzaku Kururugi",
                "faction": "Holy Britannian Empire",
                "role": "Honorary Britannian Soldier",
                "height": "176 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b559-KRvTdc6zdCuU.jpg",
                "backstory": (
                    "Lelouch's childhood friend and the son of Japan's last prime "
                    "minister, who joins the Britannian military as an Honorary "
                    "Britannian and pilots the elite Knightmare Frame Lancelot."
                ),
            },
            {
                "name": "Kallen Kouzuki",
                "faction": "Black Knights",
                "role": "Ace Pilot",
                "height": "173 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b558-8tSMZ4a0LWrn.jpg",
                "backstory": (
                    "A Britannian-Eleven girl who poses as a frail, ordinary Ashford "
                    "Academy student by day while secretly fighting Britannia as a "
                    "skilled resistance pilot."
                ),
            },
            {
                "name": "C.C.",
                "faction": None,
                "height": "167 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b1111-UhmlFtRFrnWa.png",
                "power": "Geass: Grants the Power of the King",
                "backstory": (
                    "An enigmatic, seemingly immortal girl who grants Lelouch the "
                    "power of Geass and is sought after by the Britannian military "
                    "for reasons of her own."
                ),
            },
            {
                "name": "Nunnally Lamperouge",
                "faction": "Holy Britannian Empire",
                "role": "Ashford Academy Student",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b1110-TSlN2WkhDJ1T.png",
                "backstory": (
                    "Lelouch's gentle, unfailingly kind younger sister, blind and "
                    "unable to walk since childhood, whose safety and happiness "
                    "are the one thing Lelouch will do anything to protect."
                ),
            },
            {
                "name": "Milly Ashford",
                "faction": "Holy Britannian Empire",
                "role": "Student Council President, Ashford Academy",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b1121-Y3ye9sw1u3Eh.jpg",
                "backstory": (
                    "The energetic, mischievous granddaughter of Ashford "
                    "Academy's chairman, who runs the student council with a "
                    "flair for theatrics and an eye for gossip."
                ),
            },
            {
                "name": "Rivalz Cardemonde",
                "faction": "Holy Britannian Empire",
                "role": "Student Council Member, Ashford Academy",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b1122-tzCSm261b2RP.png",
                "backstory": (
                    "Lelouch's easygoing best friend and fellow Ashford Academy "
                    "student council member, always first to suggest a bet or a "
                    "scheme to liven things up."
                ),
            },
            {
                "name": "Cécile Croomy",
                "faction": "Holy Britannian Empire",
                "role": "Britannian Military Engineer, Lancelot Development Team",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b1131-8B8jxeFXEzld.jpg",
                "backstory": (
                    "A skilled Britannian military engineer on the Lancelot "
                    "development team, whose calm professionalism balances out "
                    "her eccentric research partner, Lloyd Asplund."
                ),
            },
        ],
        "franchise_entries": [
            {
                "title": "Code Geass: Lelouch of the Rebellion",
                "entry_type": "tv",
                "release_order": 1,
                "chronological_order": 1,
            },
            {
                "title": (
                    "Code Geass: Lelouch of the Rebellion — Initiation / "
                    "Transgression / Glorification"
                ),
                "entry_type": "movie",
                "release_order": 2,
                "chronological_order": 2,
                "note": (
                    "A compressed theatrical retelling of the TV series with a "
                    "changed, alternate ending — required viewing before "
                    "Re;surrection, not just a recap."
                ),
            },
            {
                "title": "Code Geass: Lelouch of the Re;surrection",
                "entry_type": "movie",
                "release_order": 3,
                "chronological_order": 3,
                "note": (
                    "Continues from the compilation movie trilogy's alternate "
                    "ending, not the original TV series finale."
                ),
            },
            {
                "title": "Code Geass: Rozé of the Recapture",
                "entry_type": "movie",
                "release_order": 4,
                "chronological_order": 4,
                "note": "Direct sequel to Re;surrection.",
            },
        ],
        "facts": [
            {
                "subject": "Lelouch Lamperouge",
                "predicate": "royal_lineage",
                "object": "11th prince of the Holy Britannian Empire, living in exile.",
                "source_citation": "Season 1, Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": None,
                "confidence": 0.99,
            },
            {
                "subject": "C.C.",
                "predicate": "power_source",
                "object": "Grants Lelouch the power of Geass: absolute obedience over anyone he commands.",
                "source_citation": "Season 1, Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": None,
                "confidence": 0.95,
            },
            {
                "subject": "Lelouch Lamperouge",
                "predicate": "true_identity",
                "object": "Zero, masked leader of the Black Knights.",
                "source_citation": "Season 1, Episode 12",
                "first_revealed_at": "S1E12",
                "first_hinted_at": "S1E3",
                "confidence": 0.97,
            },
        ],
    },
    {
        "slug": "attack-on-titan",
        "title": "Attack on Titan",
        # Seasons 1-4 (25 + 12 + 22 + 28), verified against MAL/Wikipedia's episode
        # counts per season. The two 2023 "Final Chapters" TV specials are tracked as
        # a separate franchise_entries row below rather than folded in here, matching
        # how the Season 1 recap compilation movies are kept out of the season count.
        "total_episodes": 87,
        "season_episode_counts": [25, 12, 22, 28],
        "mal_id": 16498,
        "anilist_id": 16498,
        "cover_image_url": "https://cdn.myanimelist.net/images/anime/10/47347l.jpg",
        "genres": ["Action", "Award Winning", "Drama", "Suspense"],
        "score": 8.58,
        "synopsis": (
            "Humanity lives caged behind massive walls to keep out the man-eating "
            "Titans — until one boy watches his home fall and vows to wipe them "
            "from the earth."
        ),
        "factions": [
            {
                "name": "Survey Corps",
                "description": "Ventures beyond the walls to battle Titans and reclaim lost territory.",
            },
            {
                "name": "Garrison",
                "description": "Maintains and defends the walls that protect humanity's remaining territory.",
            },
            {
                "name": "Military Police Brigade",
                "description": "Maintains order within the innermost wall and serves the royal government.",
            },
            {
                "name": "104th Cadet Corps",
                "description": "The training regiment cadets join before choosing a military branch.",
            },
        ],
        "characters": [
            {
                "name": "Eren Yeager",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "height": "170 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b40882-dsj7IP943WFF.jpg",
                "backstory": (
                    "A hot-blooded young man from Shiganshina District who dreams "
                    "of exploring the world beyond the Walls, and vows to wipe out "
                    "every Titan after watching one devour his mother."
                ),
            },
            {
                "name": "Mikasa Ackerman",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "height": "170 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b40881-F3gr1PkreDvj.png",
                "power": "Top graduate of the 104th Training Corps; exceptional hand-to-hand and blade combat skill",
                "backstory": (
                    "Eren's fiercely protective foster sister, adopted into the "
                    "Yeager family as a child, and widely regarded as the most "
                    "naturally gifted fighter in her cadet class."
                ),
            },
            {
                "name": "Armin Arlert",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "height": "163 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b46494-g7xYYuBtYPnO.png",
                "power": "Sharp tactical mind; the squad's strategist",
                "backstory": (
                    "Eren and Mikasa's timid but brilliant childhood friend, whose "
                    "sharp strategic mind more than makes up for his lack of "
                    "physical strength."
                ),
            },
            {
                "name": "Annie Leonhart",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "height": "153 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b46490-tan274Ifc1Jf.jpg",
                "backstory": (
                    "A member of the 104th Cadet Corps' Southern Division, Annie "
                    "graduated 4th in her class before joining the Military Police. "
                    "A stoic, solitary girl, she's rarely seen smiling or "
                    "socializing, with little interest in group activities or "
                    "discipline. More than anything, what drives her is a simple "
                    "desire: to live a normal life."
                ),
            },
            {
                "name": "Levi Ackerman",
                "faction": "Survey Corps",
                "role": "Captain, Special Operations Squad",
                "height": "160 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b45627-CR68RyZmddGG.png",
                "power": "Renowned as humanity's strongest soldier",
                "backstory": (
                    "Captain of the Survey Corps' elite Special Operations Squad, "
                    "hand-picked for their strength and skill. Famed even among his "
                    "fellow soldiers as humanity's strongest, Levi is a man of few "
                    "words with an exacting, no-nonsense demeanor."
                ),
                # Doesn't appear on screen until well into the Trost arc — unlike
                # the rest of this cast (visible from Ep.1), showing him in the
                # roster any earlier would spoil his existence ahead of his real
                # debut. Matches the existing "military_rank" fact's own citation
                # below, so the character and its fact unlock together.
                "first_revealed_at": "S1E14",
            },
            {
                "name": "Erwin Smith",
                "faction": "Survey Corps",
                "role": "Commander, Survey Corps",
                "backstory": (
                    "Commander of the Survey Corps, humanity's most audacious "
                    "military branch, dedicated to venturing beyond the Walls to "
                    "reclaim lost territory from the Titans. Erwin is a calculating "
                    "strategist willing to make difficult sacrifices in pursuit of "
                    "humanity's freedom."
                ),
            },
            # The following 104th trainees are the show's own top-10 graduating
            # ranking, all named together at the graduation ceremony shown in
            # Episode 1 (verified) — same debut checkpoint as Eren/Mikasa/Armin/
            # Annie above. Backstories deliberately stop at each trainee's public
            # role/personality, never their later story arcs.
            {
                "name": "Jean Kirstein",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b46498-ritqAj9FW6jX.png",
                "backstory": (
                    "A pragmatic, sharp-tongued trainee who enlisted hoping for a "
                    "safe post in the interior Military Police Brigade, frequently "
                    "butting heads with Eren over their very different reasons for "
                    "fighting."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Connie Springer",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/n46486-izhPjzut6WCZ.png",
                "backstory": (
                    "An easygoing, high-energy trainee from the mountain village "
                    "of Ragako, better known among his classmates for his comic "
                    "timing than for taking training too seriously."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Sasha Blouse",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b45887-QPtJH0KwqthW.jpg",
                "backstory": (
                    "A skilled hunter from a remote mountain village, instantly "
                    "recognizable among her fellow trainees for her sharp "
                    "instincts, easy laugh, and famously insatiable appetite."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Krista Lenz",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b62481-ZZDa7vn17lMU.png",
                "backstory": (
                    "A gentle, selfless trainee adored by her classmates for "
                    "always putting others first, though she rarely talks about "
                    "her life before joining the 104th."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Reiner Braun",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b46484-P6A2GjNQn49F.png",
                "backstory": (
                    "A steady, level-headed trainee from Wall Rose, seen by most "
                    "of the 104th as a reliable, big-brother figure who looks out "
                    "for the group."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Bertolt Hoover",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b46488-wm6HvkdkHoZu.jpg",
                "backstory": (
                    "A tall, quiet trainee who prefers to stay out of the "
                    "spotlight, inseparable from his closest friend and fellow "
                    "trainee Reiner Braun."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Marco Bott",
                "faction": "104th Cadet Corps",
                "role": "104th Cadet Corps Trainee",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b62479-mYcTkU1RXymL.jpg",
                "backstory": (
                    "An earnest, dependable trainee who genuinely admires the "
                    "Military Police's ideals of order and service, well liked "
                    "across the 104th for his honesty."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Hannes",
                "faction": "Garrison",
                "role": "Garrison Regiment Soldier",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b46492-5kRaMLDCVD0B.jpg",
                "backstory": (
                    "A good-natured, hard-drinking Garrison soldier stationed in "
                    "Shiganshina, and a long-time family friend of the Yeager and "
                    "Ackerman households."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Hange Zoe",
                "faction": "Survey Corps",
                "role": "Survey Corps, Titan Research Squad",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b71121-7R7CnQd3lHgt.png",
                "backstory": (
                    "An endlessly curious, unconventional Survey Corps member "
                    "whose fascination with Titans as subjects of study — not "
                    "just enemies to kill — sets her apart from most of her "
                    "peers."
                ),
                # Named/substantive debut confirmed to Episode 15 ("Special
                # Operations Squad"), the same arc as Levi above — earlier crowd
                # appearances aren't a real introduction.
                "first_revealed_at": "S1E15",
            },
        ],
        "franchise_entries": [
            {
                "title": "Attack on Titan",
                "entry_type": "tv",
                "release_order": 1,
                "chronological_order": 2,
                "note": (
                    "Watch progress tracks all 4 seasons (87 episodes). Character "
                    "and fact dossier content currently covers Season 1 only — "
                    "Seasons 2-4 checkpoints are unlocked but reveal no new facts "
                    "yet."
                ),
            },
            {
                "title": "Attack on Titan: The Final Chapters (TV specials)",
                "entry_type": "special",
                "release_order": 4,
                "chronological_order": 4,
                "note": (
                    "Two feature-length specials (2023) concluding the story. Not "
                    "counted in the season_episode_counts checkpoint range above."
                ),
            },
            {
                "title": "Attack on Titan: No Regrets (OVA)",
                "entry_type": "ova",
                "release_order": 2,
                "chronological_order": 1,
                "note": (
                    "Levi's backstory — set chronologically before the main story, "
                    "but watch it after Season 1 to avoid spoilers about characters "
                    "and world details it assumes you already know."
                ),
            },
            {
                "title": (
                    "Attack on Titan: Crimson Bow and Arrow / Wings of Freedom "
                    "(compilation movies)"
                ),
                "entry_type": "movie",
                "release_order": 3,
                "chronological_order": 3,
                "note": "Recap compilations of Season 1 with no new content — safe to skip.",
            },
        ],
        "facts": [
            {
                "subject": "104th Cadet Corps",
                "predicate": "training_purpose",
                "object": "Cadets train together for years before choosing a branch: Survey Corps, Garrison, or Military Police Brigade.",
                "source_citation": "Season 1, Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": None,
                "confidence": 0.99,
            },
            {
                "subject": "Levi Ackerman",
                "predicate": "military_rank",
                "object": "Captain of the Survey Corps, renowned as humanity's strongest soldier.",
                "source_citation": "Season 1, Episode 14",
                "first_revealed_at": "S1E14",
                "first_hinted_at": None,
                "confidence": 0.95,
            },
            {
                "subject": "Eren Yeager",
                "predicate": "titan_shifter_identity",
                "object": "Can transform into a Titan himself, discovered after emerging from within a Titan's body.",
                "source_citation": "Season 1, Episode 8",
                "first_revealed_at": "S1E8",
                "first_hinted_at": "S1E5",
                "confidence": 0.96,
            },
            {
                "subject": "Eren Yeager",
                "predicate": "basement_lore",
                "object": "His father Grisha left behind a hidden basement holding the truth about the Titans and the world beyond the walls.",
                "source_citation": "Season 1, Episode 25",
                "first_revealed_at": "S1E25",
                "first_hinted_at": "S1E13",
                "confidence": 0.93,
            },
            {
                "subject": "Annie Leonhart",
                "predicate": "titan_shifter_identity",
                "object": "Secretly the Female Titan that attacked the Survey Corps during the 57th expedition beyond the walls.",
                "source_citation": "Season 1, Episode 25",
                "first_revealed_at": "S1E25",
                "first_hinted_at": "S1E17",
                "confidence": 0.9,
            },
        ],
    },
    {
        "slug": "one-piece",
        "title": "One Piece",
        # One Piece airs weekly and has no fixed finale, so this number goes stale
        # again over time — 1176 was the latest confirmed aired episode as of
        # 2026-09-01 (verified against Wikipedia's episode list). There's no
        # auto-refresh: `total_episodes`/`season_episode_counts` are only set here
        # at seed time, so this needs a manual bump periodically (the /sources
        # endpoint surfaces a conflict against live Jikan/AniList data but doesn't
        # write it back).
        "total_episodes": 1176,
        # A single continuous season: the Watch Progress slider represents plain
        # sequential episode numbers (Ep. 1 -> Ep. 1176) rather than per-arc season
        # boundaries. Checkpoints below ("S1E<n>") use n as that raw global episode
        # number directly.
        "season_episode_counts": [1176],
        "mal_id": 21,
        "anilist_id": 21,
        "cover_image_url": "https://cdn.myanimelist.net/images/anime/1244/138851l.jpg",
        "genres": ["Action", "Adventure", "Fantasy"],
        "score": 8.73,
        "synopsis": (
            "Inspired by his childhood hero, a rubber-bodied boy sets out to "
            "assemble a crew and find the greatest treasure in the world, the "
            "One Piece, to become the next Pirate King."
        ),
        # Curated, not dynamically ingested: an earlier dynamic-roster approach (live
        # AniList fetch + Gemini debut extraction at every reseed) proved unreliable in
        # two concrete ways, found via live testing rather than assumed — (1) Gemini's
        # free-tier quota (20 req/day) is easily exhausted mid-reseed, at which point
        # every character (including Luffy) silently gets excluded as "unknown debut",
        # making the demo roster non-deterministic; (2) AniList's raw character bios
        # narrate a character's full story as plain prose, not wrapped in the ~!spoiler!~
        # convention the pipeline expects — e.g. Nico Robin's bio states outright that
        # she "joined the Straw Hat Pirates" and lists her as its "seventh member,"
        # which is exactly the secret her own `crew_membership` fact below is gated to
        # reveal at Episode 296, 205 episodes after her Episode 91 debut. Hand-curating
        # this core cast (own backstories, no raw bio text) closes both gaps for good.
        "factions": [
            {"name": "Pirate Crews", "description": "Independent pirate crews sailing the Grand Line."},
            {
                "name": "Straw Hat Pirates",
                "parent": "Pirate Crews",
                "description": "Monkey D. Luffy's crew, sailing in pursuit of the One Piece.",
            },
            {
                "name": "Four Emperors (Yonko)",
                "description": "The four most powerful pirate crews ruling the New World.",
            },
            {
                "name": "Whitebeard Pirates",
                "parent": "Four Emperors (Yonko)",
                "description": "One of the most powerful pirate crews on the seas, led by Whitebeard.",
            },
            {
                "name": "Red-Hair Pirates",
                "parent": "Four Emperors (Yonko)",
                "description": "A powerful, close-knit crew led by Red-Haired Shanks.",
            },
            {
                "name": "Buggy Pirates",
                "parent": "Pirate Crews",
                "description": "A flashy, chaotic crew led by Buggy the Clown.",
            },
            {
                "name": "Alvida Pirates",
                "parent": "Pirate Crews",
                "description": "A small-time pirate crew led by Alvida, active near the East Blue.",
            },
            {
                "name": "Krieg Pirates",
                "parent": "Pirate Crews",
                "description": "A fifty-ship armada led by Don Krieg, self-proclaimed strongest crew in the East Blue.",
            },
            {
                "name": "Arlong Pirates",
                "parent": "Pirate Crews",
                "description": "A Fish-Man pirate crew led by Arlong, ruling over the village of Cocoyasi.",
            },
            {
                "name": "Bliking Pirates",
                "parent": "Pirate Crews",
                "description": "A pirate crew led by Wapol, the deposed king of Drum Kingdom.",
            },
            {
                "name": "Giants of Elbaf",
                "description": "Warriors from the giants' homeland of Elbaf, bound by a fierce code of honor.",
            },
            {
                "name": "World Government",
                "description": "The global political body whose authority the Marines enforce across the seas.",
            },
            {
                "name": "Marines",
                "parent": "World Government",
                "description": "The naval military force enforcing World Government law across the seas.",
            },
        ],
        "characters": [
            {
                "name": "Monkey D. Luffy",
                "faction": "Straw Hat Pirates",
                "role": "Captain, Straw Hat Pirates",
                "height": "172 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b40-MNypXsxSRb1R.png",
                "power": "Gomu Gomu no Mi",
                "backstory": (
                    "A cheerful, endlessly optimistic young man who ate the Gomu Gomu "
                    "no Mi, giving him a rubber body. Inspired by the pirate Red-Haired "
                    "Shanks, he sets sail to assemble a crew and find the legendary "
                    "treasure known as the One Piece."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Roronoa Zoro",
                "faction": "Straw Hat Pirates",
                "role": "Swordsman, Straw Hat Pirates",
                "height": "178 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b62-S7oAeA9WInjV.png",
                "backstory": (
                    "A fearsome swordsman known as \"Pirate Hunter Zoro,\" skilled in "
                    "the three-sword Santoryu style. He dreams of becoming the world's "
                    "greatest swordsman."
                ),
                "first_revealed_at": "S1E3",
            },
            {
                "name": "Nami",
                "faction": "Straw Hat Pirates",
                "role": "Navigator, Straw Hat Pirates",
                "height": "169 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b723-vp5hPptgnNEC.png",
                "backstory": (
                    "A sharp, resourceful navigator with a talent for thievery, drawn "
                    "into Luffy's crew by ambitions of her own. Her dream is to draw a "
                    "complete map of the entire world."
                ),
                "first_revealed_at": "S1E8",
            },
            {
                "name": "Usopp",
                "faction": "Straw Hat Pirates",
                "role": "Sniper, Straw Hat Pirates",
                "height": "174 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b724-GFGgI9AJQkfy.jpg",
                "backstory": (
                    "A boastful storyteller and skilled marksman from Syrup Village, "
                    "who dreams of becoming as brave a warrior of the sea as his father."
                ),
                "first_revealed_at": "S1E9",
            },
            {
                "name": "Sanji",
                "faction": "Straw Hat Pirates",
                "role": "Cook, Straw Hat Pirates",
                "height": "177 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b305-6lisPmHtCnLT.png",
                "backstory": (
                    "A stylish, chivalrous cook who fights exclusively with his legs to "
                    "protect his hands for cooking. He dreams of finding the legendary "
                    "sea known as the All Blue."
                ),
                "first_revealed_at": "S1E20",
            },
            {
                "name": "Tony Tony Chopper",
                "faction": "Straw Hat Pirates",
                "role": "Doctor, Straw Hat Pirates",
                "height": "90 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b309-H64NhbJ2ywIQ.jpg",
                "power": "Hito Hito no Mi",
                "backstory": (
                    "A small reindeer who ate the Hito Hito no Mi, gaining human "
                    "intelligence, speech, and the ability to transform. He aspires to "
                    "become a doctor who can cure any illness."
                ),
                "first_revealed_at": "S1E83",
            },
            {
                "name": "Nico Robin",
                # Deliberately unaffiliated: her real crew membership doesn't unlock
                # until the `crew_membership` fact at S1E296 — 205 episodes after her
                # own debut here — so grouping her under "Straw Hat Pirates" from her
                # first appearance would visually leak that reveal early. Same reasoning
                # keeps her out of "Baroque Works" until `secret_identity` unlocks.
                "role": "Archaeologist",
                "height": "188 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b61-ywXUyyocEEqt.png",
                "power": "Hana Hana no Mi",
                "backstory": (
                    "A quiet, studious archaeologist with a deep love of history, "
                    "having eaten the Hana Hana no Mi, which lets her sprout copies of "
                    "her own limbs on any surface she can see."
                ),
                "first_revealed_at": "S1E91",
            },
            {
                "name": "Franky",
                "faction": "Straw Hat Pirates",
                "role": "Shipwright, Straw Hat Pirates",
                "height": "225 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/n64-ChX6ZzHHjXqA.png",
                "backstory": (
                    "An eccentric, flamboyant shipwright from Water 7, famous for his "
                    "cola-powered gadgets and love of striking dramatic poses."
                ),
                "first_revealed_at": "S1E205",
            },
            {
                "name": "Brook",
                "faction": "Straw Hat Pirates",
                "role": "Musician, Straw Hat Pirates",
                "height": "266 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b5627-av8oD3zhKvDl.png",
                "power": "Yomi Yomi no Mi",
                "backstory": (
                    "A skeleton musician who ate the Yomi Yomi no Mi, which returned "
                    "his soul to his body long after his death. He now sails the seas "
                    "with his violin."
                ),
                "first_revealed_at": "S1E337",
            },
            {
                "name": "Jinbe",
                # Unaffiliated for the same reason as Robin: his real Straw Hat
                # membership is real-world canon common knowledge but doesn't unlock via
                # any fact in this dataset, and is hundreds of episodes past his debut —
                # stating it here would be an undated, ungated spoiler with no checkpoint
                # protecting it.
                "role": "Fish-Man Karate Master",
                "height": "301 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b18938-yZANEfjsVhW4.png",
                "backstory": (
                    "A powerful fish-man and master of Fish-Man Karate, known "
                    "throughout the Grand Line for his immense strength and "
                    "unshakable sense of honor."
                ),
                "first_revealed_at": "S1E432",
            },
            {
                "name": "Crocodile",
                # Unaffiliated deliberately: his Warlord status and Baroque Works
                # leadership *are* the `true_identity` fact below, gated to S1E272 —
                # placing him under "Seven Warlords of the Sea" from his own S1E76
                # debut would visually reveal that secret 196 episodes early. His role
                # instead reflects only his public cover identity.
                "role": "Rain Dinners Casino Owner",
                "height": "253 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b2749-e8ebEBN1SlS2.png",
                "backstory": (
                    "A composed, calculating man who owns and operates the Rain "
                    "Dinners casino in Alabasta's capital. Little is publicly known "
                    "about his past."
                ),
                "first_revealed_at": "S1E76",
            },
            {
                "name": "Edward Newgate",
                "faction": "Whitebeard Pirates",
                # "Yonko" (Emperor) is a title held by a crew's captain alone, not
                # the crew as a whole — without him seeded, the "Four Emperors
                # (Yonko)" faction card only ever showed his subordinate Ace,
                # which reads as if Ace himself held Emperor status. Role text
                # spells that distinction out explicitly for the same reason.
                "role": "Captain, Whitebeard Pirates — one of the Four Emperors (Yonko)",
                "height": "666 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b2751-NnzW0N2vCTjX.jpg",
                "backstory": (
                    "Widely known as \"Whitebeard,\" captain of the Whitebeard "
                    "Pirates and one of the four Emperors who rule the New World. "
                    "Feared across the seas as the man closest to claiming the "
                    "One Piece himself."
                ),
                "first_revealed_at": "S1E151",
            },
            {
                "name": "Portgas D. Ace",
                "faction": "Whitebeard Pirates",
                "role": "2nd Division Commander, Whitebeard Pirates",
                "height": "185 cm",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b2072-Lc6jEdsueJUK.jpg",
                "backstory": (
                    "Luffy's sworn older brother, a laid-back but formidable fighter "
                    "who serves as Second Division Commander of the Whitebeard "
                    "Pirates, one of the most powerful crews on the Grand Line."
                ),
                "first_revealed_at": "S1E91",
            },
            {
                "name": "Shanks",
                "faction": "Red-Hair Pirates",
                "role": "Captain, Red-Hair Pirates — one of the Four Emperors (Yonko)",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b727-wUJx7M1z5xON.png",
                "backstory": (
                    "A legendary pirate captain whose visit to Luffy's hometown "
                    "left a lasting mark on the boy who now wears his old straw "
                    "hat — and dreams of returning it to him one day, as the "
                    "world's greatest pirate."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Buggy",
                "faction": "Buggy Pirates",
                "role": "Captain, Buggy Pirates",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/n725-g04AaiaK5f9B.png",
                "power": "Bara Bara no Mi",
                "backstory": (
                    "A flamboyant, short-tempered pirate captain who ate the "
                    "Bara Bara no Mi, letting him split his own body apart at "
                    "will — and fiercely resents any reminder of his old "
                    "crewmate, Red-Haired Shanks."
                ),
                "first_revealed_at": "S1E4",
            },
            {
                "name": "Smoker",
                "faction": "Marines",
                "role": "Marine Captain, Loguetown",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b2753-Y2ja8Pl6PRs0.jpg",
                "power": "Moku Moku no Mi",
                "backstory": (
                    "An unusually principled Marine captain stationed in "
                    "Loguetown, whose relentless pursuit of Luffy stems less "
                    "from ambition than a rigid, uncompromising sense of "
                    "justice."
                ),
                "first_revealed_at": "S1E48",
            },
            {
                "name": "Alvida",
                "faction": "Alvida Pirates",
                "role": "Captain, Alvida Pirates",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b4899-bFPCVRWyqMtO.jpg",
                "backstory": (
                    "A pirate captain whose crew terrorized the seas near "
                    "Luffy's home village until her very first clash with him "
                    "— the encounter that set his journey in motion."
                ),
                "first_revealed_at": "S1E1",
            },
            {
                "name": "Don Krieg",
                "faction": "Krieg Pirates",
                "role": "Captain, Krieg Pirates",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b9320-lHsw9jNk5889.png",
                "backstory": (
                    "The self-proclaimed strongest man in the East Blue, "
                    "commanding a fleet of fifty ships in his ambition to "
                    "conquer the Grand Line."
                ),
                # Baratie arc confirmed to start Episode 19; Krieg's own arrival
                # is a few episodes into it. Best-effort estimate, kept
                # deliberately later rather than earlier to avoid any risk of
                # an early reveal.
                "first_revealed_at": "S1E21",
            },
            {
                "name": "Arlong",
                "faction": "Arlong Pirates",
                "role": "Captain, Arlong Pirates",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b4887-hMOqSSpR5jFc.jpg",
                "backstory": (
                    "A powerful Fish-Man pirate captain who rules the East "
                    "Blue village of Cocoyasi with an iron fist, backed by a "
                    "crew as fearsome as he is."
                ),
                # Arlong Park arc start, verified against Wikipedia's episode list.
                "first_revealed_at": "S1E31",
            },
            {
                "name": "Dorry",
                "faction": "Giants of Elbaf",
                "role": "Elbaf Giant Warrior",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/5420.jpg",
                "backstory": (
                    "One of two legendary giant warriors from the distant "
                    "land of Elbaf, locked in a duel of honor with his old "
                    "friend and rival Brogy that has lasted a hundred years."
                ),
                # Little Garden arc start, verified against Wikipedia's episode list.
                "first_revealed_at": "S1E70",
            },
            {
                "name": "Brogy",
                "faction": "Giants of Elbaf",
                "role": "Elbaf Giant Warrior",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/5421.jpg",
                "backstory": (
                    "One of two legendary giant warriors from the distant "
                    "land of Elbaf, locked in a duel of honor with his old "
                    "friend and rival Dorry that has lasted a hundred years."
                ),
                "first_revealed_at": "S1E70",
            },
            {
                "name": "Wapol",
                "faction": "Bliking Pirates",
                "role": "Captain, Bliking Pirates",
                "avatar_url": "https://s4.anilist.co/file/anilistcdn/character/large/b5422-QfzPleyyng7n.jpg",
                "backstory": (
                    "The deposed king of Drum Kingdom turned pirate captain, "
                    "ruling his Bliking Pirates crew with the same petty "
                    "tyranny he once ruled his kingdom."
                ),
                # Drum Island arc start, verified against Wikipedia's episode list.
                "first_revealed_at": "S1E78",
            },
        ],
        "franchise_entries": [
            {
                "title": "One Piece",
                "entry_type": "tv",
                "release_order": 1,
                "chronological_order": 1,
                "note": (
                    "All 15 theatrical One Piece movies below are explicitly "
                    "non-canon side stories, confirmed by Oda himself — safe to "
                    "skip entirely. None of them affect the main story."
                ),
            },
            {
                "title": "One Piece: The Movie (2000)",
                "entry_type": "movie",
                "release_order": 2,
                "chronological_order": 2,
            },
            {
                "title": "One Piece: Clockwork Island Adventure (2001)",
                "entry_type": "movie",
                "release_order": 3,
                "chronological_order": 3,
            },
            {
                "title": (
                    "One Piece: Chopper's Kingdom on the Island of Strange "
                    "Animals (2002)"
                ),
                "entry_type": "movie",
                "release_order": 4,
                "chronological_order": 4,
            },
            {
                "title": "One Piece: Dead End Adventure (2003)",
                "entry_type": "movie",
                "release_order": 5,
                "chronological_order": 5,
            },
            {
                "title": "One Piece: The Cursed Holy Sword (2004)",
                "entry_type": "movie",
                "release_order": 6,
                "chronological_order": 6,
            },
            {
                "title": "One Piece: Baron Omatsuri and the Secret Island (2005)",
                "entry_type": "movie",
                "release_order": 7,
                "chronological_order": 7,
            },
            {
                "title": (
                    "One Piece: The Giant Mechanical Soldier of Karakuri Castle (2006)"
                ),
                "entry_type": "movie",
                "release_order": 8,
                "chronological_order": 8,
            },
            {
                "title": (
                    "One Piece — Episode of Arabasta: The Desert Princess and "
                    "the Pirates (2007)"
                ),
                "entry_type": "movie",
                "release_order": 9,
                "chronological_order": 9,
            },
            {
                "title": (
                    "One Piece — Episode of Chopper Plus: Bloom in Winter, "
                    "Miracle Sakura (2008)"
                ),
                "entry_type": "movie",
                "release_order": 10,
                "chronological_order": 10,
            },
            {
                "title": "One Piece Film: Strong World (2009)",
                "entry_type": "movie",
                "release_order": 11,
                "chronological_order": 11,
            },
            {
                "title": "One Piece 3D: Straw Hat Chase (2011)",
                "entry_type": "movie",
                "release_order": 12,
                "chronological_order": 12,
            },
            {
                "title": "One Piece Film: Z (2012)",
                "entry_type": "movie",
                "release_order": 13,
                "chronological_order": 13,
            },
            {
                "title": "One Piece Film: Gold (2016)",
                "entry_type": "movie",
                "release_order": 14,
                "chronological_order": 14,
            },
            {
                "title": "One Piece: Stampede (2019)",
                "entry_type": "movie",
                "release_order": 15,
                "chronological_order": 15,
            },
            {
                "title": "One Piece Film: Red (2022)",
                "entry_type": "movie",
                "release_order": 16,
                "chronological_order": 16,
            },
        ],
        "facts": [
            {
                "subject": "Monkey D. Luffy",
                "predicate": "devil_fruit_power",
                "object": "Ate the Gomu Gomu no Mi, granting him a rubber body.",
                "source_citation": "Episode 1",
                "first_revealed_at": "S1E1",
                "first_hinted_at": "S1E1",
                "confidence": 0.99,
            },
            {
                "subject": "Monkey D. Luffy",
                "predicate": "combat_technique",
                "object": "Developed Gear Second, pumping blood at high speed for a burst of speed and striking power.",
                "source_citation": "Episode 581",
                "first_revealed_at": "S1E581",
                "first_hinted_at": "S1E580",
                "confidence": 0.95,
            },
            # Bounty is a progressively-revealed stat, not a fixed one — each milestone
            # is its own dated fact (see dossier_service._current_bounty) so a viewer at
            # Ep.1 sees no bounty at all rather than his final/current real-world amount.
            {
                "subject": "Monkey D. Luffy",
                "predicate": "bounty",
                "object": "30,000,000",
                "source_citation": "Episode 16",
                "first_revealed_at": "S1E16",
                "first_hinted_at": None,
                "confidence": 0.97,
            },
            {
                "subject": "Monkey D. Luffy",
                "predicate": "bounty",
                "object": "100,000,000",
                "source_citation": "Episode 45",
                "first_revealed_at": "S1E45",
                "first_hinted_at": None,
                "confidence": 0.97,
            },
            {
                "subject": "Monkey D. Luffy",
                "predicate": "bounty",
                "object": "300,000,000",
                "source_citation": "Episode 130",
                "first_revealed_at": "S1E130",
                "first_hinted_at": None,
                "confidence": 0.97,
            },
            {
                "subject": "Monkey D. Luffy",
                "predicate": "bounty",
                "object": "400,000,000",
                "source_citation": "Episode 230",
                "first_revealed_at": "S1E230",
                "first_hinted_at": None,
                "confidence": 0.97,
            },
            {
                "subject": "Monkey D. Luffy",
                "predicate": "bounty",
                "object": "500,000,000",
                "source_citation": "Episode 746",
                "first_revealed_at": "S1E746",
                "first_hinted_at": None,
                "confidence": 0.97,
            },
            {
                "subject": "Monkey D. Luffy",
                "predicate": "bounty",
                "object": "1,500,000,000",
                "source_citation": "Episode 879",
                "first_revealed_at": "S1E879",
                "first_hinted_at": None,
                "confidence": 0.95,
            },
            {
                "subject": "Monkey D. Luffy",
                "predicate": "bounty",
                "object": "3,000,000,000",
                "source_citation": "Episode 1081",
                "first_revealed_at": "S1E1081",
                "first_hinted_at": None,
                "confidence": 0.9,
            },
            {
                "subject": "Roronoa Zoro",
                "predicate": "combat_style",
                "object": "Master of Santoryu, the Three-Sword Style.",
                "source_citation": "Episode 2",
                "first_revealed_at": "S1E2",
                "first_hinted_at": "S1E2",
                "confidence": 0.98,
            },
            {
                "subject": "Nami",
                "predicate": "true_loyalty",
                "object": "Secretly worked for the Arlong Pirates only to earn enough money to buy back Cocoyasi Village's freedom.",
                "source_citation": "Episode 37",
                "first_revealed_at": "S1E37",
                "first_hinted_at": "S1E31",
                "confidence": 0.94,
            },
            {
                "subject": "Nico Robin",
                "predicate": "secret_identity",
                "object": "Operates as Miss All Sunday, Crocodile's partner within Baroque Works.",
                "source_citation": "Episode 128",
                "first_revealed_at": "S1E128",
                "first_hinted_at": "S1E128",
                "confidence": 0.93,
            },
            {
                "subject": "Nico Robin",
                "predicate": "crew_membership",
                "object": "Joins the Straw Hat Pirates as their archaeologist after the Alabasta incident.",
                "source_citation": "Episode 296",
                "first_revealed_at": "S1E296",
                "first_hinted_at": "S1E296",
                "confidence": 0.97,
            },
            {
                "subject": "Crocodile",
                "predicate": "true_identity",
                "object": "A former Warlord of the Sea secretly leading Baroque Works' Operation Utopia to seize Alabasta.",
                "source_citation": "Episode 272",
                "first_revealed_at": "S1E272",
                "first_hinted_at": "S1E137",
                "confidence": 0.92,
            },
            {
                "subject": "Portgas D. Ace",
                "predicate": "true_lineage",
                "object": "Biological son of the Pirate King, Gol D. Roger, and Luffy's sworn brother.",
                "source_citation": "Episode 770",
                "first_revealed_at": "S1E770",
                "first_hinted_at": "S1E152",
                "confidence": 0.9,
            },
        ],
    },
]


async def seed_all(session: AsyncSession) -> None:
    """Idempotently insert the launch corpus. Skips any anime (or franchise) whose slug
    already exists — checked independently, since a franchise can still need seeding
    even when its anime was already inserted by an earlier run."""
    for anime_data in SEED_ANIME:
        existing = await session.execute(select(Anime).where(Anime.slug == anime_data["slug"]))
        anime = existing.scalar_one_or_none()

        if anime is None:
            anime = Anime(
                slug=anime_data["slug"],
                title=anime_data["title"],
                total_episodes=anime_data["total_episodes"],
                season_episode_counts=anime_data["season_episode_counts"],
                mal_id=anime_data.get("mal_id"),
                anilist_id=anime_data.get("anilist_id"),
                cover_image_url=anime_data.get("cover_image_url"),
                genres=anime_data.get("genres", []),
                synopsis=anime_data.get("synopsis"),
                score=anime_data.get("score"),
            )
            session.add(anime)
            await session.flush()

            faction_by_name: dict[str, Faction] = {}
            for faction_data in anime_data.get("factions", []):
                parent = faction_by_name.get(faction_data.get("parent"))
                faction = Faction(
                    anime_id=anime.id,
                    name=faction_data["name"],
                    description=faction_data.get("description"),
                    parent_id=parent.id if parent else None,
                    first_revealed_at=faction_data.get("first_revealed_at"),
                )
                session.add(faction)
                await session.flush()
                faction_by_name[faction_data["name"]] = faction

            for character_data in anime_data.get("characters", []):
                faction = faction_by_name.get(character_data.get("faction"))
                character_kwargs = {
                    "anime_id": anime.id,
                    "name": character_data["name"],
                    "faction_id": faction.id if faction else None,
                    "role": character_data.get("role"),
                    "height": character_data.get("height"),
                    "avatar_url": character_data.get("avatar_url"),
                    "power": character_data.get("power"),
                    "backstory": character_data.get("backstory"),
                }
                if "first_revealed_at" in character_data:
                    character_kwargs["first_revealed_at"] = character_data["first_revealed_at"]
                session.add(Character(**character_kwargs))

            for fact_data in anime_data["facts"]:
                session.add(TemporalFact(anime_id=anime.id, **fact_data))

        if anime_data.get("franchise_entries"):
            existing_franchise = await session.execute(
                select(Franchise).where(Franchise.slug == anime.slug)
            )
            if existing_franchise.scalar_one_or_none() is None:
                franchise = Franchise(slug=anime.slug, name=anime_data["title"])
                session.add(franchise)
                await session.flush()

                for entry_data in anime_data["franchise_entries"]:
                    session.add(
                        FranchiseEntry(
                            franchise_id=franchise.id,
                            anime_id=anime.id if entry_data["entry_type"] == "tv" else None,
                            title=entry_data["title"],
                            entry_type=entry_data["entry_type"],
                            release_order=entry_data["release_order"],
                            chronological_order=entry_data["chronological_order"],
                            note=entry_data.get("note"),
                        )
                    )

    await session.commit()


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await seed_all(session)


if __name__ == "__main__":
    asyncio.run(main())
