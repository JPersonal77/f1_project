"""
Starting data for the 2026 season: 11 teams, 22 drivers, and a 24-round
calendar. Ratings are approximate/subjective, built for simulation flavour
around each driver's real-world reputation heading into 2026 -- not an
authoritative ranking.
"""
from f1sim.models import Driver, Team, Track


ENGINE_SPECS = {
    "Ferrari": {"performance": 91, "reliability": 88},
    "Mercedes": {"performance": 93, "reliability": 92},
    "Red Bull Ford": {"performance": 88, "reliability": 84},
    "Honda RBPT": {"performance": 89, "reliability": 87},
    "Audi": {"performance": 82, "reliability": 82},
}

PIT_STOP_AVERAGES_2026 = {
    "Mercedes": 3.13,
    "Ferrari": 3.22,
    "McLaren": 4.19,
    "Red Bull Racing": 3.70,
    "Racing Bulls": 2.88,
    "Alpine": 3.36,
    "Haas": 5.76,
    "Audi": 3.65,
    "Williams": 4.81,
    "Aston Martin": 5.11,
    "Cadillac": 4.42,
}


TEAM_ENGINES = {
    "McLaren": "Mercedes",
    "Ferrari": "Ferrari",
    "Red Bull Racing": "Red Bull Ford",
    "Mercedes": "Mercedes",
    "Aston Martin": "Honda RBPT",
    "Williams": "Mercedes",
    "Audi": "Audi",
    "Alpine": "Mercedes",
    "Haas": "Ferrari",
    "Racing Bulls": "Red Bull Ford",
    "Cadillac": "Ferrari",
}

# Cross-reference from the 2026 constructor standings on the supplied results
# page. These points are external reference data, separate from this sim's
# generated season_points.
TEAM_RESULTS_2026 = {
    "Mercedes": {"rank": 1, "points": 503, "car_performance": 95},
    "Ferrari": {"rank": 2, "points": 358, "car_performance": 92},
    "McLaren": {"rank": 3, "points": 306, "car_performance": 91},
    "Red Bull Racing": {"rank": 4, "points": 230, "car_performance": 88},
    "Racing Bulls": {"rank": 5, "points": 77, "car_performance": 81},
    "Alpine": {"rank": 6, "points": 68, "car_performance": 79},
    "Haas": {"rank": 7, "points": 21, "car_performance": 75},
    "Audi": {"rank": 8, "points": 17, "car_performance": 74},
    "Williams": {"rank": 9, "points": 11, "car_performance": 72},
    "Aston Martin": {"rank": 10, "points": 3, "car_performance": 69},
    "Cadillac": {"rank": 11, "points": 0, "car_performance": 66},
}

# 2026 driver scores cross-referenced from Formula 1 Dashboard. SPS is the
# season performance score; TMS is the teammate score. They are reference
# signals, not replacements for the simulator's driver attributes.
DRIVER_SCORES_2026 = {
    "Kimi Antonelli": (84.1, 48.4),
    "George Russell": (71.2, 51.6),
    "Lewis Hamilton": (74.5, 48.2),
    "Lando Norris": (68.0, 68.7),
    "Charles Leclerc": (62.1, 51.8),
    "Max Verstappen": (60.8, 85.1),
    "Oscar Piastri": (50.1, 31.3),
    "Isack Hadjar": (39.8, 18.3),
    "Liam Lawson": (42.4, 49.4),
    "Pierre Gasly": (49.0, 80.2),
    "Arvid Lindblad": (37.6, 43.5),
    "Franco Colapinto": (31.8, 19.8),
    "Oliver Bearman": (33.2, 72.0),
    "Gabriel Bortoleto": (31.9, 59.3),
    "Nico Hulkenberg": (24.1, 40.7),
    "Carlos Sainz": (29.4, 64.4),
    "Alexander Albon": (17.8, 35.6),
    "Esteban Ocon": (21.7, 28.0),
    "Fernando Alonso": (27.1, 76.0),
    "Lance Stroll": (6.9, 24.0),
    "Valtteri Bottas": (20.0, 42.9),
    "Sergio Perez": (22.5, 57.1),
}

