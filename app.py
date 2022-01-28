from flask import Flask, redirect, url_for, render_template,request
import requests
from bs4 import BeautifulSoup
import pandas
import re
import random
import time
import sqlite3
from selenium import webdriver
from selenium.webdriver.support.ui import Select
import sqlite3 as sql
import sqlite3
from datetime import datetime

app=Flask(__name__) #__name__目前執行模組
stock_id=[]
stock_id.clear()
users = []  # 这里存放所有的留言

@app.route('/', methods=("POST", "GET"))#以函式為基礎，提供附加的功能('/', methods=("POST", "GET"))
def index():
    if request.method == "POST":
        stock = request.form["nm1"] #nm是html提交表格nmae
        stock_id.append(stock)#取得股票代碼加入
        return redirect(url_for("get_table",stock_id=stock)) #url_for,後面要是函數
    return render_template("index.html")

@app.route('/123', methods=("POST", "GET"))#以函式為基礎，提供附加的功能('/', methods=("POST", "GET"))
def penumber(): 
    if request.method == "POST":
        eps =float(request.form["eps"]) #nm是html提交表格nmae
        pe = float(request.form["pe"]) #nm是html提交表格nmae
        stockprice=eps*pe
        return render_template("test.html",stockprice=stockprice, stock_id=stock_id) #url_for,後面要是函數
    return render_template("index.html")


