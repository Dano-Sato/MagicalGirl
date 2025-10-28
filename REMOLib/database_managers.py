import os, pickle, pygame, pandas, json
from enum import Enum, auto

##REMO Engine의 File I/O를 다루는 클래스.
##TODO: Path pipeline도 여기 안으로 옮긴다.

class REMODatabase:


    ##Path pipeline

    __pathData = {}  # 확장자에 따라 경로를 분류하는 딕셔너리
    __pathPipeline = {}  # 파일명과 실제 경로를 연결하는 딕셔너리
    __pathException = [".git", ".pyc", ".py"]  # 경로에서 제외할 파일 패턴

    @classmethod
    def _buildPath(cls):
        """
        현재 파일이 포함된 경로의 내부 폴더들을 모두 탐색하여 경로 파이프라인을 구성하는 메서드.
        """
        cls.__pathData.clear()
        cls.__pathPipeline.clear()

        for currentpath, _, files in os.walk('.'):
            for file in files:
                if file.startswith("."):  # 숨김 파일은 기본적으로 제외
                    continue

                path = os.path.join(currentpath, file)
                if any(ex in path for ex in cls.__pathException):
                    continue  # 예외 조건에 해당하는 파일은 제외

                extension = os.path.splitext(path)[-1]
                cls.__pathData.setdefault(extension, []).append(path)

                # 파일 이름 충돌 검사 및 경고 출력
                if file not in cls.__pathPipeline:
                    cls.__pathPipeline[file] = path
                else:
                    print(f"Possible file conflict: {file} in {path} and {cls.__pathPipeline[file]}")

    @classmethod
    def addPath(cls, alias: str, path: str):
        """
        특정 경로를 파이프라인에 수동으로 추가하는 메서드.
        
        :param alias: 파일에 대한 별칭
        :param path: 실제 파일 경로
        """
        cls.__pathPipeline[alias] = path
        extension = os.path.splitext(path)[-1]
        cls.__pathData.setdefault(extension, []).append(path)

    @classmethod
    def getPath(cls, alias: str) -> str:
        """
        파일명을 통해 실제 경로를 반환하는 메서드.
        
        :param alias: 파일명 또는 경로의 별칭
        :return: 실제 파일 경로
        :raises FileNotFoundError: 경로를 찾을 수 없을 때 예외 발생
        """
        if alias in cls.__pathPipeline:
            return cls.__pathPipeline[alias]

        extension = os.path.splitext(alias)[-1]
        if extension not in cls.__pathData:
            raise FileNotFoundError(f"Path '{alias}' does not exist!")

        for path in cls.__pathData[extension]:
            if alias in path:
                print(f"path {alias} is attached to {path}")
                cls.__pathPipeline[alias] = path
                return path

        raise FileNotFoundError(f"Path '{alias}' does not exist!")

    @classmethod
    def assetExist(cls, alias: str) -> bool:
        """
        파일이 실제로 존재하는지 확인하는 메서드.
        
        :param alias: 파일명 또는 경로의 별칭
        :return: 파일이 존재하면 True, 그렇지 않으면 False
        """
        return alias in cls.__pathPipeline
    

    __imagePipeline={}
    @classmethod
    def getImage(cls,path) -> pygame.Surface:
        '''
        이미지를 로드하여 캐싱하는 함수.\n
        '''
        path = cls.getPath(path)
        if path not in cls.__imagePipeline:
            cls.__imagePipeline[path]=pygame.image.load(path).convert_alpha()            
        return cls.__imagePipeline[path]
    
    #이미지 스프라이트에서 rect영역을 잘라낸 함수 
    __spritePipeline={}
    @classmethod
    def getSprite(cls,path,rect):
        '''
        이미지 스프라이트에서 rect영역만큼 잘라내어 반환하는 함수.\n
        해당 과정에서 캐싱이 일어난다. \n
        '''
        key = (path,str(rect))
        if key not in cls.__spritePipeline:
            sprite = cls.getImage(path).subsurface(rect)
            cls.__spritePipeline[key]=sprite
        return cls.__spritePipeline[key]
    

    ##File Input/Output
    
    ##피클로 파이썬 객체를 저장한다. 보통 딕셔너리나 리스트 계열을 저장할때 사용
    @classmethod
    def saveData(cls,path,data):
        '''
        path : 저장할 파일의 경로\n
        data : 저장할 파이썬 객체(딕셔너리, 리스트 등)
        '''
        if os.path.isfile(path):
            control = 'wb'
        else:
            control = 'xb'
        pickle.dump(data,open(path,control))

    @classmethod
    def saveJson(cls,path,data):
        '''
        path : 저장할 파일의 경로
        data : 저장할 파이썬 객체(딕셔너리, 리스트 등)
        '''
        with open(path, 'w') as json_file:
            json.dump(data, json_file, indent=4)  # indent=4로 사람이 읽기 쉽게 저장

    ##저장된 파이썬 객체를 불러온다.
    @classmethod
    def loadData(cls,path):
        '''
        path : 불러올 파일의 경로\n
        path에 저장된 파이썬 객체를 불러온다.
        '''
        return pickle.load(open(path,'rb'))
    
    @classmethod
    def loadJson(cls,path):
        '''
        path : 불러올 파일의 경로\n
        path에 저장된 파이썬 객체를 불러온다.
        '''
        with open(path, 'r') as json_file:
            data = json.load(json_file)
            return data

    ### 비주얼 노벨 계열 스크립트 파일 I/O 함수
    scriptPipeline ={}
    scriptExtension = '.scr'
    ##Script I/O

    ##.scr 파일은 텍스트 편집기를 통해서 간단하게 편집할 수 있습니다.
    ##.scr 파일의 문법은 별도의 파일에서 설명됩니다.
            
    ##현재 존재하는 .scr 파일을 묶어서 .scrs 파일로 만드는 함수.
    ##input을 통해 사용할 .scr파일을 지정할 수 있다. ['text1','text2'] 같은 식으로 쓰면 됨.
    ##{'text1.scr':*lines*, 'text2.scr':*lines*} 형식으로 파이프라인에 저장됨.
    ## prefix를 통해서 지정된 .scr 파일만 묶어서 저장할 수 있다. ex)GAME1_script1.scr GAME1_script2.scr
    ##        
    @classmethod
    def zipScript(cls, outputName,inputs=None,prefix=""):
        '''
        outputName : 저장할 .scrs 파일의 이름\n
        inputs : 묶을 .scr 파일의 이름 리스트(전체 파일들을 묶을 경우 None)\n
        prefix : 묶을 .scr 파일의 이름 중 특정 접두사를 가진 파일만 묶을 수 있음\n
        경로 내의 .scr 파일을 묶어서 .scrs 파일로 만든다.
        '''
        zipped = {}
        if inputs==None:
            current_directory = os.getcwd()
            script_files = [f for f in os.listdir(current_directory) if f.endswith(REMODatabase.scriptExtension) and prefix in f]
        else:
            script_files = [x+'.scr' for x in inputs]

        for f in script_files:
            file = open(f,'r',encoding='UTF-8')
            lines = file.readlines()
            lines = [l.strip() for l in lines if l.strip()!=""]
            zipped[f]=lines

        REMODatabase.saveData(outputName+REMODatabase.scriptExtension+'s',zipped)
        print(zipped)

        return zipped

    ##.scr 파일을 불러와 파이프라인에 저장한다.
    @classmethod
    def loadScript(cls, fileName):
        '''
        fileName : 불러올 .scr 파일의 이름\n
        '''
        if not fileName.endswith('.scr'):
            fileName += '.scr'
        file = open(REMODatabase.getPath(fileName),'r',encoding='UTF-8')
        lines = file.readlines()
        REMODatabase.scriptPipeline[fileName] = lines


    ##.scrs 파일을 불러와 파이프라인에 저장한다.
    @classmethod
    def loadScripts(cls, fileName):
        '''
        fileName : 불러올 .scrs 파일의 이름\n
        '''
        if not fileName.endswith('.scrs'):
            fileName += '.scrs'
        path = REMODatabase.getPath(fileName)
        REMODatabase.scriptPipeline.update(REMODatabase.loadData(path))


    @classmethod
    def loadExcel(cls, fileName,orient='index',indexNum=0):
        '''
        fileName : 불러올 .xlsx 파일의 이름\n
        orient: dictionary의 방향. 'index'로 지정할 경우 indexNum의 열을 key로 사용한다.\n
        'records'로 지정할 경우 각 시트를 dictionary list로 불러옵니다.\n
        '''
        path = REMODatabase.getPath(fileName)
        excel_data = pandas.read_excel(path, None)  # None loads all sheets

        # Convert each sheet in the Excel file to a list of dictionaries
        sheets_dict = {}
        if orient=='records':
            for sheet_name, data in excel_data.items():
                sheets_dict[sheet_name] = data.to_dict(orient='records')
        elif orient=='index':
            for sheet_name, data in excel_data.items():
                # Assuming the first column is to be used as the key
                if not data.empty:
                    sheets_dict[sheet_name] = data.set_index(data.columns[indexNum]).to_dict(orient='index')
        else:
            raise ValueError("orient must be 'records' or 'index'")


        return sheets_dict





