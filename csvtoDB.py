#_*_coding:utf-8 _*_

import pandas as pd
import numpy as np
import glob
import re
import copy
import json
import urllib.request as urls
import pymysql
import googlemaps

from sqlalchemy import create_engine

#사용자가 사용가능한 기능메뉴 출력
def menu():
     print('-------MENU-------')
     print('1. 물고기+판매장정보 DB생성')
     print('2. 전체 데이터 DB생성')
     print('3. 그만하기')
     return int(input('원하는 메뉴의 번호를 입력하세요: '))

def writedb(sql) :
     #mysql에 넣기
     conn = pymysql.connect(host='localhost', user='root', password='ohgg805**',db='fishchips',charset='utf8')
     curs = conn.cursor() #db 연결
     curs.execute(sql) #인서트문 실행!
     conn.commit()
     conn.close() #db 닫기

#datafame 바로 테이블로 생성해서 넣기
def writetable(dataframe,tablename) : 
     try:
          pymysql.install_as_MySQLdb()
          import MySQLdb #쿼리문 여러개를 동시에 실행하기 위해 설정
          engine = create_engine("mysql://root:ohgg805**@localhost:3306/fishchips",encoding="utf8")
          conn = engine.connect()
          dataframe.to_sql(name=tablename, con = engine, if_exists="replace", index=False)
          #같은 이름의 테이블이 있으면 현재 데이터로 다시 테이블 생성
          conn.close() #db 닫기
     except Exception as er:
        print(er)
     else:
        print('DB_Completed!!')

def fishloc(total_data) :
     #copy.deepcopy - 값만 복사해옴
     itemList = copy.deepcopy(total_data) #물고기 + 상태 + kg당 가격 + 위판장코드
     itemList.drop(itemList.columns.difference([colList[1], colList[3], colList[6], colList[9]]), axis='columns', inplace=True)
     #필요한 부분만 두고 삭제 (itemList.columns.difference괄호 안에 있는 list를 제외한 부분만 삭제)
     itemList = itemList.drop_duplicates() #중복제거
     '''
     fishList = copy.deepcopy(itemList) #물고기+상태 목록
     fishList.drop(fishList.columns.difference([colList[1], colList[3]]), axis='columns', inplace=True)
     #필요한 부분만 두고 삭제 (itemList.columns.difference괄호 안에 있는 list를 제외한 부분만 삭제)
     fishList = fishList.drop_duplicates() #중복제거
     writetable(fishList,'fish') #중복제거한 물고기+상태 목록을 바로 db에 table을 만들어서 저장
     print('물고기목록 완료')
     print(fishList)
     print()
     '''
     locList = copy.deepcopy(itemList[colList[6]]) #위판장코드 목록
     locList = locList.drop_duplicates() #중복제거
     print('중복제거한 위판장코드목록 완료')
     print(locList)
     print()

     #잘못 들어간 주소를 위해 사용할 딕셔너리 (ex.울산 어디구 / 부산광역시어디구)
     loc_jump = {'서울':'특별시', '부산':'광역시', '대구':'광역시', '인천':'광역시', '광주':'광역시', '대전':'광역시', '울산':'광역시',
            '경기':'도', '강원':'도', '충청북':'도', '충청남':'도', '경상북':'도', '경상남':'도', '전라북':'도', '전라남':'도', '제주':'특별자치도', '세종':'특별자치시'}
     loc_check = ['서울특별시','부산광역시','대구광역시','인천광역시','광주광역시','대전광역시','울산광역시','경기도','강원도','충청북도','충청남도','경상북도','경상남도','전라북도','전라남도','제주특별자치도','세종특별자치시']

     #위판장코드가 있어도 해양수산부 api에서 검색이 안된다면 걸러줘야함
     #위판장코드로 해양수산부 api에서 주소를 얻어오고
     #그렇게 얻은 주소를 구글 지도 api를 사용해 위도와 경도를 가져옴
     for loc in locList : #중복제거한 위판장코드만큼 반복
          print('위판장코드 : '+loc)
          try :
               url = 'http://apis.data.go.kr/1192000/openapi/service/ManageAcst0020Service/getAcst0020List?'
               url += 'serviceKey=F0ssmsR5BKAu4znvMzU9h9hjG4ZvlO2dwBnESSqI81NS0XH0JrrzxbuxemlQXAUKS6AOKpgSRJkSDtwu5W%2BTVA%3D%3D'
               url += '&numOfRows=10&pageNo=1&type=json&csmtmktCode='+loc
               #해양수산부 api에 위판장코드를 넣고 검색할 url

               request = urls.Request(url)
               request.get_method = lambda: 'GET'
               response_body = urls.urlopen(request).read()
               json_data = json.loads(response_body)
               #api가 응답한 메시지를 json으로 가져옴

               #응답한 메시지가 여러개 있을 수 있으므로 반복해서 저장    
               dataList = list()
               for items in json_data['response']['body']['item']:
                    dataList.append(items)
        
               if len(dataList) != 0 : #조회된 데이터가 있다면
                    for tmp in dataList: #응답메시지 아이템만큼 반복
                         print('주소 : '+tmp['addr'])
                         gmaps = googlemaps.Client(key = 'AIzaSyDBfBkXFtNIpzZI-kTBhQHoETDF1uH1tls')
                         #구글 지도 Geocoding api를 사용하기 위한 설정
                         locdata = []
                         while True : #api가 시간차를 두면서 활성화됨 > 인식될 때까지 실행
                              try :
                                   locdata = gmaps.geocode(tmp['addr'], language='ko')
                                   break #주소로 값이 반환되면 무한반복을 탈출
                              except Exception as e:
                                   print(e) #api가 제대로 인식이 안된 경우 > 다시 시도
                         # lat, lon 추출
                         print('위도 : '+str(locdata[0]['geometry']['location']['lat'])) #위도
                         print('경도 : '+str(locdata[0]['geometry']['location']['lng'])) #경도
                    addr = tmp['addr'].split(' ')
                    if(addr[0] in list(loc_jump.keys())) :
                         #광역시나 도 이런 것이 안붙은 경우
                         tmp['addr'] = addr[0]+loc_jump[addr[0]]+tmp['addr'][len(addr[0]):]
                    elif(not addr[0] in loc_check) :
                         #띄어쓰기를 잘못한 경우
                         #특별시나 도같은걸 없애면 모두 2글자에서 글자이므로 2,3글자를 떼어내 비교후 붙임
                         if(addr[0][:2] in list(loc_jump.keys())) :
                              tmp['addr'] = addr[0][:2]+loc_jump[addr[0][:2]]+' '+tmp['addr'][len(addr[0][:2]):]
                         elif(addr[0][:3] in list(loc__jump.keys())) :
                              tmp['addr'] = addr[0][:3]+loc_jump[addr[0][:3]]+' '+tmp['addr'][len(addr[0][:3]):]
                    print('주소 수정 : '+tmp['addr'])
                    sql = 'insert into loc(f_code, f_addr, f_lat, f_lng ,f_call) values (\'%s\', \'%s\', \'%s\', \'%s\', \'%s\')'%(tmp['csmtmktCode'],tmp['addr'],locdata[0]['geometry']['location']['lat'], locdata[0]['geometry']['location']['lng'], tmp['telNo'])
                    #\는 '를 쓰기위함 %는 순서대로 값을 넣어줌
                    print(sql)
                    writedb(sql) #쿼리문 실행
               else :
                    print('조회데이터 없음')
          except Exception as er :
               print(er)
               return
          else :
               print('완료!!')
               print()