@app.route('/stock/<stock_id>') #第2個網頁  
def get_table(stock_id):
    #自動抓取防擋表頭
    headers = {'user-agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36'}
    url = f"https://goodinfo.tw/StockInfo/StockBzPerformance.asp?STOCK_ID={stock_id}"  #goodinfo經營績效
    url0 = f"https://goodinfo.tw/StockInfo/ShowSaleMonChart.asp?STOCK_ID={stock_id}" #goodinfo每月收入
    ur20 = f"https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=IS_M_QUAR_ACC&STOCK_ID={stock_id}" #goodinfo季eps
    df2=get_tab01(url,headers) #goodinfo經營績效
    time.sleep(random.randrange(1,5 ))  #延遲6-13秒防鎖ip
    df20=get_tab02(url0,headers)#goodinfo每月收入
    time.sleep(random.randrange(5,8 ))  #延遲6-13秒防鎖ip
    df200=seasoneps(ur20,headers)#goodinfo季eps
  #----------------
  #把營收資料寫入各陣列中
    year=[] 
    EPS=[]
    Closing=[]
    AVClosing=[]
    # n=0
    # f=0
    # g=0
    if df2['稅後EPS'].loc[0]=="-":#第一季還沒出時
        n=1 #內容第2-8列
        f=7
        g=2 #去年收入-2
    else: 
        n=0
        f=6
        g=1 #去年收入-1
    for i in range(n,f): #range(x, y) #for 下一列要縮進喔 range(0,6)整數數列：0,1,2,3,4,5
        year.append(df2['年度'].loc[i])#year單格資料
        EPS.append(df2['稅後EPS'].loc[i])#單格資料EPS0 #最新一季EPS
        if df2['收盤'].loc[i]=="-":#年度太少除錯
            Closing.append("0")#單格資料Closing1 #去年收盤
        else:
            Closing.append(df2['收盤'].loc[i])#單格資料Closing1 #去年收盤
        if df2['平均'].loc[i]=="-":
            AVClosing.append("0")#單格資料Closing1 #每年平均
        else:
            AVClosing.append(df2['平均'].loc[i])#單格資料Closing1 #每年平均
    EPS = list(map(float,EPS)) #字串轉換成數字
    Closing = list(map(float,Closing)) #字串轉換成數字
    AVClosing = list(map(float,AVClosing)) #字串轉換成數字
    PE1=round((Closing[1]/EPS[1]),1) #(round(x,1))留小數1位PE1 #去年本益比
    income1=float((df2['營業收入'].loc[g]))#單格資料income1 #去年收入
    season1=int(year[0].split('Q')[1])#第幾季

   #----------以下從月營收來    
    mon0=int(df20['月別'].loc[0].split('/')[1])#單格資料(取出10月)，第1格月份資料取出2021/10 , 以split/取出10月,int變整數   mon0=mon0.split('/')[1] #拆分 月份   mon0=int(mon0) #轉成整數mon0  #月份
    incomeyear0=float(df20['累積營收(億)'].loc[0])#單格資料，多格incomeyear0 #最新一月
    df20=df20.head(14) #顯示近16個月(最多)，可調整
    #近12月營收相加------------------
    incom12=[]
    for i01 in range(0,12): #range(x, y) #for 下一列要縮進喔 range(0,6)整數數列：0,1,2,3,4,5
        incom12.append(df20['單月營收(億)'].loc[i01])#單格資料Closing1 #近12月營收
    incom12 = list(map(float,incom12)) #字串轉換成數字
    sumincom12=0
    for total12 in incom12: #近12月營收相加
        sumincom12+=total12
    #--------------------------------    
    Epstoyear=round(((incomeyear0/mon0*12)/income1*EPS[1]),1) #預估EPS(預估今年營收/去年營收*去年EPS)
    # 建立 Pandas 資料表(很多單資料合併)本益比表(收盤本益比)
    d2 = {year[5]+'本益比':[round(Closing[5]/EPS[5],1)],year[4]+'本益比':[round(Closing[4]/EPS[4],1)],year[3]+'本益比':[round(Closing[3]/EPS[3],1)],year[2]+'本益比':[round(Closing[2]/EPS[2],1)],year[1]+'本益比':[round(Closing[1]/EPS[1],1)],year[0]+'本益比':[round(Closing[0]/EPS[0],1)]}
    df44 = pandas.DataFrame(data=d2)
    df44['備考']="收盤" #3新增month
    # 建立 Pandas 資料表(很多單資料合併)本益比表(平均本益比)
    d3 = {year[5]+'本益比':[round(AVClosing[5]/EPS[5],1)],year[4]+'本益比':[round(AVClosing[4]/EPS[4],1)],year[3]+'本益比':[round(AVClosing[3]/EPS[3],1)],year[2]+'本益比':[round(AVClosing[2]/EPS[2],1)],year[1]+'本益比':[round(AVClosing[1]/EPS[1],1)],year[0]+'本益比':[round(AVClosing[0]/EPS[0],1)]}
    df55 = pandas.DataFrame(data=d3)
    df55['備考']="平均" #3新增month
    df77=pandas.concat([df44,df55]) #合併顯示(本益比)
    #--------------------------------

    # 建立 Pandas 資料表(income相關數據)
    d = {'去年收盤':[Closing[1]],'去年本益比':[PE1],'去年營收':[income1],'今年('+str(mon0)+'月)累積營收':[incomeyear0],'近12月累積':[round(sumincom12,1)]}
    df33 = pandas.DataFrame(data=d)
    # 建立 Pandas 資料表(EPS相關數據)    
    d1 = {'去年EPS':[EPS[1]],'預估EPS(累營/月*12)':[Epstoyear],year[0]+'季EPS':[EPS[0]],'平均每季EPS':[round(EPS[0]/season1,1)],'年預估EPS':[round(EPS[0]+EPS[0]/season1,1)],'預估EPS(近12月)':[round(sumincom12/income1*EPS[1],1)]}
    df34= pandas.DataFrame(data=d1)
     #------------
     #找出公司代碼及公司
    res=requests.get(url,headers=headers)
    res.encoding='utf-8'
    soup = BeautifulSoup(res.text, 'lxml')
    data333=soup.select("table.b0")  #使用bs4以網頁程式碼找出位置
    data66=re.findall('(\d+\D+)',data333[4].text) #正規表達法\d+1個數
    stockname=data66[0].split()[0]+data66[0].split()[1] #顯示公司#先變成字串，以空格拆分，選出要的值
    #-------------------------------------------
    
    #多個網頁合併方式
  
     #第一組資料
    nmp_t0=df2.columns.values.tolist()#標題
    len_0=len(nmp_t0)#標題長度
    nmp0_n=df2.values.tolist()#資料內容
    
    #第二組資料
    nmp_t1=df20.columns.values.tolist()#標題
    len_1=len(nmp_t1)#標題長度
    nmp_n1=df20.values.tolist()#資料內容

    #第三組資料
    nmp_t2=df33.columns.values.tolist()#標題
    len_2=len(nmp_t2)#標題長度
    nmp_n2=df33.values.tolist()#資料內容

    #第四組資料
    nmp_t3=df34.columns.values.tolist()#標題
    len_3=len(nmp_t3)#標題長度
    nmp_n3=df34.values.tolist()#資料內容

    #第五組資料
    nmp_t4=df77.columns.values.tolist()#標題
    len_4=len(nmp_t4)#標題長度
    nmp_n4=df77.values.tolist()#資料內容


    #第六組資料季eps
    nmp_t5=df200.columns.values.tolist()#標題
    len_5=len(nmp_t5)#標題長度
    nmp_n5=df200.values.tolist()#資料內容


    return render_template("test.html",stockname=stockname,nmp_t0=nmp_t0,nmp_n0=nmp0_n,len_0=len_0,nmp_t1=nmp_t1,nmp_n1=nmp_n1,len_1=len_1,nmp_t2=nmp_t2,nmp_n2=nmp_n2,len_2=len_2,nmp_t3=nmp_t3,nmp_n3=nmp_n3,len_3=len_3,nmp_t4=nmp_t4,nmp_n4=nmp_n4,len_4=len_4,nmp_t5=nmp_t5,nmp_n5=nmp_n5,len_5=len_5)

  
   
