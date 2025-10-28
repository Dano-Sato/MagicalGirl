import pygame,math,typing,random
import numpy as np
from abc import ABC
import multiprocessing as mp
from multiprocessing import Process
import threading
import time
import queue
from collections import defaultdict, Counter, deque
from dataclasses import dataclass, field
from enum import Enum, auto

'''
REMO Library의 기본 요소들을 정의하는 모듈입니다.
'''

## Idea from Pyside2.QPoint
## includes all of the method of QPoint + additional methods
## 2-Dimensional (x,y) Point
class RPoint():
    '''
    2차원 좌표를 나타내는 클래스\n
    x,y : 좌표값\n
    toTuple() : 튜플로 변환\n
    '''
    def __init__(self,x=(0,0),y=None):
        if y is None:
            self.__x, self.__y = map(int, x)
        else:
            self.__x, self.__y = int(x), int(y)

    @property            
    def x(self) -> int:
        return self.__x
    @property
    def y(self) -> int:
        return self.__y

    @x.setter    
    def x(self,x:int):
        self.__x = x
    @y.setter
    def y(self,x:int):
        self.__y = x
    
    def __add__(self,p2):
        if type(p2) != RPoint:
            p2 = RPoint(p2)
        return RPoint(self.x+p2.x,self.y+p2.y)
    # 후열 덧셈 연산자
    def __radd__(self, p2):
        return self.__add__(p2)        
    def __sub__(self,p2):
        if type(p2) != RPoint:
            p2 = RPoint(p2)
        return RPoint(self.x-p2.x,self.y-p2.y)
    # 후열 뺄셈 연산자
    def __rsub__(self, p2):
        if type(p2) != RPoint:
            p2 = RPoint(p2)
        return RPoint(p2.x - self.x, p2.y - self.y)    

    ##음수 연산자
    def __neg__(self):
        return RPoint(-self.x, -self.y)

    def __mul__(self,m):
        return RPoint(int(self.x*m),int(self.y*m))
    def __rmul__(self,m):
        return self.__mul__(m)
    def __truediv__(self,m):
        return RPoint(int(self.x/m),int(self.y/m))
    def __floordiv__(self,m):
        return self/m 
    def __eq__(self,p2):
        if type(p2) != RPoint:
            return False
        if self.x==p2.x and self.y==p2.y:
            return True
        return False
    
    def toTuple(self) -> typing.Tuple[int,int]:
        return (self.__x,self.__y)
    def transposed(self):
        return RPoint(self.y,self.x)
            
    def __repr__(self):
        return "REMOGame.RPoint({0},{1})".format(self.x,self.y)
    
    
    ##2차원 거리 출력
    def distance(self,p2) -> float:
        return math.dist(self.toTuple(),p2.toTuple())
    ## 포인트 p2로 speed값만큼 이동한 결과를 반환한다. 
    def moveTo(self,p2,speed=None,*,smoothness=5):
        '''
        p2로 이동하는 함수\n
        speed : 이동속도\n
        smoothness : 이동의 매끄러움을 조절하는 값으로, 거리가 멀면 더 빠르게, 가까우면 더 느리게 이동하는 효과를 줍니다. 더 큰 값일수록 속도가 부드럽게 증가합니다.\n
        '''
        d = self.distance(p2)
        if speed==None: #스피드를 정하지 않을경우, 거리에 비례하는 속도로 정해진다
            speed=max(d/smoothness,2)
        if d <= speed:
            return p2 ##도달
        else:
            result = self
            delta = p2-self
            delta *= (speed/d)
            result += delta
        return result



