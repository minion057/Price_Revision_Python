#_*_coding:utf-8 _*_
'''
@author: PC
'''
import folium
import webbrowser
import tkinter as tk
from tkinter.ttk import *
from tkinter import ttk
from tkcalendar import DateEntry
from datetime import date, timedelta
import pandas as pd
import numpy as np
import pymysql
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import font_manager
from mpldatacursor import datacursor

root = tk.Tk()
root.title('Fish Chips') #gui창 타이틀 지정
root.geometry('350x110+200+200') # 창 크기와 창의 위치
root.resizable(0, 0) # 창의 x와 y 의 크기 조절 불가능하게 함
root.configure(bg="WHITE") #배경색 흰색으로 지정
style = ttk.Style(root) #스타일 설정
style.theme_use('clam')


#버튼 클릭 이벤트 핸들러
def okClick(c_type):
     if(combo.get() == '수산물 종류 목록') :
        lbl.configure(text = '수산물을 선택하고 검색하세요.', background='WHITE')
        return #종류를 선택안했으면 종료
     if(int(de.get().split('/')[2]) != 19) :
        lbl.configure(text = '아직은 2019년만 검색 가능합니다.', background='WHITE')
        return #2019년을 벗어나면 종료
     
     if(c_type == 'all') : #검색 클릭
          lbl.configure(text = de.get()+' '+combo.get()+' 검색완료', background='WHITE')
          showmap(de.get().split('/'))
          showchart(de.get().split('/'))
     elif(c_type == 'map') : #지도보기 클릭
          showmap(de.get().split('/'))
     elif(c_type == 'chart') : #가격비교차트보기 클릭
          showchart(de.get().split('/'))

#지도 만들기
def showmap(day) :
     lbl.configure(text = '지도가 열리는 중입니다.', background='WHITE')
     m = folium.Map(location=[35.933189,128.6791093],zoom_start=7.25) #지도의 정중앙 좌표, 배율을 설정
     from folium.plugins import MarkerCluster
     marker_cluster = MarkerCluster().add_to(m)
     #MarkerCluster를 이용해 가까운 거리에 있는 마커들을 계산해서 갯수로 보여줌
     
     query = "select *, avg(T.price) as avg, max(T.price) as max, min(T.price) as min "
     query += "from loc as L, total as T where L.f_code = T.위판장코드 and T.수산물 = '"+combo.get()
     query += "' and T.date = '2019" +(int(day[0])<10 and '0'+day[0] or day[0])
     query += (int(day[1])<10 and '0'+day[1] or day[1])+"' group by T.수산물, L.f_code, T.date;"
     data = gettable(True, query) #필요한 데이터를 mysql에서 dataframe 형태로 가져옴
     if len(data)==0 : #데이터 길이가 0이라면 데이터가 없는 것이므로
        lbl.configure(text = '검색결과 없음.', background='WHITE')
        return #결과가 없음을 알리고 종료

     for i in data.iterrows() : #데이터만큼 반복
        where = [] #위도와 경도를 리스트로 저장
        where.append(i[1].f_lat)
        where.append(i[1].f_lng)
        #popup에 띄울 html 내용을 저장
        text = '<div width="200px"><h3>'+i[1].수산물+'</h3><br><h5>2019년'+day[0]+'월'+day[1]+'일</h5><br>'
        text += '주소 : '+i[1].f_addr+'<br>전화번호 : '+i[1].f_call+'<br>평균가 : '+str(round(i[1].avg,-1))
        text += '<br>최고가 : '+str((i[1].tolist())[len(i[1].tolist())-2])+'<br>최저가 : '+str((i[1].tolist())[len(i[1].tolist())-1])+'</div>'
        #최고가, 최저가는 바로 가져오면 type이 method로 나오기때문에 리스트로 변환시켜준 후 가져옴        
        folium.Marker(
             location = where,
             popup = folium.Popup(text, max_width=350),
             icon=folium.features.CustomIcon('fish.PNG', icon_size=(50,50))
        ).add_to(marker_cluster) #지도에 마커 추가
        
     m.save('map.html') #마커를 다 추가한 지도를 html로 저장
     webbrowser.open_new_tab('map.html') #그런 후 지도 브라우저로 열기
     lbl.configure(text = de.get()+' '+combo.get()+' 지도 열림.', background='WHITE')