TEAM_CAR_PROFILES_2026 = {
    "Mercedes": {"aero_efficiency": 93, "low_speed_performance": 86, "high_speed_performance": 94, "traction": 89, "braking": 91, "straight_line_speed": 87},
    "Ferrari": {"aero_efficiency": 90, "low_speed_performance": 89, "high_speed_performance": 87, "traction": 86, "braking": 91, "straight_line_speed": 88},
    "McLaren": {"aero_efficiency": 94, "low_speed_performance": 90, "high_speed_performance": 93, "traction": 88, "braking": 89, "straight_line_speed": 86},
    "Red Bull Racing": {"aero_efficiency": 96, "low_speed_performance": 94, "high_speed_performance": 95, "traction": 92, "braking": 93, "straight_line_speed": 82},
    "Racing Bulls": {"aero_efficiency": 82, "low_speed_performance": 79, "high_speed_performance": 80, "traction": 77, "braking": 79, "straight_line_speed": 82},
    "Alpine": {"aero_efficiency": 77, "low_speed_performance": 75, "high_speed_performance": 78, "traction": 74, "braking": 78, "straight_line_speed": 82},
    "Haas": {"aero_efficiency": 76, "low_speed_performance": 73, "high_speed_performance": 76, "traction": 72, "braking": 79, "straight_line_speed": 80},
    "Audi": {"aero_efficiency": 74, "low_speed_performance": 76, "high_speed_performance": 73, "traction": 71, "braking": 75, "straight_line_speed": 75},
    "Williams": {"aero_efficiency": 70, "low_speed_performance": 68, "high_speed_performance": 72, "traction": 69, "braking": 73, "straight_line_speed": 88},
    "Aston Martin": {"aero_efficiency": 69, "low_speed_performance": 71, "high_speed_performance": 68, "traction": 70, "braking": 72, "straight_line_speed": 79},
    "Cadillac": {"aero_efficiency": 65, "low_speed_performance": 64, "high_speed_performance": 63, "traction": 62, "braking": 68, "straight_line_speed": 76},
}

# Dry-weather compounds selected for each weekend, from the C0-C6 range.
# Wear and pit-lane loss are simulator inputs based on circuit characteristics.
TRACK_TYRE_PROFILES = {
    "Bahrain GP": (("C1", "C2", "C3"), 0.78, 22.0, 0.88),
    "Saudi Arabian GP": (("C2", "C3", "C4"), 0.58, 25.0, 0.70),
    "Australian GP": (("C2", "C3", "C4"), 0.55, 19.0, 0.65),
    "Japanese GP": (("C1", "C2", "C3"), 0.82, 19.0, 0.90),
    "Chinese GP": (("C2", "C3", "C4"), 0.68, 20.0, 0.78),
    "Miami GP": (("C2", "C3", "C4"), 0.60, 18.0, 0.72),
    "Emilia Romagna GP": (("C3", "C4", "C5"), 0.55, 20.0, 0.66),
    "Monaco GP": (("C3", "C4", "C5"), 0.42, 17.0, 0.48),
    "Canadian GP": (("C3", "C4", "C5"), 0.50, 18.0, 0.62),
    "Spanish GP": (("C1", "C2", "C3"), 0.82, 20.0, 0.88),
    "Austrian GP": (("C3", "C4", "C5"), 0.52, 17.0, 0.58),
    "British GP": (("C1", "C2", "C3"), 0.78, 19.0, 0.86),
    "Belgian GP": (("C1", "C2", "C3"), 0.72, 21.0, 0.82),
    "Hungarian GP": (("C3", "C4", "C5"), 0.58, 19.0, 0.72),
    "Dutch GP": (("C1", "C2", "C3"), 0.74, 18.0, 0.84),
    "Italian GP": (("C3", "C4", "C5"), 0.45, 21.0, 0.52),
    "Azerbaijan GP": (("C3", "C4", "C5"), 0.48, 24.0, 0.55),
    "Singapore GP": (("C3", "C4", "C5"), 0.62, 22.0, 0.76),
    "US GP (Austin)": (("C2", "C3", "C4"), 0.68, 20.0, 0.80),
    "Mexico City GP": (("C2", "C3", "C4"), 0.58, 20.0, 0.70),
    "Sao Paulo GP": (("C2", "C3", "C4"), 0.62, 18.0, 0.75),
    "Las Vegas GP": (("C3", "C4", "C5"), 0.38, 21.0, 0.45),
    "Qatar GP": (("C1", "C2", "C3"), 0.90, 18.0, 0.94),
    "Abu Dhabi GP": (("C2", "C3", "C4"), 0.60, 20.0, 0.72),
}


