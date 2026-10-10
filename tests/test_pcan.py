# -*- coding: utf-8 -*-
'''
@ File         : test_pcan.py
@ Author       : x
@ Contact      : 
@ Date         : 2026-10-10 11:15:04
@ Description  : 
                 
'''

import sys
import can
import time

import threading

class Test_PcanBus:
    def test_txrx(self):
        timing = can.BitTiming.from_sample_point(8000000, 500_000, 87.5)
        can_filters = [can.typechecking.CanFilter(can_id=0x100, can_mask=0x7FF)]
        msg = can.Message(arbitration_id=0x110, is_extended_id=False, bitrate_switch=False, is_fd=False, dlc = 8, data = b'12345678')
        
        with can.Bus(interface='pcan', channel='PCAN_USBBUS1', can_filters=can_filters, timing=timing) as bus:
            def recv():
                while True:
                    msg = bus.recv()
                    print(msg)

            task = bus.send_periodic(msg, 0.01, None)
            task_ = threading.Thread(target=recv)
            task_.start()
            input()
            task.stop()