import sys
import csv
import nmap
import requests
import threading
import os
import time
from selenium import webdriver
import selenium

#use: sudo python3 go.py xxx.csv 8080,8081
os.system("mkdir img")


#use nmap scan the hsot
def pan_scan_port(subdomain):
	portOpen = []
	#default to scan 80 and 443
	try:
		ports = "80,443," + sys.argv[2]
	except:
		ports = "80,443"
	
	nm = nmap.PortScanner()
	scanResult = nm.scan(subdomain,ports,"-sS -T4")

	#can not be resolved
	if "error" in scanResult['nmap']['scaninfo'].keys():
		return {"code" : 0}
	
	#get the result
	scanResult = list(scanResult['scan'].values())[0]['tcp']
	for info in scanResult.items():
		if info[1]['state'] == "open":
			portOpen.append(info[0])
	return {"code" : 1, "subdomain": subdomain, "portList" : portOpen}

#send requests to the subdomain. To get isalive,statuCode,title,url
def pan_uri_response(subdomain,portList):
	responseDict = {}
	for port in portList:
		responseDict[str(port)] = {
			'http': {},
			'https' : {}
		}

		url1 = "http://" + subdomain + ":" + str(port)
		url2 = "https://" + subdomain + ":" + str(port)
		try:
			r1 = requests.get(url=url1,timeout=2)
		except:
			r1 = ""
		try:
			r2 = requests.get(url=url2,timeout=2)
		except:
			r2 = ""

		if r1 != "":
			try:
				r1.encoding = r1.apparent_encoding
				title = r1.text.split("<title>")
				title = title[1].split("</title>")[0]
			except:
				title = ""
			responseDict[str(port)]['http']['title'] = title
			responseDict[str(port)]['http']['headers'] = r1.headers
			responseDict[str(port)]['http']['status_code'] = r1.status_code

		if r1 != r2 and r2 != "":
			try:
				r2.encoding = r2.apparent_encoding
				title = r2.text.split("<title>")
				title = title[1].split("</title>")[0]
			except:
				title = ""
			responseDict[str(port)]['https']['title'] = title
			responseDict[str(port)]['https']['headers'] = r2.headers
			responseDict[str(port)]['https']['status_code'] = r2.status_code

	return {"code" : 1, 'responseDict' : responseDict}


def pan_screen_shot(driver, subdomain, uri):
	result = {"subdomain" : subdomain, "main" : []}
	for port in uri['responseDict'].items():
		if port[1]['http'] != {}:
			try:
				driver.get("http://" + subdomain + ":" + str(port[0]))
				imgName = "img/pan_" + "http_" + subdomain + "_" + str(port[0]) + ".png"
				driver.get_screenshot_as_file(r""+imgName)
				res = {
					'port' : port[0],
					'method' : 'http',
					'title' : port[1]['http']['title'],
					'headers' : port[1]['http']['headers'],
					'status_code' : port[1]['http']['status_code'],
					'imgName' : imgName
				}
				result['main'].append(res)
			except selenium.common.exceptions.TimeoutException:
				pass

		if port[1]['https'] != {}:
			try:
				driver.get("https://" + subdomain + ":" + str(port[0]))
				imgName = "img/pan_" + "https_" + subdomain + "_" + str(port[0]) + ".png"
				driver.get_screenshot_as_file(r""+imgName)
				res = {
					'port' : port[0],
					'method' : 'https',
					'title' : port[1]['https']['title'],
					'headers' : port[1]['https']['headers'],
					'status_code' : port[1]['https']['status_code'],
					'imgName' : imgName
				}
				result['main'].append(res)
			except selenium.common.exceptions.TimeoutException:
				pass

	return result

def pan_write_html(result):
	head = '<!DOCTYPE html><html><head><title>Xiaopan233-scan</title><style type="text/css">.line{width: 100%;display: flex;flex-direction: row;flex-wrap: nowrap;justify-content: center;}div{padding: 20px 30px;}#shadow1{width:100%;height:100%;position:absolute;left:0;top:0;z-index:998;background-color:black;opacity:0.6;display: none;}#shadow2{width:100%;height:100%;position:absolute;left:0;top:0;z-index:999;display: flex;flex-direction: row;flex-wrap: nowrap;justify-content: center;display: none;}</style></head><body><div>'

	content = ''

	for res in result:
		subdomain = res['subdomain']
		for main in res['main']:
			content = content + '<div class="line">'

			content = content + '<div class="basic">'
			content = content + '<p>Subdomain: ' + subdomain + '</p>'
			content = content + '<p>Port: ' + str(main['port']) + '</p>'
			content = content + '<p>Method: ' + main['method'] + '</p>'
			content = content + '<p>Title: ' + main['title'] + '</p>'
			content = content + '<p>Status_code: ' + str(main['status_code']) + '</p>'
			content = content + '</div>'

			content = content + '<div class="header">'
			for h_key in main['headers']:
				content = content + '<p>' + h_key + ':' + main['headers'][h_key] + '</p>'
			content = content + '</div>'

			content = content + '<div class="img">'
			content = content + '<img src="' + main['imgName'] + '" width="300px" onclick="showPic(this)">'
			content = content + '</div>'

			content = content + '</div>'

	foot = '</div><div id="shadow1"></div><div id="shadow2" onclick="showShadow(this)"></div></body></html><script>function showPic(that){content = document.getElementById("shadow2")newImg = document.createElement("img")newImg.src = that.srcnewImg.style = "opacity:1;"content.appendChild(newImg)document.getElementById("shadow1").style.display = "block"document.getElementById("shadow2").style.display = "block"document.getElementById("shadow2").style = "display: flex;flex-direction: row;flex-wrap: nowrap;justify-content: center;"}function showShadow(that){document.getElementById("shadow1").style.display = "none"document.getElementById("shadow2").style.display = "none"}</script>'

	f = open("./xxx.html","w")
	f.write(head + content + foot)
	f.close()

subdomainsList = []
f = open(sys.argv[1])
f_csv = csv.reader(f)
for row in f_csv:
	if row[5] == "subdomain":
		continue
	else:
		subdomainsList.append(row[5])

result = []
driver = webdriver.Chrome()
driver.set_page_load_timeout(6)
for subdomain in subdomainsList:
	portOpen = pan_scan_port(subdomain)
	if portOpen['code'] == 1:
		uri = pan_uri_response(portOpen['subdomain'], portOpen['portList'])
		result.append(pan_screen_shot(driver, subdomain, uri))

pan_write_html(result)
driver.quit()

