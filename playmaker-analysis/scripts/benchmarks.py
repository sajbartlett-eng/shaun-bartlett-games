"""
Every real-world benchmark used in the audit, with its source and my confidence.

Confidence:
  high    official or league-wide tracking numbers, recent season, direct measure
  medium  credible secondary source, or a direct measure from an older/partial season
  low     indirect proxy, tiny sample, or my own arithmetic on other figures
  none    no usable public data found: the audit says so instead of inventing a number

How the game's contest states are mapped to real data (an assumption, stated in the report):
  open (no adjacent defender)            ~ NBA "wide open", nearest defender 6+ ft
  weak (adjacent, not basket side)       ~ NBA "tight", 2-4 ft, or a late closeout
  full (adjacent, basket side)           ~ NBA "very tight", 0-2 ft, defender set
"""

SOURCES = {
    "CTG": dict(
        title="Cleaning the Glass, League shooting by location (NBA regular season)",
        url="https://cleaningtheglass.com/stats/league/shots",
        note="Rim 66.6-67.0%, short mid 44.6-44.9%, long mid 41.5-42.3%, all mid 43.8-44.3%, "
             "corner 3 38.8-39.4%, non-corner 3 35.3-35.5%, all 3 36.2-36.5%. Two cached snapshots, ~2024-25.",
        confidence="high"),
    "NBA_ZONES_2022": dict(
        title="NBA.com, Stats leaders: top rim protectors (Dec 2022)",
        url="https://www.nba.com/news/stats-leaders-top-rim-protectors-dec-2022",
        note="League: restricted area 66.2%, paint non-RA 43.0%, mid-range 41.7%, corners 38.5% / 38.0%. Partial 2022-23 season.",
        confidence="high"),
    "NBA_SURVEY_2024": dict(
        title="NBA.com, 2023-24 NBA Stats Survey: League scoring averages",
        url="https://www.nba.com/news/2023-24-nba-stats-survey-league-scoring-averages",
        note="League 3P% 36.6% (2023-24); 2P% 54.5%.",
        confidence="high"),
    "NBA_MID_2023": dict(
        title="NBA.com, 2023-24 storylines: offensive efficiency rising",
        url="https://www.nba.com/news/2023-24-storylines-no-10-offensive-efficiency-rising",
        note="Mid-range FG% reached an all-time high of 42.0% in 2022-23.",
        confidence="high"),
    "WIDE_OPEN_3": dict(
        title="B. McCormick, 'Increasing Offensive Spacing' (Substack, citing NBA tracking); CBS Sports, wide-open 3s",
        url="https://brianmccormick.substack.com/p/increasing-offensive-spacing",
        note="Wide-open (6+ ft) threes 38.4% vs tight (2-4 ft) 30.1%; CBS cites 38.6% wide open. Season not stated.",
        confidence="medium"),
    "CBS_OPEN_3": dict(
        title="CBS Sports, Wide-open 3s and how each team fared",
        url="https://www.cbssports.com/nba/news/wide-open-3s-and-ranking-how-each-nba-team-fared-at-making-defenses-pay",
        note="League average 38.6% on wide-open threes (older season).",
        confidence="medium"),
    "EL_3PT": dict(
        title="EuroLeague, Stats review: threes and the EuroLeague (Sportradar)",
        url="https://www.euroleaguebasketball.net/euroleague/news/stats-review-threes-and-the-euroleague",
        note="EuroLeague catch-and-shoot 3 37.6%, pull-up 3 32.3%; ~40% of FGA are threes. FIBA-rules league.",
        confidence="medium"),
    "RIM_PROTECT": dict(
        title="NBA tracking via Stat Defender (2024-25) and Sportskeeda DPOY tracker (2023-24)",
        url="https://x.com/statdefender/status/1885751774134607878",
        note="Best DFG% at the rim 2024-25 (partial): Gafford 46.0%, Wembanyama 48.9%, Gobert 51.8%, Zubac 53.5%. "
             "2023-24: Wembanyama 53.7% within 6 ft, 10.7 pts below expected (so league expected ~64%).",
        confidence="medium"),
    "RIM_LEAGUE_2026": dict(
        title="DataDunk, NBA rim protection 2025-26 (pbpstats)",
        url="https://datadunknba.substack.com/p/nba-rim-protection-2026-27-all-30-teams",
        note="League opponent rim FG% 67.3%; best team (OKC) 61.2%.",
        confidence="medium"),
    "OPEN_10FT": dict(
        title="The Spax, Expected effective field goal percentage",
        url="https://www.thespax.com/nba/shooting-efficiency-reimagined-expected-effective-field-goal-percentage/",
        note="Wide-open shots inside 10 ft converted at about 90% in the season studied (about six years old).",
        confidence="low"),
    "POSTUP_PPP": dict(
        title="Synergy post-up efficiency: Nylon Calculus (FanSided 2017), NBA Math, The Ringer (2019)",
        url="https://fansided.com/2017/09/08/nylon-calculus-understanding-synergy-play-type-data/",
        note="League post-up 0.85-0.93 points per possession (NBA, 2014-2019).",
        confidence="medium"),
    "FIBA_WC23": dict(
        title="FIBA, Scouting report: FIBA Basketball World Cup 2023",
        url="https://assets.fiba.basketball/image/upload/documents-corporate-studies-and-facts-fiba-scouting-report-fiba-basketball-world-cup-2023.pdf",
        note="FT% 75.5% (highest in 30 years); 19.4 threes made per game; Serbia 66.4% and France 63.9% on twos; "
             "high-turnover teams 14.4-16.2 TO per game. Read via search excerpts; the PDF host is blocked in this session.",
        confidence="high"),
    "ISO_PPP": dict(
        title="Best Ball Stats, Isolation basketball 2016-2021; ESPN via Bleacher Report (2012)",
        url="https://bestballstats.com/2021/06/13/isolation-basketball-an-inefficient-yet-necessary-offense/",
        note="Isolation 0.886 PPP and 47.3% eFG (2016-21) vs 1.088 league PPP; 0.78 PPP in 2012.",
        confidence="medium"),
    "EL_ISO_PNR": dict(
        title="EuroLeague stats reviews (Sportradar/Synergy); JHSE end-of-game play types study",
        url="https://www.euroleaguebasketball.net/news/stats-review-pick-and-roll-trends",
        note="EuroLeague pick-and-roll 0.94-1.01 PPP depending on season; isolation 0.78-0.98 PPP in close-game endings.",
        confidence="medium"),
    "PNR_TEAM": dict(
        title="FantasyTeamAdvice play-type pages (Synergy-derived): 76ers 2023-24, Celtics 2025-26",
        url="https://fantasyteamadvice.com/nba/teams/philadelphia-76ers/playtypes/2023",
        note="P&R ball handler 0.92-0.93 PPP with 10.9-11.6% turnover frequency; roll man 1.14 PPP, 3.9% TO. Team-level only.",
        confidence="low"),
    "BLOWBY": dict(
        title="EssentiallySports, Finals blow-by tracking (Wembanyama, Doncic)",
        url="https://www.essentiallysports.com/nba-active-basketball-news-victor-wembanyama-posting-worse-numbers-than-luka-doncic-in-category-lakers-star-gets-criticized-for-los-angeles-lakers-san-antonio-spurs-new-york-knicks/",
        note="Defenders beaten off the dribble on 58-61% of drives they defended (18-drive samples; definition disputed).",
        confidence="low"),
    "PACE_2025": dict(
        title="NBA.com season table 2024-25; SportsEthos 2024-25 pace report",
        url="https://sportsethos.com/top-posts/fantasy-basketball-draft-guide-2025-pace-report/",
        note="Pace 98.8-99.6 possessions; ~8.2 steals and ~14.3 turnovers per team game -> steals end ~8% "
             "of possessions, turnovers ~14%.",
        confidence="medium"),
    "PASSES": dict(
        title="NBA.com team tracking (passes per game); TeamRankings steals per game 2025",
        url="https://www.nba.com/stats/teams",
        note="Teams make ~300-341 passes per game; team steals 6.9-10.2 per game. All steals / passes gives "
             "an upper bound of ~2.5% of passes intercepted (my arithmetic; not all steals are interceptions).",
        confidence="low"),
    "DEFLECT": dict(
        title="NBA.com hustle stats: Daniels 2024-25, Caruso 2023-24; Inquirer (Sixers 2023-24); Bruin Sports Analytics",
        url="https://www.nba.com/news/5-standout-stats-2024-25-season",
        note="Team deflections ~15-22 per game (leaders 17.3-21.7). Dyson Daniels 5.8 deflections and 3.0 steals per game "
             "-> about 0.5 steals per deflection for the league's best disruptor (my arithmetic).",
        confidence="low"),
    "DUNK": dict(
        title="Wikipedia, Slam dunk; RunRepeat, 82 stats on dunks in the NBA",
        url="https://en.wikipedia.org/wiki/Slam_dunk",
        note="The dunk is usually the highest-percentage shot in basketball (no league figure given); dunks are ~12.5% of "
             "two-point makes since 2000-01 (RunRepeat). The PDF itself says dunks are 'harder to block'.",
        confidence="medium"),
    "THREE_LEADERS": dict(
        title="Wikipedia, List of NBA annual 3-point field goal percentage leaders",
        url="https://en.wikipedia.org/wiki/List_of_NBA_annual_3-point_field_goal_percentage_leaders",
        note="Annual leaders typically shoot ~44-47% vs a ~36% league average: elite shooters sit ~8-10 points above average.",
        confidence="medium"),
    "FOUL_TYPES": dict(
        title="No league-wide breakdown of fouls by type (reach-in vs shooting) found",
        url="",
        note="No public rate of fouls per steal attempt exists in the sources reached.",
        confidence="none"),
    "SCREEN_CAUGHT": dict(
        title="No public rate of defenders caught on screens found",
        url="",
        note="Screen navigation is tracked privately (Second Spectrum); only P&R outcome PPP is public.",
        confidence="none"),
}