#가격비교 차트 만들기
def showchart(day) :
     plt.figure(figsize=(8,6), dpi=80) #차트 사이즈 지정
     lbl.configure(text = de.get()+' '+combo.get()+' 차트 열림.', background='WHITE')
     
     #한글을 위한 설정
     font_location="C:/Windows/Fonts/malgun.ttf"
     font_name = font_manager.FontProperties(fname=font_location).get_name()
     matplotlib.rc('font', family=font_name)
     
     day = date(2019,int(day[0]),int(day[1])) #선택한 날짜를 date형으로 저장
     days = "('" #일주일 범위로 가격을 비교할 것이기때문에 ('20191007','20191006') 이런식으로 저장
     for i in range(7) : #일주일 범위기 때문에 7번 반복
          tmp = day - timedelta(days=i) #선택한 날짜에서 0,1~6 순으로 빼면 그만큼 전 날짜가 나옴
          days += str(tmp.year) + (tmp.month<10 and '0'+str(tmp.month) or str(tmp.month)) + (tmp.day < 10 and '0'+str(tmp.day) or str(tmp.day))
          #days 처음 선언한 부분 주석 참고
          #DB에 날짜형식이 20190101 형식이기 때문에 9이하는 0을 붙여줌
          if(i<6): #처음부터 마지막날 전까지는 ,를 붙여주고
               days += "','"
          else : #마지막날은 )로 닫아줘 string을 마무리 함
               days +="')"
          
     query = "select L.f_code, L.f_addr, T.date, avg(T.price) as avg "
     query += "from loc as L, total as T where L.f_code = T.위판장코드 and T.수산물 = '"+combo.get()
     query += "' and T.date in " +days+" group by L.f_code, T.수산물, T.date;"
     data = gettable(True, query) #필요한 데이터를 mysql에서 dataframe 형태로 가져옴
     if len(data)==0 : #데이터 길이가 0이라면 데이터가 없는 것이므로
        lbl.configure(text = '검색결과 없음.', background='WHITE')
        return #결과가 없음을 알리고 종료

     #차트1
     #선택한 날짜의 판매장별 수산물 가격비교
     dayitem = data[data['date']== ((days[1:len(days)-1]).replace("'","")).split(",")[0]]
     #아까 db에서 가져온 data에서 선택한 날짜를 가진 data만 저장
     label = dayitem['f_addr'].tolist()
     #bar차트에 xlabel로 주소를 다 보여줄 수 없으므로 툴팁으로 보여줄 것임
     #따라서 툴팁에 보여줄 주소를 리스트로 저장
     x = range(len(label)) #툴팁을 위한 변수
     #툴팁을 마우스를 따라다니며 뜨게함
     def formatter(**kwargs):
          dist = abs(np.array(x) - kwargs['x'])
          i = dist.argmin()
          labels = label
          return labels[i] #툴팁에 뜰 내용 반환
     plt.subplot(1,2,1) #한 화면에서 세로로 이등분하고 1번(왼쪽)에 넣겠다 선언
     #주소별로 선택한 날짜, 수산물의 평균 가격을 bar chart로 설정
     plt.bar(np.arange(len(dayitem['f_addr'].apply(lambda e: e.split()[0]))), dayitem['avg'])
     #x축 data에 주소에서 큰 부위만 가져와서 띄움(ex. 경상북도, 서울특별시)
     plt.xticks(np.arange(len(dayitem['f_addr'].apply(lambda e: e.split()[0]))),
                (dayitem['f_addr'].apply(lambda e: e.split()[0])).tolist(), fontsize=10, rotation=45)
     if(len(dayitem)==0) :
          plt.xlabel('선택하신 날짜에는 거래가 이루어지지 않았어요.',fontsize = 15,color='r')
     else :
          plt.xlabel( '마우스를 bar에 올리면 해당 데이터의 정확한  주소가 나와요.',fontsize=15)
     plt.ylabel('평균 가격') #x,y 라벨 지정
     plt.title(((days[1:len(days)-1]).replace("'","")).split(",")[0]+' '+combo.get()+' 평균 가격 비교') #타이틀 지정
     datacursor(hover=True, formatter=formatter) #마우스 오버하면 툴팁뜨게 지정


     #차트2
     #선택한 날짜 기준으로 일주일 간 전국 가격비교
     plt.subplot(1,2,2) #한 화면에서 세로로 이등분하고 2번(오른쪽)에 넣겠다 선언
     #검색한 data의 주소를 큰 부위만 가지고 있게 설정(ex. 경상북도, 서울특별시)
     data['f_addr'] = data['f_addr'].apply(lambda e: e.split()[0])
     #중복없이 주소 큰 부위가 column, 일주일날짜가 index인 datafame 생성
     dayitem2 = pd.DataFrame(columns=data['f_addr'].drop_duplicates().tolist(), index=list(reversed((days[1:len(days)-1]).replace("'","").split(","))))
     for i in dayitem2.columns : #column만큼 반복
          tmp = []
          for d in dayitem2.index : #index > 일주일만큼 반복
               try :
                    tmp.append(int(round((data[data['date']==d])[data['f_addr'] == i]['avg'].mean(),-1)))
                    #dataframe 검색조건에서 '|'와 같은 연산자를 쓰면 오류가 나서 검색 후 검색하는 식으로 수정
                    #짧은 주소(ex.경상북도, 전라남도)와 날짜가 해당하는 데이터의  평균 계산
                    #이때, 일의자리에서 반올림하고 정수형으로 변경한다
               except Exception :
                    #만약 데이터가 없어서 오류가 난다면
                    tmp.append(0) #0을 넣음
          dayitem2[i] = tmp #한 판매장에 대해 리스트를 만들고 데이터프레임에 value로 넣어줌
     for i in dayitem2.columns :
          plt.plot(dayitem2.index.tolist(), dayitem2[i].tolist(), label = i) #꺽은선차트
     plt.legend()
     plt.title(combo.get()+' 전국 일주일 평균 가격 비교') #제목 지정
     plt.xlabel('날짜',fontsize=15)
     plt.ylabel('평균 가격') #x,y 라벨 지정

     plt.show() #차트1,2를 보여줌 

