from REMOLib import *
from dataclasses import dataclass
import pygame




@dataclass
class Girl:
    """마법소녀 단일 엔티티. 컨트롤러 없이도 단독 동작하도록 유틸을 내장."""
    id: int
    name: str
    rarity: str

    # 성장 상태
    lv: int = 1
    xp: int = 0

    # 능력치
    Force: int = 10  # 힘(전투/괴이대응/방호/퇴마 가중)
    Wisdom: int = 10  # 마력(연구/의식/정화)
    Charm: int = 10  # 매력(시민교류/외교/공연)
    Spirit: int = 10  # 의지(피로/사기/사건 내성)

    # 컨디션
    fatigue: int = 0    # 0~120
    morale: int  = 100  # 0~120


#게임 오브젝트들을 선언하는 곳입니다.
class Obj:
    None

# Demo data: 게임 시작 시 표시할 샘플 마법소녀 목록
GIRLS: list[Girl] = [
    Girl(id=1, name="하나", rarity="3", lv=5, Force=12, Wisdom=11, Charm=14, Spirit=9, fatigue=10, morale=95),
    Girl(id=2, name="유이", rarity="4", lv=8, Force=15, Wisdom=16, Charm=12, Spirit=13, fatigue=22, morale=88),
    Girl(id=3, name="미나", rarity="2", lv=3, Force=9, Wisdom=10, Charm=11, Spirit=10, fatigue=5, morale=100),
]

class GirlListScene(Scene):
    def initOnce(self):
        self.title = textObj("마법소녀 일람", pos=(80, 60), size=36, color=Cs.yellow)
        self.items = []
        return
    def init(self):
        self.items.clear()
        x, y = 100, 120
        line_h = 32
        for g in GIRLS:
            line = f"[{g.id:03}] {g.name}  (★{g.rarity})  LV {g.lv}  F:{g.Force} W:{g.Wisdom} C:{g.Charm} S:{g.Spirit}  피로:{g.fatigue} 사기:{g.morale}"
            self.items.append(textObj(line, pos=(x, y), size=24, color=Cs.white))
            y += line_h
        return
    def update(self):
        if Rs.userJustPressed(pygame.K_ESCAPE) or Rs.userJustPressed(pygame.K_BACKSPACE):
            Rs.setCurrentScene(Scenes.mainScene)
        return
    def draw(self):
        self.title.draw()
        for t in self.items:
            t.draw()
        return

class mainScene(Scene):
    def initOnce(self):
        return
    def init(self):
        return
    def update(self):
        if Rs.userJustPressed(pygame.K_g):
            Rs.setCurrentScene(Scenes.girlList)
        return
    def draw(self):
        hint1 = textObj("G: 마법소녀 일람 열기", pos=(80, 80), size=28, color=Cs.white)
        hint2 = textObj("ESC/BACK: 돌아가기", pos=(80, 116), size=20, color=Cs.gray)
        hint1.draw()
        hint2.draw()
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
    girlList = GirlListScene()


if __name__=="__main__":
    #Screen Setting
    window = REMOGame(window_resolution=(1920,1080),screen_size=(2560,1440),fullscreen=False,caption="DEFAULT")
    window.setCurrentScene(Scenes.mainScene)
    window.run()

    # Done! Time to quit.