# Make-probability benchmarks by shot and contest state: (low, high, source ids, confidence, note)
# "derived" = my estimate built from the sourced numbers; the derivation is in the note.
SHOT_BENCHMARKS = {
    "layup": {
        "all":  (0.65, 0.67, ["CTG", "NBA_ZONES_2022", "RIM_LEAGUE_2026"], "high", "all rim attempts, every contest level"),
        "open": (0.75, 0.90, ["OPEN_10FT"], "low", "wide-open inside 10 ft ~90% in one older study; layups below dunks"),
        "full": (0.46, 0.55, ["RIM_PROTECT"], "medium", "best rim protectors in the league as closest defender"),
    },
    "dunk": {
        "all":  (None, None, ["DUNK"], "none", "no public dunk FG% found; sources agree the dunk is the highest-percentage shot"),
    },
    "post": {
        "all":  (0.425, 0.465, ["POSTUP_PPP"], "medium", "0.85-0.93 PPP / 2 points ~ 42-47% (ignores fouls and turnovers)"),
    },
    "floater": {
        "all":  (0.43, 0.45, ["CTG", "NBA_ZONES_2022"], "high", "short mid-range / paint outside restricted area"),
    },
    "mid": {
        "all":  (0.415, 0.443, ["CTG", "NBA_ZONES_2022", "NBA_MID_2023"], "high", "all mid-range"),
        "open": (0.44, 0.49, ["CTG", "WIDE_OPEN_3"], "low",
                 "derived: wide-open threes run ~2-5 pts above all threes; same gap applied to mid-range"),
    },
    "long2": {
        "all":  (0.415, 0.423, ["CTG"], "high", "long mid-range (13.75 ft to the arc)"),
        "open": (0.43, 0.47, ["CTG", "WIDE_OPEN_3"], "low", "derived as for mid-range"),
    },
    "three": {
        "all":  (0.362, 0.366, ["CTG", "NBA_SURVEY_2024"], "high", "all threes; corner 38.8-39.4%, above the break 35.3-35.5%"),
        "open": (0.37, 0.386, ["WIDE_OPEN_3", "CBS_OPEN_3", "EL_3PT"], "medium", "wide open 6+ ft; EuroLeague catch-and-shoot 37.6%"),
        "weak": (0.30, 0.33, ["WIDE_OPEN_3", "EL_3PT"], "medium", "tight 2-4 ft 30.1%; EuroLeague pull-up 32.3%"),
        "full": (None, None, [], "none", "no public very-tight (0-2 ft) split found; expect below 30%"),
    },
    "ft": {
        "all":  (0.755, 0.78, ["FIBA_WC23", "NBA_SURVEY_2024"], "high", "FIBA World Cup 2023 75.5%; PDF centres FT 15 on 75%"),
    },
}

