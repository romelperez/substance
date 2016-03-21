import os
import logging
from collections import OrderedDict
from substance.monads import *
from substance.logs import *
from substance.shell import Shell
from substance.engine import Engine
from substance.utils import (readYAML,writeYAML)
from substance.config import (Config)
from substance.exceptions import (
  FileSystemError,
  FileDoesNotExist,
  EngineNotFoundError,
  EngineExistsError
)

class Core(object):

  config = None
  defaultConfig = {
    "assumeYes": False,
    "basePath": os.path.join("~", ".substance")
  }

  def __init__(self, configFile=None, basePath=None):
    self.basePath = os.path.abspath(basePath) if basePath else os.path.expanduser('~/.substance')
    self.enginesPath = os.path.join(self.basePath, "engines")

    configFile = configFile if configFile else "substance.yml"
    configFile = os.path.join(self.basePath, configFile)
    self.config = Config(configFile)

  def getBasePath(self):
    return self.basePath

  def getEnginesPath(self):
    return self.enginesPath

  def initialize(self):
    return self.assertPaths().then(self.assertConfig)

  def assertPaths(self):
    return OK([self.basePath, self.enginesPath]).mapM(Shell.makeDirectory)

  def assertConfig(self):
    return self.config.loadConfigFile()  \
      .catchError(FileDoesNotExist, self.makeDefaultConfig)

  def getDefaultConfig(self):
    defaults = OrderedDict()
    defaults['assumeYes'] = False
    defaults['basePath'] = os.path.join("~", ".substance")
    return defaults
    
  def makeDefaultConfig(self, data=None):
    logging.info("Generating default substance configuration in %s", self.config.getConfigFile())
    defaults = self.getDefaultConfig()
    for kkk, vvv in defaults.iteritems():
      self.config.set(kkk, vvv)
    self.config.set("basePath", self.basePath)
    return self.config.saveConfig()
 
  #-- Runtime

  def setAssumeYes(self, ay):
    return self.config.set('assumeYes', ay)

  def getAssumeYes(self):
    return self.config.get('assumeYes', False)

  #-- Engine library management

  def getEngines(self):
    ddebug("getEngines()")
    dirs = [ d for d in os.listdir(self.enginesPath) if os.path.isdir(os.path.join(self.enginesPath, d))] 
    return OK(dirs)

  def loadEngines(self, engines=[]):
    return OK([ self.loadEngine(x) for x in engines ] )

  def loadEngine(self, name):
    enginePath = os.path.join(self.enginesPath, name)
    if not os.path.isdir(enginePath):
      return Fail(EngineNotFoundError("Engine \"%s\" does not exist." % name))
    else:
      return OK(Engine(name, enginePath))

  def createEngine(self, name, config=None, profile=None):
    enginePath = os.path.join(self.enginesPath, name)
    newEngine = Engine(name, enginePath)
    return newEngine.create(config=config, profile=profile)

  def removeEngine(self, name):
    return self.loadEngine(name) \
      >> Engine.remove
 
  #-- Drivers

  @staticmethod
  def validDriver(driver):
    if driver == "VirtualBox":
      return True
    return False
