#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2018/10/19 15:26
# @Author  : Yao
# @Email   : 15927402897@163.com
# @project : RASER1.2
# 此程序用来爬取HZAU实验室技术安全知识学习与考试系统的测试题，网址：http://211.69.128.172/tltest/pages/StudentMain.aspx

"""
改进：
数据库是每次抽取50题目
所以爬多次，筛选独立（没有出现过的）的题目
运行请补充账号密码！
"""

from selenium import webdriver
from time import sleep
import os
import os
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.action_chains import ActionChains


account = "***"
password = "***"


def generate_question_database(paper_file):
    question_database = []
    QN = 0
    with open(paper_file, "r") as doc:
        for line in doc.readlines():
            if line.startswith(">"):
                question_database.append(line.strip("\n").split(".", 1)[1])
                QN += 1
    return question_database, QN


def main():
    # 无界面
    global browser
    opt = webdriver.ChromeOptions()
    opt.set_headless()
    browser = webdriver.Chrome(options=opt)  #环境变量设置好的情况下
    # browser = webdriver.Chrome('/public/home/yxu/tools/chromedriver/chromedriver')

    #browser = webdriver.Chrome()

    log_in_url = 'http://211.69.128.172/tltest'
    download_doc = 'F:/practice/'
    browser.get(log_in_url)
    user_name = browser.find_element_by_id('txtuserid').send_keys(account)  # 账号
    passwd = browser.find_element_by_id('txtpass').send_keys(password)  # 密码
    browser.find_element_by_xpath('//*[@id="Button1"]').click() # 登陆
    prictice_button = browser.find_element_by_xpath('//*[@id="t3"]/a')  # 对于非click的button来说，有js，需要找到位置在执行js
    browser.execute_script("$(arguments[0]).click()", prictice_button)  # 到达训练题目
    window=browser.window_handles  # 获取当前页句柄
    browser.switch_to_window(window[-1])  # 跳转到新页面
    # 得到试卷名称
    papar_name = []
    i = 1
    for ID in ("DataList1_ctl"+str(y)+"_HyperLink1" for y in (["0"+str(x) for x in range(10)]+[str(x) for x in range(10,20)])):
        papar_name.append(str(i) + browser.find_element_by_id(ID).text)
        i += 1

    def ElementExist(element, by):
        global browser
        if by == 'xpath':
            try:
                browser.find_element_by_xpath(element)
                return True
            except:
                return False

    paper_href_list = ['0'+str(x) for x in range(10)]
    paper_href_list += [str(x) for x in (10,11,12,13,14,20,21,22,23,24)]
    # 遍历所有试卷
    page = -1
    # 定义每次跑脚本添加独有题目的总个数
    total_independent_question_num = 0
    #  对每一份试卷生成单个文件
    for new_href in ('FLX.aspx?v='+x for x in paper_href_list):
        js = 'window.open("' + new_href + '");'  # 新窗口打开,到达题目
        browser.execute_script(js)
        window = browser.window_handles
        browser.switch_to_window(window[-1])  # 跳转
        page += 1
        print("page:%s" % papar_name[page])
        # 假设存在文件，预读取问题集,看问题是否已经在爬的题库里
        if os.path.exists(download_doc+papar_name[page]+'.txt'):
            question_database, QN = generate_question_database(download_doc+papar_name[page]+'.txt')
        else:
            question_database, QN = [], 0
        with open(download_doc+papar_name[page]+'.txt',"a+") as doc:
            a = browser.find_element_by_xpath('//*[@id="btnsubmit"]').click()
            alert = browser.switch_to_alert()  # confirm 弹出框确认
            alert.accept()
            # 遍历所有题目,得到题目以及答案
            question_num = u'-1'
            next_question_num = u'0'
            while question_num != next_question_num:
                sleep(0.2)
                if ElementExist('//*[@id="lblnum"]','xpath'):  # 经常出现没有该值
                    question_num = browser.find_element_by_xpath('//*[@id="lblnum"]').text
                else:
                    print(browser.page_source)
                question = browser.find_element_by_xpath('//*[@id="lblquestion"]').text  # 此xpath不会变
                if question.encode("utf-8") not in question_database:  # 题库里不存在该题目，保存.早点检查，节省时间
                    answer = browser.find_element_by_xpath('//*[@id="lb_answer"]').text  # 此xpath不会变
                    # 选项xpath会变，选项为单选、判断
                    option = {}
                    my_ASCCI = 65
                    test_xpath = ['//*[@id="RadioButtonList1"]/tbody/tr[1]/td/label', '//*[@id="CheckBoxList1"]/tbody/tr[1]/td/label']
                    if ElementExist(test_xpath[0],'xpath'):
                        for option_xpath in ('//*[@id="RadioButtonList1"]/tbody/tr[' + str(x) + ']/td/label' for x in range(1,10)):
                            if ElementExist(option_xpath, 'xpath'):
                                option[chr(my_ASCCI)]=browser.find_element_by_xpath(option_xpath).text
                                my_ASCCI += 1
                            else:
                                break
                    elif ElementExist(test_xpath[1],'xpath'):
                        # 选项xpath会变，多选
                        for option_xpath in ('//*[@id="CheckBoxList1"]/tbody/tr[' + str(x) + ']/td/label' for x in range(1,10)):
                            if ElementExist(option_xpath,'xpath'):
                                option[chr(my_ASCCI)]=browser.find_element_by_xpath(option_xpath).text
                                my_ASCCI += 1
                            else:
                                break
                    else:
                        print "Warning: Others format!!"
                    total_independent_question_num += 1
                    # print question.encode("utf-8")
                    QN += 1
                    doc.writelines((">"+str(QN)+"."+question+"\n").encode("utf-8"))
                    for key in option:
                        doc.writelines(("\t"+key+"."+option[key]+"\n").encode("utf-8"))
                    doc.writelines(("\t\t"+answer+"\n\n").encode("utf-8"))
                browser.find_element_by_xpath('//*[@id="btnnext"]').click()  # 下一题
                if ElementExist('//*[@id="lblnum"]', 'xpath'):  # 经常出现没有该值
                    next_question_num = browser.find_element_by_xpath('//*[@id="lblnum"]').text
                else:
                    print(browser.page_source)
                next_question_num = browser.find_element_by_xpath('//*[@id="lblnum"]').text
    print("此次添加的题目个数为%d" % total_independent_question_num)
    return total_independent_question_num

if __name__ == '__main__':
    num = main()
    while num != 0:
        num = main()

'''
输出每套卷子的题目个数！
def generate_question_database(paper_file):
    QN = 0
    with open(paper_file, "r") as doc:
        for line in doc.readlines():
            if line.startswith(">"):
                QN += 1
    return QN

download_doc = 'F:/practice/'
all_n = 0
for file_name in os.listdir(download_doc):
    number = generate_question_database(download_doc+"/"+file_name)
    all_n += number
    print(str(number)+"\t"+file_name)
print all_n
'''