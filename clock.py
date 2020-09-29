from apscheduler.schedulers.blocking import BlockingScheduler
import datetime
import requests
import os
import time
import csv
import json

sched = BlockingScheduler()

pgLst=['3wanahstda','6evtueubsp','8keehtakth','3ktcnhcke2','2tkcr9fa4d']
bURL='https://polis.gov.tw/api/v3/math/pca2?conversation_id='
GDOC_URL='https://docs.google.com/spreadsheets/d/12HozKwn6b2sa0jI6kwZmc3Y3SdJOgman89x68DLk6Os/'
CSVQU='export?format=csv&id=12HozKwn6b2sa0jI6kwZmc3Y3SdJOgman89x68DLk6Os&gid=1626435449'

def parse_csv():
    with requests.Session() as s:
        download = s.get(GDOC_URL+CSVQU)
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        count = 0
        for row in my_list:
            if row[5]=='':
                count += 1
    return [len(my_list)-1, len(my_list)-count-1]

def get_votenum():
    pgvoteLst=[]
    for pg in pgLst:
        reqs = requests.get(bURL+pg)
        print(reqs.status_code)
        rjson = reqs.json()
        voteLst=[]
        for n in range(len(rjson['group-votes'])):
            voteLst.append(rjson['group-votes'][str(n)]['n-members'])
        pgvoteLst.append(sum(voteLst))
    return pgvoteLst

def getVoteNum():
    #pgvoteLst=[]
    tvoterLst=[]
    tnvoteLst=[]
    tcomLst=[]
    for pg in pgLst:
        reqs = requests.get(bURL+pg)
        print(reqs.status_code)
        rjson = reqs.json()
        voterLst=[]
        nvoteLst=[]
        for d in rjson['user-vote-counts']:
            voterLst.append(d)
            nvoteLst.append(int(rjson['user-vote-counts'][str(d)]))
        tvoterLst.append(int(voterLst[-1])+1)
        tnvoteLst.append(sum(nvoteLst))
        tcomLst.append(len(rjson['tids']))
    #print(tvoterLst)
    #print(tnvoteLst) 
    #print(tcomLst)
    return [sum(tvoterLst)+102,sum(tnvoteLst),sum(tcomLst)]

def fetchPageViews():
    resp = requests.get('https://ocean.taiwan.gov.tw/OacGA_HF/ocatwgatotalpageviews.json')
    #print(resp.json())
    return resp.json()
#{'users': 5820, 'pageviews': 15075, 'updatetime': '2020/07/21 13:30:16'}

#Check new replies
def checkNewReplies():
    with open('sitedata.json','r') as json_file:
        data = json.load(json_file)
        print(data["replied"])
        cvalue = data["replied"] 
    
    with requests.Session() as s:
        download = s.get(GDOC_URL+CSVQU)
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
    outDict = dict()
    diff = len(my_list)-1 - cvalue
    outDict.update({'diff':diff})
    if diff > 0:
        updateStr=':'
        for lm in my_list[-diff:]:
            msg1 = "\n\n"+lm[0]+"\n使用類群："+lm[1]+"\n第一次使用："+lm[2]
            msg2 = "\n海域主題分類："+lm[3]+"\n滿意度："+lm[4]+"\n建議事項："+lm[5]
            updateStr+=msg1+msg2+"\n回復郵件："+lm[6]
        
        print(updateStr)
        with open('sitedata.json','w+') as js_file:   
            data["replied"] = cvalue+diff
            json.dump(data, js_file)
            print("update reply counts")
        outDict.update({'msg':updateStr})
        return outDict
    else:
        return {'msg':"",'diff':diff}


#@sched.scheduled_job('cron', day_of_week='mon-fri', minute='*/5')
def lineNotifyMessage():
    datetime_dt = datetime.datetime.today()# 獲得當地時間
    datetime_str = datetime_dt.strftime("%Y/%m/%d %H:%M")  # 格式化日期
    print(datetime_dt) 
    #time.sleep(int(os.environ.get("SLEEPTIME")))
    #print(datetime.datetime.today())
    fetchedData=fetchPageViews()
    #msg = datetime_str+'目前瀏覽人次'+str(fetchedData['pageviews'])
    #msg = str(fetchedData['updatetime'])+'目前瀏覽人次'+str(fetchedData['pageviews'])
    msg = datetime_str+'目前瀏覽人次'+str(fetchedData['pageviews'])
    headers = {
          "Authorization": "Bearer " + str(os.environ.get("LINE_TOKEN")),
          "Content-Type" : "application/x-www-form-urlencoded"
      }
    payload = {'message': msg}
    req = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
    print(req.status_code)

@sched.scheduled_job('cron', day_of_week='mon-fri', hour='8,16')
def lineNotifyPolis():
    print('=========APScheduler CRON ======')
    print(f'{datetime.datetime.now()}')
    print('=========APScheduler CRON ======')
    datetime_dt = datetime.datetime.today()# 獲得當地時間
    datetime_str = datetime_dt.strftime("%m/%d %H:%M")  # 格式化日期
    print(datetime_dt) 
    fetchedData=fetchPageViews()
    #pLst=get_votenum()
    #pLst=getVoteNum()
    csvLst=parse_csv()
    #outDic=checkNewReplies()
    head='一站式平臺狀況('+datetime_str+')'
    msg1 = '\n 1.點閱人數'+str(fetchedData['pageviews'])+'人'+'，回饋意見'+str(csvLst[0])+'件，建議事項'+str(csvLst[1])+'件。'
    #rpMsg = '\n新增'+str(outDic['diff'])+'則回饋意見'+outDic['msg']
    rpMsg =''
    #title2 = '\n\n2.眾開講五大主軸意見統計：'
    #msg2 = '投票人數：'+str(pLst[0])+'人 總投票數：'+str(pLst[1])+'次 總意見數：'+str(pLst[2])
    #msg2 = '開放'+str(pLst[0])+'人、透明'+str(pLst[1])+'人、服務'+str(pLst[2])+'人、教育'+str(pLst[3])+'人、責任'+str(pLst[4])+'人 ，計'+str(sum(pLst))+'人。'
    #title3 = '\n3.秘書室臉書貼文：'
    #title4 = '\n4.海巡署署長室臉書向海致敬貼文:'
    msg = head+msg1+rpMsg
    headers = {
          "Authorization": "Bearer " + str(os.environ.get("LINE_TOKEN")),
          "Content-Type" : "application/x-www-form-urlencoded"
      }
    payload = {'message': msg}
    req = requests.post("https://notify-api.line.me/api/notify", headers = headers, params = payload)
    print(req.status_code)



@sched.scheduled_job('cron', day_of_week='mon-fri', minute='*/20')
def scheduled_job():
    print('=========APScheduler CRON ======')
    print(f'{datetime.datetime.now()}')
    print('=========APScheduler CRON ======')
    url = "https://ocean-map-stats.herokuapp.com/"
    conn = requests.get(url)
    print(conn.status_code)
    #for key, value in conn.getheaders():
    #    print(key, value)

sched.start()
