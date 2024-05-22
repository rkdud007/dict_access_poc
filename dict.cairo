from starkware.cairo.common.dict import dict_read, dict_write
from starkware.cairo.common.default_dict import default_dict_new
from starkware.cairo.common.dict_access import DictAccess

func main() {
    let (my_dict: DictAccess*) = default_dict_new(17);
    let key = 12;
    dict_write{dict_ptr=my_dict}(key=key, new_value=34);
    // I need to get pointer of the dictionary via hint
    %{ a = ids.my_dict %}
    // let (val1: felt) = dict_read{dict_ptr=my_dict}(key=key);
    // assert val1 = 34;
    %{
        dict_tracker = __dict_manager.get_tracker(a)
        dict_tracker.current_ptr += 3
        value_from_hint = dict_tracker.data[ids.key]
        print(value_from_hint)
    %}

    return ();
}
