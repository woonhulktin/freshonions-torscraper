from flask import Flask
from flask import request
from flask import g
from flask import render_template
from flask import make_response
import flask
import werkzeug.wrappers
from flask import current_app as app
import inspect
import sys
# from werkzeug.contrib.cache import MemcachedCache
from cachelib.memcached import MemcachedCache
import os
import functools 
import logging

CACHE_TIMEOUT = 60 * 60 * 24 * 365

_cache = None
if os.environ['MEMCACHED_ENABLED'] == "true":
	_cache = MemcachedCache(['%s:%s' % (os.environ['MEMCACHED_HOST'], os.environ['MEMCACHED_PORT'])])

_is_cached = False

def is_redirect(response):
	if not isinstance(response, Response):
		return False
	if response.status_code in (301, 302):
		return True
	return False

def is_response(response):
	return isinstance(response, (flask.Response, werkzeug.wrappers.Response))


def cache_memoize(key, func, timeout=300):
	if _cache is None:
		return func()
	real_key = "memoize." + key
	obj = _cache.get(real_key)
	if obj is None:
		obj = func()
		_cache.set(real_key, obj, timeout)
	return obj

class cached(object):

    def __init__(self, timeout=0, render_layout=True):
        self.timeout = timeout or CACHE_TIMEOUT
        self.render_layout = render_layout

    def __call__(self, f):
    	@functools.wraps(f)
        def my_decorator(*args, **kwargs):
        	global _is_cached
        	_is_cached = True
        	if _cache is None:
        		return f(*args, **kwargs)
        	response = _cache.get(request.full_path)
        	if response is None:
        		response = f(*args, **kwargs)
        		_cache.set(request.path, response, self.timeout)
        	_is_cached = False
        	
        	if self.render_layout:
        		wrapped_response = make_response("%s%s%s" % (render_template("layout_header.html"), response, render_template("layout_footer.html")))
        		if is_response(response):
        			wrapped_response.status_code = response.status_code
        			wrapped_response.headers     = response.headers
        			wrapped_response.status      = response.status
        			wrapped_response.mimetype    = response.mimetype
        		return wrapped_response
        	else:
        		return response

        functools.update_wrapper(my_decorator, f)
        return my_decorator

def is_cached():
	return _is_cached

def clear():
	if _cache is not None:
		_cache.clear()

def invalidate_cache(obj):
	if _cache is None:
		return None
	path_attr = getattr(obj, "canonical_path", None)
	if not callable(path_attr):
		return None
	path = obj.canonical_path()
	_cache.delete(path)
	_cache.delete("%s/json" % path)
	return path



