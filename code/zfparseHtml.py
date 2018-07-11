# coding=utf-8
from bs4 import BeautifulSoup


# 从网页中解析学生信息，返回一个字典
def getStudentInfor(response):
    html = response.content.decode("gb2312")
    # soup = BeautifulSoup(html.decode("utf-8"), "html5lib")    
    soup = BeautifulSoup(html, "html5lib")
    # print(soup.prettify())
    d = {}
    d["studentnumber"] = str(soup.find(id="xh").string)
    d["idCardnumber"] = str(soup.find(id="lbl_sfzh").string)
    d["name"] = str(soup.find(id="xm").string)
    d["sex"] = str(soup.find(id="lbl_xb").string)
    d["enterSchoolTime"] = str(soup.find(id="lbl_rxrq").string)
    d["birthsday"] = str(soup.find(id="lbl_csrq").string)
    d["highschool"] = str(soup.find(id="byzx").string)
    d["nationality"] = str(soup.find(id="lbl_mz").string)        
    d["college"] = str(soup.find(id="lbl_xy").string)
    d["major"] = str(soup.find(id="lbl_zymc").string)
    d["classname"] = str(soup.find(id="lbl_xzb").string)
    d["gradeClass"] = str(soup.find(id="lbl_dqszj").string)    
    return d


# 从网页中解析课表信息
def getClassScheduleFromHtml(response):
    html = response.content.decode("gb2312","ignore")
    soup = BeautifulSoup(html, "html5lib")
    # 课程表所在的标签位置的所有行
    trs = soup.find(id="Table1").find_all('tr')
    classes = []
    for tr in trs:
        # 每行中的所有元素
        tds = tr.find_all('td')
        for td in tds:                        
            if td.string == None:
                oneClassKeys = ["name", "time", "teacher", "site"]
                oneClassValues = []
                for child in td.children:
                    # 删除停课信息[(停0]
                    if child.string != None and '(停0' not in child.string:
                        # bs的string类型和MySQL的类型需要装换
                        # navigablestring -> str
                        oneClassValues.append(str(child.string))
                # 课程信息不完整，添加空信息
                while len(oneClassValues) < len(oneClassKeys):
                    oneClassValues.append("")
                # 添加一个课程                
                oneClass = dict((key, value) for key, value in zip(oneClassKeys, oneClassValues))
                oneClass["timeInTheWeek"] = oneClass["time"].split("{")[0][:2]
                oneClass["timeInTheDay"] = oneClass["time"].split("{")[0][2:]
                oneClass["timeInTheTerm"] = oneClass["time"].split("{")[1][:-1]
                classes.append(oneClass)
                
                # 可能一个表格里面存在两个课程，这里就需要进行判断了
                # 如果包含两个课程，oneClassValues的数量可能有8个
                if len(oneClassValues) == 8:
                    restClassValues = oneClassValues[4:]
                    oneClass = dict((key, value) for key, value in zip(oneClassKeys, restClassValues))                    
                    oneClass["timeInTheWeek"] = oneClass["time"].split("{")[0][:2]
                    oneClass["timeInTheDay"] = oneClass["time"].split("{")[0][2:]
                    oneClass["timeInTheTerm"] = oneClass["time"].split("{")[1][:-1]
                    classes.append(oneClass)
    return classes


def get__VIEWSTATE(response):
    html = response.content.decode("gb2312")
    soup = BeautifulSoup(html, "html5lib")
    # __VIEWSTATE的input正好是第三个
    __VIEWSTATE = soup.findAll(name="input")[2]["value"]
    return __VIEWSTATE

# 返回历年的所有课程信息（一门课程为单位）
def getGrade(response):
    html = response.content.decode("gb2312")
    soup = BeautifulSoup(html, "html5lib")
    # <tr>表示行，这里表示找到表示成绩的表格，然后获取所有的行
    trs = soup.find(id="Datagrid1").findAll("tr")[1:]
    Grades = []
    # 遍历所有的行
    for tr in trs:        
        tds = tr.findAll("td")
        # 提取部分信息（分片，不包含结尾的元素）
        # tds = tds[:2] + tds[3:5] + tds[6:9]
        # oneGradeKeys = ["year", "term", "name", "type", "credit", "gradePonit", "grade"]
        tds = tds[:5] + tds[6:9]
        # 学年、学期、课程代码、课程名称、课程性质、学分、绩点、成绩
        oneGradeKeys = ["year", "term", "no", "name", "type", "credit", "gradePonit", "grade"]
        oneGradeValues = []

        # td 表示一行里面的元素，提取出分片后的数据
        for td in tds:
            oneGradeValues.append(str(td.string))
        # 生成一个key,Value对应的字典
        # zip() 函数用于将可迭代的对象作为参数，将对象中对应的元素打包成一个个元组，然后返回由这些元组组成的列表。
        # 参考链接：http://www.runoob.com/python/python-func-zip.html
        oneGrade = dict((key, value) for key, value in zip(oneGradeKeys, oneGradeValues))
        Grades.append(oneGrade)
    return Grades

