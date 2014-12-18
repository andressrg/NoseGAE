"""Patches to support service stubs that are missing init methods from testbed.INIT_STUB_METHOD_NAMES"""
from google.appengine.ext import testbed
from google.appengine.api.prospective_search.prospective_search_stub import ProspectiveSearchStub


def patch():
    """Monkeypatch the testbed for stubs that do not have an init method yet"""
    if not hasattr(testbed, 'PROSPECTIVE_SEARCH_SERVICE_NAME'):
        testbed.PROSPECTIVE_SEARCH_SERVICE_NAME = 'matcher'
        testbed.INIT_STUB_METHOD_NAMES.update({
            testbed.PROSPECTIVE_SEARCH_SERVICE_NAME: 'init_prospective_search_stub'
        })

        def init_prospective_search_stub(self, enable=True, data_file=None):
            """Workaround to avoid prospective search complain until there is a proper testbed stub

            http://stackoverflow.com/questions/16026703/testbed-stub-for-google-app-engine-prospective-search

            Args:
                :param self: The Testbed instance.
                :param enable: True if the fake service should be enabled, False if real
                    service should be disabled.
            """

            if not enable:
                self._disable_stub(testbed.PROSPECTIVE_SEARCH_SERVICE_NAME)
                return
            stub = ProspectiveSearchStub(
                prospective_search_path=data_file,
                taskqueue_stub=self.get_stub(testbed.TASKQUEUE_SERVICE_NAME))
            self._register_stub(testbed.PROSPECTIVE_SEARCH_SERVICE_NAME, stub)
        testbed.Testbed.init_prospective_search_stub = init_prospective_search_stub
