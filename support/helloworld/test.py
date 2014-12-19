from webtest import TestApp
import helloworld

app = TestApp(helloworld.app)


def test_index():
    response = app.get('/')
    assert 'Hello world!' in str(response)
