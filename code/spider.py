# coding=utf-8
# from bs4 import BeautifulSoup
import os
import sys
import urllib
import datetime, time
import requests
import re
from lxml import etree
from zfparseHtml import  getClassScheduleFromHtml, getStudentInfor, get__VIEWSTATE, getGrade
from zfmodel import Student, DBSession, ClassSchedule, Class, YearGrade, OneLessonGrade, TermGrade

from sqlalchemy import and_, or_

class ZhengFangSpider:
    def __init__(self,student,baseUrl="http://学籍系统网站或IP/(0sh5f5fnxcowan45z1oa2h55)"):            
        self.student = student
        self.baseUrl = baseUrl
        # 维护全局的请求信息
        self.session = requests.session()        
        self.session.headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'

    #含验证码登陆
    def login(self):
        # 登录的连接
        loginurl = self.baseUrl+"/default2.aspx"
        
        # 获得登录页面的HTML代码
        response = self.session.get(loginurl)        
        selector = etree.HTML(response.content)

        # Cookie = response.cookies

        # 获得HTML代码里面的 隐藏输入框：__VIEWSTATE 的值
        __VIEWSTATE = selector.xpath('//*[@id="form1"]/input/@value')[0]        

        # 等待用户输入验证码
        while True:
            # 更换验证码的链接
            imgUrl = self.baseUrl+"/CheckCode.aspx?"
            # imgresponse = self.session.get(imgUrl, stream=True, cookies=Cookie)
            imgresponse = self.session.get(imgUrl, stream=True)

            # 保存验证码
            image = imgresponse.content
            DstDir = os.getcwd() + "/"
            print("保存验证码到：" + DstDir + "code.jpg" + "\n")
            try:
                with open(DstDir + "code.jpg", "wb") as jpg:
                    jpg.write(image)
            except IOError:
                print("IO Error\n")
            finally:
                jpg.close

            code = input("验证码是(1:换一张)：")
            if code == "1":
                continue
            else:
                break;        
  

        # 登录方式选择学生,编码转换为URL会存在一些问题
        # 通过抓包发现需要的是：%D1%A7%C9%FA，如果直接填写会变成：%25D1%25A7%25C9%25FA
        RadioButtonList1 = u"学生".encode('gb2312', 'replace')
        # POST的传输数据
        data = {            
            "__VIEWSTATE": __VIEWSTATE,
            "txtUserName": self.student.studentnumber.decode('utf-8'),
            "Textbox1": "",
            "TextBox2": self.student.password.decode('utf-8'),
            "txtSecretCode": code,
            "RadioButtonList1": RadioButtonList1,
            "Button1": "",
            "lbLanguage": "",
            "hidPdrs": "",
            "hidsc": "",

        }
        # postData = urllib.parse.urlencode(data).encode('gb2312')   
        # 登陆教务系统        
        Loginresponse = self.session.post(url=loginurl, data=data)
        if Loginresponse.status_code == requests.codes.ok:
            # 获取标题的正则表达式
            pat=r'<title>(.*?)</title>'
            x=re.findall(pat, Loginresponse.text)
            if(x[0]=="欢迎使用正方教务管理系统！请登录"):
                print("登陆失败")
                pat=r'defer>alert(.*?);'
                x=re.findall(pat, Loginresponse.text)
                print (x)
                return False
            else:
                print("登陆成功")
                return True       


    #获取学生基本信息
    def getStudentBaseInfo(self, dbSession):
        # 登录后的URL,需要保持引用，不然会重定向到登录页面
        self.session.headers['Referer'] = self.baseUrl+"/xs_main.aspx?xh="+self.student.studentnumber.decode('utf-8')
        # 获取个人信息的URL（由于缺少学生名字的URL编码）
        url = self.baseUrl+"/xsgrxx.aspx?xh="+self.student.studentnumber.decode('utf-8')+"&"
        # 从HTML里面解析出学生信息
        response = self.session.get(url)

        d = getStudentInfor(response)
        print(d)
        self.student.name = d["name"]
        self.student.urlName = d["name"].encode('gb2312', 'replace')
        self.student.sex = d["sex"]
        self.student.idCardNumber = d["idCardnumber"]
        self.student.enterSchoolTime = d["enterSchoolTime"]
        self.student.birthsday = d["birthsday"]
        self.student.highschool = d["highschool"]
        self.student.nationality = d["nationality"]                
        self.student.college = d["college"]
        self.student.major = d["major"]
        self.student.classname = d["classname"]
        self.student.gradeClass = d["gradeClass"]
        # 保存到数据库   
        # Failed processing pyformat-parameters; Python 'navigablestring' cannot be converted to a MySQL type
        # 原因在于bs的字符类型，无法转换为MySQL的类型，所以在上诉字典中的数据强制转换为 str
        # 参考链接：https://www.zhihu.com/question/49146377
        dbSession.add(self.student)
        dbSession.commit()
        print ("更新学生基本信息成功")


    #获取学生课表
    def getClassSchedule(self):
        self.session.headers['Referer'] = self.baseUrl + "/xs_main.aspx?xh=" + self.student.studentnumber.decode('utf-8')
        url = self.baseUrl + "/xskbcx.aspx?xh=" + self.student.studentnumber.decode('utf-8') + "&xm=" + self.student.urlName.decode('utf-8') + "&gnmkdm=N121603"
        response = self.session.get(url, allow_redirects=False)
        __VIEWSTATE = get__VIEWSTATE(response)
        # 获得入学年份
        year = int(self.student.gradeClass.decode("utf-8"))
        term = 1
        today = datetime.date.today()
        # 今年，9月份在去查询课表
        while today.year>year or (today.year==year and today.month>=9 and term==1):
            dbSession = DBSession()
            data = {
                "__EVENTTARGET": "xqd",
                "__EVENTARGUMENT": "",
                "__VIEWSTATE": __VIEWSTATE,
                "xnd": str(year)+"-"+str(year+1),
                "xqd": str(term),
            }
            # self.session.headers['Referer'] = url 
            strYear = str(year)+"-"+str(year+1)           
            print ("正在获取"+strYear+"学年第"+str(term)+"学期课表")
            response = self.session.post(url, data)
            __VIEWSTATE = get__VIEWSTATE(response)
            classes = getClassScheduleFromHtml(response)            
            print(classes)            
            
            classSchedule = dbSession.query(ClassSchedule).filter(and_(ClassSchedule.year==strYear, ClassSchedule.term==term)).first()
            if classSchedule == None:
                classSchedule = ClassSchedule(student_id=self.student.id, year=strYear, term=term)
            else:
                classSchedule.year = strYear
                classSchedule.term = term
            dbSession.add(classSchedule)
            dbSession.commit()

            # 获取classSchedule id
            classSchedule = dbSession.query(ClassSchedule).filter(and_(ClassSchedule.year==strYear, ClassSchedule.term==term)).first()
            schedule_id = classSchedule.id

            # 遍历当前学期的所有课程
            for each in classes:
                # 相同课程在不同时间段，可能有课程
                oneClass = dbSession.query(Class).filter(and_(Class.name==each["name"], Class.timeInTheDay==each["timeInTheDay"])).first()
                if oneClass == None:
                    oneClass = Class(schedule_id=schedule_id, name=each["name"], teacher=each["teacher"], site=each["site"], timeInTheWeek=each["timeInTheWeek"], timeInTheDay=each["timeInTheDay"], timeInTheTerm=each["timeInTheTerm"])
                else:
                    oneClass.name = each["name"]
                    oneClass.teacher = each["teacher"]
                    oneClass.site = each["site"]
                    oneClass.timeInTheWeek = each["timeInTheWeek"]
                    oneClass.timeInTheDay = each["timeInTheDay"]
                    oneClass.timeInTheTerm = each["timeInTheTerm"]                
                dbSession.add(oneClass)
                dbSession.commit()

            # 学期更替
            term = term + 1
            if term>2:
                term = 1
                year = year+1
        print ("成功获取课表")

    # 获取学生绩点
    def getStudentGrade(self):
        self.session.headers['Referer'] = self.baseUrl + "/xs_main.aspx?xh=" + self.student.studentnumber.decode('utf-8')
        url = self.baseUrl + "/xscjcx.aspx?xh=" + self.student.studentnumber.decode('utf-8') + "&xm=" + self.student.urlName.decode('utf-8') + "&gnmkdm=N121618"        
        response = self.session.get(url)
        # 获取 VIEWSTATE
        __VIEWSTATE = get__VIEWSTATE(response)        
        # 学年、学期、课程性质、查询按钮类型
        data = {
            "__EVENTTARGET":"",
            "__EVENTARGUMENT":"",
            "__VIEWSTATE":__VIEWSTATE,
            'hidLanguage':"",            
            "ddlXN":"",
            "ddlXQ":"",
            "ddl_kcxz":"",
            "btn_zcj" : u"历年成绩".encode('gb2312', 'replace')
        }
        response = self.session.post(str(url), data=data)
        # 获取所学的所有课程信息（挑选过后的）
        grades = getGrade(response)
        print (grades)

        # 计算学年、学期、每科的成绩
        # 并更新数据库
        calculateOneTermAndOneYearGPA(self.student, grades)   


            
