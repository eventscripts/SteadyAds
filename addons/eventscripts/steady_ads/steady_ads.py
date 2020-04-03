from __future__ import with_statement
from path import path
from itertools import cycle
import es
import cfglib
import cmdlib
import gamethread
import playerlib
import msglib
import services


info = es.AddonInfo()
info.name = 'Steady Ads'
info.version = 1.0
info.basename = 'steady_ads'
info.url = 'http://addons.eventscripts.com/addons/view/steady_ads'
info.author = 'Dead Man Walker'


COLORS = {
 '#darkred' : "153 0 0",
 '#red' : "255 0 0",
 '#lightred' : "255 102 102",
 '#darkblue' : "0 0 255",
 '#blue' : "0 0 153",
 '#lightblue' : "102 102 255",
 '#darkgreen' : "0 153 0",
 '#green' : "0 255 0",
 '#lightgreen' : "102 255 102",
 '#darkyellow' : "153 153 0",
 '#yellow' : "255 255 0",
 '#lightyellow' : "255 255 102",
 '#darkpurple' : "76 0 153",
 '#purple' : "127 0 255",
 '#lightpurple' : "178 102 255",
 '#darkpink' : "255 0 255",
 '#pink' : "255 0 255",
 '#lightpink' : "153 0 153",
 '#darkorange' : "153 76 0",
 '#orange' : "255 128 0",
 '#lightorange' : "255 178 102",
 '#darkturquoise' : "0 153 153",
 '#turquoise' : "0 255 255",
 '#lightturquoise' : "102 255 255",
 '#white' : "255 255 255",
 '#darkgray' : "64 64 64",
 '#gray' : "128 128 128",
 '#lightgray' : "192 192 192",
}

ADVERT_INSTRUCTIONS = [
 '// *****************************************************************\n',
 '// *** %s Adverts\n' %info.name,
 '// *****************************************************************\n\n',
 '// Place your adverts below these instructions, one per line.\n',
 '// Any line prefixed with two forward slashes (//) will be ignored.\n',
 '// Each advert can be displayed in one of the colors listed in the config file.\n',
 '// Use the following syntax:\n',
 '// <color>|<advert>',
 '// Example of usage:\n',
 '// #yellow|This is my first advert\n',
 '// If no color is given the default one will be used.\n'
 '// Note that each advert may only be 27 characters long!\n\n'
]
CFG_BASE_PATH = path(es.ServerVar('eventscripts_gamedir')).joinpath('cfg').joinpath(info.basename)
CFG_CONFIG_PATH = CFG_BASE_PATH.joinpath(info.basename + '_config.cfg')
CFG_ADVERTS_PATH = CFG_BASE_PATH.joinpath(info.basename + '_adverts.txt')

if not path.exists(CFG_BASE_PATH):
   CFG_BASE_PATH.mkdir()

cfg = cfglib.AddonCFG(CFG_CONFIG_PATH)
cfg.text("*****************************************************************")
cfg.text("*** %s Config" %info.name) 
cfg.text("*****************************************************************")
cfg.text(' ')
SA_DURATION = cfg.cvar('sa_duration', 11, 'Duration of one advert to stay. Minimum is 11!')
SA_DEFAULT_COLOR = cfg.cvar('sa_default_color', '#red', 'Default color if none was specified for an advert. List of colors below.')
SA_REFRESH_ON_ROUND = cfg.cvar('sa_refresh_on_round', 0, 'Refresh advert list every round')
cfg.text(' ')
cfg.text('List of available colors:')
for color in sorted(COLORS):
   cfg.text(" -" + color)
cfg.write()
cfg.execute()

if services.isRegistered('auth'):
   auth_service = services.use('auth')
   auth_service.registerCapability('add_ad_permission', auth_service.ADMIN)
   isAuthed = lambda x: auth_service.isUseridAuthorized(x, 'add_ad_permission')
else:
   isAuthed = lambda x: False

def load():
   global adverts
   adverts = getAdverts()
   printAdverts()

def unload():
   gamethread.cancelDelayed('adverts_delay')
   cmdlib.unregisterClientCommand('add_advert')
   cmdlib.unregisterClientCommand('delete_advert')
   cmdlib.unregisterServerCommand('add_advert')
   cmdlib.unregisterServerCommand('delete_advert')

def es_map_start(event_var):
   global adverts
   adverts = getAdverts()

def round_end(event_var):
   if int(SA_REFRESH_ON_ROUND):
      global adverts
      adverts = getAdverts()