def _team_engine(team_name):
    engine = TEAM_ENGINES[team_name]
    specs = ENGINE_SPECS[engine]
    return engine, specs["performance"], specs["reliability"]


# 2026 F2 prospects available for future academy promotions or transfers.
# Ratings and potential are subjective simulator values, not official rankings.
def _f2_prospect(team, nationality, age, potential, pace, racecraft,
                 consistency, wet_skill, experience, aggression):
    return {
        "series": "F2",
        "team": team,
        "nationality": nationality,
        "age": age,
        "f1_potential": potential,
        "pace": pace,
        "racecraft": racecraft,
        "consistency": consistency,
        "wet_skill": wet_skill,
        "experience": experience,
        "aggression": aggression,
    }

# 2026 F3 prospects available for future academy promotions or transfers.
# Ratings and potential are subjective simulator values, not official rankings.
def _f3_prospect(team, nationality, age, potential, pace, racecraft,
                 consistency, wet_skill, experience, aggression):
    return {
        "series": "F3",
        "team": team,
        "nationality": nationality,
        "age": age,
        "f1_potential": potential,
        "pace": pace,
        "racecraft": racecraft,
        "consistency": consistency,
        "wet_skill": wet_skill,
        "experience": experience,
        "aggression": aggression,
    }

F1_PROSPECTS = {
    "Rafael Camara": _f2_prospect("Invicta Racing", "BRA", 21, 88, 85, 83, 80, 78, 54, 76),
    "Joshua Durksen": _f2_prospect("Invicta Racing", "PRY", 22, 84, 82, 84, 77, 80, 64, 82),
    "Ritomo Miyata": _f2_prospect("Hitech", "JPN", 26, 82, 82, 81, 79, 84, 86, 70),
    "Colton Herta": _f2_prospect("Hitech", "USA", 26, 86, 87, 84, 74, 78, 78, 87),
    "Noel Leon": _f2_prospect("Campos Racing", "MEX", 21, 84, 82, 80, 76, 77, 48, 81),
    "Nikola Tsolov": _f2_prospect("Campos Racing", "BGR", 19, 89, 87, 84, 76, 79, 42, 86),
    "Dino Beganovic": _f2_prospect("DAMS Lucas Oil", "SWE", 22, 87, 85, 82, 80, 81, 60, 76),
    "Roman Bilinski": _f2_prospect("DAMS Lucas Oil", "POL", 22, 78, 78, 76, 72, 75, 48, 79),
    "Gabriele Mini": _f2_prospect("MP Motorsport", "ITA", 21, 86, 85, 82, 77, 79, 54, 81),
    "Oliver Goethe": _f2_prospect("MP Motorsport", "DEU", 21, 82, 82, 79, 75, 77, 48, 77),
    "Sebastian Montoya": _f2_prospect("PREMA Racing", "COL", 20, 83, 82, 80, 72, 76, 44, 83),
    "Mari Boya": _f2_prospect("PREMA Racing", "ESP", 21, 80, 80, 77, 74, 75, 50, 78),
    "Martinius Stenshorne": _f2_prospect("Rodin Motorsport", "NOR", 20, 86, 84, 83, 78, 79, 48, 82),
    "Alexander Dunne": _f2_prospect("Rodin Motorsport", "IRL", 20, 89, 88, 84, 72, 77, 43, 87),
    "Kush Maini": _f2_prospect("ART Grand Prix", "IND", 26, 82, 81, 82, 76, 80, 82, 76),
    "Tasanapol Inthraphuvasak": _f2_prospect("ART Grand Prix", "THA", 21, 83, 82, 78, 73, 75, 46, 82),
    "Emerson Fittipaldi": _f2_prospect("AIX Racing", "BRA", 19, 80, 79, 75, 69, 73, 35, 81),
    "Cian Shields": _f2_prospect("AIX Racing", "GBR", 20, 78, 77, 74, 71, 74, 40, 76),
    "Nico Varrone": _f2_prospect("Van Amersfoort Racing", "ARG", 25, 81, 81, 84, 79, 80, 78, 75),
    "Rafael Villagomez": _f2_prospect("Van Amersfoort Racing", "MEX", 25, 76, 76, 73, 71, 73, 70, 77),
    "Laurens van Hoepen": _f2_prospect("TRIDENT", "NED", 21, 84, 82, 80, 76, 79, 51, 78),
    "John Bennett": _f2_prospect("TRIDENT", "GBR", 22, 79, 78, 75, 72, 74, 46, 80),

    "Freddie Slater": _f3_prospect("Trident", "GBR", 19, 82, 80, 78, 74, 76, 40, 80),
    "Ugo Ugochukwu": _f3_prospect("Campos Racing", "USA", 19, 80, 78, 76, 72, 74, 38, 78),
    "Tuuka Taponen": _f3_prospect("MP Motorsport", "FIN", 20, 78, 76, 74, 70, 72, 42, 76),
    "Fionn Mcluaghlin": _f3_prospect("Hitech", "IRL", 20, 76, 74, 72, 68, 70, 40, 74),
}