#DB에서 data를 dataframe으로 가져옴
def gettable (sql, str): #sql - 쿼리문이 있는지 여부 / str - 쿼리문 or 테이블명
     pymysql.install_as_MySQLdb()
     import MySQLdb #쿼리문 여러개를 동시에 실행시키기 위해 작성
     engine = create_engine("mysql://root:ohgg805**@localhost:3306/fish",encoding="utf8")
     conn = engine.connect() #mysql 연결
     table = pd.DataFrame()
     if(sql) : #쿼리문으로 가져오는 경우
          table = pd.read_sql(str, conn)
     else : #테이블 전체 가져오는 경우
          table = pd.read_sql_table(str, conn)
     conn.close() #db 닫음
     return table #dataframe을 반환

#달력
class MyDateEntry(DateEntry):
    def __init__(self, master=None, **kw):
        DateEntry.__init__(self, master=None, **kw)
        self._top_cal.configure(bg='black', bd=1)
        tk.Label(self._top_cal, bg='gray90', anchor='w',
                 text='Today: %s' % date.today()).pack(fill='x')
de = MyDateEntry(root, year=date.today().year, month=date.today().month, day=date.today().day,
                 selectbackground='gray80',
                 selectforeground='black',
                 normalbackground='white',
                 normalforeground='black',
                 background='gray90',
                 foreground='black',
                 bordercolor='gray90',
                 othermonthforeground='gray50',
                 othermonthbackground='white',
                 othermonthweforeground='gray50',
                 othermonthwebackground='white',
                 weekendbackground='white',
                 weekendforeground='black',
                 headersbackground='white',
                 headersforeground='gray70')
de.config(state='readonly') # 편집 불가
de.config(width="10")
de.grid(row=0, column = 0, padx=10, pady=10)

#수산물종류 콤보박스를 위해 db에서 가져옴
data = gettable(False,'fish').sort_values(by=['수산물표준코드명'], axis=0)
combo = Combobox(root, values=(data['수산물표준코드명']+data['어종상태명']).values.tolist(), width="17")
combo.config(state='readonly') # 편집 불가하게 설정
combo.set('수산물 종류 목록') #첫 화면에 보여줄 말 설정
combo.grid(row=0, column = 1, padx=10, pady=10)

#검색버튼 설정(지도+차트 동시에 보여주기)
#command에 매개변수를 넘겨주기 위해 lambda사용
b1=tk.Button(root, text="검색", width="7", command=lambda: okClick('all'))
b1.grid(row=0, column = 2, padx=10, pady=10)

#버튼 클릭시 결과를 알려줄 라벨 (검색결과 없음, 지도여는 중 등등)
lbl = Label(root, background='WHITE')
lbl.grid(row=1, column=0, columnspan=3)

#지도버튼 설정(지도 보여주기)
tk.Button(root, text="지도보기", width="10",  command=lambda: okClick('map')).grid(row=2, column = 0, padx=10, pady=10)
#차트버튼 설정(차트 보여주기)
tk.Button(root, text="가격비교차트", width="10",  command=lambda: okClick('chart')).grid(row=2, column = 1, padx=10, pady=10)
#마찬가지로 두 버튼도 command에 매개변수를 넘겨주기 위해 lambda사용

root.mainloop()
