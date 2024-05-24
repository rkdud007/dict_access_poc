from starkware.cairo.common.dict import dict_read, dict_write
from starkware.cairo.common.default_dict import default_dict_new
from starkware.cairo.common.dict_access import DictAccess
from starkware.cairo.common.registers import get_fp_and_pc

const CALL_CONTRACT_SELECTOR = 'CallContract';

// Describes the CallContract system call format.
struct CallContractRequest {
    // The system call selector
    // (= CALL_CONTRACT_SELECTOR, DELEGATE_CALL_SELECTOR or DELEGATE_L1_HANDLER_SELECTOR).
    selector: felt,
    // The address of the L2 contract to call.
    contract_address: felt,
    // The selector of the function to call.
    function_selector: felt,
    // The size of the calldata.
    calldata_size: felt,
    // The calldata.
    calldata: felt*,
}

struct CallContractResponse {
    retdata_size: felt,
    retdata: felt,
}

struct CallContract {
    request: CallContractRequest,
    response: CallContractResponse,
}

func call_contract{syscall_ptr: felt*}(
    contract_address: felt, function_selector: felt, calldata_size: felt, calldata: felt*
) -> (retdata_size: felt, retdata: felt) {
    let syscall = [cast(syscall_ptr, CallContract*)];
    assert syscall.request = CallContractRequest(
        selector=CALL_CONTRACT_SELECTOR,
        contract_address=contract_address,
        function_selector=function_selector,
        calldata_size=calldata_size,
        calldata=calldata,
    );
    %{ syscall_handler.syscall(syscall_ptr=ids.syscall_ptr) %}
    let response = syscall.response;

    let syscall_ptr = syscall_ptr + CallContract.SIZE;
    return (retdata_size=response.retdata_size, retdata=response.retdata);
}

func main() {
    alloc_locals;
    let (__fp__, _) = get_fp_and_pc();
    // =============================================================================
    // In reality, dictionary generation & write logic is done from hdp-cairo ( memorizer.cairo )

    let (my_dict: DictAccess*) = default_dict_new(17);
    let key = 12;
    dict_write{dict_ptr=my_dict}(key=key, new_value=34);

    // =============================================================================
    // I need to get pointer of the dictionary via hint
    // Now it's bootloader part, which first we need to initiate syscall handler before going through cairo1
    // Somehow we need to get syscall handler which have custom `call_contract` syscall modification.
    local syscall_ptr: felt*;
    %{ ids.syscall_ptr = segments.add() %}
    local value_from_hint;
    %{
        from syscall.syscall_handler import SyscallHandler 
        syscall_handler = SyscallHandler(segments=segments, dict_manager=__dict_manager, dict_ptr=ids.my_dict, initial_syscall_ptr=ids.syscall_ptr)
    %}

    // =============================================================================
    // SOMEHOW WE NEED TO MOCK THIS PART
    //  starknet::call_contract_syscall(
    //     contract_address_const::<0>(),
    //     123,
    //     array![].span()
    // )?;
    // %{ memory[ap + 0] = segments.add() %}

    local call_data: felt = 12;
    let (retdata_size, retdata) = call_contract{syscall_ptr=syscall_ptr}(
        contract_address=0, function_selector=123, calldata_size=1, calldata=&call_data
    );
    %{ print("Result: ", ids.retdata_size) %}
    %{ print("Result: ", ids.retdata) %}
    // let contract_address = 0;
    // let selector = 123;
    // let calldata = [12];

    // This is kinda fixed defined interface of starknet syscall calling from cairo 1
    // And this line, we will get from compiled cairo1 program.
    // %{ syscall_handler.syscall(syscall_ptr=14) %}
    // =============================================================================
    // This is actually should be part inside the syscall_handler, especially around `call_contract` syscall
    // So what we need to get is DictAccess* pointer that probably loaded into syscall_handler somehow by input parameters
    // And if we got the pointer, we can use it to read/write dictionary

    // This is just for double checking
    let (val1: felt) = dict_read{dict_ptr=my_dict}(key=key);

    return ();
}
