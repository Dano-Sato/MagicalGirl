from __future__ import annotations

"""Prototype scaffolding for a contract-driven magical girl agency sim.

The goal of this module is to provide a pure-Python gameplay core that can be
hooked into either a command line interface or a graphical layer later.  The
focus is on:

* Recruit & train magical girls through a gacha style system.
* Generate 3~5 missions every round and dispatch teams while managing fatigue.
* Earn resources (mana stones & research data) to further strengthen the
  roster, invest in facilities, and keep the city's threat level under
  control.

The rendering layer (``REMOGame``) is intentionally left untouched so that the
logic can be iterated on quickly before wiring the UI.
"""

import enum
import random
from dataclasses import dataclass, field
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

import pygame

from REMOLib import *


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
    awakened: bool = False

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

    def awaken(self) -> None:
        """One-off upgrade triggered by certain facilities or events."""

        if not self.awakened:
            for stat in (Stat.FORCE, Stat.WISDOM, Stat.CHARISMA):
                self.stats[stat] = int(self.stats.get(stat, 0) * 1.15) + 1
            self.awakened = True


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

    def spend(self, mana: int = 0, research: int = 0) -> bool:
        if self.mana_stones < mana or self.research_data < research:
            return False
        self.mana_stones -= mana
        self.research_data -= research
        return True


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


@dataclass
class Facility:
    """Simple representation of a base upgrade unlocked with research."""

    name: str
    research_cost: int
    upkeep_mana: int
    effect: Callable[[GameState], None]
    acquired: bool = False


class FacilityManager:
    """Tracks which facilities are available and unlocked."""

    def __init__(self, facilities: Iterable[Facility]):
        self.facilities: List[Facility] = list(facilities)

    def available_upgrades(self) -> List[Facility]:
        return [facility for facility in self.facilities if not facility.acquired]

    def purchase(self, facility: Facility, state: GameState) -> bool:
        if facility.acquired:
            return False
        if not state.resources.spend(mana=facility.upkeep_mana, research=facility.research_cost):
            return False
        facility.acquired = True
        facility.effect(state)
        return True


class GachaPool:
    """Very small helper that consumes mana stones to recruit girls."""

    def __init__(self, banner: Sequence[Tuple[MagicalGirl, float]]):
        total = sum(weight for _, weight in banner)
        self.banner: List[Tuple[MagicalGirl, float]] = [
            (girl, weight / total) for girl, weight in banner
        ]

    def pull(self, rng: random.Random, mana_cost: int, resources: AgencyResources) -> Optional[MagicalGirl]:
        if not resources.spend(mana=mana_cost):
            return None
        roll = rng.random()
        cumulative = 0.0
        for template, weight in self.banner:
            cumulative += weight
            if roll <= cumulative:
                # Return a lightweight copy so training does not mutate the template.
                return MagicalGirl(
                    name=template.name,
                    codename=template.codename,
                    stats=dict(template.stats),
                    rarity=template.rarity,
                    level=template.level,
                )
        return None


class GameState:
    """Lightweight container for the current run."""

    def __init__(self, roster: Iterable[MagicalGirl]):
        self.round: int = 1
        self.roster: List[MagicalGirl] = list(roster)
        self.resources = AgencyResources(mana_stones=10, research_data=0)
        self.pending_missions: List[Mission] = []
        self.facility_manager = FacilityManager(create_default_facilities())
        self.gacha_pool = GachaPool(create_default_banner())

    def advance_round(self) -> None:
        self.round += 1
        for girl in self.roster:
            girl.rest()
        # passive threat decay to reward proactive play
        if self.resources.threat_level > 0:
            self.resources.threat_level = max(0, self.resources.threat_level - 2)


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
            if mission_type in {MissionType.GATE_SCOUT, MissionType.GATE_ASSAULT, MissionType.GATE_SEAL}:
                requirements[Stat.FORCE] += 2
                requirements[Stat.SPIRIT] += 3
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

    # --- Agency actions -------------------------------------------------

    def rest_unassigned(self, assigned: Iterable[MagicalGirl]) -> None:
        assigned_ids = {id(girl) for girl in assigned}
        for girl in self.state.roster:
            if id(girl) not in assigned_ids:
                girl.rest()

    def invest_in_facility(self, facility: Facility) -> bool:
        return self.state.facility_manager.purchase(facility, self.state)

    def perform_gacha(self, mana_cost: int = 5) -> Optional[MagicalGirl]:
        recruit = self.state.gacha_pool.pull(self.director.rng, mana_cost, self.state.resources)
        if recruit:
            self.state.roster.append(recruit)
        return recruit

    def auto_assign(self) -> List[MissionAssignment]:
        assignments: List[MissionAssignment] = []
        available_girls = sorted(self.state.roster, key=lambda g: g.fatigue)
        for mission in self.state.pending_missions:
            needed = 2 if mission.difficulty <= 2 else 3
            team: List[MagicalGirl] = []
            pool = [girl for girl in available_girls if girl.fatigue < 90]
            pool.sort(key=lambda girl: girl.effective_stat(mission.primary_requirement()), reverse=True)
            for girl in pool[:needed]:
                team.append(girl)
                available_girls.remove(girl)
            if team:
                assignments.append(MissionAssignment(mission, team))
        return assignments