# F1 academy teams and the seats where their juniors are most likely to land.
ACADEMY_FEEDER_TEAMS = {
    "Red Bull Racing": {"Racing Bulls"},
    "Ferrari": {"Haas"},
    "Mercedes": {"Williams"},
    "McLaren": set(),
    "Aston Martin": set(),
    "Alpine": set(),
    "Audi": set(),
}

# Ordered academy preferences for open seats. Earlier academies are preferred.
TEAM_ACADEMY_PREFERENCES = {
    "McLaren": ["McLaren"],
    "Ferrari": ["Ferrari"],
    "Red Bull Racing": ["Red Bull Racing"],
    "Mercedes": ["Mercedes"],
    "Aston Martin": ["Aston Martin"],
    "Williams": ["Mercedes"],
    "Audi": ["Audi"],
    "Alpine": ["Alpine"],
    "Haas": ["Ferrari"],
    "Racing Bulls": ["Red Bull Racing"],
    "Cadillac": [],
}

# Probability of promoting a junior instead of signing an available free agent.
# Lower values represent teams that generally prefer experienced drivers.
TEAM_JUNIOR_APPETITE = {
    "McLaren": 0.55,
    "Ferrari": 0.025,
    "Red Bull Racing": 0.05,
    "Mercedes": 0.05,
    "Aston Martin": 0.65,
    "Williams": 0.50,
    "Audi": 0.35,
    "Alpine": 0.45,
    "Haas": 0.70,
    "Racing Bulls": 0.90,
    "Cadillac": 0.05,
}

JUNIOR_APPETITE_LABELS = {
    "very_low": (0.0, 0.20),
    "low": (0.20, 0.40),
    "moderate": (0.40, 0.60),
    "high": (0.60, 0.80),
    "very_high": (0.80, 1.01),
}


