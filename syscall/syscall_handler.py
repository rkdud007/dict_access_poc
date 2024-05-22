import dataclasses
from enum import Enum, auto
from typing import Dict, List, Optional, cast
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
from starkware.starknet.core.os.segment_utils import get_syscall_structs

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
    

class CallType(Enum):
    Call = 0
    Delegate = auto()

class EntryPointType(Enum):
    EXTERNAL = 0
    L1_HANDLER = auto()
    CONSTRUCTOR = auto()

@dataclasses.dataclass(frozen=True)
class CallResult(ValidatedDataclass):
    """
    Contains the return values of a contract call.
    """

    gas_consumed: int
    # The result selector corresponds to the Rust panic result:
    #   0 if the syscall succeeded; a non-zero otherwise.
    failure_flag: int
    retdata: List[int]

    @classmethod
    def create(
        cls,
        initial_gas: int,
        updated_gas: MaybeRelocatable,
        failure_flag: MaybeRelocatable,
        retdata: List[MaybeRelocatable],
    ) -> "CallResult":
        stark_assert(
            all(isinstance(value, int) for value in retdata),
            code=StarknetErrorCode.INVALID_RETURN_DATA,
            message="Return data expected to be non-relocatable.",
        )
        stark_assert(
            failure_flag in (0, 1),
            code=StarknetErrorCode.INVALID_RETURN_DATA,
            message="failure_flag field expected to be either 0 or 1.",
        )
        updated_gas = cast(int, updated_gas)
        stark_assert(
            isinstance(updated_gas, int) and 0 <= updated_gas <= initial_gas,
            code=StarknetErrorCode.INVALID_RETURN_DATA,
            message=f"Unexpected remaining gas: {updated_gas}.",
        )

        return cls(
            gas_consumed=initial_gas - updated_gas,
            failure_flag=cast(int, failure_flag),
            retdata=cast(List[int], retdata),
        )

    @property
    def succeeded(self) -> bool:
        return self.failure_flag == 0

class SyscallHandle():
        def __init__(
            self,
            segments: OptionalSegmentManager,
            initial_syscall_ptr: Optional[RelocatableValue],
        ):
            # Static syscall information.
            self.structs = get_syscall_structs()
            self.selector_to_syscall_info = self.get_selector_to_syscall_info()

            # Memory segments of the running program.
            self._segments = segments
            # Current syscall pointer; updated internally during the call execution.
            self._syscall_ptr = initial_syscall_ptr

            # Mapping from ec_point* to pythonic EcPoint.
            self.ec_points: Dict[RelocatableValue, EcPoint] = {}
            # A segment that holds all the ec points.
            self.ec_points_segment: Optional[RelocatableValue] = None
            self.ec_point_size = cast(int, self.structs.EcPoint.size)

        def call_contract_helper(
        self, remaining_gas: int, request: CairoStructProxy, syscall_name: str
        ) -> CallResult:
            calldata = self._get_felt_range(
                start_addr=request.calldata_start, end_addr=request.calldata_end
            )
            class_hash: Optional[int] = None
            if syscall_name == "call_contract":
                contract_address = cast_to_int(request.contract_address)
                caller_address = self.entry_point.contract_address
                call_type = CallType.Call
                # if self._is_validate_execution_mode():
                #     stark_assert(
                #         self.entry_point.contract_address == contract_address,
                #         code=StarknetErrorCode.UNAUTHORIZED_ACTION_ON_VALIDATE,
                #         message=(
                #             f"Unauthorized syscall {syscall_name} "
                #             f"in execution mode {self.tx_execution_context.execution_mode.name}."
                #         ),
                #     )

            call = self.execute_entry_point_cls(
                call_type=call_type,
                contract_address=contract_address,
                entry_point_selector=cast_to_int(request.selector),
                entry_point_type=EntryPointType.EXTERNAL,
                calldata=calldata,
                caller_address=caller_address,
                initial_gas=remaining_gas,
                class_hash=class_hash,
                code_address=None,
            )

            return self.execute_entry_point(call=call)