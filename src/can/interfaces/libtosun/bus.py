'''
Author: seven 865762826@qq.com
Date: 2023-06-11 14:14:06
LastEditors: notmmao@gmail.com
LastEditTime: 2024-12-10 11:46:49
'''
import logging
from typing import List, Optional, Tuple, Union, Deque, Any

import can
from can.typechecking import BitTimingFdDict, CanFilters
from can import (
    BitTiming,
    BitTimingFd,
    BusABC,
    Message,
    CanProtocol
)

from .TSMasterDevice import *


logger = logging.getLogger('can.interfaces.libtosun')


class libtosunBus(can.BusABC):
    def __init__(self, channel: Any = None, *, is_fd: bool, timing: Union[BitTiming, BitTimingFd], 
                 can_filters: Optional[CanFilters] = None, 
                 hwserial: bytes = b"", **kwargs: object):
        
        self.channel = channel
        is_fd = isinstance(timing, BitTimingFd) if timing else kwargs.get("fd", False)
        self._can_protocol = CanProtocol.CAN_FD if is_fd else CanProtocol.CAN_20

        configs = [{'is_fd': is_fd, 'FChannel': channel,}]

        if isinstance(timing, BitTimingFd):
            configs[0].update({'rate_baudrate':timing.nom_bitrate // 1000})
            configs[0].update({'data_baudrate':timing.data_bitrate // 1000})
        elif isinstance(timing, BitTiming):
            configs[0].update({'rate_baudrate':timing.bitrate // 1000})
            configs[0].update({'data_baudrate':2000})
        else:
            configs[0].update({'rate_baudrate':500})
            configs[0].update({'data_baudrate':2000})

        # filters = []
        # if can_filters:
        #     for f in can_filters:
        #         if f['can_mask'] == 0x7ff and f['extended'] == False:
        #             filters.append({'channel': 0, 'id': f['can_id'], 'is_std': True})
               
        # self.device = TSMasterDevice(configs=configs, hwserial=hwserial, is_include_tx=is_include_tx, dbc=dbc, filters=filters)
        self.device = TSMasterDevice(configs=configs, hwserial=hwserial, is_include_tx=False)
        super().__init__(channel, can_filters, **kwargs)


    def send(self, msg: can.Message, timeout: Optional[float] = 0.1) -> None:
        self.device.send_msg(msg, timeout)


    def _recv_internal(self, timeout: float = 0.1) -> Tuple[Optional[can.Message], bool]:
        '''
        return : [message, already_filter]
        '''
        is_fd = self._can_protocol is CanProtocol.CAN_FD
        msg = self.device.recv(channel = self.channel, timeout = timeout, is_fd = is_fd)

        return msg, False


    def shutdown(self) -> None:
        self.device.shut_down()
        super().shutdown()