def create_default_banner() -> List[Tuple[MagicalGirl, float]]:
    return [
        (
            MagicalGirl(
                name="폭풍의 유나",
                codename="Tempest",
                stats={
                    Stat.FORCE: 15,
                    Stat.WISDOM: 10,
                    Stat.CHARISMA: 9,
                    Stat.SPIRIT: 12,
                },
                rarity=4,
            ),
            1.0,
        ),
        (
            MagicalGirl(
                name="은빛의 리에",
                codename="Lierre",
                stats={
                    Stat.FORCE: 11,
                    Stat.WISDOM: 15,
                    Stat.CHARISMA: 11,
                    Stat.SPIRIT: 13,
                },
                rarity=5,
            ),
            0.6,
        ),
        (
            MagicalGirl(
                name="무대의 소라",
                codename="Stage",
                stats={
                    Stat.FORCE: 9,
                    Stat.WISDOM: 10,
                    Stat.CHARISMA: 17,
                    Stat.SPIRIT: 11,
                },
                rarity=3,
            ),
            1.4,
        ),
    ]


def create_default_facilities() -> List[Facility]:
    def training_hall(state: GameState) -> None:
        for girl in state.roster:
            girl.stats[Stat.FORCE] += 1
            girl.stats[Stat.SPIRIT] += 1

    def meditation_garden(state: GameState) -> None:
        for girl in state.roster:
            girl.morale = min(120, girl.morale + 10)

    def arcane_laboratory(state: GameState) -> None:
        for girl in state.roster:
            if girl.rarity >= 4:
                girl.awaken()

    return [
        Facility("전술 훈련장", research_cost=5, upkeep_mana=2, effect=training_hall),
        Facility("명상의 정원", research_cost=6, upkeep_mana=1, effect=meditation_garden),
        Facility("비전 실험실", research_cost=12, upkeep_mana=3, effect=arcane_laboratory),
    ]


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


def demo_round(rounds: int = 3) -> None:
    """Run a small auto-play session to validate the prototype flow."""

    state = GameState(recruit_sample_roster())
    director = MissionDirector(random.Random(1337))
    controller = GameController(state, director)

    for _ in range(rounds):
        controller.start_round()
        print(f"\n==== Round {state.round} ====")
        for mission in state.pending_missions:
            print(
                f"- {mission.name} [{mission.mission_type.value}] | diff {mission.difficulty} | "
                f"threat fail +{mission.threat_delta_on_fail}"
            )
        assignments = controller.auto_assign()
        for assignment in assignments:
            result = controller.resolve_assignment(assignment)
            members = ", ".join(girl.codename for girl in assignment.team)
            print(
                f"Mission '{assignment.mission.name}' by [{members}] -> "
                f"{'SUCCESS' if result.success else 'FAIL'}"
            )
        if not assignments:
            print("No suitable team could be formed this round!")
        controller.end_round()
        print(
            f"Resources: mana={state.resources.mana_stones}, research={state.resources.research_data}, "
            f"threat={state.resources.threat_level}, city={state.resources.city_safety}"
        )



