from starkware.cairo.common.dict import dict_read, dict_write
from starkware.cairo.common.default_dict import default_dict_new
from starkware.cairo.common.dict_access import DictAccess

func main() {
    // =============================================================================
    // In reality, dictionary generation & write logic is done from hdp-cairo ( memorizer.cairo )
    alloc_locals;
    let (my_dict: DictAccess*) = default_dict_new(17);
    let key = 12;
    dict_write{dict_ptr=my_dict}(key=key, new_value=34);

    // =============================================================================

    // I need to get pointer of the dictionary via hint
    // Now it's bootloader part, which first we need to initiate syscall handler before going through cairo1
    // Somehow we need to get syscall handler which have custom `call_contract` syscall modification.
    local value_from_hint;
    %{
        from syscall.syscall_handler import SyscallHandler 
        syscall_handler = SyscallHandler(dict_manager=__dict_manager)
    %}
    // =============================================================================
    // This is kinda fixed defined interface of starknet syscall calling from cairo 1
    // And this line, we will get from compiled cairo1 program.
    %{ syscall_handler.syscall(dict_ptr=ids.my_dict, key=ids.key) %}
    // =============================================================================
    // This is actually should be part inside the syscall_handler, especially around `call_contract` syscall
    // So what we need to get is DictAccess* pointer that probably loaded into syscall_handler somehow by input parameters
    // And if we got the pointer, we can use it to read/write dictionary

    // This is just for double checking
    let (val1: felt) = dict_read{dict_ptr=my_dict}(key=key);

    return ();
}
