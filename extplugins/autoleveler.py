#
# PowerAdmin Plugin for BigBrotherBot(B3) (www.bigbrotherbot.com)
# Copyright (C) 2008 Mark Weirath (xlr8or@xlr8or.com)
# 
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
# Changelog:
# 09/05/2010 - 1.0.1 - xlr8or - bugfix in LoadConfig naming convention

__version__ = '1.0.1'
__author__  = 'xlr8or'

import b3
import b3.events
import b3.plugin
import b3.cron
from b3 import clients

#--------------------------------------------------------------------------------------------------
class AutolevelerPlugin(b3.plugin.Plugin):
  _al_enable = False
  _al_user = 0
  _al_regular = 0
  _al_moderator = 0

  def startup(self):
    """\
    Initialize plugin settings
    """

    # get the admin plugin so we can register commands
    self._adminPlugin = self.console.getPlugin('admin')
    if not self._adminPlugin:
      # something is wrong, can't start without admin plugin
      self.error('Could not find admin plugin')
      return False
    
    # register our commands
    if 'commands' in self.config.sections():
      for cmd in self.config.options('commands'):
        level = self.config.get('commands', cmd)
        sp = cmd.split('-')
        alias = None
        if len(sp) == 2:
          cmd, alias = sp

        func = self.getCmd(cmd)
        if func:
          self._adminPlugin.registerCommand(self, cmd, level, func, alias)
    self._adminPlugin.registerCommand(self, 'alversion', 0, self.cmd_alversion, 'alver')

    # Register our events
    self.verbose('Registering events')
    self.registerEvent(b3.events.EVT_CLIENT_AUTH)
    
    self.debug('Started')

  def onLoadConfig(self):
    self.LoadAutoLeveler()

  def LoadAutoLeveler(self):
    try:
      self._al_enable = self.config.getboolean('settings', 'enable')
    except:
      self.debug('using default setting')
      pass
    self.debug(self._al_enable)
    try:
      self._al_user = self.config.getint('settings', 'user')
    except:
      self.debug('using default setting')
      pass
    self.debug(self._al_user)
    try:
      self._al_regular = self.config.getint('settings', 'regular')
    except:
      self.debug('using default setting')
      pass
    self.debug(self._al_regular)
    try:
      self._al_moderator = self.config.getint('settings', 'moderator')
    except:
      self.debug('using default setting')
      pass
    self.debug(self._al_moderator)
    self.debug('Autoleveler loaded')
    return None

  def getCmd(self, cmd):
    cmd = 'cmd_%s' % cmd
    if hasattr(self, cmd):
      func = getattr(self, cmd)
      return func

    return None

  def onEvent(self, event):
    """\
    Handle intercepted events
    """
    if not self.isEnabled:
      return None

    if event.type == b3.events.EVT_CLIENT_AUTH:
      if self._al_enable:
        self.autoLeveler(event.client)
    else:
      self.dumpEvent(event)

  def dumpEvent(self, event):
    self.debug('autoleveler.dumpEvent -- Type %s, Client %s, Target %s, Data %s',
      event.type, event.client, event.target, event.data)

  def cmd_alversion(self, data, client, cmd=None):
    """\
    This command identifies Plugin version and creator.
    """
    cmd.sayLoudOrPM(client, 'I am Autoleveler version %s by %s' % (__version__, __author__))
    return None

#-- AutoLeveler - [ALL] ---------------------------------------------------------------------------
  def autoLeveler(self, client):
    if self.isEnabled and self._al_enable:
      if self._al_moderator > 0 and client.connections >= self._al_moderator:
        self.setGroup('mod', client)
      elif self._al_regular > 0 and client.connections >= self._al_regular:
        self.setGroup('reg', client)
      elif self._al_user > 0 and client.connections >= self._al_user:
        self.setGroup('user', client)
      else:
        self.verbose('AutoLeveler has nothing to do here...(%s has %s connections)' %(client.exactName, client.connections))
        return False

  def setGroup(self, tgroup, client):
    try:
      group = clients.Group(keyword=tgroup)
      group = self.console.storage.getGroup(group)
    except:
      self.debug('Group %s does not exist' % tgroup)
      return False

    if client:
      if client.inGroup(group):
        self.verbose('%s already is in group %s' %(client.exactName, group.name))
        return False
      elif client.maxLevel >= group.level:
        self.verbose('%s already has a higher level than group %s' %(client.exactName, group.name))
        return False
      else:
        client.setGroup(group)
        client.save()
        self.verbose('%s is auto-set to group %s' %(client.exactName, group.name))

        client.message('Thanks %s, for playing with us! You\'ve been automatically put in group %s' %(client.exactName, group.name))
        return True
