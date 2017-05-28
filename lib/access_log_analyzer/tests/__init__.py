"""
Tests module
"""
import access_log_analyzer

MOCK_LOG_INPUT = []
MOCK_DATE = {}

class MockFileInputContext(): # pylint: disable=too-few-public-methods
    """
    Mock file input
    """
    def __init__(self):
        pass

    def __enter__(self):
        return MOCK_LOG_INPUT

    def __exit__(self, *args):
        pass

def set_today_y(today_y):
    """ Set current year """
    MOCK_DATE['y'] = today_y

def get_today_y():
    """ get current year """
    return MOCK_DATE['y']

def set_today_yw(today_yw):
    """ set current year + week """
    MOCK_DATE['yw'] = today_yw

def get_today_yw():
    """ get current year + week """
    return MOCK_DATE['yw']

def set_today_ym(today_ym):
    """ set current year + month """
    MOCK_DATE['ym'] = today_ym

def get_today_ym():
    """ get current year + month """
    return MOCK_DATE['ym']

def set_today_ymd(today_ymd):
    """ set current year + month + day """
    MOCK_DATE['ymd'] = today_ymd

def get_today_ymd():
    """ get current year + month + day """
    return MOCK_DATE['ymd']

def set_today_ymdh(today_ymdh):
    """ set current year + month + day + hour """
    MOCK_DATE['ymdh'] = today_ymdh

def get_today_ymdh():
    """ get current year + month + day + hour """
    return MOCK_DATE['ymdh']

def add_mock_log_input(line):
    """ Add a line to the mock log input """
    MOCK_LOG_INPUT.append(line)

def clear_mock_log_input():
    """ Clear the mock log input """
    del MOCK_LOG_INPUT[:]

def in_memory_connection_info():
    """ get mock db connection string """
    return ':memory:'

# Wire up the mocks
access_log_analyzer.log_input = MockFileInputContext()
access_log_analyzer.connection_info = in_memory_connection_info
access_log_analyzer.get_today_y = get_today_y
access_log_analyzer.get_today_yw = get_today_yw
access_log_analyzer.get_today_ym = get_today_ym
access_log_analyzer.get_today_ymd = get_today_ymd
access_log_analyzer.get_today_ymdh = get_today_ymdh
