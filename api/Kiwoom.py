from PyQt5.QAxContainer import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import time
import pandas as pd
import json
from util.const import *


class Kiwoom(QAxWidget):
    def __init__(self):
        super().__init__()

        self._make_kiwoom_instance()
        self._set_signal_slots()
        self._comm_connect()
        """ Login 과정 
        1. 설치한 API를 사용할 수 있도록 설정합니다. (_make_kiwoom_instance)
        2. 로그인, 실시간 정보, 기타 제공받을 수 있는 데이터에 대한 응답을 받을 수 있는 slot함수들을 등록합니다. (_set_signal_slots)
        3. 로그인 요청을 보냅니다 (_comm_connect)
        4. 로그인 요청에 대한 응답을 _set_signal_slots를 사용하여 등록한 슬롯(_login_slot)에서 받아 옵니다.
        """
        

        # account 정보 800111111; (;로 구분)
        self.account_number = self.get_account_number()
        print(self.account_number, "------------")

        self.tr_event_loop = QEventLoop()

        self.order = {}
        self.balance = {}
        # 실시간 체결정보를 저장할 딕셔너리 선언
        self.universe_realtime_transaction_info = {}
        # 실시가 호가잔량를 저장할 딕셔너리 선언
        self.kiwoom_realtime_hoga_info = {}

        self.json_f = []
        self.jsonCount = 0
        self.json_f2 = []
        self.jsonCount2 = 0

    #  Kiwoom class가 api를 사용할 수 있도록
    def _make_kiwoom_instance(self):
        self.setControl("KHOPENAPI.KHOpenAPICtrl.1")

    def _set_signal_slots(self):
        """ ****** API로 보내는 요청들을 받아올 slot을 등록하는 함수
            목적에 맞게 여러개의 slot을 설정하고 설정할 수 있음. 
        """
        # 로그인 응답의 결과를 _on_login_connect을 통해 받도록 설정
        self.OnEventConnect.connect(self._login_slot)


        # TR의 응답 결과를 _on_receive_tr_data를 통해 받도록 설정
        self.OnReceiveTrData.connect(self._on_receive_tr_data)
        # TR/주문 메시지를 _on_receive_msg을 통해 받도록 설정
        self.OnReceiveMsg.connect(self._on_receive_msg)
        # 주문 접수/체결 결과를 _on_chejan_slot을 통해 받도록 설정
        self.OnReceiveChejanData.connect(self._on_chejan_slot)

        # 실시간 체결 데이터를 _on_receive_real_data을 통해 받도록 설정
        self.OnReceiveRealData.connect(self._on_receive_real_data)

    def _login_slot(self, err_code):
        if err_code == 0:
            print("connected")
        else:
            print("not connected")

        self.login_event_loop.exit()

    def _comm_connect(self):
        # API서버로 로그인을 요청하는 함수. 
        self.dynamicCall("CommConnect()")

        # 로그인 시도 결과에 대해 응답 대기 시작. 
        self.login_event_loop = QEventLoop()
        self.login_event_loop.exec_()

    """
    ACCOUNT_CNT : 게좌 수, ACCLIST or ACCNO : 목록;목록
    USER_ID : id, USER_NAME : name 
    GetServerGubun : 1-모의, 나머지-실서버, KEY_BSECGB : 키보드 보안 해지 여부 (0-정상, 1-해지)
    FIREW_SECGB : 방화벽 설정 여부 (0-미설정, 1-설정, 2-해지)
    """
    def get_account_number(self, tag="ACCNO"):
        account_list = self.dynamicCall("GetLoginInfo(QString)", tag)  # tag로 전달한 요청에 대한 응답을 받아옴
        account_number = account_list.split(';')[0]
        print(account_number, account_list)
        return account_number

    def get_code_list_by_market(self, market_type):
        code_list = self.dynamicCall("GetCodeListByMarket(QString)", market_type)
        code_list = code_list.split(';')[:-1]
        return code_list

    def get_master_code_name(self, code):
        code_name = self.dynamicCall("GetMasterCodeName(QString)", code)
        return code_name

    def get_price_data(self, code):
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
        self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 0, "0001")

        self.tr_event_loop.exec_()

        ohlcv = self.tr_data

        while self.has_next_tr_data:
            self.dynamicCall("SetInputValue(QString, QString)", "종목코드", code)
            self.dynamicCall("SetInputValue(QString, QString)", "수정주가구분", "1")
            self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10081_req", "opt10081", 2, "0001")
            self.tr_event_loop.exec_()

            for key, val in self.tr_data.items():
                ohlcv[key] += val

        df = pd.DataFrame(ohlcv, columns=['open', 'high', 'low', 'close', 'volume'], index=ohlcv['date'])

        return df[::-1]

    def _on_receive_tr_data(self, screen_no, rqname, trcode, record_name, next, unused1, unused2, unused3, unused4):
        "TR조회의 응답 결과를 얻어오는 함수"
        print("[Kiwoom] _on_receive_tr_data is called {} / {} / {}".format(screen_no, rqname, trcode))
        tr_data_cnt = self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname)

        if next == '2':
            self.has_next_tr_data = True
        else:
            self.has_next_tr_data = False

        if rqname == "opt10081_req":    # 주식일봉차트조회요청
            ohlcv = {'date': [], 'open': [], 'high': [], 'low': [], 'close': [], 'volume': []}

            for i in range(tr_data_cnt):
                date = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "일자")
                open = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시가")
                high = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "고가")
                low = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "저가")
                close = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                volume = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "거래량")

                ohlcv['date'].append(date.strip())
                ohlcv['open'].append(int(open))
                ohlcv['high'].append(int(high))
                ohlcv['low'].append(int(low))
                ohlcv['close'].append(int(close))
                ohlcv['volume'].append(int(volume))

            self.tr_data = ohlcv

        elif rqname == "opw00001_req":      #예수금 상세현황 요청
            deposit = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, 0, "주문가능금액")
            self.tr_data = int(deposit)
            print(self.tr_data)

        elif rqname == "opt10075_req":  # 미체결요청
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목코드")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                order_number = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문번호")
                order_status = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문상태")
                order_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문수량")
                order_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문가격")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                order_type = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "주문구분")
                left_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "미체결수량")
                executed_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "체결량")
                ordered_at = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "시간")
                fee = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매수수료")
                tax = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "당일매매세금")

                # 데이터 형변환 및 가공
                code = code.strip()
                code_name = code_name.strip()
                order_number = str(int(order_number.strip()))
                order_status = order_status.strip()
                order_quantity = int(order_quantity.strip())
                order_price = int(order_price.strip())

                current_price = int(current_price.strip().lstrip('+').lstrip('-'))
                order_type = order_type.strip().lstrip('+').lstrip('-')  # +매수,-매도처럼 +,- 제거
                left_quantity = int(left_quantity.strip())
                executed_quantity = int(executed_quantity.strip())
                ordered_at = ordered_at.strip()
                fee = int(fee)
                tax = int(tax)

                # code를 key값으로 한 딕셔너리 변환
                self.order[code] = {
                    '종목코드': code,
                    '종목명': code_name,
                    '주문번호': order_number,
                    '주문상태': order_status,
                    '주문수량': order_quantity,
                    '주문가격': order_price,
                    '현재가': current_price,
                    '주문구분': order_type,
                    '미체결수량': left_quantity,
                    '체결량': executed_quantity,
                    '주문시간': ordered_at,
                    '당일매매수수료': fee,
                    '당일매매세금': tax
                }

            self.tr_data = self.order

        elif rqname == "opw00018_req":      # 계좌 평가잔고 내역요청
            for i in range(tr_data_cnt):
                code = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목번호")
                code_name = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "종목명")
                quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "보유수량")
                purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "매입가")
                return_rate = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "수익률(%)")
                current_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i, "현재가")
                total_purchase_price = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,"매입금액")
                available_quantity = self.dynamicCall("GetCommData(QString, QString, int, QString", trcode, rqname, i,"매매가능수량")

                # 데이터 형변환 및 가공
                code = code.strip()[1:]
                code_name = code_name.strip()
                quantity = int(quantity)
                purchase_price = int(purchase_price)
                return_rate = float(return_rate)
                current_price = int(current_price)
                total_purchase_price = int(total_purchase_price)
                available_quantity = int(available_quantity)

                # code를 key값으로 한 딕셔너리 변환
                self.balance[code] = {
                    '종목명': code_name,
                    '보유수량': quantity,
                    '매입가': purchase_price,
                    '수익률': return_rate,
                    '현재가': current_price,
                    '매입금액': total_purchase_price,
                    '매매가능수량': available_quantity
                }

            self.tr_data = self.balance

        self.tr_event_loop.exit()
        time.sleep(0.5)

    def get_deposit(self):
        #print("rrrrrrr", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "2")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00001_req", "opw00001", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def send_order(self, rqname, screen_no, order_type, code, order_quantity, order_price, order_classification, origin_order_number=""):
        order_result = self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",[rqname, screen_no, self.account_number, order_type, code, order_quantity, order_price,order_classification, origin_order_number])
        return order_result

    def _on_receive_msg(self, screen_no, rqname, trcode, msg):
        print("[Kiwoom] _on_receive_msg is called {} / {} / {} / {}".format(screen_no, rqname, trcode, msg))

    def _on_chejan_slot(self, s_gubun, n_item_cnt, s_fid_list):
        print("[Kiwoom] _on_chejan_slot is called {} / {} / {}".format(s_gubun, n_item_cnt, s_fid_list))

        # 9201;9203;9205;9001;912;913;302;900;901;처럼 전달되는 fid 리스트를 ';' 기준으로 구분함
        for fid in s_fid_list.split(";"):
            if fid in FID_CODES:
                # 9001-종목코드 얻어오기, 종목코드는 A007700처럼 앞자리에 문자가 오기 때문에 앞자리를 제거함
                code = self.dynamicCall("GetChejanData(int)", '9001')[1:]

                # fid를 이용해 data를 얻어오기(ex: fid:9203를 전달하면 주문번호를 수신해 data에 저장됨)
                data = self.dynamicCall("GetChejanData(int)", fid)

                # 데이터에 +,-가 붙어있는 경우 (ex: +매수, -매도) 제거
                data = data.strip().lstrip('+').lstrip('-')

                # 수신한 데이터는 전부 문자형인데 문자형 중에 숫자인 항목들(ex:매수가)은 숫자로 변형이 필요함
                if data.isdigit():
                    data = int(data)

                # fid 코드에 해당하는 항목(item_name)을 찾음(ex: fid=9201 > item_name=계좌번호)
                item_name = FID_CODES[fid]

                # 얻어온 데이터를 출력(ex: 주문가격 : 37600)
                print("{}: {}".format(item_name, data))

                # 접수/체결(s_gubun=0)이면 self.order, 잔고이동이면 self.balance에 값을 저장
                if int(s_gubun) == 0:
                    # 아직 order에 종목코드가 없다면 신규 생성하는 과정
                    if code not in self.order.keys():
                        self.order[code] = {}

                    # order 딕셔너리에 데이터 저장
                    self.order[code].update({item_name: data})
                elif int(s_gubun) == 1:
                    # 아직 balance에 종목코드가 없다면 신규 생성하는 과정
                    if code not in self.balance.keys():
                        self.balance[code] = {}

                    # order 딕셔너리에 데이터 저장
                    self.balance[code].update({item_name: data})

        # s_gubun값에 따라 저장한 결과를 출력
        if int(s_gubun) == 0:
            print("* 주문 출력(self.order)")
            print(self.order)
        elif int(s_gubun) == 1:
            print("* 잔고 출력(self.balance)")
            print(self.balance)

    def get_order(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "체결구분", "0")  # 0:전체, 1:미체결, 2:체결
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")  # 0:전체, 1:매도, 2:매수
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10075_req", "opt10075", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    def get_balance(self):
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")
        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00018_req", "opw00018", 0, "0002")

        self.tr_event_loop.exec_()
        return self.tr_data

    """
        str_screen_no:화면번호, str_code_list:종목코드리스트, str_fidlist:실시간fid리스트, str_opt_type:실시간 등록타입, 0 or 1
        한번에 100종목 100fid개수 가능 
        fid는 고유 번호들 - util/const.py 에 정의해 두었음. 
        opt_type :0 이면 초기화 신규 등록, 1이면 추가해서 등록 
    """
    def set_real_reg(self, str_screen_no, str_code_list, str_fid_list, str_opt_type):
        self.dynamicCall("SetRealReg(QString, QString, QString, QString)", str_screen_no, str_code_list, str_fid_list, str_opt_type)
        time.sleep(0.5)

    def _on_receive_real_data(self, s_code, real_type, real_data):
        #print ("call _on_receive_real_data")
        #print (s_code, real_type)
        if real_type == "장시작시간":
            pass

        # 장시작 전. 
        #if real_type == "주식예상체결":
        #    signed_at = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("체결시간"))

        #    close = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("현재가"))
        #    close = abs(int(close))

        #    print (signed_at, close)
        #    pass

        if real_type == "주식호가잔량":
            #print ("hoga----------------------------------------")
            signed_at = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("호가시간"))
            total_hoga_sell = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 총잔량"))
            total_hoga_sell = abs(int(total_hoga_sell))
            total_hoga_sell_b_rate = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 총잔량 직전대비"))
            total_hoga_sell_b_rate = abs(int(total_hoga_sell_b_rate))

            hoga_sell_1 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가1"))
            hoga_sell_1 = abs(int(hoga_sell_1))
            hoga_sell_2 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가2"))
            hoga_sell_2 = abs(int(hoga_sell_2))
            hoga_sell_3 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가3"))
            hoga_sell_3 = abs(int(hoga_sell_3))
            hoga_sell_4 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가4"))
            hoga_sell_4 = abs(int(hoga_sell_4))
            hoga_sell_5 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가5"))
            hoga_sell_5 = abs(int(hoga_sell_5))
            hoga_sell_6 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가6"))
            hoga_sell_6 = abs(int(hoga_sell_6))
            hoga_sell_7 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가7"))
            hoga_sell_7 = abs(int(hoga_sell_7))
            hoga_sell_8 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가8"))
            hoga_sell_8 = abs(int(hoga_sell_8))
            hoga_sell_9 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가9"))
            hoga_sell_9 = abs(int(hoga_sell_9))
            hoga_sell_10 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가10"))
            hoga_sell_10 = abs(int(hoga_sell_10))
            
            hoga_sell_1_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량1"))
            hoga_sell_1_cnt = abs(int(hoga_sell_1_cnt))
            hoga_sell_2_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량2"))
            hoga_sell_2_cnt = abs(int(hoga_sell_2_cnt))
            hoga_sell_3_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량3"))
            hoga_sell_3_cnt = abs(int(hoga_sell_3_cnt))
            hoga_sell_4_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량4"))
            hoga_sell_4_cnt = abs(int(hoga_sell_4_cnt))
            hoga_sell_5_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량5"))
            hoga_sell_5_cnt = abs(int(hoga_sell_5_cnt))
            hoga_sell_6_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량6"))
            hoga_sell_6_cnt = abs(int(hoga_sell_6_cnt))
            hoga_sell_7_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량7"))
            hoga_sell_7_cnt = abs(int(hoga_sell_7_cnt))
            hoga_sell_8_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량8"))
            hoga_sell_8_cnt = abs(int(hoga_sell_8_cnt))
            hoga_sell_9_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량9"))
            hoga_sell_9_cnt = abs(int(hoga_sell_9_cnt))
            hoga_sell_10_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매도호가 수량10"))
            hoga_sell_10_cnt = abs(int(hoga_sell_10_cnt))
            
            

            total_hoga_buy = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 총잔량"))
            total_hoga_buy = abs(int(total_hoga_buy))

            total_hoga_buy_b_rate = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 총잔량 직전대비"))
            total_hoga_buy_b_rate = abs(int(total_hoga_sell_b_rate))

            hoga_buy_1 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가1"))
            hoga_buy_1 = abs(int(hoga_buy_1))
            hoga_buy_2 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가2"))
            hoga_buy_2 = abs(int(hoga_buy_2))
            hoga_buy_3 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가3"))
            hoga_buy_3 = abs(int(hoga_buy_3))
            hoga_buy_4 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가4"))
            hoga_buy_4 = abs(int(hoga_buy_4))
            hoga_buy_5 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가5"))
            hoga_buy_5 = abs(int(hoga_buy_5))
            hoga_buy_6 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가6"))
            hoga_buy_6 = abs(int(hoga_buy_6))
            hoga_buy_7 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가7"))
            hoga_buy_7 = abs(int(hoga_buy_7))
            hoga_buy_8 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가8"))
            hoga_buy_8 = abs(int(hoga_buy_8))
            hoga_buy_9 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가9"))
            hoga_buy_9 = abs(int(hoga_buy_9))
            hoga_buy_10 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가10"))
            hoga_buy_10 = abs(int(hoga_buy_10))

            hoga_buy_1_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량1"))
            hoga_buy_1_cnt = abs(int(hoga_buy_1_cnt))
            hoga_buy_2_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량2"))
            hoga_buy_2_cnt = abs(int(hoga_buy_2_cnt))
            hoga_buy_3_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량3"))
            hoga_buy_3_cnt = abs(int(hoga_buy_3_cnt))
            hoga_buy_4_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량4"))
            hoga_buy_4_cnt = abs(int(hoga_buy_4_cnt))
            hoga_buy_5_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량5"))
            hoga_buy_5_cnt = abs(int(hoga_buy_5_cnt))
            hoga_buy_6_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량6"))
            hoga_buy_6_cnt = abs(int(hoga_buy_6_cnt))
            hoga_buy_7_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량7"))
            hoga_buy_7_cnt = abs(int(hoga_buy_7_cnt))
            hoga_buy_8_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량8"))
            hoga_buy_8_cnt = abs(int(hoga_buy_8_cnt))
            hoga_buy_9_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량9"))
            hoga_buy_9_cnt = abs(int(hoga_buy_9_cnt))
            hoga_buy_10_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("매수호가 수량10"))
            hoga_buy_10_cnt = abs(int(hoga_buy_10_cnt))

            

            #누적거래량
            total_trade_cnt = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("누적거래량"))
            total_trade_cnt = abs(int(total_trade_cnt))
            
            # kiwoom_realtime_hoga_info 딕셔너리에 종목코드가 키값으로 존재하지 않는다면 생성(해당 종목 실시간 데이터 최초 수신시)
            if s_code not in self.kiwoom_realtime_hoga_info:
                self.kiwoom_realtime_hoga_info.update({s_code: {}})

            # 최초 수신 이후 계속 수신되는 데이터는 update를 이용해서 값 갱신
            self.kiwoom_realtime_hoga_info[s_code].update({
                "호가시간": signed_at,
                "누적거래량" : total_trade_cnt, 

                "매도호가 총잔량": total_hoga_sell,
                "매도호가 총잔량 직전대비" : total_hoga_sell_b_rate,

                "매수호가 총잔량": total_hoga_buy,
                "매수호가 총잔량 직전대비" : total_hoga_buy_b_rate,

                "매도호가1" : hoga_sell_1, 
                "매도호가2" : hoga_sell_2, 
                "매도호가3" : hoga_sell_3, 
                "매도호가4" : hoga_sell_4, 
                "매도호가5" : hoga_sell_5, 
                "매도호가6" : hoga_sell_6, 
                "매도호가7" : hoga_sell_7, 
                "매도호가8" : hoga_sell_8, 
                "매도호가9" : hoga_sell_9, 
                "매도호가10" : hoga_sell_10,  

                "매도호가 수량1" : hoga_sell_1_cnt,
                "매도호가 수량2" : hoga_sell_2_cnt,
                "매도호가 수량3" : hoga_sell_3_cnt,
                "매도호가 수량4" : hoga_sell_4_cnt,
                "매도호가 수량5" : hoga_sell_5_cnt,
                "매도호가 수량6" : hoga_sell_6_cnt,
                "매도호가 수량7" : hoga_sell_7_cnt,
                "매도호가 수량8" : hoga_sell_8_cnt,
                "매도호가 수량9" : hoga_sell_9_cnt,
                "매도호가 수량10" : hoga_sell_10_cnt,



                "매수호가1" : hoga_buy_1, 
                "매수호가2" : hoga_buy_2, 
                "매수호가3" : hoga_buy_3, 
                "매수호가4" : hoga_buy_4, 
                "매수호가5" : hoga_buy_5, 
                "매수호가6" : hoga_buy_6, 
                "매수호가7" : hoga_buy_7, 
                "매수호가8" : hoga_buy_8, 
                "매수호가9" : hoga_buy_9, 
                "매수호가10" : hoga_buy_10,

                "매수호가 수량1" : hoga_buy_1_cnt,
                "매수호가 수량2" : hoga_buy_2_cnt,
                "매수호가 수량3" : hoga_buy_3_cnt,
                "매수호가 수량4" : hoga_buy_4_cnt,
                "매수호가 수량5" : hoga_buy_5_cnt,
                "매수호가 수량6" : hoga_buy_6_cnt,
                "매수호가 수량7" : hoga_buy_7_cnt,
                "매수호가 수량8" : hoga_buy_8_cnt,
                "매수호가 수량9" : hoga_buy_9_cnt,
                "매수호가 수량10" : hoga_buy_10_cnt

            })

            #self.json_f2.append( [s_code,self.kiwoom_realtime_hoga_info[s_code]])
            #self.jsonCount2 += 1
            #if self.jsonCount2 % 1000 == 0:
            #    with open('real_real_hoga.json','w') as f:
            #        json.dump(self.json_f2,f)

        if real_type == "주식체결":
            signed_at = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("체결시간"))

            close = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid("현재가"))
            close = abs(int(close))

            high = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('고가'))
            high = abs(int(high))

            open1 = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('시가'))
            open1 = abs(int(open1))

            low = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('저가'))
            low = abs(int(low))

            top_priority_ask = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('(최우선)매도호가'))
            top_priority_ask = abs(int(top_priority_ask))

            top_priority_bid = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('(최우선)매수호가'))
            top_priority_bid = abs(int(top_priority_bid))

            accum_volume = self.dynamicCall("GetCommRealData(QString, int)", s_code, get_fid('누적거래량'))
            accum_volume = abs(int(accum_volume))

            # print(s_code, signed_at, close, high, open1, low, top_priority_ask, top_priority_bid, accum_volume)

            # universe_realtime_transaction_info 딕셔너리에 종목코드가 키값으로 존재하지 않는다면 생성(해당 종목 실시간 데이터 최초 수신시)
            if s_code not in self.universe_realtime_transaction_info:
                self.universe_realtime_transaction_info.update({s_code: {}})

            # 최초 수신 이후 계속 수신되는 데이터는 update를 이용해서 값 갱신
            self.universe_realtime_transaction_info[s_code].update({
                "체결시간": signed_at,
                "시가": open1,
                "고가": high,
                "저가": low,
                "현재가": close,
                "(최우선)매도호가": top_priority_ask,
                "(최우선)매수호가": top_priority_bid,
                "누적거래량": accum_volume
            })
            #print ("-------------------------------------")
            #self.json_f.append( [s_code,self.universe_realtime_transaction_info[s_code]])
            #self.jsonCount += 1
            #if self.jsonCount % 10 == 0:
            #    with open('real_real_uni.json','w') as f:
            #        json.dump(self.json_f,f)
