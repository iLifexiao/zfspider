# coding=utf-8
from sqlalchemy import create_engine, ForeignKey, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Float
from sqlalchemy.orm import sessionmaker, relationship

Base = declarative_base()

engine = create_engine('mysql+mysqlconnector://root:123456@localhost:3306/test')
# 创建DBSession类型:
DBSession = sessionmaker(bind=engine)

class Student(Base):
    __tablename__ = 'student'

    # 自动递增的ID
    id = Column(Integer, primary_key=True)
    name = Column(String(20))   # 姓名
    urlName = Column(String(40))  # url编码后的姓名
    studentnumber = Column(String(20))  # 学号
    password = Column(String(40))  # 教务系统密码
    idCardNumber = Column(String(30))  # 身份证号
    sex = Column(String(20))  # 性别
    enterSchoolTime = Column(String(20))  # 入学时间
    birthsday = Column(String(20))  # 出生日期
    highschool = Column(String(40))  # 毕业中学
    nationality = Column(String(20))  # 名族     
    college = Column(String(40))  # 学院
    major = Column(String(40))  # 专业
    classname = Column(String(20))  # 所在班级
    gradeClass = Column(String(20))  # 年级

    # 一对多关系，包含多个classSchedule的list
    classSchedules = relationship('ClassSchedule', backref='student')
    yeargrades = relationship('YearGrade', backref='student')


class ClassSchedule(Base):
    __tablename__ = 'classschedule'

    id = Column(Integer, primary_key=True)    
    student_id = Column(Integer, ForeignKey('student.id'))  # 学号
    year = Column(String(20))  # 年度
    term = Column(Integer)  # 学期

    classs = relationship('Class', backref='classschedule')


class Class(Base):
    __tablename__ = 'class'

    id = Column(Integer, primary_key=True)    
    schedule_id = Column(Integer, ForeignKey('classschedule.id'))  # 归属课表    
    name = Column(String(40))  # 课程名称
    timeInTheWeek = Column(String(20))  # 星期几
    timeInTheDay = Column(String(20))  # 第几节课
    timeInTheTerm = Column(String(20))  # 上课周数
    teacher = Column(String(20))  # 授课教师
    # location = Column(String(40))  # 授课地点
    site = Column(String(40))  # 授课地点


class YearGrade(Base):
    __tablename__ = 'yeargrade'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('student.id'))  # 学号
    year = Column(String(20)) # 学年
    yearGPA = Column(Float)  # 学年GPA
    yearCredit = Column(Float)  # 学年总学分

    trems = relationship('TermGrade', backref='yeargrade')


class TermGrade(Base):
    __tablename__ = 'termgrade'

    id = Column(Integer, primary_key=True)
    year_id = Column(Integer, ForeignKey('yeargrade.id'))  # 归属学年
    term = Column(String(20)) # 学期
    termGPA = Column(Float) # 学期GPA
    termCredit = Column(Float) #学期总学分


class OneLessonGrade(Base):
    __tablename__ = 'onelessongrade'

    id = Column(Integer, primary_key=True)
    term_id = Column(Integer, ForeignKey('termgrade.id'))  # 归属学期
    no = Column(String(40))  # 课程代码
    name = Column(String(40))  # 课程名
    type = Column(String(20))  # 课程性质
    credit = Column(Float)  # 学分
    grade_point = Column(Float)  # 绩点
    grade = Column(String(20))  # 成绩


# 用于初始创建表用
# if __name__ == '__main__':
#     Base.metadata.create_all(engine)