def academy_policy_report():
    """Return readable team academy preferences for the CLI or other callers."""
    report = []
    for team, appetite in TEAM_JUNIOR_APPETITE.items():
        label = next(name for name, bounds in JUNIOR_APPETITE_LABELS.items()
                     if bounds[0] <= appetite < bounds[1])
        academies = ", ".join(TEAM_ACADEMY_PREFERENCES[team]) or "none"
        report.append({
            "team": team,
            "preferred_academies": academies,
            "junior_appetite": label,
            "junior_probability": appetite,
        })
    return report

PROSPECT_ACADEMIES = {

    #F2 prospects (not yet in F1) are assigned to academies based on their current F2 team. 
    "Dino Beganovic": "Ferrari",
    "Nikola Tsolov": "Red Bull Racing",
    "Mari Boya": "Aston Martin",
    "Gabriele Mini": "Alpine",
    "Rafael Camara": "Ferrari",
    "Joshua Durksen": "Mercedes",
    "Alexander Dunne": "Alpine",
    "Kush Maini": "Alpine",

    # F3 prospects (not yet in F1) are assigned to academies based on their current F3 team.
    "Freddie Slater": "Audi",
    "Ugo Ugochukwu": "Red Bull Racing",
    "Tuuka Taponen": "Ferrari",
    'Fionn Mcluaghlin': "Red Bull Racing",
}

ACTIVE_ACADEMIES = {
    "Oliver Bearman": "Ferrari",
    "Liam Lawson": "Red Bull Racing",
    "Isack Hadjar": "Red Bull Racing",
    "Arvid Lindblad": "Red Bull Racing",
    "Kimi Antonelli": "Mercedes",
}

for prospect_name, academy in PROSPECT_ACADEMIES.items():
    F1_PROSPECTS[prospect_name]["academy"] = academy


