import sys
import csv
import nmap
import requests
import threading
import os
import time
import math
import queue
from selenium import webdriver
import selenium
import urllib3

#use: sudo python3 go.py xxx.csv xxx.html 200 30 8080,8081
os.system("mkdir img")


running_status = {}
running_status_a = {}
req_tmp = []
result_200 = []
result_n200 = []

def log_file(filename, content):
	f = open(filename,"a")
	f.write(content)
	f.close()

def log_errors(e, subdomain, port):
	print("==============================================================")
	print("log errors")
	print(e)
	print("==============================================================")

	localtime = time.strftime("%a %b %d %H:%M:%S %Y", time.localtime())
	log_file("error.log", localtime + "\n" + e + "\n" + str(port) + "\n"  + subdomain + "\n")

#use nmap scan the hsot
def pan_scan_port(subdomain, ports):
	portOpen = []
	noWebFlag = [0,0]
	
	nm = nmap.PortScanner()
	scanResult = nm.scan(subdomain, ports,"-sS -T4")

	#can not be resolved
	if "error" in scanResult['nmap']['scaninfo'].keys():
		return {"code" : 0}
	
	#get the result
	try:
		scanResult = list(scanResult['scan'].values())[0]['tcp']
		for info in scanResult.items():
			if info[1]['state'] == "open":
				portOpen.append(info[0])

			if info[1]['state'] != 'open' and info[0] == 80:
				noWebFlag[0] = 1
			if info[1]['state'] != 'open' and info[0] == 443:
				noWebFlag[1] = 1

		if noWebFlag[0] == noWebFlag[1] == 1:
			log_file("noWebHost.log", subdomain+"\n")

	except IndexError:
		pass

	return {"code" : 1, "portOpen" : portOpen}

#send requests to the subdomain. To get isalive,statuCode,title,url
def pan_uri_response(subdomain,portList):
	responseDict = {}

	if portList != []:
		for port in portList:
			responseDict[str(port)] = {}

			url = "http://" + subdomain + ":" + str(port)
			try:
				r = requests.get(url=url,timeout=2)
			except:
				r = ""

			if r != "":
				try:
					r.encoding = r.apparent_encoding
					title = r.text.split("<title>")
					title = title[1].split("</title>")[0]
				except:
					title = ""
				responseDict[str(port)]['title'] = title
				responseDict[str(port)]['subdomain'] = subdomain
				responseDict[str(port)]['port'] = port
				responseDict[str(port)]['headers'] = r.headers
				responseDict[str(port)]['status_code'] = r.status_code

	return {"code" : 1, 'subdomain' : subdomain, 'responseDict' : responseDict}

#get the web screen shot
def pan_screen_shot(driver, subdomain, port, q):
	try:
		driver.get(subdomain)
		imgName = "img/pan_http_" + subdomain + "_" + str(port[0]) + ".png"
		imgName = imgName.replace("://","_")
		imgName = imgName.replace(":","_")
		driver.get_screenshot_as_file(r""+imgName)
		q.put(imgName)
	except selenium.common.exceptions.TimeoutException:
		q.put(1)
		pass
	except selenium.common.exceptions.WebDriverException:
		q.put(1)
		log_errors("selenium.common.exceptions.WebDriverException", subdomain, str(port))
	except selenium.common.exceptions.UnexpectedAlertPresentException:
		q.put(1)
		log_errors("selenium.common.exceptions.UnexpectedAlertPresentException", subdomain, str(port))
	except urllib3.exceptions.ProtocolError:
		q.put(1)
		log_errors("urllib3.exceptions.ProtocolError", subdomain, str(port))
	except KeyError:
		q.put(1)
		pass

def req_to_go(subdomainsList,i):
	global running_status
	global req_tmp

	running_status[i]['count'] = len(subdomainsList)
	running_status[i]['now'] = 0
	running_status[i]['state'] = 0

	for subdomain in subdomainsList:
		running_status[i]['subdomain'] = subdomain
		running_status[i]['now'] = running_status[i]['now'] + 1

		try:
			ports = sys.argv[5]
		except:
			ports = "80,443"
		portOpen = pan_scan_port(subdomain, ports)

		if portOpen['code'] == 1:
			uri = pan_uri_response(subdomain, portOpen['portOpen'])
			req_tmp.append(uri)

	running_status[i]['state'] = 1

def shot_to_go(subdomainsList,i):
	global result_200
	global result_n200

	running_status_a[i]['count'] = len(subdomainsList)
	running_status_a[i]['now'] = 0
	running_status_a[i]['state'] = 0

	driver = webdriver.Chrome()
	driver.set_page_load_timeout(10)
	driver.set_script_timeout(10)

	for s in subdomainsList:
		running_status_a[i]['now'] = running_status_a[i]['now'] + 1
		running_status_a[i]['subdomain'] = s['subdomain']

		#the result that the port not be opened
		if s["responseDict"] == {}:
			log_file("responseDictNone.log", "NULL " + s['subdomain'] + "\n")
			continue

		#the result that port not be requested successed
		for code in s["responseDict"].items():
			if code[1] == {}:
				log_file("responseDictNone.log", "Port " + s['subdomain'] + "\n")
			else:
				if int(code[1]['status_code']) < 200 or int(code[1]['status_code']) > 399:
					code[1]['imgName'] = ""
					result_n200.append(code[1])
				else:
					q = queue.Queue()
					code[1]['imgName'] = ""
					url = "http://" + s['subdomain'] + ":" + str(code[0])
					threading.Thread(target=pan_screen_shot, args=(driver, url, code[0], q)).start()
					while True:
						try:
							res =  q.get()
							break
						except:
							print("q  time out")
					if res != 1:
						code[1]['imgName'] = res
					result_200.append(code[1])

	driver.quit()
	running_status_a[i]['state'] = 1


