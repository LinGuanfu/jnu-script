#!/usr/bin/python
# -*- coding: utf-8-*-
# __auther__ : AstroBruce

import requests
import re
from bs4 import BeautifulSoup

from bin.binarizate import *


HOST_URL = 'http://202.116.0.176/'
POST_URL = 'http://202.116.0.176/Login.aspx'
VALIDATE_CODE = 'http://202.116.0.176/ValidateCode.aspx'
GET_URL = 'http://202.116.0.176/Secure/PaiKeXuanKe/wfrm_XK_MainCX.aspx'
TEMP_PATH = 'F:\\pic\\test2\\temp.tif'

# 初始化post过去的headers和form
headers = {'Referer': 'http://202.116.0.176/Login.aspx',
		   'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64) Chrome/41.0.2272.89 Safari/537.36'}
post_data = {'__VIEWSTATEGENERATOR': 'C2EE9ABB'}
data = {}
session = requests.Session()
session.get(HOST_URL, headers=headers)

# 预登录，为的是下载cookie和form中的某些项的值
def prepare():
	resp = session.get(POST_URL, data=data, headers=headers, timeout=0.3)
	text = BeautifulSoup(resp.content)
	global post_data

	for i in text.select("input#__VIEWSTATE"):
		post_data['__VIEWSTATE'] = i['value'].encode('utf-8')

	for j in text.select("input#__EVENTVALIDATION"):
		post_data['__EVENTVALIDATION'] = j['value'].encode('utf-8')

	for k in text.select("input#btnLogin"):
		post_data['btnLogin'] = k['value'].encode('utf-8')

# 模拟登陆，传入id号跟密码即可
def login(id_number, password):

	# 下载验证码
	resp = session.get(VALIDATE_CODE)
	data = resp.content
	temp = open(TEMP_PATH, "wb")
	temp.write(data)
	temp.close()

	# 用OutputString函数识别验证码
	text = outputString(TEMP_PATH)
	# print text
	global post_data

	post_data['txtFJM'] = '%s' % text
	post_data['txtYHBS'] = '%s' % id_number
	post_data['txtYHMM'] = '%s' % password

	resp = session.post(POST_URL, data=post_data, headers=headers, timeout=0.5)
	length = resp.headers['Content-Length']
	if length == "7819":
		print u"failed"
	elif length == "1325":
		print u"succeed"
	else:
		print u'error'
		raise


def get_examation_time():

	# 初始化post的数据
	local_post_data = {'__EVENTTARGET' : "",
					   '__EVENTARGUMENT' : "",
					   '__LASTFOCUS' : "",
					   }

	#get到排课选课的框架内，下载post内的另外三个数据
	resp = session.get('http://202.116.0.176/Secure/PaiKeXuanKe/wfrm_xk_StudentKcb.aspx')
	html_text = BeautifulSoup(resp.content)

	for input_tag in html_text.findAll('input', limit=3):
		try:
			name = input_tag['name'].encode('utf-8')
			value = input_tag['value'].encode('utf-8')
		except Exception:
			pass
		else:
			local_post_data[name] = '%s' % value

	# 选择的项目
	select_list = [u'导出或打印课程表', u'导出或打印考试安排表', u'第一学期', u'第二学期']

	# 依次是：课表/考试表/考试座位安排学期选择/课表或者考试表学期选择/考试座位安排年份选择/课表或者考试表年份选择
	value_list = ['btnExpKcb', 'btnNewExpKsb', 'dlstNdxq0', 'dlstNdxq', 'dlstXndZ0', 'dlstXndZ']

	for year_tag in html_text.findAll(id="dlstXndZ0"):
		for option_tag in year_tag.findAll("option"):
			if option_tag.has_attr('selected'):
				local_post_data[value_list[4]] = option_tag['value'].encode('utf-8')

	for year_tag in html_text.findAll(id="dlstXndZ"):
		for option_tag in year_tag.findAll("option"):
			if option_tag.has_attr('selected'):
				local_post_data[value_list[5]] = option_tag['value'].encode('utf-8')

	local_post_data[value_list[1]] = select_list[1].encode('GBK')
	local_post_data[value_list[2]] = select_list[3].encode('GBK')
	local_post_data[value_list[3]] = select_list[3].encode('GBK')

	# 到此为止，post的数据构造完毕

	# 先post到排课选课的框架
	resp = session.post('http://202.116.0.176/Secure/PaiKeXuanKe/wfrm_xk_StudentKcb.aspx',
						data=local_post_data,
						headers=headers)
	print resp.content
	# 抓取内部嵌套的frame标签的src
	html = BeautifulSoup(resp.content, from_encoding="GBK")
	ReportFrameReportViewer = html.find(id='ReportFrameReportViewer1')

	# 重定位URL
	redict_url = 'http://202.116.0.176' + ReportFrameReportViewer['src']

	# 进入外面一层frame
	resp = session.get(redict_url)

	# 继续抓取内部frame标签的src
	html = BeautifulSoup(resp.content, from_encoding="GBK")
	report = html.find(id='report')

	# 最终重定位
	redict_url = 'http://202.116.0.176' + report['src']

	# 进入最终界面
	response = session.get(redict_url)

	# 即将进行json封装操作
	html = BeautifulSoup(response.content, from_encoding="GBK")
	# print html.prettify(encoding='utf-8')

	print html.findAll("td", class_="a4")[0].text
	print html.findAll("td", class_="a8")[0].text
	course_list = []

	for i in html.findAll("div", class_="r11"):
		if len(i.text) >= 15:
			fliter = u'考试'
			colon = u'：'
			course = re.findall(r'%s.*?\)' % fliter, i.text)
			test = re.findall(r'(?<=%s)\S*(?=\()' % colon, i.text)
			for test in test:
				print test
			for j in course:
				course_list.append(j.encode('utf-8'))
	# for k in course_list:
		# print k
	# print course_list
			# print i.text.encode('utf-8')

def main():
	try:
		prepare()
	except Exception, e:
		if hasattr(e, 'code'):
			print 'The server could not fullfill our POST-request, ERROR CODE:', [e.code]
		elif hasattr(e, 'reason'):
			print 'We failed to connect the server,error reason:', e.reason
		else:
			print 'Something wrong that we don\'t know had happened.'

	else:
		try:
			login(2014051470, 19951018)
		except Exception, e:
			if hasattr(e, 'code'):
				print 'The server could not fullfill our request, ERROR CODE:', [e.code]
			elif hasattr(e, 'reason'):
				print 'We failed to connect the server,error reason:', e.reason
			else:
				print 'something wrong'
		else:
			get_examation_time()
# -------------------------main----------------------------------------
if __name__ == '__main__':
	main()