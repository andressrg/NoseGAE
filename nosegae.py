import os
import logging
import sys
import tempfile
from nose.plugins.base import Plugin


log = logging.getLogger(__name__)


class NoseGAE(Plugin):
    """Activate this plugin to run tests in Google App Engine dev environment. When the plugin is active,
    Google App Engine dev stubs such as the datastore, memcache, taskqueue, and more can be made available.
    """
    name = 'gae'

    def options(self, parser, env=os.environ):
        super(NoseGAE, self).options(parser, env)
        parser.add_option(
            '--gae-lib-root', default='/usr/local/google_appengine',
            dest='gae_lib_root',
            help='Set the path to the root directory of the Google '
            'Application Engine installation')
        parser.add_option(
            '--gae-application', default=None, action='store', dest='gae_app',
            help='Set the path to the GAE application '
            'under test. Default is the nose `where` '
            'directory (generally the cwd)')
        parser.add_option(
            '--gae-datastore', default=None, action='store', dest='gae_data',
            help='Set the path to the GAE datastore to use in tests. '
            'Note that when using an existing datastore directory, the '
            'datastore will not be cleared before testing begins.')

    def configure(self, options, config):
        super(NoseGAE, self).configure(options, config)
        if not self.enabled:
            return

        if sys.version_info[0:2] < (2, 7):
            raise EnvironmentError(
                "Python version must be 2.7 or greater, like the Google App Engine environment.  "
                "Tests are running with: %s" % sys.version)

        if options.gae_lib_root not in sys.path:
            sys.path.append(options.gae_lib_root)

        self._app_path = options.gae_app or config.workingDir
        self._data_path = options.gae_data or os.path.join(tempfile.gettempdir(),
                                                           'nosegae.sqlite3')

        if 'google' in sys.modules:
            # make sure an egg (e.g. protobuf) is not cached
            # with the wrong path:
            del sys.modules['google']
        try:
            import appengine_config
        except ImportError:
            pass

        import dev_appserver
        dev_appserver.fix_sys_path()  # add paths to libs specified in app.yaml, etc

        from google.appengine.tools.devappserver2 import application_configuration

        # get the app id out of your app.yaml en stuff
        configuration = application_configuration.ApplicationConfiguration([self._app_path])

        os.environ['APPLICATION_ID'] = configuration.app_id

    def startTest(self, test):
        """Initializes Testbed stubs based off of attributes of the executing test

        allow tests to register and configure stubs by setting properties like
        nosegae_<stub_name> and nosegae_<stub_name>_kwargs

        Example

        class MyTest(unittest.TestCase):
            nosegae_datastore_v3 = True
            nosegae_datastore_v3_kwargs = {
              'datastore_file': '/tmp/nosegae.sqlite3,
              'use_sqlite': True
            }

            def test_something(self):
               entity = MyModel(name='NoseGAE')
               entity.put()
               self.assertNotNone(entity.key.id())

        Args
            :param google.appengine.ext.testbed.Testbed the_test: The unittest.TestCase being run
        """
        import testbed_patch
        testbed_patch.patch()
        from google.appengine.ext import testbed

        self.testbed = testbed.Testbed()
        self.testbed.activate()
        # Give the test access to the active testbed
        the_test = test.test
        the_test.testbed = self.testbed

        for stub_name, stub_init in testbed.INIT_STUB_METHOD_NAMES.iteritems():
            if not getattr(the_test, 'nosegae_%s' % stub_name, False):
                continue
            stub_kwargs = getattr(the_test, 'nosegae_%s_kwargs' % stub_name, {})
            if stub_name == testbed.TASKQUEUE_SERVICE_NAME:
                # root_path is required so the stub can find queue.yaml
                task_args = dict(root_path=self._app_path)
                task_args.update(stub_kwargs)
                stub_kwargs = task_args
            elif stub_name == testbed.DATASTORE_SERVICE_NAME:
                if not self.testbed.get_stub(testbed.MEMCACHE_SERVICE_NAME):
                    # ndb requires memcache so enable it as well as the datastore_v3
                    self.testbed.init_memcache_stub()
                task_args = dict(datastore_file=self._data_path)
                task_args.update(stub_kwargs)
                stub_kwargs = task_args
            getattr(self.testbed, stub_init)(**stub_kwargs)

    def stopTest(self, test):
        self.testbed.deactivate()
        del test.test.testbed