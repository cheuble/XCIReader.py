#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os
import urllib
import struct
from zlib import crc32
from lxml import etree

def printHelp():
	print("Usage: " + sys.argv[0] + " [options]")
	print("Options:")
	print("-h | --help            Print this help")
	print("-f | --file            Path to XCI rom")
	print("-u | --update          Updates the XML DB")
	print("--dump-cert            Dumps the cert to the location specified")
	print("--inject-cert          Injects the cert from the location specified")
	
def updateXMLDB():
	print("Updating DB from nswdb.com...")
	urllib.urlretrieve("http://nswdb.com/xml.php", "DB.xml")

def getDataFromXCI(path):
	crc32Value = 0
	sha256HFS0 = ""
	sha256crypto = ""
	with open(path, "r+b") as XCIFile:
		XCIFile.seek(0x10D)
		cartridgeSize = XCIFile.read(1)
		if cartridgeSize == '\xf8':
			size = "2GB"
		elif cartridgeSize == '\xf0':
			size = "4GB"
		elif cartridgeSize == '\xe0':
			size = "8GB"
		elif cartridgeSize == '\xe1':
			size = "16GB"
		else:
			size = "Unknown"
		XCIFile.seek(0x140)
		buffer = XCIFile.read(0x20)
		sha256HFS0 = "".join( [ "%02X" % ord( x ) for x in buffer ] ).strip()
		buffer = XCIFile.read(0x20)
		sha256crypto = "".join( [ "%02X" % ord( x ) for x in buffer ] ).strip()
		XCIFile.seek(0)
		buffer = XCIFile.read(0x10000)
		while len(buffer) > 0: #Calculate the crc32 of the whole file
			crc32Value = crc32(buffer, crc32Value)
			buffer = XCIFile.read(0x10000)
		if "--dump-cert" in sys.argv:
			if sys.argv.index("--dump-cert") == len(sys.argv) - 1:
				print("Error! No path for the cert file provided!")
			else:
				print("Dumping cert...")
				XCIFile.seek(0x7000)
				buffer = XCIFile.read(0x200)
				with open(sys.argv[sys.argv.index("--dump-cert")+1], "wb") as certFile:
					certFile.write(buffer)
		if "--inject-cert" in sys.argv:
			if sys.argv.index("--inject-cert") == len(sys.argv) - 1:
				print("Error! No path for the cert file provided!")
			else:
				print("Injecting cert...")
				with open(sys.argv[sys.argv.index("--inject-cert")+1], "rb") as certFile:
					buffer = certFile.read(0x200)
					XCIFile.seek(0x7000)
					XCIFile.write(buffer)
					
	crc32Value = crc32Value & 0xFFFFFFFF
	tree = etree.parse("DB.xml")
	for imgcrc in tree.xpath("/releases/release/imgcrc"):
		if imgcrc.text == str("%08X" % crc32Value):
			print("Game Name: " + imgcrc.getparent().find("name").text)
			print("Publisher: " + imgcrc.getparent().find("publisher").text)
			region = imgcrc.getparent().find("region").text
			if region == "WLD":
				print("Region: ALL")
			else:
				print("Region: " + region)
			print("Title ID: " + imgcrc.getparent().find("titleid").text)
			print("Serial: " + imgcrc.getparent().find("serial").text)
			firmware = imgcrc.getparent().find("firmware").text
			if firmware == "None":
				print("Firmware Version: Unknown")
			else:
				print("Firmware Version: " + firmware)
	print("Cartridge Size: " + size)
	print("CRC32: " + "%08X" % crc32Value)
	print("SHA256 of the HFS0 Header: " + sha256HFS0)
	print("SHA256 of the crypto Header: " + sha256crypto)
	
if not os.path.isfile("DB.xml"):
	updateXMLDB()


if len(sys.argv) < 2:
	printHelp()
else:
	for i in range(0, len(sys.argv)):
		if sys.argv[i] == "-h" or sys.argv[i] == "--help":
			printHelp()
			break
		elif sys.argv[i] == "-u" or sys.argv[i] == "--update":
			updateXMLDB()
		elif sys.argv[i] == "-f" or sys.argv[i] == "--file":
			if i == len(sys.argv) - 1:
				printHelp()
				break
			else:
				getDataFromXCI(sys.argv[i+1])