subdomainsList = []
f = open(sys.argv[1],encoding="utf-8")
f_csv = csv.reader(f)
for row in f_csv:
	if row[7] == "subdomain":
		continue
	else:
		subdomainsList.append(row[7])

#default 200 and 30 thread
try:
	req_tNumber = int(sys.argv[3])
	shot_tNumber = int(sys.argv[4])
except:
	req_tNumber = 200
	shot_tNumber = 30


if len(subdomainsList) < req_tNumber:
	req_tNumber = len(subdomainsList)

if len(subdomainsList) < shot_tNumber:
	shot_tNumber = len(subdomainsList)


for i in range(req_tNumber):
	interval = math.ceil(len(subdomainsList) / req_tNumber)
	if((i*interval) < len(subdomainsList)):
		subsList = subdomainsList[(i*interval):(i+1)*interval]

		if not len(subsList) <= 0:
			running_status[i] = {}
			threading.Thread(target=req_to_go,args=(subsList,i)).start()


#SHOW LOG
while True:
	DoneFlag = 1
	for r in running_status.items():
		print(r)
		try:
			if r[1]['state'] == 0:
				DoneFlag = 0
		except:
			DoneFlag = 0
			print("state warnning!")
	if DoneFlag == 1:
		break
	time.sleep(1)

print("===========================================================")
print("===========================================================")
print("=================!!! shot screen time !!!==================")
print("===========================================================")
print("===========================================================")
time.sleep(1)

for i in range(shot_tNumber):
	interval = math.ceil(len(req_tmp) / shot_tNumber)
	if((i*interval) < len(req_tmp)):
		subsList = req_tmp[(i*interval):(i+1)*interval]

		if not len(subsList) <= 0:
			running_status_a[i] = {}
			threading.Thread(target=shot_to_go,args=(subsList,i)).start()
			time.sleep(1)

#SHOW LOG
while True:
	DoneFlag = 1
	for r in running_status_a.items():
		print(r)
		try:
			if r[1]['state'] == 0:
				DoneFlag = 0
		except:
			DoneFlag = 0
			print("state warnning!")
	if DoneFlag == 1:
		break
	time.sleep(1)

print("====================================================")
print("WIll be Down")
print("====================================================")

time.sleep(1)

f = open(sys.argv[2],"w")
content = ""
head = '<!DOCTYPE html><html><head><title>Xiaopan233-scan</title><style type="text/css">.line{width: 100%;display: flex;flex-direction: row;flex-wrap: nowrap;justify-content: center;}div{padding: 20px 30px;}#shadow1{width:100%;height:100%;position:fixed;left:0;top:0;z-index:998;background-color:black;opacity:0.6;display: none;}#shadow2{width:100%;height:100%;position:fixed;left:0;top:0;z-index:999;display: flex;flex-direction: row;flex-wrap: nowrap;justify-content: center;display: none;}</style></head><body><div>'
for r in result_200:
	content = content + ""

	content = content + '<div class="line">'

	content = content + '<div class="basic">'
	content = content + '<p>Subdomain: ' + r['subdomain'] + '</p>'
	content = content + '<p>Port: ' + str(r['port']) + '</p>'
	content = content + '<p>Title: ' + r['title'] + '</p>'
	content = content + '<p>Status_code: ' + str(r['status_code']) + '</p>'
	content = content + '</div>'

	content = content + '<div class="header">'
	for h_key in r['headers'].items():
		content = content + '<p>' + h_key[0] + ': ' + h_key[1] + '</p>'
	content = content + '</div>'

	content = content + '<div class="img">'
	content = content + '<img src="' + r['imgName'] + '" width="300px" onclick="showPic(this)">'
	content = content + '</div>'

	content = content + '</div>'

for r in result_n200:
	content = content + ""

	content = content + '<div class="line">'

	content = content + '<div class="basic">'
	content = content + '<p>Subdomain: ' + r['subdomain'] + '</p>'
	content = content + '<p>Port: ' + str(r['port']) + '</p>'
	content = content + '<p>Title: ' + r['title'] + '</p>'
	content = content + '<p>Status_code: ' + str(r['status_code']) + '</p>'
	content = content + '</div>'

	content = content + '<div class="header">'
	for h_key in r['headers'].items():
		content = content + '<p>' + h_key[0] + ': ' + h_key[1] + '</p>'
	content = content + '</div>'

	content = content + '</div>'

foot = '</div><div id="shadow1"></div><div id="shadow2" onclick="showShadow(this)"></div></body></html><script>function showPic(that){var content = document.getElementById("shadow2");var newImg = document.createElement("img");newImg.src = that.src;newImg.id = "newImg";content.appendChild(newImg);document.getElementById("shadow1").style.display = "block";document.getElementById("shadow2").style.display = "block";document.getElementById("shadow2").style = "display: flex;flex-direction: row;flex-wrap: nowrap;justify-content: center;";} function showShadow(that){var content = document.getElementById("shadow2");var newImg = document.getElementById("newImg");content.removeChild(newImg);document.getElementById("shadow1").style.display = "none";document.getElementById("shadow2").style.display = "none";}</script>'

f.write(head + content + foot)
f.close()