def build_2026_grid():
    teams = [
        Team("McLaren", "McLaren Formula 1 Team", car_performance=94, reliability=93, pit_crew=95, tier="front", engine="Mercedes", engine_performance=93, engine_reliability=92, drivers=[
            Driver("Lando Norris", 4, "GBR", pace=93, racecraft=88, consistency=88, wet_skill=85, experience=85, aggression=78, age=26, contract_years=3),
            Driver("Oscar Piastri", 81, "AUS", pace=92, racecraft=87, consistency=90, wet_skill=82, experience=78, aggression=75, age=25, contract_years=3),
        ]),
        Team("Ferrari", "Scuderia Ferrari", car_performance=91, reliability=87, pit_crew=90, tier="front", engine="Ferrari", engine_performance=91, engine_reliability=88, drivers=[
            Driver("Charles Leclerc", 16, "MON", pace=93, racecraft=89, consistency=85, wet_skill=87, experience=88, aggression=82, age=28, contract_years=4),
            Driver("Lewis Hamilton", 44, "GBR", pace=90, racecraft=92, consistency=87, wet_skill=93, experience=99, aggression=80, age=41, contract_years=2),
        ]),
        Team("Red Bull Racing", "Oracle Red Bull Racing", car_performance=92, reliability=88, pit_crew=97, tier="front", engine="Red Bull Ford", engine_performance=88, engine_reliability=84, drivers=[
            Driver("Max Verstappen", 1, "NED", pace=97, racecraft=96, consistency=93, wet_skill=95, experience=93, aggression=90, age=28, contract_years=3),
            Driver("Isack Hadjar", 6, "FRA", pace=83, racecraft=80, consistency=78, wet_skill=76, experience=60, aggression=80, age=21, contract_years=2),
        ]),
        Team("Mercedes", "Mercedes-AMG Petronas F1 Team", car_performance=90, reliability=91, pit_crew=93, tier="front", engine="Mercedes", engine_performance=93, engine_reliability=92, drivers=[
            Driver("George Russell", 63, "GBR", pace=90, racecraft=87, consistency=88, wet_skill=86, experience=83, aggression=76, age=28, contract_years=3),
            Driver("Kimi Antonelli", 12, "ITA", pace=85, racecraft=79, consistency=76, wet_skill=80, experience=58, aggression=78, age=20, contract_years=2),
        ]),
        Team("Aston Martin", "Aston Martin Aramco F1 Team", car_performance=84, reliability=85, pit_crew=86, tier="midfield", engine="Honda RBPT", engine_performance=89, engine_reliability=87, drivers=[
            Driver("Fernando Alonso", 14, "ESP", pace=89, racecraft=95, consistency=90, wet_skill=92, experience=99, aggression=82, age=44, contract_years=1),
            Driver("Lance Stroll", 18, "CAN", pace=78, racecraft=72, consistency=75, wet_skill=74, experience=76, aggression=65, age=27, contract_years=3),
        ]),
        Team("Williams", "Atlassian Williams Racing", car_performance=85, reliability=86, pit_crew=84, tier="midfield", engine="Mercedes", engine_performance=93, engine_reliability=92, drivers=[
            Driver("Carlos Sainz", 55, "ESP", pace=88, racecraft=86, consistency=87, wet_skill=83, experience=90, aggression=76, age=31, contract_years=2),
            Driver("Alexander Albon", 23, "THA", pace=85, racecraft=83, consistency=82, wet_skill=80, experience=81, aggression=74, age=29, contract_years=2),
        ]),
        Team("Audi", "Audi F1 Team", car_performance=80, reliability=80, pit_crew=78, tier="midfield", engine="Audi", engine_performance=82, engine_reliability=82, drivers=[
            Driver("Nico Hulkenberg", 27, "GER", pace=84, racecraft=85, consistency=84, wet_skill=88, experience=95, aggression=70, age=38, contract_years=2),
            Driver("Gabriel Bortoleto", 5, "BRA", pace=80, racecraft=77, consistency=74, wet_skill=76, experience=55, aggression=75, age=21, contract_years=2),
        ]),
        Team("Alpine", "BWT Alpine F1 Team", car_performance=78, reliability=79, pit_crew=80, tier="midfield", engine="Mercedes", engine_performance=93, engine_reliability=92, drivers=[
            Driver("Pierre Gasly", 10, "FRA", pace=84, racecraft=83, consistency=82, wet_skill=85, experience=88, aggression=77, age=29, contract_years=2),
            Driver("Franco Colapinto", 43, "ARG", pace=78, racecraft=75, consistency=70, wet_skill=74, experience=55, aggression=82, age=23, contract_years=1),
        ]),
        Team("Haas", "MoneyGram Haas F1 Team", car_performance=79, reliability=82, pit_crew=79, tier="midfield", engine="Ferrari", engine_performance=91, engine_reliability=88, drivers=[
            Driver("Esteban Ocon", 31, "FRA", pace=82, racecraft=81, consistency=81, wet_skill=79, experience=87, aggression=73, age=29, contract_years=2),
            Driver("Oliver Bearman", 87, "GBR", pace=81, racecraft=78, consistency=76, wet_skill=77, experience=62, aggression=79, age=21, contract_years=2),
        ]),
        Team("Racing Bulls", "Visa Cash App Racing Bulls", car_performance=81, reliability=83, pit_crew=85, tier="midfield", engine="Red Bull Ford", engine_performance=88, engine_reliability=84, drivers=[
            Driver("Liam Lawson", 30, "NZL", pace=81, racecraft=79, consistency=76, wet_skill=78, experience=68, aggression=83, age=24, contract_years=2),
            Driver("Arvid Lindblad", 41, "GBR", pace=79, racecraft=74, consistency=70, wet_skill=72, experience=40, aggression=80, age=18, contract_years=2),
        ]),
        Team("Cadillac", "Cadillac F1 Team", car_performance=72, reliability=75, pit_crew=72, tier="back", engine="Ferrari", engine_performance=91, engine_reliability=88, drivers=[
            Driver("Sergio Perez", 11, "MEX", pace=84, racecraft=85, consistency=80, wet_skill=79, experience=90, aggression=72, age=36, contract_years=2),
            Driver("Valtteri Bottas", 77, "FIN", pace=82, racecraft=80, consistency=85, wet_skill=81, experience=91, aggression=62, age=36, contract_years=2),
        ]),
    ]

    for team in teams:
        reference = TEAM_RESULTS_2026[team.name]
        team.car_performance = reference["car_performance"]
        team.reference_rank = reference["rank"]
        team.reference_points = reference["points"]
        team.pit_stop_average_seconds = PIT_STOP_AVERAGES_2026[team.name]
        for attribute, value in TEAM_CAR_PROFILES_2026[team.name].items():
            setattr(team, attribute, value)
        for d in team.drivers:
            d.team = team.name
            d.academy = ACTIVE_ACADEMIES.get(d.name)
            d.reference_sps, d.reference_tms = DRIVER_SCORES_2026[d.name]

    return teams