class RTimer:
    '''
    타이머 클래스\n
    정해진 시간이 지나면 True를 반환한다.\n
    '''
    def __init__(self, duration, startNow=True):
        """
        :param duration: 타이머의 기간(밀리초 단위)
        :param start_now: 즉시 타이머를 시작할지 여부
        """
        self.duration = duration
        self.startTime = pygame.time.get_ticks() if startNow else None

    def start(self, duration=None):
        """타이머를 시작합니다."""
        if duration:
            self.duration = duration
        self.startTime = pygame.time.get_ticks()

    def end(self):
        """
        타이머를 종료합니다.
        """
        self.startTime = pygame.time.get_ticks() - self.duration

    def reset(self):
        """타이머를 리셋하고 다시 시작합니다."""
        self.start()

    def stop(self):
        """타이머를 중지합니다."""
        self.startTime = None

    def isOver(self):
        """타이머가 완료되었는지 확인합니다."""
        if self.startTime is None:
            return False
        return pygame.time.get_ticks() - self.startTime >= self.duration
    
    def isRunning(self):
        '''타이머가 활성화되어 있는지 확인합니다.'''
        if self.startTime is None:
            return False
        return True

    def timeLeft(self):
        """남은 시간을 반환합니다. (밀리초 단위)"""
        if self.startTime is None:
            return self.duration
        elapsed = pygame.time.get_ticks() - self.startTime
        return max(0, self.duration - elapsed)

    def timeElapsed(self):
        """경과된 시간을 반환합니다. (밀리초 단위)"""
        if self.startTime is None:
            return 0
        return pygame.time.get_ticks() - self.startTime