def get_tab01(url,headers):#goodinfo經營績效
    res=requests.get(url,headers=headers)
    res.encoding='utf-8'
    soup = BeautifulSoup(res.text, 'lxml')
    data=soup.select_one('#txtFinDetailData')  #使用bs4以網頁程式碼找出位置
    dfs = pandas.read_html(data.prettify())#使用pandas
    df=dfs[0]#使用pandas讀資料
    df.columns=df.columns.get_level_values(1)#取第二列為標題
    #df.columns=[]修改標題
    df.columns=['年度','股本(億)','財報評分','收盤','平均','漲跌','漲跌(%)','營業收入','營業毛利','營業利益','業外損益','稅後淨利','營業毛利1','營業利益1','業外損益1','稅後淨利1','ROE(%)','ROA(%)','稅後EPS','年增(元)','BPS(元)'] #修改標題
    df = df.iloc[[0,1,2,3,4,5,6],:]#iloc保留前6筆資料 參考：frame.loc[:,'1':'B']等於A1:B；frame.loc['1':'2',:]等於A1:Z2,#frame.loc['1','A']=A1, iloc行索引和列索引（index，columns） 都是從 0 開始frame.iloc[0:2,:]
    df2=df.drop(['財報評分','漲跌','漲跌(%)','營業毛利1','營業利益1','業外損益1','稅後淨利1','ROA(%)','年增(元)','BPS(元)'],axis=1) #不要的列號拿掉[0,1,3,4], # 刪除列  >>> df.drop(['B', 'C'], axis=1) >>> df.drop(index='cow', columns='small')
    return df2

def get_tab02(url0,headers): #goodinfo每月收入
    res=requests.get(url0,headers=headers)
    res.encoding='utf-8'  
    soup = BeautifulSoup(res.text, 'lxml')
    data=soup.select_one('#divDetail')  #使用bs4以網頁程式碼找出位置
    dfs = pandas.read_html(data.prettify())#使用pandas
    df00=dfs[0]   
    df00.columns=df00.columns.get_level_values(2)#取第二列為標題
    df00.columns=['月別','開盤','收盤','最高','最低','漲跌','漲跌','營收(億)','月增(%)','年增(%)','營收(億)','年增(%)','單月營收(億)','單月月增(%)','單月年增(%)','累積營收(億)','累積年增(%)'] #修改標題
    df00 = df00.iloc[0:16,:]### 保留近16月 取前兩列對應資料frame.loc[:,'1':'B']等於A1:B30000,### 取前兩行對應資料frame.loc['1':'2',:]等於A1:Z2,#frame.loc['1','A']=A1, iloc基於行索引和列索引（index，columns） 都是從 0 開始frame.iloc[0:2,:]
    df20=df00.drop(['開盤','收盤','最高','最低','漲跌','漲跌','營收(億)','月增(%)','年增(%)','營收(億)','年增(%)'],axis=1) #不要的列號拿掉[0,1,3,4], # 刪除列 >>> df.drop(['B', 'C'], axis=1) >>> df.drop(index='cow', columns='small')
    return df20
