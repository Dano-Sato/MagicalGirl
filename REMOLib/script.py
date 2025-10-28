'''
비주얼 노벨 형식의 대화 스크립트를 처리하는 모듈입니다.
'''

from .core import *
from .motion import RMotion

##스크립트 렌더링을 위한 레이아웃들을 저장하는 클래스.
class scriptRenderLayouts:
    layouts = {
        #1920*1080 스크린을 위한 기본 레이아웃.
        "default_1920_1080":
        {
            "name-rect":pygame.Rect(300,600,200,60), #이름이 들어갈 사각형 영역
            'name-alpha':200, #이름 영역의 배경 알파값. 입력하지 않을경우 불투명(255)
            "font":"unifont_script.ttf", # 폰트. 기본으로 지원되는 한국어 폰트(맑은고딕). 영어 한국어 지원 가능
            "font-size":40, # 폰트 크기
            "script-rect":pygame.Rect(100,680,1700,380), ##스크립트가 들어갈 사각형 영역
            "script-pos":RPoint(200,710), ##스크립트 텍스트의 위치
            "script-text-width":1500, ##스크립트의 좌우 텍스트 최대길이
            "script-alpha":200 ## 스크립트 영역의 배경 알파값. 입력하지 않을경우 255(완전 불투명)
            ### 추가 옵션들
            ##"name-image":이름 영역의 이미지를 지정할 수 있습니다.
            ##"script-image" : 스크립트 영역의 이미지를 지정할 수 있습니다.
            ###
        },
        "default_2560_1440":
        {
            "name-rect":pygame.Rect(300,800,200,60), #이름이 들어갈 사각형 영역
            'name-alpha':200, #이름 영역의 배경 알파값. 입력하지 않을경우 불투명(255)
            "font":"unifont_script.ttf", # 폰트. 기본으로 지원되는 한국어 폰트(맑은고딕). 영어 한국어 지원 가능
            "font-size":45, # 폰트 크기
            "script-rect":pygame.Rect(100,880,2300,480), ##스크립트가 들어갈 사각형 영역
            "script-pos":RPoint(200,910), ##스크립트 텍스트의 위치
            "script-text-width":2000, ##스크립트의 좌우 텍스트 최대길이
            "script-alpha":200 ## 스크립트 영역의 배경 알파값. 입력하지 않을경우 255(완전 불투명)
            ### 추가 옵션들
            ##"name-image":이름 영역의 이미지를 지정할 수 있습니다.
            ##"script-image" : 스크립트 영역의 이미지를 지정할 수 있습니다.
            ###
        }
        ##TODO: 유저 커스텀 레이아웃을 추가해 보세요. 네이밍 양식을 지켜서!
    }

    @classmethod
    def updateLayout(cls,name:str,layout:dict):
        '''
        name : 레이아웃의 이름\n
        layout : 레이아웃의 딕셔너리. 양식은 scriptRenderLayouts.layouts 참고\n
        '''
        cls.layouts[name] = layout


class scriptMode(Enum):
    Normal = 0
    QuestioningStart = 1
    Questioning = 2
    Answering = 3

