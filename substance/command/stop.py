# -*- coding: utf-8 -*-
# $Id$

import logging
import sys
from substance.command import Command
from substance.shell import Shell
from substance.engine import EngineProfile
from substance.driver.virtualbox import VirtualBoxDriver
from substance.exceptions import ( SubstanceError, EngineNotFoundError, EngineNotProvisioned, SubstanceDriverError )

class Stop(Command):

  def getShellOptions(self, optparser):
    optparser.add_option("-f","--force", dest="force", help="Force power off",action="store_true")
    return optparser
 
  def main(self):

    name = self.args[0]

    try:
      engine = self.core.getEngine(name)

      if self.options.force and not self.core.getConfigKey('assumeYes') and not Shell.printConfirm("You are about to force stop engine \"%s\"." % name):
        self.exitOK("User cancelled.")
   
      engine.readConfig() 
      engine.stop(force=self.options.force) 

    except SubstanceError as err:
      self.exitError(err.errorLabel)
    except Exception as err:
      self.exitError("Failed to stop engine \"%s\": %s" % (name, err))