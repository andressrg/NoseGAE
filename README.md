NoseGAE: Nose for Google App Engine Testing
==================================================


## Overview


NoseGAE is a [nose](http://nose.readthedocs.org/en/latest/index.html) plugin that makes it easier to write functional and unit tests for [Google App Engine](https://cloud.google.com/appengine/) applications. 

1. [What does it do?](#what-does-it-do)
	1. [Functional tests](#functional-tests) 
	1. [Unit tests](#unit-tests) 

## What does it do?

### Functional tests

The plugin sets up the GAE development environment before your test
run. This means that you can easily write functional tests for your
application without having to actually start the dev server and test
over http.

Consider a simple hello world application in `support/helloworld`:


```
import webapp2

class Hello(webapp2.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'text/plain'
        self.response.out.write('Hello world!')

app = webapp2.WSGIApplication([('/', Hello)], debug=True)
```

And a simple functional test suite `support/helloworld/test.py` for the application:

```
from webtest import TestApp
import helloworld

app = TestApp(helloworld.app)

def test_index():
    response = app.get('/')
    assert 'Hello world!' in str(response)
```


The important part to note is `helloworld.app` attribute that
holds the application. That attribute provides a way get the
application under test and call it directly, without having to pass
through the dev app server. And that's all you need to do for basic
functional testing.

```
helloworld$ nosetests --with-gae
.
----------------------------------------------------------------------
Ran 1 test in 0.264s

OK

```

### Unit tests

Functional tests are only one kind of test, of course. What if you
want to write unit tests for your data models? Normally, you can't use
your models at all outside of the dev environment, because the Google
App Engine datastore isn't available. However, since the NoseGAE
plugin sets up the development environment around your test run, you
can use models directly in your tests.

Consider the `support/pets/models.py` file that includes some doctests:

```
from google.appengine.ext import ndb

class Pet(ndb.Model):
    """
    The Pet class provides storage for pets. You can create a pet:
    >>> testbed.init_memcache_stub()  # initialize stubs
    >>> testbed.init_datastore_v3_stub()  # initialize stubs

    >>> muffy = Pet(name=u'muffy', type=u'dog', breed=u"Shi'Tzu")
    >>> muffy # doctest: +ELLIPSIS
    Pet(name=u'muffy', type=u'dog', breed=u"Shi'Tzu", ...)
    >>> muffy_key = muffy.put()

    Once created, you can load a pet by its key:

    >>> muffy_key.get() # doctest: +ELLIPSIS
    Pet(name=u'muffy', type=u'dog', breed=u"Shi'Tzu", ...)

    Or by a query that selects the pet:

    >>> list(Pet.query(Pet.type == 'dog')) # doctest: +ELLIPSIS
    [Pet(name=u'muffy', ...)]

    To modify a pet, change one of its properties and ``put()`` it again.

    >>> muffy_2 = muffy
    >>> muffy_2.age = 10
    >>> muffy_key_2 = muffy_2.put()

    The pet's key doesn't change when it is updated.

    >>> bool(muffy_key == muffy_key_2)
    True
    """
    name = ndb.StringProperty(required=True)
    type = ndb.StringProperty(required=True, choices=("cat", "dog", "bird", "fish", "monkey"))
    breed = ndb.StringProperty()
    age = ndb.IntegerProperty()
    comments = ndb.TextProperty()
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)

    def __repr__(self):
        return ("Pet(name=%r, type=%r, breed=%r, age=%r, "
                "comments=%r, created=%r)" %
                (self.name, self.type, self.breed, self.age,
                 self.comments, self.created))

```

Without NoseGAE, the doctests fail.

```
pets$ nosetests --with-doctest
EE
======================================================================
ERROR: Failure: ImportError (No module named google.appengine.ext)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/Josh/Developer/Github/jj/lib/python2.7/site-packages/nose-1.3.4-py2.7.egg/nose/loader.py", line 414, in loadTestsFromName
    addr.filename, addr.module)
  File "/Users/Josh/Developer/Github/jj/lib/python2.7/site-packages/nose-1.3.4-py2.7.egg/nose/importer.py", line 47, in importFromPath
    return self.importFromDir(dir_path, fqname)
  File "/Users/Josh/Developer/Github/jj/lib/python2.7/site-packages/nose-1.3.4-py2.7.egg/nose/importer.py", line 94, in importFromDir
    mod = load_module(part_fqname, fh, filename, desc)
  File "/Users/Josh/Developer/Github/nosegae/support/pets/models.py", line 1, in <module>
    from google.appengine.ext import ndb
ImportError: No module named google.appengine.ext

======================================================================
ERROR: Failure: ImportError (No module named webapp2)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/Users/Josh/Developer/Github/jj/lib/python2.7/site-packages/nose-1.3.4-py2.7.egg/nose/loader.py", line 414, in loadTestsFromName
    addr.filename, addr.module)
  File "/Users/Josh/Developer/Github/jj/lib/python2.7/site-packages/nose-1.3.4-py2.7.egg/nose/importer.py", line 47, in importFromPath
    return self.importFromDir(dir_path, fqname)
  File "/Users/Josh/Developer/Github/jj/lib/python2.7/site-packages/nose-1.3.4-py2.7.egg/nose/importer.py", line 94, in importFromDir
    mod = load_module(part_fqname, fh, filename, desc)
  File "/Users/Josh/Developer/Github/nosegae/support/pets/pets.py", line 1, in <module>
    import webapp2
ImportError: No module named webapp2

----------------------------------------------------------------------
Ran 2 tests in 0.002s

FAILED (errors=2)
```
     
With NoseGAE, they pass.

```
pets$ nosetests --with-doctest --with-gae
.
----------------------------------------------------------------------
Ran 1 test in 0.228s

OK
```

## Realism in testing


Besides the dev appserver and the datastore, the main sticking point
for testing Google App Engine applications is the highly restrictive
runtime environment. When you test without NoseGAE, tests that should
fail (because the tested code **will fail** when run inside the Google
App Engine) may pass.

For instance, consider an app that uses the `socket` module, like this one:

.. include :: support/bad_app/bad_app.py
   :literal:

With a simple functional test:

.. include :: support/bad_app/test.py
   :literal:

This test will pass when run outside of the Google App Engine
environment.
 
.. shell :: nosetests -v
   :cwd: support/bad_app
   :post: cleanup
   :stderr:

   test.test_index_calls_gethostbyname ... ok
   <BLANKLINE>
   ----------------------------------------------------------------------
   Ran 1 test in ...s
   <BLANKLINE>
   OK
..
    
When run with NoseGAE, it will fail, as it should.

.. shell :: nosetests -v --with-gae
   :cwd: support/bad_app
   :post: cleanup
   :stderr:

   test.test_index_calls_gethostbyname ... ERROR
   <BLANKLINE>
   ======================================================================
   ERROR: test.test_index_calls_gethostbyname
   ----------------------------------------------------------------------
   Traceback (most recent call last):
   ...
   <BLANKLINE>
   ----------------------------------------------------------------------
   Ran 1 test in ...s
   <BLANKLINE>
   FAILED (errors=1)
..
    
It is important to note that only **application** code is sandboxed by
NoseGAE. Test code imports outside of the sandbox, so your test code has full
access to the system and available python libraries, including the Google App
Engine datastore and other Google App Engine libraries.

For this reason, **file access is not restricted** in the same way as it
is under GAE, because it is impossible to differentiate application code file
access from test code file access.

However, this means that some things like profiling or Nose's --coverage option 
will not work without some hacks.  If you run into these issues you can pass in 
the option --without-sandbox to turn off the GAE import hook simulation.

.. _nose : http://somethingaboutorange.com/mrl/projects/nose/
.. _`google app engine` : http://code.google.com/appengine/
.. _wsgi : http://www.wsgi.org/wsgi