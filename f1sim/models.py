"""
Core data models: Driver, Team, Track.

Ratings are on a rough 0-100 scale, meant as flavourful simulation inputs
rather than precise real-world assessments.
"""
from dataclasses import dataclass, field
from typing import Optional

NATIONALITY_FLAGS = {
    "ARG": "🇦🇷", "AUS": "🇦🇺", "AUT": "🇦🇹", "BEL": "🇧🇪", "BGR": "🇧🇬",
    "BRA": "🇧🇷", "CAN": "🇨🇦", "CHE": "🇨🇭", "CHL": "🇨🇱", "COL": "🇨🇴",
    "CZE": "🇨🇿", "DEU": "🇩🇪", "DNK": "🇩🇰", "ESP": "🇪🇸", "FIN": "🇫🇮",
    "FRA": "🇫🇷", "GBR": "🇬🇧", "GER": "🇩🇪", "HUN": "🇭🇺", "IND": "🇮🇳",
    "IRL": "🇮🇪", "ITA": "🇮🇹", "JPN": "🇯🇵", "MEX": "🇲🇽", "MON": "🇲🇨",
    "NED": "🇳🇱", "NLD": "🇳🇱", "NOR": "🇳🇴", "NZL": "🇳🇿", "POL": "🇵🇱",
    "POR": "🇵🇹", "PRY": "🇵🇾", "SWE": "🇸🇪", "THA": "🇹🇭", "TUR": "🇹🇷",
    "URY": "🇺🇾", "USA": "🇺🇸", "ZAF": "🇿🇦",
}


@dataclass
class Driver:
    name: str
    number: int
    nationality: str
    pace: int              # raw single-lap speed
    racecraft: int         # overtaking / defending / wheel-to-wheel
    consistency: int       # avoids mistakes, manages tires
    wet_skill: int         # performance in wet conditions
    experience: int        # affects consistency under pressure, tire mgmt
    aggression: int        # willingness to attack; raises both overtakes and crash risk
    age: int
    contract_years: int = 2
    team: Optional[str] = None
    academy: Optional[str] = None
    reference_sps: float = 0.0
    reference_tms: float = 0.0

    # season-scoped stats (reset each season)
    season_points: float = 0.0
    season_wins: int = 0
    season_podiums: int = 0
    season_dnfs: int = 0
    season_poles: int = 0
    best_finish: Optional[int] = None

    # career-scoped stats
    career_points: float = 0.0
    career_wins: int = 0
    career_races: int = 0

    def reset_season(self):
        self.season_points = 0.0
        self.season_wins = 0
        self.season_podiums = 0
        self.season_dnfs = 0
        self.season_poles = 0
        self.best_finish = None

    @property
    def overall(self) -> float:
        """Rough single-number skill rating, used by the transfer market."""
        return (
            self.pace * 0.35
            + self.racecraft * 0.25
            + self.consistency * 0.20
            + self.experience * 0.10
            + self.wet_skill * 0.10
        )

    @property
    def flag(self) -> str:
        return NATIONALITY_FLAGS.get(self.nationality, "🏳️")

    def __repr__(self):
        return f"{self.name} (#{self.number}, {self.team})"


@dataclass
class Team:
    name: str
    full_name: str
    car_performance: int   # 0-100, this team's current-year full car package
    reliability: int       # 0-100, higher = fewer mechanical DNFs
    pit_crew: int          # 0-100, affects pit stop time loss
    tier: str              # "front", "midfield", "back" - used by transfer market
    drivers: list = field(default_factory=list)  # list[Driver]
    engine: str = ""
    engine_performance: int = 0  # 0-100, supplier-level power-unit rating
    engine_reliability: int = 0  # 0-100, supplier-level power-unit reliability
    pit_stop_average_seconds: float = 4.05
    reference_rank: int = 0      # external 2026 constructor-results reference
    reference_points: int = 0
    weekend_form: float = 0.0
    aero_efficiency: int = 50
    low_speed_performance: int = 50
    high_speed_performance: int = 50
    traction: int = 50
    braking: int = 50
    straight_line_speed: int = 50

    season_points: float = 0.0
    season_wins: int = 0

    def reset_season(self):
        self.season_points = 0.0
        self.season_wins = 0
        for d in self.drivers:
            d.reset_season()

    def __repr__(self):
        names = ", ".join(d.name for d in self.drivers)
        return f"{self.name} [{names}]"


@dataclass
class Track:
    name: str
    country: str
    laps: int
    overtaking_difficulty: float  # 0 (easy to pass) - 1 (Monaco-hard)
    wet_chance: float             # probability this round is wet
    is_sprint: bool = False
    turn_count: int = 0
    circuit_length_km: float = 0.0
    track_type: str = "permanent"
    slow_corners: int = 0
    medium_corners: int = 0
    high_speed_corners: int = 0
    long_straights: int = 0
    downforce_demand: float = 0.5
    braking_demand: float = 0.5
    traction_demand: float = 0.5
    straight_line_demand: float = 0.5
    tyre_selection: tuple = ("C2", "C3", "C4")
    tyre_wear_rate: float = 0.5
    pit_lane_time_seconds: float = 22.0
    pit_stop_probability: float = 0.65
