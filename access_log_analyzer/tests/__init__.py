import access_log_analyzer

_mock_log_input = []
_mock_date = {}

class MockFileInputContext():
    def __init__(self):
        pass

    def __enter__(self):
        return _mock_log_input

    def __exit__(self, *args):
        pass

def set_today_y(today_y):
    _mock_date['y'] = today_y

def get_today_y():
    return _mock_date['y']

def set_today_yw(today_yw):
    _mock_date['yw'] = today_yw

def get_today_yw():
    return _mock_date['yw']

def set_today_ym(today_ym):
    _mock_date['ym'] = today_ym

def get_today_ym():
    return _mock_date['ym']

def set_today_ymd(today_ymd):
    _mock_date['ymd'] = today_ymd

def get_today_ymd():
    return _mock_date['ymd']

def set_today_ymdh(today_ymdh):
    _mock_date['ymdh'] = today_ymdh

def get_today_ymdh():
    return _mock_date['ymdh']

def add_mock_log_input(line):
    _mock_log_input.append(line)

def clear_mock_log_input():
    del _mock_log_input[:]

def in_memory_connection_info():
    return ':memory:'

access_log_analyzer.log_input = MockFileInputContext()
access_log_analyzer.connection_info = in_memory_connection_info
access_log_analyzer.get_today_y = get_today_y
access_log_analyzer.get_today_yw = get_today_yw
access_log_analyzer.get_today_ym = get_today_ym
access_log_analyzer.get_today_ymd = get_today_ymd
access_log_analyzer.get_today_ymdh = get_today_ymdh