# Size of the contest effect: points of make % a contest removes from an open look.
# (low, high, sources, confidence, basis, game state it should be compared with)
CONTEST_DROP_BENCHMARKS = {
    "rim":   (0.31, 0.44, ["OPEN_10FT", "RIM_PROTECT"], "low-medium",
              "open rim ~85-90% (low confidence) down to 46-54% against the best rim protectors (medium)", "full"),
    "three": (0.07, 0.09, ["WIDE_OPEN_3"], "medium", "wide open 38.4% -> tight (2-4 ft) 30.1%: about 8 points", "weak"),
}

# Action benchmarks. The game rolls per attempt; real data is mostly per possession or per pass.
ACTION_BENCHMARKS = {
    "dribble": dict(real="Defenders beaten on 58-61% of drives they defended (Finals samples); isolation 0.78-0.90 PPP, "
                         "47% eFG", sources=["BLOWBY", "ISO_PPP", "EL_ISO_PNR"], confidence="low",
                    usable_range=(0.45, 0.60),
                    note="Only drives that happened are counted, so a per-attempt rate is unknown. Treat as a loose check."),
    "pass":    dict(real="<=~2.5% of all passes intercepted; ~5-7% deflected (15-22 deflections on 300+ passes)",
                    sources=["PASSES", "DEFLECT"], confidence="low", usable_range=None,
                    note="No public rate for passes into a denied lane. Real interceptions are rare events."),
    "screen":  dict(real="P&R ball handler 0.85-0.93 PPP, ~11% turnover frequency; EuroLeague P&R 0.94-1.01 PPP",
                    sources=["PNR_TEAM", "EL_ISO_PNR", "SCREEN_CAUGHT"], confidence="none", usable_range=None,
                    note="No public rate for a defender being caught on a screen."),
    "steal":   dict(real="Steals end ~8% of possessions; best disruptor converts ~0.5 steals per deflection",
                    sources=["PACE_2025", "DEFLECT"], confidence="low", usable_range=None,
                    note="Per-attempt steal success is not tracked publicly. A deflection is already a successful touch, "
                         "so per-attempt success should sit below ~50% even for the best defender."),
    "foul_stl": dict(real="No public data", sources=["FOUL_TYPES"], confidence="none", usable_range=None, note=""),
    "turnover": dict(real="Turnovers end ~14% of NBA possessions; FIBA WC 2023 high-turnover teams 14-16 per game; "
                          "P&R ball-handler turnover frequency ~11%",
                     sources=["PACE_2025", "FIBA_WC23", "PNR_TEAM"], confidence="medium", usable_range=None, note=""),
}


def source_table():
    """Rows for output/sources.csv."""
    return [dict(source_id=k, **v) for k, v in SOURCES.items()]