class mainScene(Scene):
    """Simple REMO scene that visualises the strategy prototype."""

    LOG_LIMIT = 12

    def initOnce(self):
        self.state = GameState(recruit_sample_roster())
        self.director = MissionDirector(random.Random(1337))
        self.controller = GameController(self.state, self.director)

        self.log_messages: List[str] = []
        self.mission_cards: List[rectObj] = []
        self.roster_cards: List[rectObj] = []
        self.buttons: List[textButton] = []
        self.drawables: List[graphicObj] = []

        self.controller.start_round()
        self._build_ui()
        self._refresh_all()

    def init(self):
        # Scene swap entry point (no-op for now)
        return

    # ------------------------------------------------------------------
    # UI setup helpers
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        screen_w, screen_h = Rs.screen_size
        base_color = Cs.hexColor("101421")

        self.background = rectObj(
            pygame.Rect(0, 0, screen_w, screen_h), radius=0, color=base_color
        )

        self.title = textObj(
            "마법소녀 관할국",
            pos=RPoint(70, 40),
            font="unifont_script.ttf",
            size=56,
            color=Cs.white,
        )

        self.resource_panel = rectObj(
            pygame.Rect(60, 120, 820, 180),
            radius=26,
            color=Cs.hexColor("1c2336"),
        )
        self.round_text = textObj(
            "",
            pos=RPoint(32, 30),
            font="unifont_script.ttf",
            size=42,
            color=Cs.white,
        )
        self.round_text.setParent(self.resource_panel)
        self.resource_text = longTextObj(
            "",
            pos=RPoint(32, 100),
            font="unifont_script.ttf",
            size=28,
            color=Cs.grey75,
            textWidth=760,
        )
        self.resource_text.setParent(self.resource_panel)

        self.mission_header = textObj(
            "",
            pos=RPoint(60, 330),
            font="unifont_script.ttf",
            size=38,
            color=Cs.white,
        )
        self.mission_layout = layoutObj(
            pygame.Rect(60, 380, 960, 0),
            spacing=18,
            childs=[],
            isVertical=True,
        )

        self.roster_header = textObj(
            "",
            pos=RPoint(1120, 120),
            font="unifont_script.ttf",
            size=38,
            color=Cs.white,
        )
        self.roster_layout = layoutObj(
            pygame.Rect(1120, 170, 620, 0),
            spacing=14,
            childs=[],
            isVertical=True,
        )

        self.actions_panel = rectObj(
            pygame.Rect(1800, 120, 640, 400),
            radius=26,
            color=Cs.hexColor("1c2336"),
        )
        self.actions_title = textObj(
            "작전 지시",
            pos=RPoint(32, 28),
            font="unifont_script.ttf",
            size=34,
            color=Cs.white,
        )
        self.actions_title.setParent(self.actions_panel)

        button_specs = [
            ("자동 배치", self._auto_assign_and_resolve),
            ("라운드 종료", self._end_round_and_refresh),
            ("마력석 소환", self._perform_gacha),
            ("시설 투자", self._invest_in_facility),
        ]

        self.button_layout = layoutObj(
            pygame.Rect(0, 0, 0, 0), spacing=20, childs=[], isVertical=True
        )
        self.button_layout.pos = RPoint(32, 90)
        self.button_layout.setParent(self.actions_panel)

        for label, callback in button_specs:
            button = textButton(
                label,
                pygame.Rect(0, 0, 520, 72),
                radius=18,
                color=Cs.hexColor("28324a"),
                textColor=Cs.white,
            )
            button.setParent(self.button_layout)
            button.connect(callback)
            self.buttons.append(button)

        self.facility_status = longTextObj(
            "",
            pos=RPoint(32, 320),
            font="unifont_script.ttf",
            size=24,
            color=Cs.grey75,
            textWidth=560,
        )
        self.facility_status.setParent(self.actions_panel)

        self.log_panel = rectObj(
            pygame.Rect(60, 940, 2380, 380),
            radius=26,
            color=Cs.hexColor("151b2a"),
        )
        self.log_title = textObj(
            "상황 로그",
            pos=RPoint(32, 28),
            font="unifont_script.ttf",
            size=34,
            color=Cs.white,
        )
        self.log_title.setParent(self.log_panel)
        self.log_text = longTextObj(
            "",
            pos=RPoint(32, 96),
            font="unifont_script.ttf",
            size=26,
            color=Cs.grey75,
            textWidth=2300,
        )
        self.log_text.setParent(self.log_panel)

        self.drawables = [
            self.background,
            self.resource_panel,
            self.mission_layout,
            self.roster_layout,
            self.actions_panel,
            self.log_panel,
            self.title,
            self.mission_header,
            self.roster_header,
        ]

    def _refresh_all(self) -> None:
        self._refresh_resources()
        self._refresh_missions()
        self._refresh_roster()
        self._refresh_facility_status()

    def _refresh_resources(self) -> None:
        res = self.state.resources
        self.round_text.text = f"라운드 {self.state.round}"
        self.resource_text.text = (
            f"마력석 {res.mana_stones}개  |  연구데이터 {res.research_data}점\n"
            f"위협도 {res.threat_level}  |  도시 안정도 {res.city_safety}"
        )
        gacha_button, facility_button = self.buttons[2], self.buttons[3]
        if res.mana_stones >= 5:
            gacha_button.enabled = True
            gacha_button.showChilds(0)
        else:
            gacha_button.enabled = False
            gacha_button.hideChilds(0)

        if self.state.facility_manager.available_upgrades():
            facility_button.enabled = True
            facility_button.showChilds(0)
        else:
            facility_button.enabled = False
            facility_button.hideChilds(0)

    def _refresh_missions(self) -> None:
        for card in self.mission_cards:
            card.setParent(None)
        self.mission_cards.clear()

        total = len(self.state.pending_missions)
        urgent = sum(
            1
            for mission in self.state.pending_missions
            if mission.mission_type
            in {MissionType.GATE_SCOUT, MissionType.GATE_ASSAULT, MissionType.GATE_SEAL}
        )
        self.mission_header.text = f"대기 중 임무 {total}건 (게이트 {urgent}건)"

        for mission in self.state.pending_missions:
            card = self._create_mission_card(mission)
            card.setParent(self.mission_layout)
            self.mission_cards.append(card)

    def _refresh_roster(self) -> None:
        for card in self.roster_cards:
            card.setParent(None)
        self.roster_cards.clear()

        self.roster_header.text = f"계약 소녀 {len(self.state.roster)}명"
        for girl in sorted(self.state.roster, key=lambda g: g.codename):
            card = self._create_roster_card(girl)
            card.setParent(self.roster_layout)
            self.roster_cards.append(card)

    def _refresh_facility_status(self) -> None:
        facilities = self.state.facility_manager.facilities
        active = [facility.name for facility in facilities if facility.acquired]
        if active:
            summary = "가동 중 시설: " + ", ".join(active)
        else:
            summary = "가동 중 시설 없음"

        upcoming = [facility for facility in facilities if not facility.acquired]
        if upcoming:
            next_name = upcoming[0].name
            summary += f"\n다음 투자 후보: {next_name}"
        else:
            summary += "\n모든 시설을 해금했습니다!"
        self.facility_status.text = summary

    def _create_mission_card(self, mission: Mission) -> rectObj:
        card = rectObj(
            pygame.Rect(0, 0, 920, 180),
            radius=22,
            color=Cs.hexColor("1b2334"),
        )
        title = textObj(
            f"{mission.name}",
            pos=RPoint(28, 24),
            font="unifont_script.ttf",
            size=34,
            color=Cs.white,
        )
        title.setParent(card)
        subtitle = textObj(
            f"유형: {mission.mission_type.value} | 위험도 +{mission.threat_delta_on_fail}",
            pos=RPoint(28, 72),
            font="unifont_script.ttf",
            size=24,
            color=Cs.grey75,
        )
        subtitle.setParent(card)
        req_lines = [
            f"{stat.value}: {value}"
            for stat, value in mission.requirements.items()
        ]
        req_text = textObj(
            " / ".join(req_lines),
            pos=RPoint(28, 118),
            font="unifont_script.ttf",
            size=24,
            color=Cs.grey75,
        )
        req_text.setParent(card)
        reward_text = textObj(
            self._format_rewards(mission.rewards),
            pos=RPoint(28, 146),
            font="unifont_script.ttf",
            size=24,
            color=Cs.tiffanyBlue,
        )
        reward_text.setParent(card)
        return card

    def _create_roster_card(self, girl: MagicalGirl) -> rectObj:
        card = rectObj(
            pygame.Rect(0, 0, 580, 150),
            radius=20,
            color=Cs.hexColor("1b2334"),
        )
        title = textObj(
            f"{girl.name} ({girl.codename})", 
            pos=RPoint(24, 20),
            font="unifont_script.ttf",
            size=30,
            color=Cs.white,
        )
        title.setParent(card)

        stats = (
            f"힘 {girl.stats.get(Stat.FORCE, 0)}  |  마력 {girl.stats.get(Stat.WISDOM, 0)}  |  "
            f"매력 {girl.stats.get(Stat.CHARISMA, 0)}  |  의지 {girl.stats.get(Stat.SPIRIT, 0)}"
        )
        stats_text = textObj(
            stats,
            pos=RPoint(24, 66),
            font="unifont_script.ttf",
            size=24,
            color=Cs.grey75,
        )
        stats_text.setParent(card)

        status = (
            f"레벨 {girl.level}  |  피로 {girl.fatigue}  |  사기 {girl.morale}  |  유대 {girl.bonds}"
        )
        status_text = textObj(
            status,
            pos=RPoint(24, 104),
            font="unifont_script.ttf",
            size=24,
            color=Cs.grey75,
        )
        status_text.setParent(card)

        if girl.awakened:
            awakened_text = textObj(
                "각성 완료",
                pos=RPoint(24, 124),
                font="unifont_script.ttf",
                size=22,
                color=Cs.tiffanyBlue,
            )
            awakened_text.setParent(card)
        return card

    # ------------------------------------------------------------------
    # Button callbacks
    # ------------------------------------------------------------------
    def _auto_assign_and_resolve(self) -> None:
        if not self.state.pending_missions:
            self._append_log("남은 임무가 없습니다.")
            return

        assignments = self.controller.auto_assign()
        if not assignments:
            self._append_log("투입 가능한 팀이 없습니다!")
            return

        resolved = []
        for assignment in assignments:
            result = self.controller.resolve_assignment(assignment)
            resolved.append(assignment.mission)
            members = ", ".join(girl.codename for girl in assignment.team)
            if result.success:
                reward_summary = self._format_rewards(result.rewards)
                self._append_log(
                    f"{assignment.mission.name} 성공! 팀[{members}] 보상: {reward_summary}"
                )
            else:
                self._append_log(
                    f"{assignment.mission.name} 실패... 위협도 +{result.threat_change}"
                )

        self.state.pending_missions = [
            mission
            for mission in self.state.pending_missions
            if mission not in resolved
        ]

        self._refresh_resources()
        self._refresh_missions()
        self._refresh_roster()

    def _end_round_and_refresh(self) -> None:
        self.controller.end_round()
        self.controller.start_round()
        self._append_log(f"라운드 {self.state.round} 시작! 새로운 임무가 도착했습니다.")
        self._refresh_all()

    def _perform_gacha(self) -> None:
        recruit = self.controller.perform_gacha(mana_cost=5)
        if recruit:
            self._append_log(
                f"{recruit.name}({recruit.codename}) 영입! 희귀도 ★{recruit.rarity}"
            )
            self._refresh_roster()
        else:
            self._append_log("마력석이 부족해 소환에 실패했습니다.")
        self._refresh_resources()

    def _invest_in_facility(self) -> None:
        available = self.state.facility_manager.available_upgrades()
        if not available:
            self._append_log("모든 시설을 이미 확보했습니다.")
            return

        facility = available[0]
        if self.controller.invest_in_facility(facility):
            self._append_log(f"{facility.name} 가동! 전력이 향상되었습니다.")
            self._refresh_roster()
            self._refresh_facility_status()
        else:
            self._append_log("자원이 부족해 시설을 건설할 수 없습니다.")
        self._refresh_resources()

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------
    def _format_rewards(self, rewards: Dict[str, int]) -> str:
        if not rewards:
            return "보상 없음"
        parts = []
        for key, value in rewards.items():
            label = {
                "mana_stones": "마력석",
                "research_data": "연구데이터",
                "city_safety": "도시 안정도",
            }.get(key, key)
            parts.append(f"{label} +{value}")
        return ", ".join(parts)

    def _append_log(self, message: str) -> None:
        self.log_messages.append(message)
        self.log_messages = self.log_messages[-self.LOG_LIMIT :]
        self.log_text.text = "\n".join(self.log_messages)

    # ------------------------------------------------------------------
    # Scene loop
    # ------------------------------------------------------------------
    def update(self):
        for button in self.buttons:
            button.update()
        self.button_layout.update()
        self.mission_layout.update()
        self.roster_layout.update()

    def draw(self):
        for drawable in self.drawables:
            drawable.draw()
        for button in self.buttons:
            button.draw()


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
    # Quick smoke test of the backend logic when run directly.
    demo_round(rounds=2)

    #Screen Setting
    window = REMOGame(window_resolution=(1920,1080),screen_size=(2560,1440),fullscreen=False,caption="DEFAULT")
    window.setCurrentScene(Scenes.mainScene)
    window.run()

    # Done! Time to quit.