class safeInt:
    bigNumber = 2147483648
    '''
    안전한 정수형 클래스입니다.
    실제 값을 저장하지 않으며 getter에서만 반환됩니다.
    '''

    def __makeOffset(self):
        return random.randint(-safeInt.bigNumber,safeInt.bigNumber)

    def __init__(self,value:int):
        self.__m = self.__makeOffset()
        self.__n = int(value) - self.__m

    @property
    def value(self):
        return self.__m + self.__n
    
    @value.setter
    def value(self,value):
        self.__m = self.__makeOffset()
        self.__n = int(value) - self.__m

    def __add__(self,other):
        return safeInt(self.value+int(other))
    def __sub__(self,other):
        return safeInt(self.value-int(other))
    def __mul__(self,other):
        return safeInt(self.value*int(other))
    def __truediv__(self,other):
        return safeInt(self.value//int(other))
    def __str__(self):
        return str(self.value)
    def __int__(self):
        return self.value
    def __float__(self):
        return float(self.value)
    def __repr__(self) -> str:
        return "safeInt({0})".format(str(self.value))

    # Comparison operators
    def __eq__(self, other):
        return self.value == other
    
    def __ne__(self, other):
        return self.value != other
    
    def __lt__(self, other):
        return self.value < other
    
    def __le__(self, other):
        return self.value <= other
    
    def __gt__(self, other):
        return self.value > other
    
    def __ge__(self, other):
        return self.value >= other


class Scene(ABC):

    def __init__(self):
        self.initiated=False
        return
    def _init(self):
        if self.initiated==False:
            self.initOnce()
            self.initiated = True
        self.init()
        
    #Scene을 불러올 때마다 initiation 되는 메소드 부분 
    def init(self):
        return
    
    #Scene을 처음 불러올때만 initiation 되는 메소드
    def initOnce(self):
        return

    def update(self):
        #update childs
        #if child has update method, it updates child
        return
    def draw(self):
        #draw childs
        return



class EventHandler:
    def __init__(self):
        # 이벤트와 해당 이벤트에 연결된 리스너(함수)들을 저장하는 딕셔너리
        self.events = {}

    def addEvent(self, event_name, listener):
        """
        새로운 이벤트 리스너를 특정 이벤트에 추가합니다.
        
        Args:
            event_name: 이벤트의 이름 또는 키.
            listener: 이벤트가 발생할 때 호출될 함수(리스너).
        """
        # 이벤트 이름이 딕셔너리에 없을 경우, 빈 리스트로 초기화
        if event_name not in self.events:
            self.events[event_name] = []
        # 해당 이벤트에 리스너를 추가
        self.events[event_name].append(listener)

    def occurEvent(self, event_name, *args, **kwargs):
        """
        특정 이벤트가 발생했을 때 해당 이벤트에 등록된 모든 리스너를 호출합니다.
        
        Args:
            event_name: 발생한 이벤트의 이름.
            *args: 리스너에 전달될 위치 기반 인자들.
            **kwargs: 리스너에 전달될 키워드 기반 인자들.
        """
        # 이벤트가 존재할 경우, 등록된 모든 리스너를 호출
        if event_name in self.events:
            for listener in self.events[event_name]:
                # *args와 **kwargs를 통해 리스너 함수에 전달
                listener(*args, **kwargs)


class interpolateManager:
    __interpolablePipeline = {}
    __shownObjs = {}
    DEFAULT_STEPS = 50
    DEFAULT_FRAME_DURATION = 1000/60
    @classmethod
    def interpolate(cls, obj, attributes, ends, *, frameDuration=DEFAULT_FRAME_DURATION, steps=DEFAULT_STEPS, callback=lambda: None, interpolation=lambda x: x, revert=False, on_update=lambda: None, show=False):
        '''
        지정한 오브젝트의 속성을 서서히 변화시키는 함수입니다.
        obj: 변화시킬 오브젝트
        attributes: 변화시킬 속성 (문자열 또는 문자열 리스트)
        ends: 속성의 최종 값 (리스트 혹은 단일 스칼라, 벡터)
        frameDuration: 한 프레임당 지속 시간 (기본값: 1000/60 밀리초)
        steps: 변화시킬 단계 수 (기본값: 50)
        callback: 변화가 끝났을 때 호출할 함수 (기본값: 빈 함수)
        interpolation: 보간 함수 (기본값: 선형 보간)
        revert: True일 경우, 보간이 끝난 후 다시 되돌아갑니다. (역재생)
        on_update: 보간이 업데이트될 때마다 호출되는 함수
        show: 보간 중인 오브젝트를 화면에 표시할지 여부 (*False일 경우 명시적으로 draw() 호출 필요)
        '''
        # attributes가 리스트나 튜플이 아니면 리스트로 변환
        if not isinstance(attributes, (list, tuple)):
            attributes = [attributes]
            ends = [ends]
        
        t_s = np.linspace(0, 1, steps)
        insts = {
            attr: [cls.__interpolate(getattr(obj, attr), ends[i], t, interpolation) for t in t_s]
            for i, attr in enumerate(attributes)
        }

        # reset=True일 경우 insts를 뒤집어서 원상복구 추가
        if revert:
            for attr in insts:
                insts[attr].extend(insts[attr][::-1])  # 뒤집어서 리스트에 추가

        if show:
            cls.__shownObjs[id(obj)] = obj
      

        cls.__interpolablePipeline[id(obj)]={
            "obj": obj,
            "attributes": attributes,
            "ends": ends,
            "insts": insts,
            "timer": RTimer(frameDuration),
            "callback": callback,
            "interpolation": interpolation,
            "on_update": on_update,
            "show": show
        }
        return

    @classmethod
    def easein(cls, obj, attributes, ends, *, frameDuration=DEFAULT_FRAME_DURATION, steps=DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        cls.interpolate(obj, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, interpolation=lambda x: x**2.5, revert=revert, on_update=on_update, show=show)
        return

    @classmethod
    def easeout(cls, obj, attributes, ends, *, frameDuration=DEFAULT_FRAME_DURATION, steps=DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        cls.interpolate(obj, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, interpolation=lambda x: 1 - (1 - x)**2.5, revert=revert, on_update=on_update, show=show)
        return
    
    @classmethod
    def smooth(cls, obj, attributes, ends, *, frameDuration=DEFAULT_FRAME_DURATION, steps=DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        cls.interpolate(obj, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, interpolation=lambda t: t**3 * (t * (6 * t - 15) + 10), revert=revert, on_update=on_update, show=show)
        return

    @classmethod
    def jump(cls, obj, attributes, ends, *, frameDuration=DEFAULT_FRAME_DURATION, steps=DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        cls.interpolate(obj, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, interpolation=lambda t: 4 * t * (1-t), revert=revert, on_update=on_update, show=show)
        return

    @classmethod
    def bounce(cls, obj, attributes, ends, *, frameDuration=DEFAULT_FRAME_DURATION, steps=DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        cls.interpolate(obj, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, interpolation=cls.__bounce, revert=revert, on_update=on_update, show=show)
        return
    

    @classmethod
    def _update(cls):
        '''
        시간에 따른 보간을 업데이트합니다.
        '''
        keys_to_remove = []

        for obj_id, interpolable in cls.__interpolablePipeline.items():
            if interpolable["timer"].isOver():
                # 각 속성 업데이트
                for attr in interpolable["attributes"]:
                    setattr(interpolable["obj"], attr, interpolable["insts"][attr].pop(0))

                # on_update 함수를 실행하여 업데이트 이벤트 발생
                if interpolable["on_update"]:
                    interpolable["on_update"]()

                # 모든 insts가 완료되었는지 확인하고 callback 실행 후 제거
                if len(interpolable["insts"][interpolable["attributes"][0]]) == 0:
                    keys_to_remove.append(obj_id)  # 나중에 제거할 키 추적

                interpolable["timer"].reset()

        # 처리 후에 사전에서 키 제거
        for key in keys_to_remove:
            if cls.__interpolablePipeline[key]["callback"]:
                callback = cls.__interpolablePipeline[key]["callback"]
            else:
                callback = lambda: None

            if cls.__interpolablePipeline[key]["show"]:
                del cls.__shownObjs[key]
            del cls.__interpolablePipeline[key]
            callback() # 제거 후 콜백 실행
        return
    
    @classmethod
    def _draw(cls):
        '''
        보간 중인 오브젝트를 그립니다.
        '''
        for id in cls.__shownObjs:
            cls.__shownObjs[id].draw()
        return


    @classmethod
    def __interpolate(cls,a, b, t, interpolation=lambda x:x):
        """ a와 b 사이를 t만큼 보간하고, 벡터 혹은 스칼라 값을 처리합니다.
        :param a: 시작 값 또는 벡터
        :param b: 끝 값 또는 벡터
        :param t: 보간 계수 (0에서 1 사이)
        :param mode: 보간 모드 ('linear', 'exponential', 'bounce', 'elastic', 'quadratic')
        :param smoothness: 부드러움 조절 인자
        :return: 보간된 값 또는 벡터
        """

        # t 값이 범위를 넘지 않도록 클램핑
        t = np.clip(t, 0.0, 1.0)
        t = interpolation(t)
        # 벡터 또는 스칼라 보간 처리
        if isinstance(a, (list, tuple, np.ndarray)):
            a = np.array(a)
            b = np.array(b)
        return a + (b - a) * t
    
    @classmethod
    def __bounce(cls, t):
        """ 바운스 보간 (강도 조절 가능) """

        if t < 1 / 2.75:
            return (7.5625 * t * t)
        elif t < 2 / 2.75:
            t -= 1.5 / 2.75
            return (7.5625 * t * t + 0.75)
        elif t < 2.5 / 2.75:
            t -= 2.25 / 2.75
            return (7.5625 * t * t + 0.9375)
        else:
            t -= 2.625 / 2.75
            return (7.5625 * t * t + 0.984375)
        
    @classmethod
    def check_on_interpolation(cls,obj):
        '''
        해당 오브젝트가 보간 중인지 확인합니다.
        '''
        return id(obj) in cls.__interpolablePipeline 

    @classmethod
    def release(cls,obj):
        '''
        해당 오브젝트의 보간을 제거합니다.
        '''
        if cls.check_on_interpolation(obj):
            if cls.__interpolablePipeline[id(obj)]["show"]:
                del cls.__shownObjs[id(obj)]
            del cls.__interpolablePipeline[id(obj)]
        return

class interpolableObj:
    
     
    def easein(self, attributes, ends, *, frameDuration=interpolateManager.DEFAULT_FRAME_DURATION, steps=interpolateManager.DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        '''
        점점 가속되는 보간을 수행합니다.

        Args:
            attributes (list or str): 보간할 속성 리스트 (예: "pos", "scale" 등).
            ends (list or value): 보간 종료 시 속성들이 도달할 값.
            frameDuration (float, optional): 한 프레임의 지속 시간 (기본값: 1000/60 ms).
            steps (int, optional): 보간이 완료될 때까지의 단계 수 (기본값: 50).
            callback (function, optional): 보간 완료 후 호출되는 함수.
            revert (bool, optional): True일 경우 원래 상태로 복귀. (역재생)
            on_update (function, optional): 각 프레임마다 호출되는 함수.
            show: 보간 중인 오브젝트를 화면에 표시할지 여부 (*False일 경우 명시적으로 draw() 호출 필요)

        Returns:
            None
        '''

        interpolateManager.easein(self, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, revert=revert, on_update=on_update, show=show)
        return
    
    def easeout(self, attributes, ends, *, frameDuration=interpolateManager.DEFAULT_FRAME_DURATION, steps=interpolateManager.DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        '''
        점점 감속되는 보간을 수행합니다.

        Args:
            attributes (list or str): 보간할 속성 리스트 (예: "pos", "scale" 등).
            ends (list or value): 보간 종료 시 속성들이 도달할 값.
            frameDuration (float, optional): 한 프레임의 지속 시간 (기본값: 1000/60 ms).
            steps (int, optional): 보간이 완료될 때까지의 단계 수 (기본값: 50).
            callback (function, optional): 보간 완료 후 호출되는 함수.
            revert (bool, optional): True일 경우 원래 상태로 복귀. (역재생)
            on_update (function, optional): 각 프레임마다 호출되는 함수.
            show: 보간 중인 오브젝트를 화면에 표시할지 여부 (*False일 경우 명시적으로 draw() 호출 필요)

        Returns:
            None
        '''

        interpolateManager.easeout(self, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, revert=revert, on_update=on_update, show=show)
        return
    
    def smooth(self, attributes, ends, *, frameDuration=interpolateManager.DEFAULT_FRAME_DURATION, steps=interpolateManager.DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        '''
        시작과 끝이 부드러운 보간을 수행합니다.

        Args:
            attributes (list or str): 보간할 속성 리스트 (예: "pos", "scale" 등).
            ends (list or value): 보간 종료 시 속성들이 도달할 값.
            frameDuration (float, optional): 한 프레임의 지속 시간 (기본값: 1000/60 ms).
            steps (int, optional): 보간이 완료될 때까지의 단계 수 (기본값: 50).
            callback (function, optional): 보간 완료 후 호출되는 함수.
            revert (bool, optional): True일 경우 원래 상태로 복귀. (역재생)
            on_update (function, optional): 각 프레임마다 호출되는 함수.
            show: 보간 중인 오브젝트를 화면에 표시할지 여부 (*False일 경우 명시적으로 draw() 호출 필요)

        Returns:
            None
        '''

        interpolateManager.smooth(self, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, revert=revert, on_update=on_update, show=show)
        return
    
    def jump(self, attributes, ends, *, frameDuration=interpolateManager.DEFAULT_FRAME_DURATION, steps=interpolateManager.DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        '''
        점프하는 듯한 보간을 수행합니다.

        Args:
            attributes (list or str): 보간할 속성 리스트 (예: "pos", "scale" 등).
            ends (list or value): 보간 종료 시 속성들이 도달할 값.
            frameDuration (float, optional): 한 프레임의 지속 시간 (기본값: 1000/60 ms).
            steps (int, optional): 보간이 완료될 때까지의 단계 수 (기본값: 50).
            callback (function, optional): 보간 완료 후 호출되는 함수.
            revert (bool, optional): True일 경우 원래 상태로 복귀. (역재생)
            on_update (function, optional): 각 프레임마다 호출되는 함수.
            show: 보간 중인 오브젝트를 화면에 표시할지 여부 (*False일 경우 명시적으로 draw() 호출 필요)

        Returns:
            None
        '''

        interpolateManager.jump(self, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, revert=revert, on_update=on_update, show=show)
        return
    
    def bounce(self, attributes, ends, *, frameDuration=interpolateManager.DEFAULT_FRAME_DURATION, steps=interpolateManager.DEFAULT_STEPS, callback=lambda: None, revert=False, on_update=lambda: None, show=False):
        '''
        통통 튀는 듯한 보간을 수행합니다.

        Args:
            attributes (list or str): 보간할 속성 리스트 (예: "pos", "scale" 등).
            ends (list or value): 보간 종료 시 속성들이 도달할 값.
            frameDuration (float, optional): 한 프레임의 지속 시간 (기본값: 1000/60 ms).
            steps (int, optional): 보간이 완료될 때까지의 단계 수 (기본값: 50).
            callback (function, optional): 보간 완료 후 호출되는 함수.
            revert (bool, optional): True일 경우 원래 상태로 복귀. (역재생)
            on_update (function, optional): 각 프레임마다 호출되는 함수.
            show: 보간 중인 오브젝트를 화면에 표시할지 여부 (*False일 경우 명시적으로 draw() 호출 필요)

        Returns:
            None
        '''


        interpolateManager.bounce(self, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, revert=revert, on_update=on_update, show=show)
        return
    
    def interpolate(self, attributes, ends, *, frameDuration=interpolateManager.DEFAULT_FRAME_DURATION, steps=interpolateManager.DEFAULT_STEPS, callback=lambda: None, interpolation=lambda x: x, revert=False, on_update=lambda: None, show=False):
        '''
        주어진 보간 함수를 이용해 보간을 수행합니다.

        Args:
            attributes (list or str): 보간할 속성 리스트 (예: "pos", "scale" 등).
            ends (list or value): 보간 종료 시 속성들이 도달할 값.
            frameDuration (float, optional): 한 프레임의 지속 시간 (기본값: 1000/60 ms).
            steps (int, optional): 보간이 완료될 때까지의 단계 수 (기본값: 50).
            callback (function, optional): 보간 완료 후 호출되는 함수.
            interpolation (function, optional): 보간 함수 (기본값: 선형 보간).
            revert (bool, optional): True일 경우 원래 상태로 복귀. (역재생)
            on_update (function, optional): 각 프레임마다 호출되는 함수.
            show: 보간 중인 오브젝트를 화면에 표시할지 여부 (*False일 경우 명시적으로 draw() 호출 필요)

        Returns:
            None
        '''
        interpolateManager.interpolate(self, attributes, ends, frameDuration=frameDuration, steps=steps, callback=callback, interpolation=interpolation, revert=revert, on_update=on_update, show=show)
        return
    
    def slidein(self, delta=RPoint(50, 0), *, speed=1.5, callback=lambda: None, revert=False, on_update=lambda: None):
        '''
            오브젝트를 슬라이딩시키며 나타나게 하는 함수.

            Args:
                delta (RPoint, optional): 시작 위치에서의 변위.
                speed (float, optional): 슬라이드 속도 조절 (기본값: 1.5).
                callback (function, optional): 슬라이드 완료 후 호출되는 함수.
                revert (bool, optional): True일 경우 슬라이드 후 원래 위치로 돌아갑니다.
                on_update (function, optional): 슬라이드가 진행되는 동안 매 프레임마다 호출되는 함수.

            Returns:
                None
        '''


        self.pos -= delta
        self.alpha = 0
        steps = int(interpolateManager.DEFAULT_STEPS // speed)
        self.easeout(["pos", "alpha"], [self.pos + delta, 255], steps=steps, callback=callback, revert=revert, on_update=on_update)

    def onInterpolation(self):
        '''
        해당 오브젝트가 보간 중인지 확인합니다.
        '''
        return interpolateManager.check_on_interpolation(self)



@dataclass
class SurfacePoolConfig:
    max_target_sizes: int = 100
    request_threshold: int = 10
    size_expire_time: float = 20.0
    min_pool_size: int = 20
    max_pool_size: int = 64
    max_pixels_per_frame: int = 1_000_000
    frame_budget: float = 1 / 60
    maintenance_interval: float = 5.0


@dataclass
class _SurfaceStats:
    request_count: int = 0
    last_request: float = field(default_factory=time.monotonic)

    def register_request(self, expire_time: float) -> int:
        """요청 정보를 갱신하고 누적 요청 수를 반환합니다."""
        now = time.monotonic()
        if now - self.last_request > expire_time:
            # 오랫동안 요청이 없었던 사이즈는 카운트를 초기화합니다.
            self.request_count = 0
        self.last_request = now
        self.request_count += 1
        return self.request_count


class SurfacePoolCommand(Enum):
    REQUEST = auto()
    STOP = auto()
    CREATE = auto()


class SurfacePoolManager:
    def __init__(self, initial_target_sizes=None, *, config: typing.Optional[SurfacePoolConfig] = None):
        self.config = config or SurfacePoolConfig()
        initial_targets = initial_target_sizes or [(800, 600), (400, 300)]
        self._target_sizes = {self._normalize_size(size) for size in initial_targets}
        self.pools: typing.DefaultDict[typing.Tuple[int, int], typing.List[pygame.Surface]] = defaultdict(list)
        self._stats: typing.DefaultDict[typing.Tuple[int, int], _SurfaceStats] = defaultdict(_SurfaceStats)

        self.task_queue: mp.Queue = mp.Queue()
        self.result_queue: mp.Queue = mp.Queue()

        self.worker = Process(
            target=self._pool_worker,
            args=(
                self.task_queue,
                self.result_queue,
                self.config,
                self._target_sizes.copy(),
            ),
            daemon=True,
        )
        self.worker.start()

        self.process_timer = pygame.time.Clock()
        self._running = True

    @staticmethod
    def _normalize_size(size) -> typing.Tuple[int, int]:
        if isinstance(size, pygame.Rect):
            return size.width, size.height
        if isinstance(size, (list, tuple)) and len(size) == 2:
            return int(size[0]), int(size[1])
        raise ValueError(f"Invalid surface size: {size}")

    def request_surface(self, size):
        """Surface 요청을 기록하고 워커 프로세스에 전달합니다."""
        normalized = self._normalize_size(size)
        if self._running:
            stats = self._stats[normalized]
            stats.register_request(self.config.size_expire_time)
            self.task_queue.put((SurfacePoolCommand.REQUEST, normalized))
        return normalized

    def get_surface(self, size):
        """Surface 가져오기"""
        normalized = self.request_surface(size)
        pool = self.pools.get(normalized)
        if pool:
            return pool.pop()
        return self.make_surface(normalized)

    def return_surface(self, surface):
        """Surface 반환"""
        size = self._normalize_size((surface.get_width(), surface.get_height()))
        surface.fill((0, 0, 0, 0))

        optimal_size = self._get_optimal_pool_size(size)
        pool = self.pools[size]
        if len(pool) < optimal_size:
            pool.append(surface)
        else:
            del surface

    def process_main_thread(self):
        """메인 스레드에서 Surface 생성 처리"""
        try:
            surface_pixels_created = 0
            time_start = time.perf_counter()
            while surface_pixels_created < self.config.max_pixels_per_frame:
                action, data = self.result_queue.get_nowait()
                if action is SurfacePoolCommand.CREATE:
                    size = data
                    pool = self.pools[size]
                    if len(pool) < self._get_optimal_pool_size(size):
                        surface = self.make_surface(size)
                        pool.append(surface)
                        surface_pixels_created += size[0] * size[1]
                if time.perf_counter() - time_start > self.config.frame_budget:
                    break
        except queue.Empty:
            pass

        self.process_timer.tick(60)  # 프레임 제한

    def _get_optimal_pool_size(self, size: typing.Tuple[int, int]) -> int:
        """요청 빈도 기반으로 최적의 Surface 풀 크기를 계산합니다."""
        stats = self._stats.get(size)
        if not stats:
            return self.config.min_pool_size

        if time.monotonic() - stats.last_request > self.config.size_expire_time:
            return self.config.min_pool_size

        dynamic_limit = int(stats.request_count * 1.2)
        dynamic_limit = max(dynamic_limit, self.config.min_pool_size)
        return min(dynamic_limit, self.config.max_pool_size)

    @staticmethod
    def make_surface(size):
        return pygame.Surface(size, pygame.SRCALPHA, 32)

    @staticmethod
    def _maintain_target_sizes(
        target_sizes: typing.Set[typing.Tuple[int, int]],
        size_requests: Counter,
        last_request_time: dict,
        config: SurfacePoolConfig,
        now: float,
    ) -> None:
        """자주 사용되는 Surface 크기를 추적하여 우선순위를 유지합니다."""
        stale = [
            size for size, last_time in list(last_request_time.items())
            if now - last_time > config.size_expire_time
        ]
        for size in stale:
            last_request_time.pop(size, None)
            size_requests.pop(size, None)
            target_sizes.discard(size)

        frequent = {
            size for size, count in size_requests.items()
            if count >= config.request_threshold
        }

        if len(target_sizes) + len(frequent) > config.max_target_sizes:
            scored = sorted(
                (
                    (size, size_requests.get(size, 0), last_request_time.get(size, 0))
                    for size in target_sizes | frequent
                ),
                key=lambda item: (item[1], item[2]),
                reverse=True,
            )
            target_sizes.clear()
            target_sizes.update(size for size, _, _ in scored[:config.max_target_sizes])
        else:
            target_sizes.update(frequent)

    @staticmethod
    def _pool_worker(task_queue, result_queue, config: SurfacePoolConfig, initial_targets):
        """별도 프로세스에서 실행되는 워커"""
        size_requests: Counter = Counter()
        last_request_time: dict = {}
        target_sizes = set(initial_targets)
        last_maintenance = time.monotonic()

        while True:
            try:
                command, payload = task_queue.get(timeout=0.001)
            except queue.Empty:
                command, payload = None, None

            if command is SurfacePoolCommand.STOP:
                break
            if command is SurfacePoolCommand.REQUEST:
                size = payload
                now = time.monotonic()
                size_requests[size] += 1
                last_request_time[size] = now

                if size in target_sizes or size_requests[size] >= config.request_threshold:
                    result_queue.put((SurfacePoolCommand.CREATE, size))

            current_time = time.monotonic()
            if current_time - last_maintenance >= config.maintenance_interval:
                SurfacePoolManager._maintain_target_sizes(
                    target_sizes,
                    size_requests,
                    last_request_time,
                    config,
                    current_time,
                )
                last_maintenance = current_time

            time.sleep(0.001)  # CPU 사용량 조절

    def shutdown(self):
        """종료 처리"""
        if not self._running:
            return

        self._running = False
        try:
            self.task_queue.put((SurfacePoolCommand.STOP, None))
        except Exception:
            pass

        self.worker.join(timeout=1.0)
        if self.worker.is_alive():
            self.worker.terminate()
            self.worker.join()

        for q in (self.task_queue, self.result_queue):
            try:
                q.cancel_join_thread()
                q.close()
            except Exception:
                pass
