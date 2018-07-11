# zfspider
> 正方学籍系统爬虫

#### 想法：

1. 通过用户名和密码登录，自动获取绩点、成绩、课程表、个人信息等（自动选课、学期自动评价）
2. 将获取到的信息，存入MYSQL
3. 通过MySQL搭建校园服务平台信息（1.后台 2.小程序 3. iOS 4. Android）

#### 已完成：

1. 通过用户名和密码登录，自动获取绩点、成绩、课程表、个人信息
2. 将信息存入数据库

#### 待完成：

1. 学籍系统其他信息挖掘
2. 验证码自动识别
3. 后台API服务
4. 小程序
5. iOS
6. Android
7. WEB



## 1. 爬虫过程

### 1. 环境：

**1. 采用的工具**：

1. sublime Text（代码编写）
2. iTerm2（代码运行）
3. Anaconda （Python包管理）
4. Chrome（访问抓包、测试）

**2. 运行环境：**

1. 系统：OSX 10.11.6
2. 数据库：MYSQL 5.6
3. Python：Python 3.6
4. Charles：抓包工具



### 2. 项目文件：

`spider.py`：主文件

`zfmodel.py`：模型文件，构建数据库

`zfparesHtml.py`：解析返回的HTML数据



## 2. 源码分析

### spider.py

**运行流程：**

1. 建立数据库连接，通过**学号**获取数据库中已用的学生信息，否则就将用户输入的学生信息（学号、密码、姓名）添加到数据库里
2. 实例化爬虫类`ZhengFangSpider`，传入学生信息，默认的`baseURL=http://学籍系统网站或IP/(0sh5f5fnxcowan45z1oa2h55)`，关于`0sh5f5fnxcowan45z1oa2h55`，因为在不同时间访问的时候，发现会在URL的后面添加这**一串字符**会随时间的改变而改变（可能为时间的MD5值截取部分（25位），只要不为空就能访问）
3. 用户登录，等待用户输入验证码（手动，保存在`./code.jpg`），可以输入1，换一张验证码。这里可以优化为**AI自动识别**
4. 登录成功，获取学生的信息，并更新数据库
5. 获取学生的所有成绩、绩点、学分
6. 获取学生的所有课程表



### zfmodel.py

使用Python中`SQLAlchemy`作为`ORM`来构建模型，数据库驱动使用`mysql-connector`



#### 初次使用

```python
# engine = create_engine('mysql+mysqlconnector://root:123456@localhost:3306/test')
# 单独运行该文件，用于初始创建表用，前提你的数据库连接完毕
if __name__ == '__main__':
    Base.metadata.create_all(engine)
```



#### SQLAlchemy

1. 导入包

```python
# 数据库引擎、外键
from sqlalchemy import create_engine, ForeignKey
# 数据库模型
from sqlalchemy.ext.declarative import declarative_base
# 数据库类型
from sqlalchemy import Column, String, Integer, Float
# 事物和关系(1:1、1:n、m:n)
from sqlalchemy.orm import sessionmaker, relationship
```



2.模型构建

> 注意设置好模型之间的关系、外键和类型

1. `Student`：学生模型
2. `ClassSchedule`：课表模型
3. `Class`：课程模型
4. `YearGrade`：学年成绩模型
5. `TermGrade`：学期成绩模型
6. `OneLessonGrade`：课程模型





### zfparHtml.py

用到了HTML解析：`bs4`



#### 实现的功

1. 从网页中解析学生信息，返回一个字典

```python
def getStudentInfor(response):
    return d
```



2. 从网页中解析课表信息

> 获取课程表，是比较复杂的操作，因课程表里面的信息，排列关系每个单元格可能不同，所以需要进行判断

```python
def getClassScheduleFromHtml(response):
    return classes
```



3. 获取`__VIEWSTATE`

> 这个是.net中独有的信息

```python
def get__VIEWSTATE(response):
    return __VIEWSTATE
```



4. 返回历年的所有课程信息（一门课程为单位）

```python
def getGrade(response):
    return Grades
```





## 3. 注意点

1. 从数据库里获取（要注意数据的格式），可能需要转码

2. 数据存储的顺序(外键关系)

3. POST提交的Data

4. Failed processing pyformat-parameters; Python 'navigablestring' cannot be converted to a MySQL type

   ```python
       # 原因在于bs的字符类型，无法转换为MySQL的类型，所以在上诉字典中的数据强制转换为 str
       # 参考链接：https://www.zhihu.com/question/49146377
   ```

5. 获取个人信息的URL（由于缺少学生名字的URL编码）,# 通过抓包发现需要的是：`%D1%A7%C9%FA`，如果直接填写会变成：`%25D1%25A7%25C9%25FA`

6. 正则表达式



## 4. 总结

1. Python中的工具，可以说是减少了大部分时间去重复造轮子，能让你把注意力放在实现上面，减少了时间的浪费并提供了效率，这次项目原型来自于[GitHub](<https://github.com/SimpleBrightMan/ZhengFang>)，这里感谢**TA**，提供的框架和思路
2. 实现过程主要是采用了`request`、`bs4`库，`request`从网页中提取和提交信息，`bs4`解析网页返回`HTML`代码，通过正则表达式或者遍历，提取出自己感兴趣的内容（这里是整个项目中消耗时间最多的地方，因为网页的信息比较**复杂**，可能随时会改变（这里就需要**抓包工具**的配合），需要不断地维护爬虫的源码）。并通过`SQLAlchemy`将信息保存到数据库里面
3. 对于数据库的构建来说，注意点在于（id）这个是自动递增的，其他的属性可以作为**超键**来唯一标识一个数据是关键（换句话说，要想构建id为主键，那么你需要有除i外的属性能够唯一标识元组），同时需要设计好模型之间的关系
4. 最后，需要对代码进行重构，提高代码的可读性和结构，降低耦合性，模块化、**维护**，同样自己也要更加地区学习Python



## 5. 贡献

如果你有好的意见或建议，欢迎给我提 [issue](https://github.com/iLifexiao/zfspider/issues) 或 [pull request](https://github.com/iLifexiao/zfspider/pulls)。