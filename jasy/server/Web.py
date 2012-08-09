#
# Jasy - Web Tooling Framework
# Copyright 2010-2012 Zynga Inc.
#

import sys, os, jasy, time, threading, logging
from urllib.parse import urlparse

from jasy.core.Logging import debug, info, error, header, indent, outdent
from jasy.env.State import session
from jasy.core.Lock import lock, release
from jasy.core.Util import getKey

try:
    import requests
    
    # Disable logging HTTP request being created
    logging.getLogger("requests").setLevel(logging.WARNING)
    
except ImportError as err:
    requests = None

try:
    import cherrypy
    from cherrypy.lib.static import serve_file as serveFile
    from cherrypy.lib.static import serve_file as serveFile
    
except ImportError as err:
    cherrypy = None


__all__ = ["serve"]


#
# UTILITIES
#

def enableCrossDomain():
    # See also: https://developer.mozilla.org/En/HTTP_Access_Control
    
    # Allow requests from all locations
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"
   
    # Allow all methods supported by urlfetch
    cherrypy.response.headers["Access-Control-Allow-Methods"] = "GET, POST, HEAD, PUT, DELETE"
    
    # Allow cache-control and our custom headers
    cherrypy.response.headers["Access-Control-Allow-Headers"] = "Cache-Control, X-Proxy-Authorization, X-Requested-With"    
    
    # Cache allowence for cross domain for 7 days
    cherrypy.response.headers["Access-Control-Max-Age"] = "604800"


def findIndex(path):
    all = ["index.html", "index.php"]
    for candidate in all:
        rel = os.path.join(path, candidate)
        if os.path.exists(rel):
            return candidate
            
    return None



#
# ROUTERS
#

class Proxy(object):
    
    def __init__(self, id, config):
        self.id = id
        self.config = config
        self.host = getKey(config, "host")
        self.debug = getKey(config, "debug", False)

        info('Proxy "%s" => "%s" [debug:%s]', self.id, self.host, self.debug)
        
        
    # These headers will be blocked between header copies
    __blockHeaders = set([
        "content-encoding", 
        "content-length", 
        "connection", 
        "keep-alive", 
        "proxy-authenticate", 
        "proxy-authorization", 
        "transfer-encoding", 
        "remote-addr", 
        "host"
    ])
    
    
    @cherrypy.expose
    def default(self, *args, **query):
        """
        This method returns the content of existing files on the file system.
        Query string might be used for cache busting and are otherwise ignored.
        """
        
        # Append special header to all responses
        cherrypy.response.headers["X-Jasy-Version"] = jasy.__version__
        
        # Enable cross domain access
        enableCrossDomain()
        
        url = self.config["host"] + "/".join(args)
        
        # Prepare request
        headers = {name: cherrypy.request.headers[name] for name in cherrypy.request.headers if not name.lower() in self.__blockHeaders}
        
        # Load URL from remote host
        try:
            if self.debug:
                info("Requesting %s", url)
                
            result = requests.get(url, params=query, headers=headers)
        except Exception as err:
            raise cherrypy.HTTPError(403)

        # Copy response headers to our reponse
        for name in result.headers:
            if not name in self.__blockHeaders:
                cherrypy.response.headers[name] = result.headers[name]

        # Apply headers for basic HTTP authentification
        if "X-Proxy-Authorization" in result.headers:
            cherrypy.response.headers["Authorization"] = result.headers["X-Proxy-Authorization"]
            del cherrypy.response.headers["X-Proxy-Authorization"]

        return result.content
        
        
class Static(object):
    
    def __init__(self, id, config):
        self.id = id
        self.config = config
        self.root = getKey(config, "root", ".")
        self.debug = getKey(config, "debug", False)

        info('Static "%s" => "%s" [debug:%s]', self.id, self.root, self.debug)
        
    @cherrypy.expose
    def default(self, *args, **query):
        """
        This method returns the content of existing files on the file system.
        Query string might be used for cache busting and are otherwise ignored.
        """
        
        # Append special header to all responses
        cherrypy.response.headers["X-Jasy-Version"] = jasy.__version__
        
        # Enable cross domain access
        enableCrossDomain()
        
        # When it's a file name in the local folder... load it
        if args:
            path = os.path.join(*args)
        else:
            path = "index.html"
        
        path = os.path.join(self.root, path)
        
        # Check for existance first
        if os.path.isfile(path):
            if self.debug:
                info("Serving file %s", path)
            
            return serveFile(os.path.abspath(path))
            
        # Otherwise return a classic 404
        else:
            if self.debug:
                info("File not found %s", path)
            
            raise cherrypy.NotFound(path)
        


#
# START
#

def serve(routes=None, port=8080):
    
    header("HTTP Server")
    
    # Lock jasy for executing other servers on the same port
    lock("http-%s" % port)
    
    # We need to pause the session to make room for other jasy executions
    session.pause()

    # Shared configuration (global/app)
    config = {
        "global" : {
            "environment" : "production",
            "log.screen" : False,
            "server.socket_port": port,
            "engine.autoreload_on" : False
        },
        
        "/" : {
            "log.screen" : False
        }
    }
    
    # Update global config
    cherrypy.config.update(config)

    # Somehow this screen disabling does not work
    # This hack to disable all access/error logging works
    def empty(*param, **args): pass
    cherrypy.log.access = empty
    cherrypy.log.error = empty
    cherrypy.log.screen = False

    # Initialize routing
    info("Initialize routing...")
    indent()
    root = Static("/", {})
    for key in routes:
        entry = routes[key]
        if "host" in entry:
            node = Proxy(key + "/", entry)
        else:
            node = Static(key + "/", entry)
            
        setattr(root, key, node)
    outdent()
    
    # Finally start the server
    app = cherrypy.tree.mount(root, "", config)
    cherrypy.engine.start()
    info("Started HTTP server at port %s... [PID=%s]", port, os.getpid())
    indent()
    cherrypy.engine.block()

    outdent()
    info("Stopped HTTP server at port %s.", port)
    
    # Release created lock file
    release("http-%s" % port)
    
    # Resume session to continue work on next task (if given)
    session.resume()
