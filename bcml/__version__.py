_MAJOR=3
_MINOR=11
_PATCH="0a1"

VERSION = f"{_MAJOR}.{_MINOR}.{_PATCH}"

if "a" in _PATCH:
    _PATCH, _PRE_RELEASE = _PATCH.split("a", maxsplit=1)
    USER_VERSION = f"{_MAJOR}.{_MINOR}.{_PATCH} alpha {_PRE_RELEASE}"
elif "b" in _PATCH:
    _PATCH, _PRE_RELEASE = _PATCH.split("b", maxsplit=1)
    USER_VERSION = f"{_MAJOR}.{_MINOR}.{_PATCH} beta {_PRE_RELEASE}"
elif "rc" in _PATCH:
    _PATCH, _PRE_RELEASE = _PATCH.split("rc", maxsplit=1)
    USER_VERSION = f"{_MAJOR}.{_MINOR}.{_PATCH} release candidate {_PRE_RELEASE}"
else:
    USER_VERSION = VERSION
