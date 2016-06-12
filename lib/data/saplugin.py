import cherrypy
from cherrypy.process import wspbus, plugins
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import String, Integer 
from sqlalchemy.orm import validates

__all__ = ['SAEnginePlugin']

Base = declarative_base()

class SAEnginePlugin(plugins.SimplePlugin):

  def __init__(self, bus, connection_string=None):
    """
        The plugin is registered to the CherryPy engine and therefore
        is part of the bus (the engine *is* a bus) registery.
 
        We use this plugin to create the SA engine. At the same time,
        when the plugin starts we create the tables into the database
        using the mapped class of the global metadata.
    """
    plugins.SimplePlugin.__init__(self, bus)
    self.sa_engine = None
    self.connection_string = connection_string
    self.session = scoped_session(sessionmaker(autoflush=True,
                                               autocommit=False))

  def start(self):
    self.bus.log('Starting up DB access')
    self.sa_engine = create_engine(self.connection_string, echo=False)
    self.bus.subscribe("bind-session", self.bind)
    self.bus.subscribe("commit-session", self.commit)
    self.bus.log('Creating DB Schema')
    Base.metadata.create_all(self.sa_engine)
    self.bus.log('DB Schema created')

  def stop(self):
    self.bus.log('Stopping DB access')
    self.bus.unsubscribe("bind-session", self.bind)
    self.bus.unsubscribe("commit-session", self.commit)
    if self.sa_engine:
      self.sa_engine.dispose()
      self.sa_engine = None

  def bind(self):
    self.session.configure(bind=self.sa_engine)
    return self.session

  def commit(self):
    try:
      self.session.commit()
    except:
      self.session.rollback()
      raise
    finally:
      self.session.remove()
