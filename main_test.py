# -*- coding: utf-8 -*- 
""" 
@ File         : main_test.py 
@ Author       : Jackie 
@ Contact      : 
@ Date         : 2026-10-05 00:33:21 
@ Description  : the test entry 
""" 
 
import sys
import unittest 
import logging 
 
# from tests.test_app import TestApp 
from tests.test_pcan import Test_PcanBus
 
def main(): 
    logger = logging.getLogger() 
    logger.setLevel(logging.INFO) 
    handler = logging.StreamHandler(stream=sys.stdout) 
    handler.setLevel(logging.INFO) 
    formater = logging.Formatter(fmt='%(asctime)s.%(msecs)d [%(name)s]: %(message)s', 
                                 datefmt='%Y-%m-%d %H:%M:%S') 
    handler.setFormatter(formater) 
    logger.addHandler(handler) 
 
    # suite = unittest.TestSuite() 
    # loader = unittest.TestLoader() 
    # runner = unittest.TextTestRunner() 
 
    # suite.addTest(loader.loadTestsFromTestCase(TestApp)) 
 
    # runner.run(suite) 

    Test_PcanBus().test_txrx()
 
if __name__ == '__main__': 
    main() 
 
 
