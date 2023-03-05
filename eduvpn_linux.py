#!/usr/bin/env python3

from datetime import datetime, timedelta
import os
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
import subprocess
import pyotp

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


if conn_time is not None and conn_time > (curr_time - timedelta(hours=18)):
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

		wait = WebDriverWait(driver, 30)

		login_btn = wait.until(EC.visibility_of_element_located((By.ID, 'submit_button')))
		username_field = driver.find_element_by_id('username')
		password_field = driver.find_element_by_id('password')

		# retrieve username from secret store
		netid = subprocess.check_output(['secret-tool', 'lookup', 'account', 'tudelft', 'type', 'username']).decode("utf-8") 

		assert len(netid) > 0
		
		# retrieve password and totp secret
		password = subprocess.check_output(['secret-tool', 'lookup', 'account', 'tudelft', 'type', 'password', 'username', netid]).decode("utf-8") 
		totp_secret = subprocess.check_output(['secret-tool', 'lookup', 'account', 'tudelft', 'type', 'totp', 'username', netid]).decode("utf-8") 

		assert len(password) > 0
		assert len(totp_secret) > 0

		username_field.send_keys(netid)
		password_field.send_keys(password)
		login_btn.click()

		# wait until the mfa page loads
		wait.until(EC.visibility_of_element_located((By.ID, 'submit-btn')))

		totp_token = pyotp.TOTP(totp_secret).now()

		for i in range(0, 6):
			token_field = driver.find_element_by_id(f"otp_{i}")
			token_field.send_keys(totp_token[i])
		
		# login_token_btn.click()
		# no need to click the login button as the page auto-redirects

		print('[*] Login completed as ' + netid)
		print('[*] Creating configuration...')
		# navigate to configurations page
		wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/nav/ul/li[2]/a'))).click()

		wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/main/details/summary')))
		try:
			# delete existing configuration if any are present
			driver.find_element_by_xpath('/html/body/main/table/tbody/tr/td[3]/form/button').click()
		except:
			pass
		# create and download new configuration
		wait.until(EC.visibility_of_element_located((By.XPATH, '/html/body/main/details/summary'))).click()
		driver.find_element_by_id('displayName').send_keys('a')
		driver.find_element_by_xpath('/html/body/main/details/form/fieldset[2]/button').click()
		print('[*] Configuration created, downloading...')
		time.sleep(1)
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
