from REMOLib import *
from dataclasses import dataclass
import pygame
import json
import os

from typing import Dict, Iterable, List, Optional, Sequence


import enum
import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence


"""Skeleton code for a contract-driven magical girl agency simulation.

This module sketches the core data structures and game loop needed for a
turn-based management game where the player recruits magical girls through
contracts (gacha) and sends them on missions to protect the city.
"""

from __future__ import annotations

import enum
import random
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence


class Stat(enum.Enum):
    """Primary attributes shared by every magical girl."""

    FORCE = "Force"  # 전투, 위험 임무 대응력, 괴이 토벌, 방호, 퇴마
    WISDOM = "Wisdom"  # 연구·해석·마법 의식, 정화, 조사, 연구
    CHARISMA = "Charisma"  # 협상·아이돌·홍보, 시민 교류, 외교, 공연
    SPIRIT = "Spirit"  # 피로·사기·사건 내성


STAT_ORDER: Sequence[Stat] = (
    Stat.FORCE,
    Stat.WISDOM,
    Stat.CHARISMA,
    Stat.SPIRIT,
)


@dataclass
class MagicalGirl:
    """Contracted magical girl with combat and support attributes."""

    name: str
    codename: str
    stats: Dict[Stat, int]
    rarity: int = 3
    fatigue: int = 0
    morale: int = 100
    level: int = 1
    bonds: int = 0

    def effective_stat(self, stat: Stat) -> int:
        """Return the current effective stat value including fatigue penalties."""

        base = self.stats.get(stat, 0)
        if stat is Stat.SPIRIT:
            return base

        fatigue_penalty = max(0.5, 1.0 - self.fatigue / 150.0)
        morale_bonus = 1.0 + (self.morale - 100) / 250.0
        return max(1, int(base * fatigue_penalty * morale_bonus))

    def apply_mission_fatigue(self, intensity: int) -> None:
        """Increase fatigue and reduce morale after a mission resolves."""

        self.fatigue = min(120, self.fatigue + 10 + intensity)
        if intensity > 0:
            self.morale = max(0, self.morale - intensity // 2)

    def rest(self, recovery_bonus: int = 0) -> None:
        """Recover fatigue and morale while the girl is not deployed."""

        recovery = 25 + recovery_bonus
        self.fatigue = max(0, self.fatigue - recovery)
        self.morale = min(120, self.morale + 12 + recovery_bonus // 2)

    def gain_experience(self, xp: int) -> bool:
        """Add experience and perform a level-up if the threshold is reached."""

        threshold = 50 + self.level * 15
        leveled = False
        self.bonds += xp // 2
        while xp > 0:
            if xp >= threshold:
                xp -= threshold
                self.level += 1
                leveled = True
                self._improve_stats()
                threshold = 50 + self.level * 15
            else:
                break
        return leveled

    def _improve_stats(self) -> None:
        """Boost base stats in a simple, deterministic manner."""

        for stat in STAT_ORDER:
            self.stats[stat] = self.stats.get(stat, 0) + 1
        self.stats[Stat.FORCE] += 1
        self.stats[Stat.WISDOM] += 1


class MissionType(enum.Enum):
    """Mission categories with different failure penalties."""

    GATE_SCOUT = "Gate Scout"
    GATE_ASSAULT = "Gate Assault"
    GATE_SEAL = "Gate Seal"
    SUPPORT = "Support"
    PUBLIC_RELATIONS = "Public Relations"


@dataclass
class Mission:
    """Mission template generated each round."""

    name: str
    mission_type: MissionType
    difficulty: int
    requirements: Dict[Stat, int]
    threat_delta_on_fail: int
    rewards: Dict[str, int]
    description: str = ""

    def primary_requirement(self) -> Stat:
        return max(self.requirements, key=self.requirements.get)


@dataclass
class AgencyResources:
    """Resources tracked across rounds."""

    mana_stones: int = 0
    research_data: int = 0
    threat_level: int = 0
    city_safety: int = 100

    def apply_rewards(self, rewards: Dict[str, int]) -> None:
        self.mana_stones += rewards.get("mana_stones", 0)
        self.research_data += rewards.get("research_data", 0)
        self.city_safety = min(100, self.city_safety + rewards.get("city_safety", 0))

    def escalate_threat(self, amount: int) -> None:
        self.threat_level += amount
        self.city_safety = max(0, self.city_safety - amount // 2)


@dataclass
class MissionAssignment:
    mission: Mission
    team: List[MagicalGirl] = field(default_factory=list)

    def team_power(self) -> Dict[Stat, int]:
        totals: Dict[Stat, int] = {stat: 0 for stat in STAT_ORDER}
        for girl in self.team:
            for stat in STAT_ORDER:
                totals[stat] += girl.effective_stat(stat)
        return totals


@dataclass
class MissionResult:
    assignment: MissionAssignment
    success: bool
    xp_gain: int
    fatigue_cost: int
    threat_change: int
    rewards: Dict[str, int]


class GameState:
    """Lightweight container for the current run."""

    def __init__(self, roster: Iterable[MagicalGirl]):
        self.round: int = 1
        self.roster: List[MagicalGirl] = list(roster)
        self.resources = AgencyResources(mana_stones=10, research_data=0)
        self.pending_missions: List[Mission] = []

    def advance_round(self) -> None:
        self.round += 1
        for girl in self.roster:
            girl.rest()


class MissionDirector:
    """Handles mission generation and resolution logic."""

    def __init__(self, rng: Optional[random.Random] = None):
        self.rng = rng or random.Random()

    def generate_missions(self, difficulty: int = 1) -> List[Mission]:
        count = self.rng.randint(3, 5)
        missions: List[Mission] = []
        for _ in range(count):
            mission_type = self.rng.choice(list(MissionType))
            base_diff = difficulty + self.rng.randint(0, 2)
            requirements = {
                Stat.FORCE: 12 + base_diff * 2,
                Stat.WISDOM: 8 + base_diff,
                Stat.CHARISMA: 6 + base_diff,
                Stat.SPIRIT: 10,
            }
            rewards = {
                "mana_stones": self.rng.randint(2, 5),
                "research_data": self.rng.randint(1, 4),
            }
            if mission_type is MissionType.PUBLIC_RELATIONS:
                rewards["city_safety"] = 5
            name = f"{mission_type.value} Lv.{base_diff}"
            missions.append(
                Mission(
                    name=name,
                    mission_type=mission_type,
                    difficulty=base_diff,
                    requirements=requirements,
                    threat_delta_on_fail=5 + base_diff * 3,
                    rewards=rewards,
                    description="TODO: Write flavorful mission text.",
                )
            )
        return missions

    def resolve(self, assignment: MissionAssignment) -> MissionResult:
        team_power = assignment.team_power()
        difficulty = assignment.mission.difficulty
        success_margin = 0
        for stat, requirement in assignment.mission.requirements.items():
            success_margin += team_power.get(stat, 0) - requirement
        spirit = team_power.get(Stat.SPIRIT, 0)
        success_threshold = difficulty * 10
        success_chance = max(5, min(95, 50 + success_margin + spirit // 5))
        roll = self.rng.randint(1, 100)
        success = roll <= success_chance
        xp_gain = 5 + difficulty * 2
        fatigue_cost = 10 + difficulty * 3
        threat_change = 0
        rewards: Dict[str, int] = {}
        if success:
            rewards = assignment.mission.rewards
        else:
            threat_change = assignment.mission.threat_delta_on_fail
        return MissionResult(
            assignment=assignment,
            success=success,
            xp_gain=xp_gain,
            fatigue_cost=fatigue_cost,
            threat_change=threat_change,
            rewards=rewards,
        )


class GameController:
    """High-level coordinator between state, missions, and player actions."""

    def __init__(self, state: GameState, director: MissionDirector):
        self.state = state
        self.director = director

    def start_round(self) -> None:
        difficulty = 1 + (self.state.round - 1) // 3
        self.state.pending_missions = self.director.generate_missions(difficulty)

    def assign_team(self, mission: Mission, team: Iterable[MagicalGirl]) -> MissionAssignment:
        assignment = MissionAssignment(mission=mission, team=list(team))
        for girl in assignment.team:
            girl.apply_mission_fatigue(mission.difficulty * 5)
        return assignment

    def resolve_assignment(self, assignment: MissionAssignment) -> MissionResult:
        result = self.director.resolve(assignment)
        for girl in assignment.team:
            girl.gain_experience(result.xp_gain)
            girl.apply_mission_fatigue(result.fatigue_cost)
        if result.success:
            self.state.resources.apply_rewards(result.rewards)
        else:
            self.state.resources.escalate_threat(result.threat_change)
        return result

    def end_round(self) -> None:
        urgent = [m for m in self.state.pending_missions if m.mission_type in {
            MissionType.GATE_SCOUT,
            MissionType.GATE_ASSAULT,
            MissionType.GATE_SEAL,
        }]
        for mission in urgent:
            self.state.resources.escalate_threat(mission.threat_delta_on_fail)
        self.state.pending_missions.clear()
        self.state.advance_round()


def recruit_sample_roster() -> List[MagicalGirl]:
    """Create a few placeholder magical girls for testing the skeleton."""

    return [
        MagicalGirl(
            name="하늘의 루나",
            codename="Luna",
            stats={
                Stat.FORCE: 16,
                Stat.WISDOM: 11,
                Stat.CHARISMA: 10,
                Stat.SPIRIT: 14,
            },
            rarity=4,
        ),
        MagicalGirl(
            name="별빛의 아리",
            codename="Ari",
            stats={
                Stat.FORCE: 12,
                Stat.WISDOM: 15,
                Stat.CHARISMA: 13,
                Stat.SPIRIT: 12,
            },
        ),
        MagicalGirl(
            name="도시의 미카",
            codename="Mika",
            stats={
                Stat.FORCE: 10,
                Stat.WISDOM: 9,
                Stat.CHARISMA: 16,
                Stat.SPIRIT: 11,
            },
        ),
    ]


def demo_round() -> None:
    """Run a text-based demo round to validate the skeleton flow."""

    state = GameState(recruit_sample_roster())
    director = MissionDirector(random.Random(1337))
    controller = GameController(state, director)

    controller.start_round()
    print(f"Round {state.round} Missions:")
    for index, mission in enumerate(state.pending_missions, start=1):
        print(f"  {index}. {mission.name} -> requires {mission.requirements}")

    if state.pending_missions:
        assignment = controller.assign_team(
            state.pending_missions[0],
            team=state.roster[:2],
        )
        result = controller.resolve_assignment(assignment)
        print(f"\nMission result: {'SUCCESS' if result.success else 'FAILURE'}")
        print(f"Resources: {state.resources}")

    controller.end_round()
    print(f"Threat level after round {state.round}: {state.resources.threat_level}")



class mainScene(Scene):
    def initOnce(self):
        return
    def init(self):
        return
    def update(self):
        return
    def draw(self):
        return


class defaultScene(Scene):
    def initOnce(self):
        return
    def init(self):
        return
    def update(self):
        return
    def draw(self):
        return

class Scenes:
    mainScene = mainScene()


if __name__=="__main__":
    #Screen Setting
    window = REMOGame(window_resolution=(1920,1080),screen_size=(2560,1440),fullscreen=False,caption="DEFAULT")
    window.setCurrentScene(Scenes.mainScene)
    window.run()

    # Done! Time to quit.