def build_2026_calendar():
    # Overtaking difficulty: 0 = easy passing, 1 = Monaco-esque procession.
    # Wet chance: rough probability of a wet or mixed-conditions weekend.
    sprint_rounds = {"Australian GP", "Chinese GP", "Miami GP", "Canadian GP",
                     "British GP", "Dutch GP"}
    rounds = [
        ("Bahrain GP", "Bahrain", 57, 0.25, 0.02),
        ("Saudi Arabian GP", "Saudi Arabia", 50, 0.55, 0.01),
        ("Australian GP", "Australia", 58, 0.45, 0.20),
        ("Japanese GP", "Japan", 53, 0.60, 0.32),
        ("Chinese GP", "China", 56, 0.40, 0.25),
        ("Miami GP", "USA", 57, 0.45, 0.15),
        ("Emilia Romagna GP", "Italy", 63, 0.65, 0.22),
        ("Monaco GP", "Monaco", 78, 0.92, 0.20),
        ("Canadian GP", "Canada", 70, 0.40, 0.35),
        ("Spanish GP", "Spain", 66, 0.55, 0.15),
        ("Austrian GP", "Austria", 71, 0.35, 0.46),
        ("British GP", "UK", 52, 0.35, 0.30),
        ("Belgian GP", "Belgium", 44, 0.30, 0.35),
        ("Hungarian GP", "Hungary", 70, 0.75, 0.15),
        ("Dutch GP", "Netherlands", 72, 0.60, 0.28),
        ("Italian GP", "Italy", 53, 0.15, 0.18),
        ("Azerbaijan GP", "Azerbaijan", 51, 0.50, 0.05),
        ("Singapore GP", "Singapore", 62, 0.70, 0.42),
        ("US GP (Austin)", "USA", 56, 0.40, 0.12),
        ("Mexico City GP", "Mexico", 71, 0.55, 0.10),
        ("Sao Paulo GP", "Brazil", 71, 0.45, 0.45),
        ("Las Vegas GP", "USA", 50, 0.35, 0.04),
        ("Qatar GP", "Qatar", 57, 0.40, 0.01),
        ("Abu Dhabi GP", "UAE", 58, 0.35, 0.01),
    ]
    tracks = []
    for name, country, laps, ot, wet in rounds:
        (turn_count, circuit_length_km, track_type, slow_corners,
         medium_corners, high_speed_corners, long_straights,
         downforce_demand, braking_demand, traction_demand,
         straight_line_demand) = TRACK_DNA[name]
        tyre_selection, tyre_wear_rate, pit_lane_time, pit_probability = TRACK_TYRE_PROFILES[name]
        tracks.append(Track(
            name=name,
            country=country,
            laps=laps,
            overtaking_difficulty=ot,
            wet_chance=wet,
            is_sprint=name in sprint_rounds,
            turn_count=turn_count,
            circuit_length_km=circuit_length_km,
            track_type=track_type,
            slow_corners=slow_corners,
            medium_corners=medium_corners,
            high_speed_corners=high_speed_corners,
            long_straights=long_straights,
            downforce_demand=downforce_demand,
            braking_demand=braking_demand,
            traction_demand=traction_demand,
            straight_line_demand=straight_line_demand,
            tyre_selection=tyre_selection,
            tyre_wear_rate=tyre_wear_rate,
            pit_lane_time_seconds=pit_lane_time,
            pit_stop_probability=pit_probability,
        ))
    return tracks

