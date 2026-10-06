import ctypes
import os
import sys

# Define C Structures
class Config(ctypes.Structure):
    _fields_ = [
        ("id", ctypes.c_int),
        ("params", ctypes.c_double * 10),
        ("param_count", ctypes.c_int),
        ("score", ctypes.c_double)
    ]

# Global oracle handle
_oracle_lib = None

def _load_dll():
    """Load the Oracle DLL (called lazily)"""
    global _oracle_lib
    
    if _oracle_lib is not None:
        return _oracle_lib
    
    extension = ".dll" if sys.platform == "win32" else ".so"
    dll_path = os.path.abspath(os.path.join(os.path.dirname(__file__), f"../../build/oracle{extension}"))
    if not os.path.exists(dll_path):
        raise FileNotFoundError(f"DLL/SO not found at {dll_path}")
    
    try:
        _oracle_lib = ctypes.CDLL(dll_path)
    except OSError as e:
        raise OSError(f"Error loading library: {e}")
    
    # Define Argument Types
    _oracle_lib.oracle_init.argtypes = []
    _oracle_lib.oracle_init.restype = None
    
    _oracle_lib.oracle_free.argtypes = []
    _oracle_lib.oracle_free.restype = None
    
    _oracle_lib.register_config.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    _oracle_lib.register_config.restype = ctypes.c_int
    
    _oracle_lib.update_score.argtypes = [ctypes.c_int, ctypes.c_double]
    _oracle_lib.update_score.restype = None
    
    _oracle_lib.get_next_suggestion.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    _oracle_lib.get_next_suggestion.restype = None
    
    _oracle_lib.bloom_check.argtypes = [ctypes.POINTER(ctypes.c_double), ctypes.c_int]
    _oracle_lib.bloom_check.restype = ctypes.c_bool
    
    _oracle_lib.segment_tree_query_range.argtypes = [ctypes.c_int, ctypes.c_int]
    _oracle_lib.segment_tree_query_range.restype = ctypes.c_double
    
    _oracle_lib.fenwick_query_prefix.argtypes = [ctypes.c_int]
    _oracle_lib.fenwick_query_prefix.restype = ctypes.c_double
    
    _oracle_lib.hll_count_unique.argtypes = []
    _oracle_lib.hll_count_unique.restype = ctypes.c_int
    
    return _oracle_lib

# Wrapper Class
class OracleInterface:
    def __init__(self):
        self.lib = _load_dll()
        self.lib.oracle_init()

    def close(self):
        self.lib.oracle_free()

    def register_config(self, params):
        arr = (ctypes.c_double * len(params))(*params)
        return self.lib.register_config(arr, len(params))

    def update_score(self, config_id, score):
        self.lib.update_score(config_id, score)

    def get_next_suggestion(self, param_count):
        arr = (ctypes.c_double * param_count)()
        self.lib.get_next_suggestion(arr, param_count)
        return list(arr)

    def get_stats(self):
        return {
            "unique_configs": self.lib.hll_count_unique(),
            "best_recent": self.lib.segment_tree_query_range(0, 1000)
        }
