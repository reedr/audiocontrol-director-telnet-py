"""Classes for communicating with the AudioControl Director M6400/M6800"""

from __future__ import annotations

import typing
import logging
import telnetlib3


_LOGGER = logging.getLogger("audiocontrol_director_telnet")

class InputID:
    """Represents an input, which can be either an analog stereo input or a digital stereo input"""

    def __init__(self):
        self._pretty_name = ''
        self._status_name = ''
        self._protocol_name = ''
        self._is_analog = False

    @classmethod
    def create_analog(cls, index: int) -> InputID:
        instance = InputID()
        c2 = index*2
        c1 = c2-1
        instance._is_analog = True
        instance._pretty_name = f'Channel {c1}-{c2}'
        instance._status_name = f'MX{index} & {index}'
        instance._protocol_name = f'MX{index}'
        return instance
    
    @classmethod
    def create_digital(cls, index: int, num_analog: int) -> InputID:
        c = chr(ord('a') + index - 1)
        bigc = chr(ord('A') + index - 1)
        c1 = num_analog + index
        instance = InputID()
        instance._pretty_name = f'Digital In {bigc}'
        instance._status_name = f'MX{c1} & {c1}'
        instance._protocol_name = f'DX{c}' 
        return instance
    
    @classmethod
    def create_from_pretty_name(cls, name: int, num_analog: int) -> InputID:
        name_parts = name.split(' ')
        print(name_parts[0])
        if name_parts[0] == "Channel":
            channels = name_parts[1].split('-')
            return InputID.create_analog((int(channels[0]) // 2) + 1)
        elif name_parts[0] == "Digital":
            return InputID.create_digital(ord(name_parts[2]) - ord('A') + 1, num_analog)
        else:
            return False

    @classmethod
    def create_from_status_id(cls, status_name: str, num_analog: int) -> InputID:
        """Create instance from status ID string"""
        channels = status_name[2:]
        channel_parts = channels.split(' & ')
        index = int(channel_parts[0])
        if index <= num_analog:
            return InputID.create_analog(index)
        else:
            return InputID.create_digital(index - num_analog, num_analog)

    @property
    def name(self) -> str:
        """The friendly name of the input"""
        return self._pretty_name
    
    @property
    def status_name(self) -> str:
        return self._status_name

    @property
    def protocol_name(self) -> str:
        return self._protocol_name
    
    @property
    def is_analog(self) -> bool:
        return self._is_analog
    
    def __str__(self) -> str:
        return self.protocol_name
\
    def __add__(self, other: str) -> str:
        return str(self) + other

    def __radd__(self, other: str) -> str:
        return other + str(self)


class OutputID:
    """Represents an output, which can be either an analog stereo amplifier
        zone or a a digital stereo output"""

    def __init__(self):
        self._zone_id = 0
        self._group_id = 0
        self._digital_id = ""

    @classmethod
    def all(cls) -> typing.List[OutputID]:
        """Returns list of all output options"""
        return_list = []
        for i in range(1, 8):
            return_list.append(OutputID.create(i, 0, ""))
        return_list.append(OutputID.create(9, 0, "a"))
        return_list.append(OutputID.create(10, 0, "b"))
        return return_list

    @classmethod
    def create(cls, zone_id: int, group_id: int, digital_id: str) -> OutputID:
        """Analog stereo amplifier zone options are 1-8, inclusive"""
        instance = OutputID()
        instance._zone_id = zone_id
        instance._group_id = group_id
        instance._digital_id = digital_id
        return instance

    @classmethod
    def create_from_status_id(cls, status_id: str, group_id: str, name: str) -> OutputID:
        """Create instance from status ID string"""
        if name[0:10] == "Digital Out":
            digital_id = name[12].lower()
        else:
            digital_id = ""
        return OutputID().create(int(status_id), int(group_id), digital_id)

    @property
    def name(self) -> str:
        """The friendly name of the output"""
        if self._digital_id == "":
            return f'Zone {self._zone_id}'
        return f'Digital Out {self._digital_id.upper()}'

    def __str__(self) -> str:
        if self._digital_id == "":
            return f'Z{self._zone_id}'
        return f'DXO{self._digital_id}'

    def op_str(self) -> str:
        if self._group_id > 0:
            return f'GRP{self._group_id}'
        return str(self)

    def __add__(self, other: str) -> str:
        return str(self) + other

    def __radd__(self, other: str) -> str:
        return other + str(self)


class OutputStatus:
    """Represents the status of an analog zone or digital output"""

    def __init__(
        self,
        output_id: OutputID,
        name: str,
        input_id: InputID,
        is_on: bool,
        volume: int,
        is_signal_sense_on: bool,
        group_id: int
    ):
        self._output_id = output_id
        self._name = name
        self._input_id = input_id
        self._is_on = is_on
        self._volume = volume
        self._is_signal_sense_on = is_signal_sense_on
        self._group_id = group_id

    @property
    def output_id(self) -> OutputID:
        """Output ID"""
        return self._output_id

    @property
    def name(self) -> str:
        """Name"""
        return self._name

    @property
    def input_id(self) -> InputID:
        """Input ID"""
        return self._input_id

    @property
    def is_on(self) -> bool:
        """Power status (True for 'on', False for 'off')"""
        return self._is_on

    @property
    def volume(self) -> int:
        """Volume (0-100)"""
        return self._volume

    @property
    def is_signal_sense_on(self) -> bool:
        """Signal sense status (True for 'on', False for 'off')"""
        return self._is_signal_sense_on


class SystemStatus:
    """Represents the status of a Director and its outputs"""

    def __init__(
        self,
        name: str,
        outputs: typing.Dict[str, OutputStatus],
        inputs: typing.Dict[str, InputID],
        input_names: typing.List[str]
    ):
        self._name = name
        self._outputs = outputs
        self._inputs = inputs
        self._input_names = input_names

    @property
    def name(self) -> str:
        """Name"""
        return self._name

    @property
    def outputs(self) -> typing.Dict[str, OutputStatus]:
        """Output statuses by output ID strings"""
        return self._outputs
    
    @property
    def inputs(self) -> typing.Dict[str, InputID]:
        return self._inputs
    
    @property
    def input_names(self) -> typing.List[str]:
        return self._input_names


class TelnetClient:
    """Represents a client for communicating with the telnet server of an
        AudioControl Director M6400/M6800."""

    def __init__(self, host):
        self._reader = None
        self._writer = None
        self._host = host

    async def async_connect(self) -> None:
        """Connects to the telnet server."""
        self._reader, self._writer = await telnetlib3.open_connection(
            self._host,
            connect_minwait=0.0,
            connect_maxwait=0.0
        )

    def disconnect(self) -> None:
        """Disconnects from the telnet server."""
        self._writer.close()

    async def _async_send_command(
        self,
        command: str,
        min_line_count: int
    ) -> str:
        """Sends given command to the server. Automatically appends
            CR to the command string."""
        if command != "SYSTEMstat?" and command != "INPUT?":
            _LOGGER.debug(command)
        self._writer.write(command + '\r')
        await self._writer.drain()

        empty_bytes = ''
        result = ''
        line_count = 0
        while True:
            partial_result = await self._reader.read(4096)
            if partial_result == empty_bytes:
                break
            result += partial_result
            line_count += len(partial_result.split('\n')) - 1
            if line_count >= min_line_count:
                break
        return result

    @staticmethod
    def _interpret_result(
            command: str,
            response: str,
            expect_success_code: bool
    ) -> tuple[bool, str]:
        """Parses the response for errors or successes, with results."""
        succeeded = False

        response_parts = response.split('\r', 1)

        # response should start with echo of command; anything else is unexpected
        command_echo = response_parts[0]
        if command_echo != command:
            raise Exception(f'Received unexpected response; \
                first line was not echo of command; got: {command_echo}')

        # remainder of the response is the result of the command
        result = response_parts[1]
        if result == f'xx{command}xx\r':
            # this is a "bad command" response
            raise BadCommandError(
                f'Received "bad command" response: xx{command}xx')
        if result == f'01{command}\r':
            # this is a "success" response
            succeeded = True
        if expect_success_code:
            return succeeded, result
        return True, result

    async def async_map_input_to_output(
        self,
        input_id: InputID,
        output_id: OutputID
    ) -> None:
        """Maps an input (analog input/digital input) to an output (analog zone/digital output)"""
        output_arg = output_id.op_str()
        command = f'{output_arg}source{input_id}'
        await self._async_send_command(command, 1)

    async def async_set_output_power_state(self, output_id: OutputID, state: bool) -> None:
        """Sets an outputs power state to on (True) or off (False)"""
        state_string = 'on' if state else 'off'
        output_arg = output_id.op_str()
        command = f'{output_arg}{state_string}'
        await self._async_send_command(command, 1)

    async def async_set_output_volume(self, output_id: OutputID, volume: int) -> None:
        """Sets an outputs volume, range 0..100"""
        output_arg = str(output_id)
        command = f'{output_arg}setvol{str(volume)}'
        await self._async_send_command(command, 1)

    async def async_get_system_status_raw(self) -> str:
        """Returns full system status in raw form"""
        command = 'SYSTEMstat?'
        result = await self._async_send_command(command, 17)
        return self._interpret_result(command, result, False)[1]

    async def async_get_input_raw(self) -> str:
        """Returns full inputs in raw form"""
        command = 'INPUT?'
        result = await self._async_send_command(command, 8)
        return self._interpret_result(command, result, False)[1]

    async def async_get_system_status(self) -> SystemStatus:
        
        inputs = {}
        input_names = []
        raw_result = await self.async_get_input_raw()
        result_lines = raw_result.split('\r\n')

        num_analog = 0
        for result_line in result_lines:
            fields = result_line.split(': ')
            if len(fields) < 2:
                break

            name = fields[0]
            input_id = InputID.create_from_pretty_name(name, num_analog)
            if input_id != False:
                if input_id.is_analog:
                    num_analog += 1
                inputs[name] = input_id
                input_names.append(name)

        raw_result = await self.async_get_system_status_raw()
        result_lines = raw_result.split('\r\n')

        # ------------------------------
        # Response format is as follows:
        # ------------------------------
        # pylint: disable=trailing-whitespace
        # ------------------------------

        # AMPLIFIER NAME: Director Matrix 6800 #3
        # GLOBAL TEMP: 111 F & Normal
        # GLOBAL VOLTAGE: 126 & Normal
        # ZONE OUTPUT PROTECT:
        # GLOBAL PROTECTION: Normal
        # THERMAL PROTECTION: Normal
        # IP ADDRESS: 10.111.16.52
        # DATE 10/10/2022
        # TIME '17:30:08
        #
        # ZONES, #, POWER STATE, INPUT, VOLUME, BASS, TREBLE, EQ, GROUP, TEMP, SIG. SENSE
        # Zone 1, 1, on, MX1 & 1, 100, 0, 0, Acoustic and 0, 0, 111 F/Normal, off
        # Zone 2, 2, on, MX2 & 2, 100, 0, 0, Acoustic and 0, 0, 111 F/Normal, off
        # Zone 3, 3, on, MX3 & 3, 100, 0, 0, User 3 and 5, 0, 113 F/Normal, off
        # Zone 4, 4, on, MX4 & 4, 100, 0, 0, unsaved values and -1, 0, 113 F/Normal, off
        # Zone 5, 5, on, MX5 & 5, 100, 0, 0, User 3 and 5, 0, 113 F/Normal, off
        # Zone 6, 6, on, MX6 & 6, 100, 0, 0, User 3 and 5, 0, 113 F/Normal, off
        # Zone 7, 7, on, MX7 & 7, 100, 0, 0, Party and 2, 0, 109 F/Normal, off
        # Zone 8, 8, on, MX8 & 8, 100, 0, 0, Party and 2, 0, 109 F/Normal, off
        # Digital Out A, 9, on, MX10 & 10, 100, 0, 0, unsaved values and -1, 0, 0 F/Low, off
        # Digital Out B, 10, on, MX10 & 10, 100, 0, 0, unsaved values and -1, 0, 0 F/Low, off

        # ------------------------------
        # pylint: enable=trailing-whitespace
        # ------------------------------

        # get the line that represents the name of the device
        system_name_line = result_lines[0]
        system_name = system_name_line.split('AMPLIFIER NAME: ')[1]
        # system_is_on = system_power_line.

        # get the lines that represent the comma-separated data for each analog zone/digital output
        outputs = {}
        output_lines = result_lines[11:]
        for result_line in output_lines:
            fields = result_line.split(', ')
            if len(fields) < 11:
                break

            name = fields[0]

            output_id = OutputID.create_from_status_id(fields[1], fields[8], name)

            is_on = fields[2] == 'on'

            raw_input_id = fields[3]
            input_id = InputID.create_from_status_id(raw_input_id, num_analog)

            volume = int(fields[4])

            # bass = int(fields[5])
            # treble = int(fields[6])
            # eq = fields[7] # parse the "Acoustic and 0" format
            group_id = int(fields[8])
            # temperature = fields[9] # parse temp

            is_signal_sense_on = fields[10] == 'on'
            output = OutputStatus(
                output_id, name, input_id, is_on, volume, is_signal_sense_on, group_id)
            outputs[str(output_id)] = output

        return SystemStatus(system_name, outputs, inputs, input_names)


class BadCommandError(Exception):
    """Signifies that an unrecognized command was sent"""