def seasoneps(ur20,headers):#每季收入
        
    #-------下拉式選單(桌機用)
    driver = webdriver.Chrome()#建立webdriver，傳入剛剛所下載的「瀏覽器驅動程式路徑」及「瀏覽器設定(chrome_options)」，其中的「瀏覽器驅動程式路徑」一定要傳入，而「瀏覽器設定(chrome_options)」則可視情況傳入，為選擇性的。
    #-------下拉式選單(桌機用)
      
    #-------下拉式選單(heroku用)
    # chrome_options = webdriver.ChromeOptions()#建立webdriver物件，傳入剛剛所下載的「瀏覽器驅動程式路徑」及「瀏覽器設定(chrome_options)」，其中的「瀏覽器驅動程式路徑」一定要傳入，而「瀏覽器設定(chrome_options)」則可視情況傳入，為選擇性的。
    # chrome_options.binary_location = os.environ.get("GOOGLE_CHROME_BIN")
    # chrome_options.add_argument("--headless") #無頭模式
    # chrome_options.add_argument("--disable-dev-shm-usage")#防彈跳視窗
    # chrome_options.add_argument("--no-sandbox")#防彈跳視窗
    # driver = webdriver.Chrome(executable_path=os.environ.get("CHROMEDRIVER_PATH"), chrome_options=chrome_options)
    #-------下拉式選單(heroku用)---------
    
    driver.get(ur20)#要抓取網址
    # 抓取下拉選單元件
    #抓取到下拉式元件後，可透過以下三種方法來選取下拉選單選項：
    #select.select_by_index(0)#方法 1：透過 index 值選取資料, 執行後會選取「option 1」選項
    #方法 2：透過 option 的 value 值選取資料, 執行後會選取「選項 2」選項
    #select.select_by_visible_text(u"選項三")#方法 3：透過選項顯示的文字選取資料, 執行後會選取「選項三」選項
    select = Select(driver.find_element_by_id('RPT_CAT'))
    select.select_by_value("IS_M_QUAR")
    time.sleep(4)
    #----------------
    html_text=driver.page_source
    soup = BeautifulSoup(html_text, 'lxml')
    data=soup.select_one('#divFinDetail')  #使用bs4以網頁程式碼找出位置    
    dfs = pandas.read_html(data.prettify())#使用pandas
    driver.close()
    df00=dfs[0]
    # df = df00.iloc[[28,29,30,31,32,33],:]### 保留 取前兩列對應資料frame.loc[:,'1':'B']等於A1:B30000,### 取前兩行對應資料frame.loc['1':'2',:]等於A1:Z2,#frame.loc['1','A']=A1, iloc基於行索引和列索引（index，columns） 都是從 0 開始frame.iloc[0:2,:]
    df200=df00.iloc[:,[0,1,3,5,7,9,11,13]]### 保留 季資料
    df200.columns=[col[0] for col in df200.columns]#標題重複刪除
    df200.set_index("本業獲利",inplace=True) #設定第二行本業獲利為index
    df200 = df200.loc[["每股稅後盈餘(元)"]] ### 保留 

    return df200
#測試區
@app.route('/addrec',methods = ['POST', 'GET'])
def addrec():
    epspe=""
    differ=""
    if request.method == 'POST':
       try:
          eps = request.form['EPS']
          pe = request.form['PE']
          stockname = request.form['stockname']
          price = request.form['price']
          epspe = float(eps)*float(pe)
          differ =(float(price)/float(epspe))*100
          now=datetime.now() 
          with sql.connect("database.db") as con:              
            cur = con.cursor()
            if differ<80:
                cur.execute("create table IF NOT EXISTS students(stockname TEXT,price TEXT,eps real, pe real, epspe TEXT, differ integer, now TEXT)")#建立資料庫名稱及屬性string=text,float=real,int=integer,binary=blob   
                cur.execute("INSERT INTO students (stockname,price,eps,pe,epspe,differ,now) VALUES (?,?,?,?,?,?,?)",(stockname,price,eps,pe,epspe,differ,now) )            
                con.commit()
                msg = "資料紀錄成功！" 
                print(msg)  
            else:  
                con.commit()
                msg = "因為現值太高，不紀錄「好股區」"
                print(msg)      
       except:
          con.rollback()
          msg = "加入失敗"
          print(msg)   
       finally:


        

        #print database rows
          for row in cur.execute("select * from students"):
            print(row)
          
          return render_template("result.html",msg = msg,epspe=epspe,differ=differ,price=price)                
          con.close() 






@app.route('/list')
def list1():
    con = sql.connect("database.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("select * from students ORDER BY now DESC")#ASC,排序

    rows = cur.fetchall();
    return render_template("list.html",rows = rows)

@app.route('/list2')    
def list2():
    con = sql.connect("database.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("select * from students ORDER BY stockname DESC")#ASC,排序

    rows = cur.fetchall();
    return render_template("list.html",rows = rows)


if __name__=='__main__':
   app.run(debug=True)#啟動
 
 
 
   
 


   