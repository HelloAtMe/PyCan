# -*- coding: utf-8 -*-
"""
@ File         : zlg.py
@ Author       : wcy
@ Contact      :
@ Date         : 2025-11-13 14:27:24
@ Description  :

"""

from typing import Optional, Any, Tuple, Union
from ctypes import *
import time
import logging

from can.typechecking import CanFilters
from can import BitTiming, BitTimingFd, BusABC, Message, CanProtocol

from .zlgcan import *

logger = logging.getLogger("can.interfaces.zlgcan")


ZCAN_SUPPORT_DEVICES = {
    "ZCAN_USBCANFD_100U": ZCAN_USBCANFD_100U,
    "ZCAN_USBCANFD_200U": ZCAN_USBCANFD_200U,
    "ZCAN_USBCANFD_400U": ZCAN_USBCANFD_400U,
    "ZCAN_USBCANFD_800U": ZCAN_USBCANFD_800U,
    "ZCAN_USBCANFD_MINI": ZCAN_USBCANFD_MINI,
    'ZCAN_USBCAN1':ZCAN_USBCAN1,

}


class ZCANBus(BusABC):
    def __init__(
        self,
        channel: int,
        device: str,
        timing: Optional[Union[BitTiming, BitTimingFd]] = None,
        can_filters: Optional[CanFilters] = None,
        **kwargs: object,
    ):
        try:
            self.m_objZCANLib = ZCAN()
        except OSError:
            raise OSError(f"zlgcan.dll not found in this PC.")

        # check channel is support
        if zcan_device := ZCAN_SUPPORT_DEVICES.get(device, None) is None:
            logger.error(f'ZCAN "{device}" not recognized.')
            raise SystemError(f'ZCAN "{device}" not recognized.')

        self.m_ChnIndex = channel

        self.m_ZcanHandle = self.m_objZCANLib.OpenDevice(
            zcan_device, self.m_ChnIndex, 0
        )
        if self.m_ZcanHandle == INVALID_DEVICE_HANDLE:
            logger.error("Open ZcanBus Failed.")
            raise SystemError("Open ZcanBus Failed.")

        is_fd = isinstance(timing, BitTimingFd) if timing else kwargs.get("fd", False)
        self._can_protocol = CanProtocol.CAN_FD if is_fd else CanProtocol.CAN_20

        if isinstance(timing, BitTiming):
            # timing.sample_point
            bitrate = timing.bitrate
            ret = self.m_objZCANLib.ZCAN_SetValue(
                self.m_ZcanHandle,
                f"{self.m_ChnIndex}/canfd_abit_baud_rate",
                f"{bitrate}".encode("utf8"),
            )
            if ret != ZCAN_STATUS_OK:
                raise SystemError("set buadrate failed.")

            bitrate = 2000_000
            ret = self.m_objZCANLib.ZCAN_SetValue(
                self.m_ZcanHandle,
                f"{self.m_ChnIndex}/canfd_dbit_baud_rate",
                f"{bitrate}".encode("utf8"),
            )
            if ret != ZCAN_STATUS_OK:
                raise SystemError("set data buadrate failed.")

        elif isinstance(timing, BitTimingFd):
            # timing.nom_sample_point
            # timing.data_sample_point

            bitrate = timing.nom_bitrate
            ret = self.m_objZCANLib.ZCAN_SetValue(
                self.m_ZcanHandle,
                f"{self.m_ChnIndex}/canfd_abit_baud_rate",
                f"{bitrate}".encode("utf8"),
            )
            if ret != ZCAN_STATUS_OK:
                raise SystemError("set buadrate failed.")

            bitrate = timing.data_bitrate
            ret = self.m_objZCANLib.ZCAN_SetValue(
                self.m_ZcanHandle,
                f"{self.m_ChnIndex}/canfd_dbit_baud_rate",
                f"{bitrate}".encode("utf8"),
            )
            if ret != ZCAN_STATUS_OK:
                raise SystemError("set data buadrate failed.")

            # ret = self.m_objZCANLib.ZCAN_SetValue(self.m_ZcanHandle, str(self.m_ChnIndex) + "/baud_rate_custom", "500Kbps(80%),2.0Mbps(80%),(80,07C00002,01C00002)".encode("utf-8"))
            # if ret != ZCAN_STATUS_OK:
            #     print("Set CH%d baud failed!" % self.m_ChnIndex)
            #     return None
        else:
            pass

        ret = self.m_objZCANLib.ZCAN_SetValue(
            self.m_ZcanHandle,
            str(self.m_ChnIndex) + "/initenal_resistance",
            "1".encode("utf-8"),
        )
        if ret != ZCAN_STATUS_OK:
            logger.error("Open Zcan resistance failed!" % self.m_ChnIndex)
            raise SystemError("Open Zcan resistance failed!")

        chn_init_cfg = ZCAN_CHANNEL_INIT_CONFIG()
        chn_init_cfg.can_type = ZCAN_TYPE_CANFD
        chn_init_cfg.config.canfd.mode = 0  # 0 Normal Mode 1 Leisen Only

        self.m_ChnHandle = self.m_objZCANLib.InitCAN(
            self.m_ZcanHandle, self.m_ChnIndex, chn_init_cfg
        )
        if self.m_ChnHandle is None:
            logger.error("Initialize Zcan failed.")
            raise SystemError("Initialize Zcan failed.")
        time.sleep(0.1)

        super().__init__(channel, can_filters)

        ret = self.m_objZCANLib.ZCAN_SetValue(
            self.m_ZcanHandle, f"{self.m_ChnIndex}/set_device_recv_merge", repr(1)
        )  # default enable the merge
        if ret != ZCAN_STATUS_OK:
            logger.error("Set Zcan recv mode as merge failed.")
            raise SystemError("Set Zcan recv mode as merge failed.")

        time.sleep(0.1)

        ret = self.m_objZCANLib.StartCAN(self.m_ChnHandle)
        if ret != ZCAN_STATUS_OK:
            logger.error("Start Zcan bus failed.")
            raise SystemError("Start Zcan bus failed.")

        time.sleep(0.5)

    def send(self, msg: Message, timeout: Optional[float] = None) -> None:

        zdataObj = ZCANDataObj()
        memset(addressof(zdataObj), 0, sizeof(zdataObj))

        zdataObj.dataType = ZCAN_DT_ZCAN_CAN_CANFD_DATA  # can/canfd frame
        zdataObj.chnl = 0  # can_channel
        zdataObj.zcanfddata.flag.frameType = 1 if msg.is_fd else 0  # 0-can,1-canfd
        zdataObj.zcanfddata.flag.txDelay = 0  # 不添加延迟
        zdataObj.zcanfddata.flag.transmitType = 0  # 发送方式，0-正常发送，2-自发自收
        zdataObj.zcanfddata.flag.txEchoRequest = 0  # 发送回显请求，0-不回显，1-回显
        zdataObj.zcanfddata.frame.len = msg.dlc

        zdataObj.zcanfddata.frame.flags |= (1 << 0) if msg.bitrate_switch else 0
        zdataObj.zcanfddata.frame.can_id = msg.arbitration_id
        zdataObj.zcanfddata.frame.can_id |= (1 << 31) if msg.is_extended_id else 0
        zdataObj.zcanfddata.frame.can_id |= (1 << 30) if msg.is_remote_frame else 0
        zdataObj.zcanfddata.frame.can_id |= (1 << 29) if msg.is_error_frame else 0

        for j in range(zdataObj.zcanfddata.frame.len):
            zdataObj.zcanfddata.frame.data[j] = msg.data[j]

        ret = self.m_objZCANLib.TransmitData(self.m_ZcanHandle, zdataObj, 1)
        if ret != ZCAN_STATUS_OK:
            logger.error("Send failed.")

        # if self._can_protocol is CanProtocol.CAN_20:
        #     pass
        # else:
        #     pass

    def _recv_internal(
        self, timeout: Optional[float]
    ) -> tuple[Optional[Message], bool]:
        end_time = time.time() + timeout if timeout is not None else None

        while True:
            rcv_merge_num = self.m_objZCANLib.GetReceiveNum(
                self.m_ZcanHandle, ZCAN_TYPE_MERGE
            )

            if rcv_merge_num > 0:
                break
            else:
                if end_time is None:
                    time_left: Optional[float] = None
                    timed_out = False
                else:
                    time_left = max(0.0, end_time - time.time())
                    timed_out = time_left == 0.0

                if timed_out:
                    return None, False

        rcv_merge_msgs, rcv_merge_num = self.m_objZCANLib.ReceiveData(
            self.m_ChnHandle, 1, 0
        )

        if rcv_merge_num >= 1:
            msg = rcv_merge_msgs[0]
            if msg.dataType == ZCAN_DT_ZCAN_CAN_CANFD_DATA:

                timestamp = msg.zcanfddata.timestamp / (1000.0 * 1000.0)
                arbitration_id = msg.zcanfddata.frame.can_id & 0x1FFFFFFF
                is_extended_id = (msg.zcanfddata.frame.can_id & (1 << 31)) > 0
                is_remote_frame = (msg.zcanfddata.frame.can_id & (1 << 30)) > 0
                is_error_frame = (msg.zcanfddata.frame.can_id & (1 << 29)) > 0
                is_fd = msg.zcanfddata.flag.frameType == 1
                is_rx = True
                bitrate_switch = (msg.zcanfddata.frame.flags & 1) > 0
                error_state_indicator = False
                dlc = msg.zcanfddata.frame.len
                data = bytes(msg.zcanfddata.frame.data)

                rx_msg = Message(
                    channel=self.channel_info,
                    timestamp=timestamp,
                    arbitration_id=arbitration_id,
                    is_extended_id=is_extended_id,
                    is_remote_frame=is_remote_frame,
                    is_error_frame=is_error_frame,
                    dlc=dlc,
                    data=data,
                    is_fd=is_fd,
                    is_rx=is_rx,
                    bitrate_switch=bitrate_switch,
                    error_state_indicator=error_state_indicator,
                )

                return rx_msg, False
        return None, False

    # def _apply_filters(self, _filters: Optional[CanFilters]) -> None:
    #     filters = None

    #     if _filters is not None:
    #         filters = []
    #         for f in _filters:
    #             if f['can_mask'] == 0x7FF and f['extended'] == False:
    #                 filters.append((0, f['can_id'], f['can_id']))

    #     if filters:
    #         ret = self.m_objZCANLib.ZCAN_SetValue(self.m_ZcanHandle, str(self.m_ChnIndex) + "/filter_clear", "0".encode("utf-8")) # 清除滤波
    #         if ret != ZCAN_STATUS_OK:
    #             logger.error("Set CH%d  filter_clear failed!" % self.m_ChnIndex)
    #             return None

    #         for _f in filters:
    #             # 流程为：for【set_mode(与前一组滤波同类型可以省略) + set_start + set_end】+ ack
    #             # 这里设置第一道滤波：标准帧0~0x7F，第二道滤波：标准帧0xFF~0x1FF，第三道滤波：扩展帧0xFF~0x2FF
    #             _mode = f'{_f[0]}'
    #             ret = self.m_objZCANLib.ZCAN_SetValue(self.m_ZcanHandle, str(self.m_ChnIndex) + "/filter_mode", _mode.encode("utf-8"))  # 设置滤波模式 标准帧滤波
    #             if ret != ZCAN_STATUS_OK:
    #                 logger.error("Set CH%d  filter_mode failed!" % self.m_ChnIndex)
    #                 return None

    #             _start = f'0x{_f[1]:x}'
    #             ret = self.m_objZCANLib.ZCAN_SetValue(self.m_ZcanHandle, str(self.m_ChnIndex) + "/filter_start", _start.encode("utf-8")) # 设置白名单范围 起始ID
    #             # ret = self.m_objZCANLib.ZCAN_SetValue(self.m_ZcanHandle, str(self.m_ChnIndex) + "/filter_start", f"0x{_f['start']:x}".encode("utf-8")) # 设置白名单范围 起始ID
    #             if ret != ZCAN_STATUS_OK:
    #                 logger.error("Set CH%d  filter_start failed!" % self.m_ChnIndex)
    #                 return None

    #             _end = f'0x{_f[2]:x}'
    #             ret = self.m_objZCANLib.ZCAN_SetValue(self.m_ZcanHandle, str(self.m_ChnIndex) + "/filter_end", _end.encode("utf-8"))   # 设置白名单范围 结束ID
    #             # ret = self.m_objZCANLib.ZCAN_SetValue(self.m_ZcanHandle, str(self.m_ChnIndex) + "/filter_end", f"0x{_f['end']:x}".encode("utf-8"))   # 设置白名单范围 结束ID
    #             if ret != ZCAN_STATUS_OK:
    #                 logger.error("Set CH%d  filter_end failed!" % self.m_ChnIndex)
    #                 return None

    #         ret = self.m_objZCANLib.ZCAN_SetValue(self.m_ZcanHandle, str(self.m_ChnIndex) + "/filter_ack", "0".encode("utf-8"))  # 使能滤波
    #         if ret != ZCAN_STATUS_OK:
    #             logger.error("Set CH%d  filter_ack failed!" % self.m_ChnIndex)
    #             return None

    #         super()._apply_filters(_filters)

    def shutdown(self):
        self.m_objZCANLib.ResetCAN(self.m_ChnHandle)
        self.m_objZCANLib.CloseDevice(self.m_ZcanHandle)
        super().shutdown()

    @staticmethod
    def _detect_available_configs():
        interfaces = []
        try:
            library_handle = ZCAN()
        except OSError:
            return interfaces

        for device_name, device_object in ZCAN_SUPPORT_DEVICES.items():
            for i in range(5):
                if (device_handle := library_handle.OpenDevice(device_object, i, 0)) != INVALID_DEVICE_HANDLE:
                    if ZCAN_STATUS_ONLINE == library_handle.DeviceOnLine(device_handle):
                        interfaces.append(
                            {"interface": "zlgcan", "device": device_name, "channel": i}
                        )
                library_handle.CloseDevice(device_handle)

        return interfaces