def calculateOneTermAndOneYearGPA(student, grades):
    # 获取入学年份 & 当前的年份
    entYear = student.gradeClass.decode('utf-8')
    curYear = time.strftime("%Y", time.localtime())
    
    # 存放学年的数组
    # ['2015-2016', '2016-2017', '2017-2018']
    years = []
    for year in range(int(entYear), int(curYear)):
        years.append(str(year) + "-" + str(year+1))            

    # 遍历学年        
    for year in years:
        dbSession = DBSession()
        print("")
        print("-----------------------------------")            
        print("年份: %s"%(year))

        # 分别计算同一学年一二学期的绩点和 & 学分和            
        sumGrade1 = 0.0
        sumCredit1 = 0.0            
        count1 = 0

        sumGrade2 = 0.0
        sumCredit2 = 0.0            
        count2 = 0

        # 遍历所有的课程成绩
        for grade in grades:
            if grade["year"] == year:
                # 第一学期
                if grade["term"] == "1":
                    count1 += 1
                    sumGrade1 += float(grade["gradePonit"]) * float(grade["credit"])
                    sumCredit1 += float(grade["credit"])

                # 第二学期
                if grade["term"] == "2":
                    count2 += 1
                    sumGrade2 += float(grade["gradePonit"]) * float(grade["credit"])
                    sumCredit2 += float(grade["credit"])

        # 学年 GPA & 总学分
        yearGPA = float( '%.2f'% ((sumGrade1 + sumGrade2)/(sumCredit1 + sumCredit2)))
        yearCredit = sumCredit1 + sumCredit2
        print("yearGPA: %.2f, yearCredit:%.2f"%(yearGPA, yearCredit))
        
        # 学年成绩表
        # 先从数据库获取，不存在，则添加，存在更新
        # filter 和 filter_by 的区别
        # 参考：https://segmentfault.com/q/1010000000140472、https://my.oschina.net/freegeek/blog/222725
        yearGrade = dbSession.query(YearGrade).filter(and_(YearGrade.year==year, YearGrade.student_id==student.id)).first()
        if yearGrade == None:
            yearGrade = YearGrade(student_id=student.id, year=year, yearGPA=yearGPA, yearCredit=yearCredit)
        else:
            yearGrade.yearGPA = yearGPA
            yearGrade.yearCredit = yearCredit
        dbSession.add(yearGrade)
        dbSession.commit()
        # dbSession.close()

        # 为了获取year_id，所以需要先存储yearGrade
        yearGrade = dbSession.query(YearGrade).filter(and_(YearGrade.year==year, YearGrade.student_id==student.id)).first()
        year_id = yearGrade.id
        
        # 学期1 GPA & 总学分
        if count1 != 0:            
            termGPA1 = float('%.2f'%(sumGrade1/sumCredit1))
            termCredit1 = sumCredit1

            print("第一学期，绩点和:%.2f, 学分和:%.2f, 课程数量:%d"%(sumGrade1, sumCredit1, count1))
            # 学期成绩表
            termGrade = dbSession.query(TermGrade).filter(and_(TermGrade.year_id==year_id, TermGrade.term=="1")).first()
            if termGrade == None:
                termGrade = TermGrade(year_id=year_id, term="1", termGPA=termGPA1, termCredit=termCredit1)
            else:
                termGrade.termGPA = termGPA1
                termGrade.termCredit = termCredit1
            dbSession.add(termGrade)
            dbSession.commit()
        
        # 学期2 GPA & 总学分
        if count2 != 0:            
            termGPA2 = float( '%.2f'%(sumGrade2/sumCredit2))
            termCredit2 = sumCredit2                
            print("第二学期，绩点和:%.2f, 学分和:%.2f, 课程数量:%d"%(sumGrade2, sumCredit2, count2))
            # 学期成绩表
            termGrade = dbSession.query(TermGrade).filter(and_(TermGrade.year_id==year_id, TermGrade.term=="2")).first()
            if termGrade == None:
                termGrade = TermGrade(year_id=year_id, term="2", termGPA=termGPA2, termCredit=termCredit2)
            else:
                termGrade.termGPA = termGPA2
                termGrade.termCredit = termCredit2
            dbSession.add(termGrade)
            dbSession.commit()

        # 记录每学期的课程成绩        
        # 遍历所有的课程成绩
        for oneGrade in grades:
            if oneGrade["year"] == year:
                # 获取term_id
                termGrade = dbSession.query(TermGrade).filter(and_(TermGrade.year_id==year_id, TermGrade.term==oneGrade["term"])).first()
                term_id = termGrade.id
                
                oneLessonGrade = dbSession.query(OneLessonGrade).filter(and_(OneLessonGrade.term_id==term_id, OneLessonGrade.no==oneGrade["no"])).first()
                if oneLessonGrade == None:
                    # TypeError: 'gradesPonit' is an invalid keyword argument for OneLessonGrade
                    # 换成其他字母就行？？？
                    oneLessonGrade = OneLessonGrade(term_id=term_id, no=oneGrade["no"], name=oneGrade["name"],
                                                    type=oneGrade["type"], credit=float(oneGrade["credit"]), grade_point=float(oneGrade["gradePonit"]), grade=oneGrade["grade"])                    
                else:
                    oneLessonGrade.name = oneGrade["name"]
                    oneLessonGrade.type = oneGrade["type"]
                    oneLessonGrade.credit = float(oneGrade["credit"])
                    oneLessonGrade.grade_point = float(oneGrade["gradePonit"])
                    oneLessonGrade.grade = oneGrade["grade"]
                dbSession.add(oneLessonGrade)
                dbSession.commit()

if __name__ == "__main__":
    # 查找学生，若不存在则创建账号
    dbSession = DBSession()
    student = dbSession.query(Student).filter_by(studentnumber="学号").first()
    if student == None:
        #用自己的教务系统账号密码
        student = Student(studentnumber="学号", password="密码", name="姓名")
        dbSession.add(student)
        dbSession.commit()
        print("新增学生成功")
    else:
        print("获取学生成功")
        # 从数据库里获取（要注意数据的格式）
        # print("学号：%s, 姓名：%s"%(student.studentnumber, student.name))
        # 打印对象的所有属性
        # print(student.__dict__)
        print("学号：%s, 姓名：%s"%(student.studentnumber.decode('utf-8'), student.name.decode('utf-8')))
    
    # 开始爬虫
    spider = ZhengFangSpider(student=student) # 实例化爬虫    
    # spider.testgetGrade()
    # spider.getClassScheduleTest()
    if spider.login():        
        # spider.getStudentBaseInfo(dbSession)
        # spider.getStudentGrade()
        spider.getClassSchedule()

