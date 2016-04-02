import os
import logging
from collections import OrderedDict

from substance.monads import *
from substance.logs import *
from substance.shell import Shell
from substance.engine import Engine
from substance.link import Link
from substance.utils import (readYAML,writeYAML,readSupportFile,getSupportFile)
from substance.config import (Config)
from substance.driver.virtualbox import VirtualBoxDriver
from substance.exceptions import (
  FileSystemError,
  FileDoesNotExist,
  EngineNotFoundError,
  EngineExistsError
)

class Core(object):

  def __init__(self, configFile=None, basePath=None):
    self.basePath = os.path.abspath(basePath) if basePath else os.path.expanduser('~/.substance')
    self.enginesPath = os.path.join(self.basePath, "engines")

    configFile = configFile if configFile else "substance.yml"
    configFile = os.path.join(self.basePath, configFile)
    self.config = Config(configFile)

    self.insecureKey = None
    self.insecurePubKey = None

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
    defaults['drivers'] = ['virtualbox']
    defaults['virtualbox'] = OrderedDict()
    defaults['virtualbox']['network'] = "172.21.21.0/24"
    defaults['virtualbox']['interface'] = None
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
      return OK(Engine(name, enginePath=enginePath, core=self))

  def createEngine(self, name, config=None, profile=None):
    enginePath = os.path.join(self.enginesPath, name)
    newEngine = Engine(name, enginePath=enginePath, core=self)
    return newEngine.create(config=config, profile=profile)

  def removeEngine(self, name):
    return self.loadEngine(name) \
      >> Engine.remove
 
  #-- Drivers

  def getDrivers(self):
    return self.config.get('drivers', [])

  def validateDriver(self, driver):
    return driver in self.getDrivers()

  def getDriver(self, name):
    cls = {
      'virtualbox': VirtualBoxDriver
    }.get(name, 'virtualbox')
    driver = cls(core=self)
    return driver

  #-- Engine Link

  def getLink(self, type="ssh"):
    link = Link(keyFile=self.getInsecureKeyFile())
    return link

  #-- Key and Auth

  def getInsecureKeyFile(self):
    return getSupportFile('support/substance_insecure')

  def getInsecurePubKeyFile(self):
    return getSupportFile('support/substance_insecure.pub')
 