#필요한 데이터만 dataframe으로 만들어 db 저장
def total(total_data) :
     total = pd.DataFrame()
     total['수산물'] = total_data[colList[1]]+total_data[colList[3]]
     total[colList[6]] = total_data[colList[6]]
     total['price'] = total_data[colList[13]].astype(np.int64)
     total['date'] = total_data[colList[9]]
     print('전체 데이터 정리 완료')
     print(total)
     print()
     writetable(total,'total')


filenames = glob.glob(u'2019_해양수산부_위판장별\\*.csv')
#현재 실행되는 파일 경로에서 '2019_해양수산부_위판장별' 폴더 안 csv파일을 다 가져옴
total_data = pd.DataFrame()
colList = [] #파일들 header 구분문자들이 다 다르지만 글자는 동일 > 첫번째 파일 기준으로 columns list를 지정
for col_tmp in pd.read_csv(filenames[0], encoding = 'CP949', sep='\s+', quoting=3 , error_bad_lines=False).columns :
    '''
        encoding = 'utf-8' 오류로 인해 'CP49'로 변경
        오류 이유 1. EUC-KR과 CP949를 구분하는 경우
                  2. EUC-KR만 지원하는 프로그램에서 CP494로 작성된 텍스트 파일을 여는 경우
        결론 > 파이썬 인코딩 환경과 데이터 파일 인코딩 설정 환경이 안맞아서 나는 오류

        구분자는 길이가 정해져 있지 않아 'Ws+'로 줌 >> Warning 뜰 수 도 있음

        quoting=3 , error_bad_lines=False >> 'C error: EOF inside string starting at row 0'인해 추가 
    '''
    tmp = re.sub('[-=+,#/\?:^$@*\"※~&%ㆍ!』\\‘|\[\]\<\>`\'…》]', '', col_tmp)
    #구분자로 잘라줘도 특수문자가 들어가서 한 번 더 정규식으로 정렬
    #단, '(KG당)'과 소수점을 위해 '()','.'를 제외한 특수문자만 제거
    if(tmp != '') :
            colList.append(tmp)
            #특수문자를 column으로 인식한 경우 >> 진짜 column이 아닌데 들어간 경우를 제외하고 columns List 에 넣어준다

#인식한 파일만큼 반복해서 데이터를 합침
for file in filenames :
    print(file)
    data = pd.read_csv(file, encoding = 'CP949', names=colList, skiprows=[0], quoting=3 , error_bad_lines=False)
    total_data = pd.concat([total_data, data]) #column이 다 동일하므로 concat으로 하나의 DataFrame으로 만듦
print('total_data 합치기 완료')
print(total_data)
print()

#합친 데이터 value에 '들어간 것을 삭제
for i in total_data.columns : 
    total_data[i] = total_data[i].str.replace("'","") 
print('total_data value에서 따옴표 제거 완료')
print(total_data)
print()

total_data = total_data[total_data[colList[13]]!='']#가격정보가 없는 행은 삭제
total_data = total_data[total_data[colList[1]]!=' ']#물고기 이름없는 행은 삭제
total_data = total_data[total_data[colList[3]]!='기타']#상태가 기타인 행도 삭제
total_data = total_data.dropna(axis=0) #결측값으로 인식되는 행 삭제
print('결측값 혹은 빈문자열이 들어간 행 삭제')
print(total_data)
print()

while True : #사용자가 종로를 원할 때까지 메뉴 출력 반복
     try :
          answer = menu()
          if(answer == 3) :
               break
          elif(answer == 1) :
               fishloc(total_data)
          elif(answer == 2) :
               total(total_data)
          else :
               print('그런 메뉴는 없습니다')
     except Exception as er :
          print('숫자로만 입력해주세요!!')
     print()
               