class REMOLocalizeManager:
    '''
    REMO 프로젝트의 텍스트 번역과 폰트 등을 관리하는 클래스입니다.
    textObj, textButton, longTextObj 등에서 사용할 수 있습니다.
    '''
    __localizationPipeline = {}  # 로컬라이제이션을 관리할 오브젝트와 키를 저장
    __language = "en"            # 기본 언어는 영어로 설정
    __translations = {}          # 번역 데이터를 저장하는 딕셔너리
    __fonts = {"default":{"en":"korean_button.ttf","kr":"korean_button.ttf","jp":"japanese_button.ttf"}} # 폰트 데이터를 저장하는 딕셔너리


    @classmethod
    def setLanguage(cls, language: str):
        '''
        언어를 설정하는 함수입니다.
        '''
        cls.__language = language
        cls._updateAllObjs() # 언어가 변경되면 로컬라이제이션과 관련된 모든 오브젝트의 텍스트를 업데이트합니다.

    @classmethod
    def getLanguage(cls):
        '''
        현재 언어를 반환하는 함수입니다.
        '''
        return cls.__language
    
    @classmethod
    def getFont(cls,key=None):
        '''
        폰트를 반환하는 함수입니다.
        '''
        if key==None:
            key = "default"
        if key in cls.__fonts:
            return cls.__fonts[key][REMOLocalizeManager.getLanguage()]

    @classmethod
    def manageObj(cls,obj,key,*,font=None,callback=lambda obj:None):
        '''
        오브젝트의 텍스트를 관리하는 함수입니다. 이후 언어 변경이 있을 때마다 텍스트가 업데이트됩니다.
        callback을 지정하면 업데이트시 함수가 호출됩니다.
        '''
        obj_id = id(obj)
        REMOLocalizeManager.__localizationPipeline[obj_id]={"obj":obj,"key":key,"font":font,"callback":callback}
        REMOLocalizeManager._updateObj(obj,key,font=font,callback=callback)
        return


    @classmethod
    def _updateObj(cls, obj, key,*,font=None,callback=lambda obj:None):
        '''
        개별 오브젝트의 텍스트를 업데이트하는 함수입니다.
        폰트를 지정하면 해당 폰트로 텍스트를 업데이트합니다.
        '''
        language = cls.getLanguage()
        if key in cls.__translations and language in cls.__translations[key]:
            translated_text = cls.__translations[key][language]
            obj.text = translated_text  # 오브젝트에 번역된 텍스트를 설정하는 메서드
            obj.font = REMOLocalizeManager.getFont(font)
            callback(obj)

    @classmethod
    def _updateAllObjs(cls):
        '''
        로컬라이제이션 파이프라인에 등록된 모든 오브젝트의 텍스트를 업데이트하는 함수입니다.
        '''
        for key in cls.__localizationPipeline:
            item = cls.__localizationPipeline[key]
            obj = item["obj"]
            key = item["key"]
            font = item["font"]
            callback = item["callback"]
            cls._updateObj(obj, key, font=font, callback=callback)

    @classmethod
    def importTranslations(cls, translations: dict):
        '''
        번역 데이터를 가져오는 함수입니다.
        번역 데이터는 {"hello": {"en": "Hello", "kr": "안녕하세요"}}와 같은 형식으로 구성됩니다.
        '''
        cls.__translations.update(translations)

    @classmethod
    def importFonts(cls, fonts: dict):
        '''
        폰트 데이터를 가져오는 함수입니다.
        폰트 데이터는 {"default": {"en": "Arial", "kr": "맑은 고딕"}}과 같은 형식으로 구성됩니다.
        '''
        cls.__fonts.update(fonts)

    @classmethod
    def getText(cls, key: str):
        '''
        키에 해당하는 텍스트를 반환하는 함수입니다.
        '''
        language = cls.getLanguage()
        if key in cls.__translations and language in cls.__translations[key]:
            return cls.__translations[key][language]
        raise KeyError(f"Key '{key}' not found in translations for language '{language}'")

