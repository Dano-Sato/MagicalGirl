from REMOLib import *




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