##작성한 비주얼노벨 스크립트를 화면에 그려주는 오브젝트 클래스.
class scriptRenderer():
    ##감정 벌룬 스프라이트(emotion-ballon.png)에 담겨진 감정의 순서를 나열한다.
    emotions = ["awkward","depressed","love","excited","joyful","angry","surprised","curious","sad","idea","ok","zzz","no"]
    emotionSpriteFile = "emotion-ballon.png" # 감정 벌룬 스프라이트의 파일 이름
    emotionTime = 1700 ##1700ms동안 감정 벌룬이 재생된다.


    ##렌더러를 초기화한다. (clear의 역할을 함)
    def _init(self):
        ##기본 이미지 초기화
        self.imageObjs = [] #화면에 출력될 이미지들
        self.charaObjs=[None,None,None] #화면에 출력될 캐릭터들
        self.moveInstructions = [[],[],[]] #캐릭터들의 움직임에 대한 지시문
        self.emotionObjs = [] # 화면에 출력될 (캐릭터의) 감정들
        self.freezeTimer = time.time() ## 스크립트를 멈추는 타이머
        self.bgObj = rectObj(Rs.screen.get_rect(),color=Cs.black,radius=0) #배경 이미지
        self.nameObj = textButton()

        ##스크립트 텍스트 오브젝트
        self.scriptObj = longTextObj("",pos=self.layout["script-pos"],font=self.font,size=self.layout["font-size"],textWidth=self.layout["script-text-width"])

        self.frameTimer = RTimer(1000/60) ##프레임 타이머

    def clear(self):
        self._init()


    #textSpeed:값이 클수록 느리게 재생된다.
    def __init__(self,fileName,*,textSpeed:float = 5.0,layout="default_2560_1440",endFunc = lambda :None):
        '''
        textSpeed: 값이 클수록 느리게 재생된다.
        target_fps가 60보다 낮을 경우 캐릭터의 움직임이 느려질 수 있다.
        '''
        if not fileName.endswith('.scr'):
            fileName += '.scr'
        if fileName in REMODatabase.scriptPipeline:
            self.data = REMODatabase.scriptPipeline[fileName]
        else:
            raise Exception("script file:"+fileName+" not loaded. use method: REMODatabase.loadScripts")



        self.layout = scriptRenderLayouts.layouts[layout]
        self.index = 0
        self.font = self.layout["font"]
        
        self.currentScript = "" #현재 출력해야 되는 스크립트
        self.endFunc = endFunc #스크립트가 끝날 경우 실행되는 함수.
        self.scriptMode = scriptMode.Normal

        self.textSpeed=textSpeed
        self.textFrameTimer = RTimer((1000/60)*self.textSpeed) ##텍스트 출력 속도를 조절하는 타이머

        self._init()

        self.endMarker = rectObj(pygame.Rect(0,0,7,10)) ##스크립트 재생이 끝났음을 알려주는 점멸 마커

        ##점멸을 위한 내부 인자들.
        self.endMarker.switch = True
        self.endMarker.timer = time.time()
        self.endMarker.tick = 0.5 ##0.5초마다 점멸 

        ##스크립트 영역 배경 오브젝트
        if "script-image" in self.layout:
            ##TODO: 이미지를 불러온다.
            self.scriptBgObj = imageButton(self.layout["script-image"],self.layout["script-rect"],hoverMode=False)
            None
        else:
            self.scriptBgObj = textButton("",self.layout["script-rect"],color=Cs.hexColor("111111"))
            self.scriptBgObj.hoverRect.alpha=5

        if "script-alpha" in self.layout:
            self.scriptBgObj.alpha = self.layout["script-alpha"]

        ##스크립트의 배경을 클릭하면, 다음 스크립트를 불러온다.
        def nextScript():
            if not self.scriptLoaded():
                self.scriptObj.text = self.currentScript
                self.scriptObj._clearGraphicCache() # 스크립트가 간헐적으로 한번에 출력이 안되는 버그가 있어서 임시방편으로 이렇게 해놓음.
            elif not self.isEnded():
                ##다음 스크립트를 불러온다.
                self.indexIncrement()
                self.updateScript()
                self.endMarker.switch = False
            else:
                if self.scriptMode == scriptMode.Normal:
                    ##파일의 재생이 끝남.
                    self._init() ## 초기화(오브젝트를 비운다)
                    self.endFunc()
                    print("script is ended")
                elif self.scriptMode == scriptMode.Answering:
                    self.scriptMode = scriptMode.Questioning
                    self.qnaIndex = 0
                    self.updateScript()

        self.scriptBgObj.connect(nextScript)
        self.updateScript()



    ##현 스크립트 재생이 끝났는지를 확인하는 함수
    def scriptLoaded(self):
        return self.scriptObj.text == self.currentScript

    ##전체 파일을 다 읽었는지 확인하는 함수.
    def isEnded(self):
        if self.scriptMode == scriptMode.Normal:
            if self.index == len(self.data)-1:
                return True
            return False
        elif self.scriptMode == scriptMode.Answering:
            if self.qnaIndex == len(self.answers[self.currentCase])-1:
                return True
            return False
        return True

    @property
    def currentLine(self):
        if self.scriptMode == scriptMode.Normal:
            return self.data[self.index].strip()
        elif self.scriptMode == scriptMode.Questioning:
            return self.qnaScript.strip()
        elif self.scriptMode == scriptMode.QuestioningStart:
            return self.lastScript.strip()
        elif self.scriptMode == scriptMode.Answering:
            return self.answers[self.currentCase][self.qnaIndex].strip()
    
    ##렌더러의 폰트 변경.
    def setFont(self,font):
        self.scriptObj.font = font
        self.nameObj.textObj.font = font

    ##캐릭터에게 움직임을 지시한다.
    ##num:캐릭터 번호
    def makeMove(self,num,moves):
        moveInst = self.moveInstructions[num]
        for j,move in enumerate(moves):
            if j<len(moveInst):
                moveInst[j]=moveInst[j]+move
            else:
                moveInst.append(move)


    def updateScript(self):
        """
        현재 스크립트 라인을 처리하는 함수.\n
        
        이 함수는 현재 스크립트에서 명령어로 시작하는 라인을 처리합니다.\n
        명령어는 '#'로 시작하며, 이 함수는 각 명령어에 맞는 처리를 수행합니다.\n
        
        주요 기능:\n
        - 스크립트 라인이 '#'로 시작하는 경우, 해당 태그를 분석하고 적절한 처리를 실행.\n
        - '#question' 태그를 만나면 Q&A 모드를 시작.\n
        - '#clear', '#bgm', '#sound', '#bg', '#chara', '#image' 등의 태그에 따라 각각의 처리 메소드를 호출.\n
        - 스크립트 라인이 명령어가 아닌 경우, 일반적인 대사 처리로 넘어감.\n
        
        주의사항:\n
        - 지원되지 않는 태그를 만나면 예외(Exception)를 발생시킴.\n
        - 현재 인덱스가 스크립트 데이터의 끝에 도달하면 함수를 종료함.\n
        """    

        ## 명령어 처리 ##
        while self.currentLine[0] == "#":
            l = self.currentLine.split()
            tag = l[0]  # Tag : '#bgm', '#bg', '#image' 등의 태그
            fileName, parameters = self.parse_parameters(l[1:])

            if tag == '#qna_open':
                self.startQnaMode(l)
            elif tag == '#clear':
                self.clearImages()
            elif tag == '#bgm':
                self.handleBgm(fileName, parameters)
            elif tag == '#sound':
                self.handleSound(fileName, parameters)
            elif tag == "#color":
                color_name = fileName.split(".")[-1].lower()
                self.scriptObj.color = getattr(Cs,color_name,Cs.white)
            elif tag == '#effect':
                self.apply_effect(fileName, parameters)
            elif tag == '#bg':
                self.handleBg(fileName)
            elif '#chara' in tag:
                self.handleChara(tag, fileName, parameters)
            elif tag == '#image':
                self.handleImage(fileName, parameters)
            else:
                raise Exception("Tag Not Supported, please check the script file(.scr): " + self.currentLine)

            if self.index == len(self.data) - 1:
                return
            self.indexIncrement()

        ## 스크립트 처리 ##
        ## ex: '민혁: 너는 왜 그렇게 생각해?'
        self.handleScriptLine(self.currentLine)

    def indexIncrement(self):
        if self.scriptMode == scriptMode.Normal:
            self.index += 1
        elif self.scriptMode == scriptMode.Questioning:
            return
        elif self.scriptMode == scriptMode.QuestioningStart:
            return
        elif self.scriptMode == scriptMode.Answering:
            self.qnaIndex += 1

    def startQnaMode(self, l):
        '''
        질문과 답변 모드를 시작하는 함수입니다.
        '''
        try:
            self.qnaScript = self.data[self.index-1]
            self.lastScript = self.qnaScript
        except IndexError:
            raise IndexError("선택지 이전에 qna를 시작하는 스크립트가 없습니다.")
        
        self.qnaIndex = 0
        # 선택지 파싱
        choice_string = " ".join(l[1:])  # l[1:] 부분을 하나의 문자열로 결합
        self.choices = self.parse_choices(choice_string)
        self.questionButtons = buttonLayout(self.choices,RPoint(0,0),buttonSize=RPoint(700,100),spacing=30,buttonColor=Cs.black)
        for i,button in enumerate(self.questionButtons.getChilds()[:-1]):
            def selectAnswer(i,button):
                def x():
                    self.currentCase = i+1
                    self.scriptMode = scriptMode.Answering
                    button.setParent(None)
                    self.questionButtons._clearGraphicCache()
                    self.questionButtons.adjustBoundary()
                    self.questionButtons.center = RPoint(950,360)
                    self.updateScript()
                return x
            button.connect(selectAnswer(i,button))
        def endQna():
            self.scriptMode = scriptMode.Normal
            self.indexIncrement()
            self.updateScript()
        self.questionButtons.getChilds()[-1].connect(endQna)

        self.questionButtons.center = RPoint(950,360)
        self.answers = {}
        self.currentCase = None

        # while문으로 #close까지 스크립트 읽어들이기
        while True:
            self.index += 1
            if self.index >= len(self.data):
                raise Exception("Unexpected end of script while in listening mode.")            
            if self.currentLine.startswith("#qna_script"):
                sentence = self.currentLine.split(" ",1)[1]
                self.qnaScript = sentence
            elif self.currentLine.startswith("#answer"):
                answer_number = int(self.currentLine[7:])  # '#answerX'에서 'X' 추출
                self.currentCase = answer_number
                self.answers[answer_number] = []  # 새로운 case 스크립트 저장 공간 생성
            elif self.currentLine.startswith("#qna_close"):
                break
            elif self.currentCase is not None:
                self.answers[self.currentCase].append(self.currentLine)        

        self.currentCase = None # 현재 선택지 초기화. 선택시 다시 설정됨.
        self.scriptMode = scriptMode.QuestioningStart


    def parse_choices(self, choice_string):
        import re
        # 정규 표현식을 사용하여 선택지를 나누기
        return [choice.strip() for choice in re.split(r' / ', choice_string)]

    def parse_parameters(self, l):
        fileName = None
        parameters = {}
        for nibble in l:
            if '=' in nibble:
                param_name, param_value = nibble.split("=")
                parameters[param_name] = param_value
            elif '.' in nibble:
                fileName = nibble
            else:
                if nibble == 'jump':
                    parameters['jump'] = 12
                if nibble == 'clear':
                    parameters['clear'] = True
        return fileName, parameters

    def clearImages(self):
        self.imageObjs = []
        self.charaObjs = [None, None, None]
        self.moveInstructions = [[], [], []]  # 움직임 초기화

    def handleBgm(self, fileName, parameters):
        _volume = float(parameters.get('volume', 1.0))
        Rs.changeMusic(fileName, volume=_volume)

    def handleSound(self, fileName, parameters):
        _volume = float(parameters.get('volume', 1.0))
        Rs.playSound(fileName, volume=_volume)

    def handleBg(self, fileName):
        self.bgObj = imageObj(fileName, Rs.screen.get_rect())

    def handleChara(self, tag, fileName, parameters):
        num = 0 if tag == '#chara' else int(tag[-1]) - 1
        _pos = self.safe_eval_pos(parameters)
        _scale = float(parameters.get('scale', 1))

        if fileName:
            if self.charaObjs[num]:
                self.charaObjs[num].setImage(fileName)
            else:
                self.charaObjs[num] = imageObj(fileName, pos=_pos, scale=_scale)

        if 'emotion' in parameters:
            self.apply_emotion(num, parameters['emotion'])

        if 'jump' in parameters:
            self.apply_jump(num, parameters['jump'])

        if 'move' in parameters:
            self.apply_move(num, parameters['move'])

        if 'clear' in parameters:
            self.charaObjs[num] = None


    def literal_eval(self, parameters,key,default=None):
        '''
        parameters : 스크립트에서 파싱한 파라미터 딕셔너리
        key : 파라미터 딕셔너리에서 가져올 키
        default : 키가 없을 경우 반환할 기본값
        '''
        import ast
        result_str = parameters.get(key, default)
        try:
            result = ast.literal_eval(result_str)
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing str: {e}")
            result = ast.literal_eval(default)  # 기본값 또는 에러 처리 로직
        return result
    
    @staticmethod
    def _safe_eval(expr, allowed_names=None):
        '''
        안전하지 않은 eval() 함수를 대신하여 사용할 수 있는 함수입니다.\n
        '''
        import ast
        import operator as op

        # 지원하는 연산자 매핑
        operators = {
            ast.Add: op.add,
            ast.Sub: op.sub,
            ast.Mult: op.mul,
            ast.Div: op.truediv,
            ast.Pow: op.pow,
            ast.Mod: op.mod,
            ast.FloorDiv: op.floordiv,
            # 필요한 경우 더 많은 연산자를 추가할 수 있습니다.
        }

        allowed_names = allowed_names or {}
        node = ast.parse(expr, mode='eval')

        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.Constant):  # 숫자 리터럴
                return node.value
            elif isinstance(node, ast.Tuple):  # 튜플 처리
                return tuple(_eval(elt) for elt in node.elts)            
            elif isinstance(node, ast.BinOp):  # 이항 연산자
                left = _eval(node.left)
                right = _eval(node.right)
                if type(node.op) in operators:
                    return operators[type(node.op)](left, right)
                else:
                    raise TypeError(f"지원되지 않는 연산자: {type(node.op)}")
            elif isinstance(node, ast.UnaryOp):  # 단항 연산자
                operand = _eval(node.operand)
                if isinstance(node.op, ast.UAdd):  # 양수(+)
                    return +operand
                elif isinstance(node.op, ast.USub):  # 음수(-)
                    return -operand
                else:
                    raise TypeError(f"지원되지 않는 단항 연산자: {type(node.op)}")
            elif isinstance(node, ast.Name):
                if node.id in allowed_names:
                    return allowed_names[node.id]
                raise ValueError(f"'{node.id}'은 허용되지 않은 이름입니다.")
            elif isinstance(node, ast.Call):  # 함수 호출
                func = _eval(node.func)
                args = [_eval(arg) for arg in node.args]
                return func(*args)
            else:
                raise TypeError(f"지원되지 않는 노드 유형: {type(node)}")
        return _eval(node)    
    
    def safe_eval(self, parameter,key,default=None,*,allowed_names=None):
        '''
        parameters : 스크립트에서 파싱한 파라미터 딕셔너리
        key : 파라미터 딕셔너리에서 가져올 키
        default : 키가 없을 경우 반환할 기본값
        allowed_names : eval() 함수에서 사용할 수 있는 이름들
        '''

        result_str = parameter.get(key, default)
        try:
            result = self._safe_eval(result_str, allowed_names)
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing str: {e}")
            result = self._safe_eval(default, allowed_names) # 기본값 또는 에러 처리 로직
        return result
    
    def safe_eval_pos(self,parameters):
        return self.safe_eval(parameters,'pos','RPoint(0,0)',allowed_names={'RPoint':RPoint})
        
    def apply_effect(self, fileName, parameters):
        '''
        스프라이트 시트를 이용한 이펙트를 적용하는 함수입니다. \n
        예시 : #effect effect1.png matrix=(5,3) pos=(300,300) scale=0.5 frameDuration=125
        '''
        #effect effect1.png matrix=(5,3) pos=(300,300) scale=0.5 frameDuration=125
        _pos = self.safe_eval_pos(parameters)
        _center = self.safe_eval(parameters,'center','None')
        _scale = float(parameters.get('scale', 1))
        _matrix = self.literal_eval(parameters,'matrix',(1,1))
        _frameDuration = self.safe_eval(parameters,'frameDuration', '1000/60')
        _stay = int(parameters.get('stay', 0))
        _freeze = int(parameters.get('freeze', 0))

        Rs.playAnimation(fileName,stay=_stay, pos=_pos,center=_center, scale=_scale, sheetMatrix=_matrix, frameDuration=_frameDuration)
        self.freezeTimer = time.time() + _freeze / 1000.0


    def apply_emotion(self, num, emotion):
        try:
            i = scriptRenderer.emotions.index(emotion)
            e_pos = RPoint(self.charaObjs[num].rect.centerx, 30)
            Rs.playAnimation(
                scriptRenderer.emotionSpriteFile,
                stay=scriptRenderer.emotionTime,
                pos=e_pos,
                sheetMatrix=(13, 8),
                fromSprite=8 * i,
                toSprite=8 * (i + 1) - 1,
                frameDuration=125,
                scale=2
            )
            self.freezeTimer = time.time() + scriptRenderer.emotionTime / 1000.0
        except ValueError:
            raise Exception("Emotion not Supported: " + emotion +
                            ", currently supported are:" + str(scriptRenderer.emotions))

    def apply_jump(self, num, jump_value):
        RMotion.jump(self.charaObjs[num],RPoint(0,-3*int(jump_value)))

    def apply_move(self, num, move_value):
        RMotion.move(self.charaObjs[num],RPoint(int(move_value),0),smoothness=18)

    def handleImage(self, fileName, parameters):
        _pos = self.safe_eval_pos(parameters)
        _scale = float(parameters.get('scale', 1))

        obj = imageObj(fileName, pos=_pos, scale=_scale)
        self.imageObjs.append(obj)

    def handleScriptLine(self,line):
        '''
        line : "이름: 대사" 형식의 스크립트 라인
        line을 받아서 GUI에 출력할 수 있도록 처리한다.
        '''
        if self.scriptMode == scriptMode.QuestioningStart:
            return
        if ":" in line:
            name, script = line.split(":")
            script = script.strip()

            self.nameObj = textButton(
                name,
                rect=self.layout["name-rect"],
                font=self.font,
                size=self.layout['font-size'],
                enabled=False,
                color=Cs.hexColor("222222")
            )
            if "name-alpha" in self.layout:
                self.nameObj.alpha = self.layout["name-alpha"]
            self.currentScript = script
        else:
            self.nameObj.textObj.text = ""
            self.currentScript = line.strip()

        self.scriptObj.text = ""



        
    def update(self):
        '''
        스크립트 렌더러를 업데이트하는 함수입니다.
        '''
        current_time = time.time()  # 한 번만 시간 체크

        # 감정 애니메이션 재생 중 체크
        if current_time < self.freezeTimer:
            if self.scriptObj.text:  # != "" 보다 빠름
                self.scriptObj.text = ""
            return


        self.scriptBgObj.update()

        # 텍스트 업데이트 최적화
        if self.textFrameTimer.isOver():
            if not self.scriptLoaded():
                self._update_script_text()
            self.textFrameTimer.reset()

        # 점멸 마커 업데이트 최적화
        if self.scriptLoaded() and self.scriptObj.childs:  # != [] 보다 빠름
            if current_time > self.endMarker.timer:
                self.endMarker.timer = current_time + self.endMarker.tick 
                self.endMarker.switch = not self.endMarker.switch
            
            # 마커 위치 업데이트 - 계산 캐싱
            last_child = self.scriptObj.childs[0][-1]
            marker_pos = RPoint(last_child.geometry.bottomright) + RPoint(20,0)
            if self.endMarker.bottomleft != marker_pos:
                self.endMarker.bottomleft = marker_pos

        # 질문 모드 체크 최적화
        if self.scriptMode in (scriptMode.Questioning, scriptMode.QuestioningStart):
            self.questionButtons.update()

    def _update_script_text(self):
        """더 급진적인 최적화 버전 - 메모리와 속도 트레이드오프"""
        current_len = len(self.scriptObj.text)
        
        # 미리 계산된 줄바꿈 위치를 사용
        if not hasattr(self, '_line_breaks'):
            self._line_breaks = set()
            temp_text = ''
            for i in range(len(self.currentScript)):
                temp_text += self.currentScript[i]
                if ' ' in temp_text or '\n' in temp_text:
                    lines = self.scriptObj.getStringList(temp_text)[:-1]
                    if lines and len(lines) > 1:
                        self._line_breaks.add(i)
        
        # 현재 위치가 줄바꿈 위치인지 확인
        if current_len in self._line_breaks:
            # 공백까지 진행
            while current_len < len(self.currentScript):
                if self.currentScript[current_len] == ' ':
                    break
                current_len += 1
        
        self.scriptObj.text = self.currentScript[:current_len + 1]

    def draw(self):
        self.bgObj.draw()
        for imageObj in self.imageObjs:
            imageObj.draw()
        for chara in self.charaObjs:
            if chara:
                chara.draw()
        self.scriptBgObj.draw()
        if not self.freezeTimer>time.time():
            self.scriptObj.draw()
        if self.scriptLoaded() and self.endMarker.switch:
            self.endMarker.draw()
        if self.nameObj.textObj.text!="":
            self.nameObj.draw()
            self.nameObj.textObj.draw()
        for emotion in self.emotionObjs:
            emotion.draw()
        if self.scriptMode == scriptMode.Questioning or self.scriptMode == scriptMode.QuestioningStart:
            self.questionButtons.draw()




