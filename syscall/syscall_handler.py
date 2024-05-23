import dataclasses
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Tuple, cast
from starkware.starknet.core.os.syscall_handler import SyscallHandlerBase
from starkware.starknet.core.os.syscall_utils import cast_to_int
from starkware.cairo.common.structs import CairoStructProxy
from starkware.starknet.definitions.error_codes import StarknetErrorCode
from starkware.cairo.lang.vm.relocatable import MaybeRelocatable
from starkware.starkware_utils.error_handling import stark_assert
from starkware.starkware_utils.validated_dataclass import ValidatedDataclass
from starkware.starknet.core.os.os_logger import OptionalSegmentManager
from starkware.cairo.lang.vm.memory_segments import MemorySegmentManager
from starkware.cairo.lang.vm.relocatable import RelocatableValue
from starkware.starknet.core.os.syscall_utils import get_syscall_structs, load_program

class OptionalSegmentManager:
    def __init__(self, segments: Optional[MemorySegmentManager]):
        self._segments = segments

    def set_segments(self, segments: MemorySegmentManager):
        assert self._segments is None, "segments is already set."
        self._segments = segments

    @property
    def segments(self) -> MemorySegmentManager:
        assert self._segments is not None, "segments must be set before using the SyscallHandler."
        return self._segments
    
SyscallFullResponse = Tuple[tuple, tuple]
ExecuteSyscallCallback = Callable[
    ["SyscallHandlerBase", int, CairoStructProxy], SyscallFullResponse
]

@dataclasses.dataclass(frozen=True)
class SyscallInfo:
    name: str
    execute_callback: ExecuteSyscallCallback
    request_struct: CairoStructProxy    

class CallType(Enum):
    Call = 0
    Delegate = auto()

class EntryPointType(Enum):
    EXTERNAL = 0
    L1_HANDLER = auto()
    CONSTRUCTOR = auto()

class SyscallHandler():
    def __init__(
        self,
    ):
        # Static syscall information.
        self.structs = get_syscall_structs()

    
    def syscall(self, syscall_ptr: RelocatableValue):
        """
        Executes the selected system call.
        """
        print("syscall_ptr", syscall_ptr)
