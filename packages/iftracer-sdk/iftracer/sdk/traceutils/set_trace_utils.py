
from opentelemetry.trace.span import Span
from opentelemetry.semconv.ai import SpanAttributes
from typing import Dict, Any

from collections.abc import Iterable
MAX_DEPTH = 4
# _add_model_traces_to_spans
INSIGHTFINDER_ENTITY_PROMPT_TOKEN = ['prompt_tokens','prompt_eval_count']
INSIGHTFINDER_ENTITY_EVAL_TOKEN = ['eval_tokens', 'eval_count']
INSIGHTFINDER_ENTITY_COMPLETION_TOKEN = ['completion_tokens','completion_count']
INSIGHTFINDER_ENTITY_TOTAL_TOKEN = ['total_tokens','total_count']
INSIGHTFINDER_ENTITY_ERROR_MESSAGES = ['error_messages','error_message']
INSIGHTFINDER_ENTITY_TOTAL_DURATION = ['total_duration']
INSIGHTFINDER_ENTITY_LOAD_DURATION = ['load_duration']
INSIGHTFINDER_ENTITY_EVAL_DURATION = ['eval_duration']
INSIGHTFINDER_ENTITY_LLM_MODEL_NAME = ['llm_model','model','model_name']

# _add_result_traces_to_spans
INSIGHTFINDER_ENTITY_ERROR_MESSAGES = ['error_messages','error_message']
INSIGHTFINDER_ENTITY_VECTOR_STORE = ['vectorstore']
INSIGHTFINDER_ENTITY_DOCS_USED = ['docs_used']
INSIGHTFINDER_ENTITY_REDIS_URL = ['redis_url','redis']
INSIGHTFINDER_ENTITY_RAG_CONFIG = ['rag_config']
'''
Add tags and its value to spans. 
This method only adds tags to the span with entity name 'trace_model_response'
This is only limited to single input. For example, if input contains 2 different prompt token, this will give you only the 1st prompt token
'''
def _add_model_traces_to_spans(span: Span, res: Dict[str, Any] , *args, **kwargs) -> None:

    keys_list = INSIGHTFINDER_ENTITY_PROMPT_TOKEN + INSIGHTFINDER_ENTITY_EVAL_TOKEN + INSIGHTFINDER_ENTITY_COMPLETION_TOKEN +\
    INSIGHTFINDER_ENTITY_TOTAL_TOKEN + INSIGHTFINDER_ENTITY_ERROR_MESSAGES + INSIGHTFINDER_ENTITY_TOTAL_DURATION + INSIGHTFINDER_ENTITY_LOAD_DURATION +\
    INSIGHTFINDER_ENTITY_EVAL_DURATION + INSIGHTFINDER_ENTITY_LLM_MODEL_NAME
    keys_dict = {key: None for key in keys_list}
    _set_res_dict_values(args, keys_dict, keys_list)
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_PROMPT_TOKEN, _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_PROMPT_TOKEN))
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_EVAL_TOKEN,  _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_EVAL_TOKEN))
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_COMPLETION_TOKEN,  _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_COMPLETION_TOKEN))
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_TOTAL_TOKEN,  _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_TOTAL_TOKEN))
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_ERROR_MESSAGES, _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_ERROR_MESSAGES))
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_TOTAL_DURATION,  _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_TOTAL_DURATION))
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_LOAD_DURATION,  _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_LOAD_DURATION))
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_EVAL_DURATION,  _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_EVAL_DURATION))
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_LLM_MODEL_NAME, _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_LLM_MODEL_NAME))

'''
Add tags and its value to spans. 
This method adds tags to spans other than 'trace_model_response'
This method is to get rag_config, gpvector, or other values to tags.
'''
def _add_result_traces_to_spans(span: Span, res: Dict[str, Any] , *args, **kwargs) -> None:
    keys_list = INSIGHTFINDER_ENTITY_ERROR_MESSAGES + INSIGHTFINDER_ENTITY_VECTOR_STORE + INSIGHTFINDER_ENTITY_DOCS_USED + INSIGHTFINDER_ENTITY_REDIS_URL +\
    INSIGHTFINDER_ENTITY_RAG_CONFIG
    keys_dict = {key: None for key in keys_list}
    _set_res_dict_values(args, keys_dict, keys_list)
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_ERROR_MESSAGES,  _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_ERROR_MESSAGES))
    vectorstore =  _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_VECTOR_STORE)
    if vectorstore is not None and vectorstore.embedding_function is not None:
        span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_EMBEDDING_MODEL_NAME, vectorstore.embedding_function.model_name )
    if vectorstore is not None:    
        span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_VECTOR_STORE_COLLECTION_NAME, vectorstore.collection_name )
        span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_VECTOR_STORE_COLLECTION_METADATA, vectorstore.collection_metadata)
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_DOCS_USED,  _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_DOCS_USED))
    span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_REDIS_URL, _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_REDIS_URL))

    rag_config = _find_value_from_keys_list(keys_dict, INSIGHTFINDER_ENTITY_RAG_CONFIG)
    if rag_config is not None:
        span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_RAG_CONFIG_COMPANY, rag_config.company )
        span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_RAG_CONFIG_DATASET, rag_config.dataset )
        span.set_attribute(SpanAttributes.INSIGHTFINDER_ENTITY_RAG_CONFIG_MODEL_FIELDS_SET, rag_config.model_fields_set )



'''
Get value from the result dict using keys' list
'''
def _find_value_from_keys_list(dict, keys_list):
    for key in keys_list:
        if dict[key] is not None:
            return dict[key]
    return None


'''
Use this method to find the value of a field inside the input/output dict.
This method should traverse the entire dict and its sub-dicts until reaching the max_depth.
Get the desired values and put them in res_dict after the corresponding key. 
'''
def _set_res_dict_values(list, res_dict, keys_list):
    return _set_res_dict_values_cnt(list, res_dict, keys_list, 0)
        
def _set_res_dict_values_cnt(list, res_dict, keys_list, depth):
    if depth >= MAX_DEPTH or keys_list is None or keys_list == []:
        return 
    if isinstance(list, Iterable):
        for data in list:
            if type(data) is list or type(data) is tuple:
                _set_res_dict_values_cnt(data, res_dict, keys_list, depth+1)
            else:
                _set_field_value_cnt(data, res_dict, keys_list, 0)
    # else:
    #     _set_field_value_cnt(data, res_dict, keys_list, 0)

def _set_field_value_cnt(data, res_dict, keys_list, depth):
    if depth >= MAX_DEPTH or keys_list is None or keys_list == []:
        return None
    # Check if the data is a dictionary
    if isinstance(data, dict):
        # Iterate through all keys in the dictionary
        for key, value in data.items():
            _process_keys_list_dict(key, value, res_dict, keys_list)
            _set_field_value_cnt(value, res_dict, keys_list, depth+1)
    # Check if the data is an obj that contains __dict__. If so, recursively search in the nested structure    
    elif data is not None and hasattr(data, "__dict__") and data.__dict__ and data.__dict__.items() is not None:
        for key, value in data.__dict__.items():
            _process_keys_list_dict(key, value, res_dict, keys_list)
            _set_field_value_cnt(value, res_dict, keys_list, depth+1)

    # Check if the data is a list
    elif type(data) is list or type(data) is tuple:
        for item in data:
            # Recursively search through each item in the list
            _set_res_dict_values_cnt(item, res_dict, keys_list, depth+1)

def _process_keys_list_dict(key, value, res_dict, keys_list):
    if key in keys_list:
        keys_list.remove(key)
    if key in res_dict and res_dict[key] is None:
        res_dict[key] = value  