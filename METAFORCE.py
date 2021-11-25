#!/usr/bin/env python2

import os
import sys
import time
import logging
import argparse
import itertools
import subprocess
from time import sleep
import queue
from threading import Thread
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


# Constants for this specific project
CONST_MAX_WORDS = 12
CONST_PASSWORD = "P@55word!"


class METAFORCE(object):

    def __init__(self, wordlist, knownlist):
        self.guesses = queue.Queue(maxsize=0)
        self.wordlist = wordlist
        self.knownlist = self._string_to_list(knownlist)
        self.chrome_driver = None
        self.chrome_option = None
        self.chrome_binary = None
        self.logger = None

        self._logger_init()
        self._generate_wordlist(self.wordlist, self.knownlist)

    def _logger_init(self, filename='debug.log'):
        self.logger = logging.getLogger('unMetamask')
        log_handler = logging.FileHandler(filename)
        log_handler.setFormatter(logging.Formatter('%(name)s %(levelname)s - %(message)s'))
        self.logger.addHandler(log_handler)
        self.logger.setLevel(logging.DEBUG)

    def _chrome_init(self):
        self.chrome_binary = "/usr/bin/chromedriver"
        self.chrome_option = webdriver.ChromeOptions()
        self.chrome_option.add_extension("nkbihfbeogaeaoehlefnkodbefgpgknn.crx")
        self.chrome_driver = webdriver.Chrome(
            executable_path=self.chrome_binary,
            chrome_options=self.chrome_option,
        )

    def _check_exists_by_xpath(self, xpath):
        try:
            self.chrome_driver.find_element_by_xpath(xpath)
        except NoSuchElementException:
            return False
        return True

    def _get_number_needed(self, knownlist):
        return (CONST_MAX_WORDS - len(knownlist))

    def _string_to_list(self, string):
        stub_list = string.split(",")
        return [x.strip(' ') for x in stub_list]

    def _list_to_string(self, list):
        return (' '.join(list))

    def _clear_field(self, element):
        length = len(element.get_attribute('value'))
        if length != 0:
            element.send_keys(length * Keys.BACKSPACE)

    def _generate_wordlist(self, wordlist, knownlist):
        stub = None
        self.logger.info("Attempting to parse provided wordlist")
        if os.path.isfile(wordlist):
            with open(wordlist) as f:
                stub = f.read().splitlines()
            self.logger.info("Building master wordlist...")
            for x in list(itertools.combinations(stub, self._get_number_needed(self.knownlist))):
                self.guesses.put(self.knownlist + list(x))
            self._is_list_created = True
            self.logger.info("Master wordlist completed!")


    def start(self):

        self._chrome_init()

        try:
            while True:
                self.chrome_driver.get("chrome-extension://nkbihfbeogaeaoehlefnkodbefgpgknn/home.html")
                self.chrome_driver.implicitly_wait(20)

                self.chrome_driver.find_element_by_css_selector('button.button').click()
                self.chrome_driver.implicitly_wait(2)

                self.chrome_driver.find_element_by_xpath("//*[contains(text(), 'Import wallet')]").click()
                self.chrome_driver.implicitly_wait(2)

                self.chrome_driver.find_element_by_css_selector('button.btn-primary').click()
                self.chrome_driver.implicitly_wait(3)

                textarea = self.chrome_driver.find_element_by_css_selector("div.first-time-flow__seedphrase input")
                password1 = self.chrome_driver.find_element_by_id("password")
                password2 = self.chrome_driver.find_element_by_id("confirm-password")
                clicked = False

                #WALLET RECOVERY
                while not self.guesses.empty():
                    stub_guess = self.guesses.get()
                    self.chrome_driver.implicitly_wait(3)

                    try:
                        print(self.chrome_driver.find_element_by_xpath("//*[contains(text(), 'All done')]"))
                        return
                    except Exception as e:
                        print('All done not found')


                    self._clear_field(textarea)
                    self._clear_field(password1)
                    self._clear_field(password2)

                    textarea.send_keys(' '.join(stub_guess))
                    password1.send_keys(CONST_PASSWORD)
                    password2.send_keys(CONST_PASSWORD)

                    if (clicked == False):
                        self.chrome_driver.execute_script("document.getElementsByClassName('first-time-flow__checkbox')[0].click()");
                        self.chrome_driver.execute_script("document.getElementsByClassName('first-time-flow__checkbox')[1].click()");
                        clicked = True

                    try:
                        self.chrome_driver.find_element_by_css_selector('button.button').click()
                        self.chrome_driver.implicitly_wait(3)
                    except Exception as e:
                        print(e)
                        print('cant validate')

                    self.guesses.task_done()


        except KeyboardInterrupt:
            print "Exiting by User Interrupt"
            self.chrome_driver.quit()



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--wordlist', required=True, action='store', dest='wordlist', default='')
    parser.add_argument('-k', '--knownlist', required=True, action='store', dest='knownlist', default='')
    parser.add_argument('-t', '--threads', action='store', dest='threads', default='3')

    try:
        args = parser.parse_args()
    except TypeError:
        print("The options you provided were not supplied correctly. Please take another look at the examples.")
        sys.exit(1)

    test_obj = METAFORCE(args.wordlist, args.knownlist)

    test_obj.start()