# Track DNA is simulator metadata based on circuit characteristics. The
# demand values are normalized from 0 (low) to 1 (high), not official ratings.
TRACK_DNA = {
    "Bahrain GP": (15, 5.412, "permanent", 5, 7, 3, 3, 0.70, 0.85, 0.75, 0.80),
    "Saudi Arabian GP": (27, 6.174, "street", 4, 12, 11, 4, 0.65, 0.80, 0.65, 0.90),
    "Australian GP": (14, 5.278, "street", 5, 6, 3, 2, 0.65, 0.70, 0.70, 0.65),
    "Japanese GP": (18, 5.807, "permanent", 4, 7, 7, 2, 0.85, 0.75, 0.55, 0.55),
    "Chinese GP": (16, 5.451, "permanent", 6, 6, 4, 2, 0.65, 0.70, 0.80, 0.65),
    "Miami GP": (19, 5.412, "street", 8, 7, 4, 2, 0.60, 0.70, 0.80, 0.70),
    "Emilia Romagna GP": (19, 4.909, "permanent", 7, 7, 5, 1, 0.75, 0.65, 0.75, 0.45),
    "Monaco GP": (19, 3.337, "street", 12, 6, 1, 0, 0.95, 0.55, 0.95, 0.20),
    "Canadian GP": (14, 4.361, "semi-permanent", 4, 7, 3, 4, 0.45, 0.95, 0.85, 0.85),
    "Spanish GP": (14, 4.657, "permanent", 5, 6, 3, 2, 0.70, 0.75, 0.65, 0.60),
    "Austrian GP": (10, 4.318, "permanent", 3, 4, 3, 3, 0.55, 0.80, 0.85, 0.80),
    "British GP": (18, 5.891, "permanent", 3, 8, 7, 2, 0.90, 0.65, 0.50, 0.50),
    "Belgian GP": (19, 7.004, "permanent", 5, 7, 7, 3, 0.75, 0.80, 0.65, 0.90),
    "Hungarian GP": (14, 4.381, "permanent", 8, 5, 1, 1, 0.90, 0.55, 0.90, 0.30),
    "Dutch GP": (14, 4.259, "permanent", 5, 6, 3, 1, 0.80, 0.60, 0.75, 0.35),
    "Italian GP": (11, 5.793, "permanent", 3, 5, 3, 3, 0.35, 0.95, 0.55, 0.95),
    "Azerbaijan GP": (20, 6.003, "street", 8, 7, 5, 3, 0.55, 0.85, 0.80, 0.90),
    "Singapore GP": (19, 4.940, "street", 11, 7, 1, 0, 0.85, 0.75, 0.95, 0.25),
    "US GP (Austin)": (20, 5.513, "permanent", 6, 8, 6, 2, 0.75, 0.75, 0.70, 0.65),
    "Mexico City GP": (17, 4.304, "permanent", 7, 6, 4, 2, 0.65, 0.70, 0.75, 0.60),
    "Sao Paulo GP": (15, 4.309, "permanent", 5, 6, 4, 2, 0.65, 0.75, 0.70, 0.70),
    "Las Vegas GP": (17, 6.201, "street", 7, 6, 4, 3, 0.45, 0.85, 0.65, 0.95),
    "Qatar GP": (16, 5.419, "permanent", 4, 8, 4, 2, 0.80, 0.65, 0.60, 0.65),
    "Abu Dhabi GP": (16, 5.281, "permanent", 7, 6, 3, 2, 0.65, 0.70, 0.85, 0.70),
}