class EventManager:
    '''
    게임 내에서 발생하는 이벤트와 트리거를 관리하는 클래스입니다.
    event, trigger(Enum 타입)으로 이벤트를 관리합니다.
    '''
    __triggers = {}
    __events = {}
    __event_counters = {}

    @classmethod
    def activateTrigger(cls, *triggers: Enum):
        """
        여러 트리거를 한 번에 활성화하는 클래스 메서드.
        """
        for trigger in triggers:
            cls.__triggers[trigger] = True

    @classmethod
    def disableTrigger(cls, *triggers: Enum):
        """
        여러 트리거를 한 번에 비활성화하는 클래스 메서드.
        """
        for trigger in triggers:
            cls.__triggers[trigger] = False

    @classmethod
    def checkTrigger(cls, *triggers: Enum, operation="and"):
        """
        트리거들을 AND/OR 조건에 따라 확인하는 클래스 메서드.
        :param operation: "and" 또는 "or" (기본값은 "and")
        :param *triggers: 확인할 트리거 리스트
        :return: AND 연산일 경우 모두 True면 True, OR 연산일 경우 하나라도 True면 True
        """
        if operation == "and":
            return all(cls.__triggers.get(trigger, False) for trigger in triggers)
        elif operation == "or":
            return any(cls.__triggers.get(trigger, False) for trigger in triggers)
        else:
            raise ValueError("operation must be 'and' or 'or'")

    @classmethod
    def addEvent(cls, event_name: Enum, listener):
        """
        새로운 이벤트 리스너를 특정 이벤트에 추가합니다.
        :param event_name: 이벤트의 이름 또는 키.
        :param listener: 이벤트가 발생할 때 호출될 함수(리스너).
        """
        if event_name not in cls.__events:
            cls.__events[event_name] = []
            cls.__event_counters[event_name] = 0  # 이벤트 카운터 초기화
        cls.__events[event_name].append(listener)

    @classmethod
    def occurEvent(cls, event_name: Enum, *args, required_triggers=None, trigger_operation="and", **kwargs):
        """
        특정 이벤트가 발생했을 때 트리거를 확인하고, 등록된 리스너를 호출하며 카운터를 증가시킵니다.
        :param event_name: 발생한 이벤트의 이름.
        :param required_triggers: 이벤트 발생에 필요한 트리거 리스트.
        :param trigger_operation: "and" 또는 "or" (기본값은 "and")
        :param *args: 리스너에 전달될 위치 기반 인자들.
        :param **kwargs: 리스너에 전달될 키워드 기반 인자들.
        """
        # 트리거 조건 확인
        if required_triggers:
            if not cls.checkTrigger(*required_triggers, operation=trigger_operation):
                print(f"이벤트 '{event_name}'는 필요한 트리거 조건을 만족하지 않습니다.")
                return

        if event_name in cls.__events:
            cls.__event_counters[event_name] += 1
            for listener in cls.__events[event_name]:
                listener(*args, **kwargs)
        else:
            print(f"이벤트 '{event_name}'가 존재하지 않습니다.")

    @classmethod
    def getEventCount(cls, event_name):
        """
        특정 이벤트가 몇 번 호출되었는지 반환합니다.
        :param event_name: 이벤트의 이름.
        :return: 이벤트 호출 횟수.
        """
        return cls.__event_counters.get(event_name, 0)
