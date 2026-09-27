from typing import Optional

_SIZE_MULTIPLIERS = {'K': 1024, 'M': 1024 ** 2, 'G': 1024 ** 3}

def parse_size(size_str: Optional[str]) -> int:
    if not size_str:
        return 0
    size_str = size_str.upper().strip()
    suffix = size_str[-1]
    if suffix in _SIZE_MULTIPLIERS:
        return int(size_str[:-1]) * _SIZE_MULTIPLIERS[suffix]
    return int(size_str)