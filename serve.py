
import sys
import logging
from logging import handlers
import os, os.path

import cherrypy
from cherrypy import _cplogging
from cherrypy.lib import httputil
#Docker conatiner didn't like daemonizing the app
#from cherrypy.process.plugins import Daemonizer


class Server(object):

  def __init__(self, options):
    #configure app paths
    self.base_dir = os.path.normpath(os.path.abspath(options.basedir))
    self.conf_path = os.path.join(self.base_dir, "conf")
    log_dir = os.path.join(self.base_dir, "logs")
    if not os.path.exists(log_dir):
      os.mkdir(log_dir)

    # app configurations
    cherrypy.config.update(os.path.join(self.conf_path, "server.cfg"))
    cherrypy.config.update(os.path.join(self.conf_path, "db.cfg"))
    cherrypy.config.update({'error_page.default': self.on_error})

    engine = cherrypy.engine

    sys.path.insert(0, self.base_dir)

    #import services
    #from webapp.messages import RestMessages
    #events = RestMessages()
    
    #configure sqlalchemy DB plugin 
    from lib.data.saplugin import SAEnginePlugin
    SAEnginePlugin(cherrypy.engine, cherrypy.config['Database']['dbdriver'] + "://" + cherrypy.config['Database']['dbuser'] + ":" + cherrypy.config['Database']['dbpassword'] + "@" + cherrypy.config['Database']['dbhost'] + "/" + cherrypy.config['Database']['dbname']).subscribe()
    from lib.data.satool import SATool
    cherrypy.tools.db = SATool()
    
    conf = {
      '/' : {
        'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
        'tools.response_headers.on': True,
        #Will probably make these JSON
        'tools.response_headers.headers': [('Content-Type', 'application/json')],
        'tools.proxy.on': True,
        'tools.db.on': True
      }
    }
    
    #app = cherrypy.tree.mount(events, '/events',conf)


  def run(self):
    #Starting and running the cherrypy engine and daemonizing 
    engine = cherrypy.engine
    #d = Daemonizer(engine)
    #d.subscribe()

    if hasattr(engine, "signal_handler"):
      engine.signal_handler.subscribe()

    if hasattr(engine, "console_control_handler"):
      engine.console_control_handler.subscribe()

    engine.start()
   
    engine.block()


  def on_error(self, status, message, traceback, version):
    #Least of my concerns at the moment
    return traceback





if __name__ == '__main__':
  from optparse import OptionParser

  def parse_commandline():
    curdir = os.path.normpath(os.path.abspath(os.path.curdir))
  
    parser = OptionParser()
    parser.add_option("-b","--base-dir", dest="basedir",help="Base directory in which the server "\
        "is launched (default: %s)" % curdir)
    parser.set_defaults(basedir=curdir)
    (options, args) = parser.parse_args()
    return options

  Server(parse_commandline()).run()
