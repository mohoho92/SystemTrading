# 쉽게 따라 만드는 주식자동매매시스템
- conda activate py38_32

# git hub 사용법
- https://technote.kr/353


# 환경설정
windows 
- anaconda 설치 (kiwoom api는 32bits) : 64bits용으로 설치하였음. 
-- conda 가상 환경을 만들고 32bits로 변경할 수 있음. 
-- https://separang.tistory.com/107 
-- conda create -n '가상환경 이름'  // 예 py38_32
-- conda activate '가상환경 이름'
-- conda config --env --set subdir win-32
-- conda install python=3.8        // 가상환경 안에서 설치해야 함. 
-- conda info
-- python (32bits 확인)
-- import platform
-- print(Platform.architecture())
- 코드 실행시 발행하는 에러는 pip install로 설치하면 됨. 

- vscode 설치
https://code.visualstudio.com/download

- PyQt5
Kiwoom API는 ActiveX Control인 OCX방식으로 연결하게 되어 있음. (32bits)
(base) conda env list
(base) conda activate py38_32
(py38_32) pip install pyqt5 

- 키움 API 
https://www.kiwoom.com/h/customer/download/VOpenApiInfoView?dummyVal=0
pykiwoom은 계속해서 업데이트 되고 있는 모듈입니다. 한 번 설치한 후에도 최신 버전이 나왔다면 여러분도 새로 설치를 해야합니다. 기존에 설치된 버전을 지우고 새로 설치하려면 아나콘다 프롬프트를 실행한 후 다음과 같이 입력하면 됩니다.
pip install -U pykiwoom
최근 버전은 다음 웹 페이지를 통해 확인할 수 있습니다.
https://pypi.org/project/pykiwoom/



- System Trading 구조
|--- api package
|------ __init__.py  // api 폴더가 package임을 표시한 빈파일
|------ Kiwoom.py 
|--- util package
|------ __init__.py
|--- strategy package
|------ __init__.py
---- main.py


- 실현 계획
1) 관심종목 리스트를 화면에 보여주기 (csv 파일로 읽어오는게 빠를것 같다)
2) 관심종목별 시가를 확인하고, 장 시작 후 시가 아래로 갔다가 시가를 돌파할때 1차 매수 하기. 
: case 1 - 시가 아래로 안내려 오는 경우 > 매수하지 않음
: case 2 - 시가 근처에서 왔다 갔다 하는 경우 

매도 조건
: 매수가 보다 -1% 떨어 진 경우 매도  (손절)
: 매수 후 3분이 지나면 자동 매도 (강세종목이고, 시가에서 올라가는 종목임으로) (손절 or 익절)
  :: 손실일 경우도 팔 것인가???
: 매수 후 목표 %에 도달하면 매도 



- 참고사이트
https://wikidocs.net/book/1173  // 퀀트투자를 위한 키움증권 API (파이썬 버전)
https://doc.qt.io/qtforpython-6/examples/example_axcontainer_axviewer.html  // Qt for python, win32지원 안함. pyQt5로해야 함.
https://doc.qt.io/qt-5/reference-overview.html 
https://doc.qt.io/qtforpython-5/gettingstarted.html 
https://trustyou.tistory.com/  // 참고사이트
https://auto-trading.tistory.com/category/%EC%A3%BC%EC%8B%9D%20%EC%9E%90%EB%8F%99%EB%A7%A4%EB%A7%A4%20%EA%B0%95%EC%9D%98
https://cafe.naver.com/moneytuja/1212?boardType=L
https://wikidocs.net/book/110  // 파이썬으로 배우는 알고리즘 트레이딩 (개정판-2쇄)

- Qt
https://coding-kindergarten.tistory.com/171

- google 
https://jofresh.tistory.com/entry/%ED%8C%8C%EC%9D%B4%EC%8D%AC%EA%B5%AC%EA%B8%80%EC%8B%9C%ED%8A%B8-%ED%8C%8C%EC%9D%B4%EC%8D%AC%EC%9C%BC%EB%A1%9C-%EA%B5%AC%EA%B8%80%EC%8A%A4%ED%94%84%EB%A0%88%EB%93%9C%EC%8B%9C%ED%8A%B8-%EC%9E%91%EC%84%B1%ED%95%98%EA%B8%B0with-gspread-%EB%9D%BC%EC%9D%B4%EB%B8%8C%EB%9F%AC%EB%A6%AC
https://greeksharifa.github.io/references/2023/04/10/gspread-usage/



- 기능개발 항목
1. csv 파일에서 읽어서 target items 초기화 하기. (프로그램 시작시)
i) 파일은 strategy 폴더에 있음. (target_times.csv) 
: 한글 깨지는 문제는 확인 필요 마지막 ticker값만 얻어 오면 됨.
: 추가적인 초기 정보 (전일가등)등은 hts에서 관심종목 필드 추가/삭제를 통해 가져 올 수 있음.  


"""
             {
            '종목코드' : "042700",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "007660",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "031980",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "317330",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "028300",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "405100",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "086790",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "000270",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "196170",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "141080",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            {
            '종목코드' : "028300",
            'is시가Down'    : False,   #시가 아래로 내려가면 True
            '주문수량'      : 10,       # 10주, 살수 있는 가격으로 나중에 계산 필요.
            '매수금액'      : 2000000,  # 매수 금액이 필요할 수 있다.  
            'CntAfterOrder' : 0,        # 매수 후 채결정보 받은 cnt,  매수후 바로 팔지 않도록 사용할 수 있음.
            'is시가UpAgain' : False,   #시가 아래로 갔다 올라오면 True
            '목표수익율'        : 2,        # 2% 수익나면 익절
            '매수시현재가'      : 0,     # 매수가격
            '매수시저가'        : 0,     # 매수시점 저점 가격 저장으로 매도시 사용 함.
            '체결수신Cnt'       : 0,     # 체결정보 수신 Cnt
            },
            """