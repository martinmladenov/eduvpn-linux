#!/usr/bin/env python3

from datetime import datetime, timedelta
import os
from selenium import webdriver
import time
from getpass import getpass

# constants
netid = ''

time_format = '%Y%m%d_%H%M%S'
openvpn_connection_name = 'tudelft_%s'
openvpn_connection_time_format = openvpn_connection_name % time_format
openvpn_file_path = '/tmp/eduvpn_script'


curr_time = datetime.now()

# get available vpn connection
connection = os.popen('nmcli connection show | grep \'%s\' | awk \'{print $1}\'' % (openvpn_connection_name % '')).read().strip()

assert '\n' not in connection

# parse datetime of connection
if len(connection) > 0:
	conn_time = datetime.strptime(connection, openvpn_connection_time_format)
else:
	conn_time = None
	print('[*] No existing connection found')


if conn_time is not None and conn_time > (curr_time - timedelta(hours=24)):
	print(f'[*] Connecting to existing connection: {connection}')
	os.system(f'nmcli connection up {connection}')
else:
	if conn_time is not None:
		print(f'[*] Connection {connection} has expired, deleting...')
		os.system(f'nmcli connection delete {connection}')

	print('[*] Downloading new connection profile...')

	os.system(f'mkdir {openvpn_file_path}')
	profile = webdriver.FirefoxProfile()
	profile.set_preference("browser.download.folderList", 2)
	profile.set_preference("browser.download.manager.showWhenStarting", False)
	profile.set_preference("browser.download.dir", openvpn_file_path)
	profile.set_preference("browser.helperApps.neverAsk.saveToDisk", "application/x-gzip")	

	options = webdriver.firefox.options.Options()
	options.add_argument("--headless")

	driver = webdriver.Firefox(firefox_profile=profile, options=options)

	try:
		driver.get('https://tudelft.eduvpn.nl/portal/home')

		username_field = driver.find_element_by_id('username')
		password_field = driver.find_element_by_id('password')
		login_btn = driver.find_element_by_id('submit_button')
		if len(netid) > 0:
			print(f'Username: {netid}')
		else:
			netid = input('Username: ')
		username_field.send_keys(netid)
		# password = input('Password: ')
		password = getpass()
		password_field.send_keys(password)
		login_btn.click()

		token_field = driver.find_element_by_id('code_id')
		token = input('Token: ')
		token_field.send_keys(token)
		login_token_btn = driver.find_element_by_xpath('/html/body/div[1]/div[4]/div/div[3]/form/input[2]')
		login_token_btn.click()

		print('[*] Login completed')
		time.sleep(2)
		print('[*] Creating configuration...')
		# navigate to configurations page
		driver.find_element_by_xpath('/html/body/nav/ul/li[2]/a').click()
		# delete existing configuration
		driver.find_element_by_xpath('/html/body/main/table/tbody/tr/td[3]/form/button').click()
		# create and download new configuration
		driver.find_element_by_xpath('/html/body/main/details/summary').click()
		driver.find_element_by_id('displayName').send_keys('a')
		driver.find_element_by_xpath('/html/body/main/details/form/fieldset[2]/button').click()
		print('[*] Configuration created, downloading...')
		time.sleep(2)
		driver.quit()
	except:
		driver.quit()
		raise

	print('[*] Installing configuration...')
	conn_name = openvpn_connection_name % curr_time.strftime(time_format)
	full_path = f'{openvpn_file_path}/{conn_name}.ovpn'
	os.system(f'mv {openvpn_file_path}/*.ovpn {full_path}')

	os.system(f'nmcli connection import type openvpn file {full_path}')

	print('[*] Cleaning up...')
	os.system(f'rm {full_path} && rmdir {openvpn_file_path}')

	print('[*] Activating configuration...')
	os.system(f'nmcli connection up {conn_name}')

print('[*] Done!')