def getAdverts():
   global new_adverts
   new_adverts = []
   if not path.exists(CFG_ADVERTS_PATH):
      with CFG_ADVERTS_PATH.open('w') as file:
         file.writelines(ADVERT_INSTRUCTIONS)
      return None
   with CFG_ADVERTS_PATH.open() as file:
      adverts_list = [line for line in file.readlines() if line.strip() and not line.strip().startswith('//')]
   if adverts_list:

      for a in adverts_list:
         a_split = a.split('|', 1)
         if len(a_split) == 1:
            new_adverts.append(str(SA_DEFAULT_COLOR) + "|" + a.replace('\n', ''))
         else:  
            color = a_split[0]
            if color not in COLORS:
               color = str(SA_DEFAULT_COLOR)
            new_adverts.append(color + "|" + a_split[1].replace('\n', ''))
      return cycle(new_adverts)
   return None

def printAdverts():
   duration = int(SA_DURATION)
   if adverts:
      advert = adverts.next()
      advert_split = advert.split('|', 1)
      ad = advert_split[1]
      color = advert_split[0]
      msg = msglib.VguiDialog(title=ad, level=5, color=COLORS[color]+" 255", time=duration, mode=msglib.VguiMode.MSG)
      for userid in playerlib.getUseridList('#human'):
         msg.send(userid)
   gamethread.delayedname(duration, 'adverts_delay', printAdverts)

def addAdvertClient(userid, args):
   addAdvert(args, userid)

def deleteAdvertClient(userid, args):
   deleteAdvert(args, userid)

def addAdvertServer(args):
   addAdvert(args)

def deleteAdvertServer(args):
   deleteAdvert(args)
   
def addAdvert(args, userid=None):
   if not args:
      if userid:
         es.cexec(userid, 'echo Syntax: add_advert <color>|<advert>') 
      else:
         print('Syntax: add_advert <color>|<advert>')
      return
   global adverts
   args = str(args)
   a_split = args.split('|', 1)
   if len(a_split) == 1:
      ad =  args.replace('\n', '')
      color = str(SA_DEFAULT_COLOR)
      new_adverts.append(color + "|" + ad)
   else:  
      color = a_split[0]
      if color not in COLORS:
         color = str(SA_DEFAULT_COLOR)
      ad = a_split[1].replace('\n', '')
      new_adverts.append(color + "|" + ad)
   if userid:
      es.cexec(userid, "echo Added the advert: --%s-- in the color: --%s--" %(ad, color))
   else:
      print('Added the advert: "%s" in the color: "%s"' %(ad, color))
   adverts = cycle(new_adverts)
   with CFG_ADVERTS_PATH.open('a') as file:
      file.write(args + '\n')

def deleteAdvert(args, userid=None):
   if not args:
      if userid:
         es.cexec(userid, 'echo Syntax: delete_advert <partial advert>') 
      else:
         print('Syntax: delete_advert <partial advert>')
      return
   global adverts
   args = str(args)
   for ad in new_adverts:
      if args in ad:
         new_adverts.remove(ad)
         ad_split = ad.split('|', 1)
         if len(ad_split) == 2:
            pure_ad = ad_split[1]
         else:
            pure_ad = ad_split[0]
         if userid:
            es.cexec(userid, "echo Deleted the advert: --%s--" %pure_ad) 
         else:
            print('Deleted the advert: "%s"' %pure_ad)
         adverts = cycle(new_adverts)
         with CFG_ADVERTS_PATH.open('r') as file:
            lines = file.readlines()
         with CFG_ADVERTS_PATH.open('w') as file:
            for line in lines:
               if not line.startswith('//'):
                  line_split = line.replace('\n', '').split('|', 1)
                  if len(line_split) == 2:
                     line = line_split[1]
                  else:
                     line = line_split[0]
               if line != pure_ad:
                  if line.endswith('\n'):
                     file.write(line)
                  else:
                     file.write(line + '\n')
         if new_adverts:
            adverts = cycle(new_adverts)
         else:
            adverts = None
         break
   else:
      if userid:
         es.cexec(userid, "echo No advert found") 
      else:
         print('No advert found')
         

cmdlib.registerClientCommand('add_advert', addAdvertClient, 'adds an advert', 'add_ad_permission', 'ADMIN')
cmdlib.registerClientCommand('delete_advert', deleteAdvertClient, 'deletes an advert', 'add_ad_permission', 'ADMIN')
cmdlib.registerServerCommand('add_advert', addAdvertServer, 'adds an advert')
cmdlib.registerServerCommand('delete_advert', deleteAdvertServer, 'deletes an advert')