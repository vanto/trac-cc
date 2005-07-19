#
# Copyright (C) 2005 Tammo van Lessen <tvanlessen@gmail.com>
#
# Trac is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 2 of the
# License, or (at your option) any later version.
#
# Trac is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
# Author: Tammo van Lessen <tvanlessen@gmail.com>

from trac.core import *
from trac.web.chrome import INavigationContributor
from trac.web.main import IRequestHandler
import urllib, os, time

class CruiseControlPlugin(Component):
    implements(INavigationContributor, IRequestHandler)

    cc_cs = """
<?cs include "header.cs"?>
<div id="ctxtnav" class="nav">
 <h2>About Navigation</h2>
 <ul>
  <li class="first last"><a href="<?cs
    var:cc.baseLink ?>">Overview</a></li>
 </ul>
</div>
<div id="content" class="cc<?cs if:cc.page ?>_<?cs var:cc.page ?><?cs /if ?>"
<h1>CruiseControl Status Page</h1>
<p><?cs var:cc.buildstatus ?></p>
<h2>Builds</h2>
<p>
<?cs each:build = cc.builds ?>
   <?cs if:build.successful ?><img src="<?cs var:htdocs_location ?>ccsuccess.gif" border="0"/> 
   <?cs else ?><img src="<?cs var:htdocs_location ?>ccerror.gif" border="0"/>
   <?cs /if ?>
   <a href="<?cs var:cc.baseLink ?>/<?cs var:build.id ?>"><?cs var:build.datetimeStr ?> <?cs var:build.label ?></a><br/>
<?cs /each ?>
</p>
</div>
<?cs include "footer.cs"?>
""" # cc_cs


    cc_details_cs = """
<?cs include "header.cs"?>
<div id="ctxtnav" class="nav">
 <h2>About Navigation</h2>
 <ul>
  <li class="first last"><a href="<?cs
    var:cc.baseLink ?>">Overview</a></li>
 </ul>
</div>
<div id="content" class="cc<?cs if:cc.page ?>_<?cs var:cc.page ?><?cs /if ?>"
<h1>CruiseControl Details Page</h1>
<p>
   <?cs if:cc.build.successful ?><img src="http://statcvs-xml.berlios.de/images/icon_success_sml.gif" border="0"/> 
   <?cs else ?><img src="http://statcvs-xml.berlios.de/images/icon_error_sml.gif" border="0"/>
   <?cs /if ?>
   <b>Build from <?cs var:cc.build.datetimeStr ?> <?cs var:cc.build.label ?></b>
</p>
<?cs var:cc.html_result ?>
</div>
<?cs include "footer.cs"?>
""" # cc_details_cs

    __datePatternLength = 14
    __prefixLength = 3
    __labelSeparator = 'L'

    def createBuildInfo(self, filename):
        compressed = filename.endswith('.gz')
        if compressed:
            id = filename[self.__prefixLength:-7]
        else:
            id = filename[self.__prefixLength:-4]
        datetime = time.strptime(id[0:self.__datePatternLength],'%Y%m%d%H%M%S')
        successful = len(id) > self.__datePatternLength + len(self.__labelSeparator)
        build = {'id': '' + id,
            'filename': filename, 
            'datetime': datetime, 
            'datetimeStr': time.strftime('%x %X', datetime),
            'label': id[self.__datePatternLength + len(self.__labelSeparator):],
            'successful': successful,
            'compressed': compressed}
        return build

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        return 'cruisecontrol'
    def get_navigation_items(self, req):
        yield 'mainnav', 'cruisecontrol', '<a href="%s">CruiseControl</a>' \
                                       % self.env.href.cruisecontrol()
    # IRequestHandler methods
    def match_request(self, req):
        #return req.path_info == '/cruisecontrol'
	import re
        match = re.match(r'/cruisecontrol(?:/(.*))?$', req.path_info)
        if match:
            if match.group(1):
                req.args['cc_id'] = match.group(1)
            return 1


    def process_request(self, req):
        cc_id = req.args.get('cc_id', 'overview')

        req.hdf['title'] = 'CruiseControl'
        req.hdf['cc.baseLink'] = self.env.href.cruisecontrol()

        ccpath = self.config.get('cruisecontrol', 'ccpath') + '/'
        ccstatus = self.config.get('cruisecontrol', 'buildstatusfile')

	if cc_id == 'overview':

            f = urllib.urlopen(ccpath + ccstatus)
            req.hdf['cc.buildstatus'] = f.read()

            if os.path.isdir(ccpath) & os.path.exists(ccpath + "/" + ccstatus):
                modlist = filter(lambda x: x[0:3] == 'log' and (\
                    (len(x) > self.__prefixLength + self.__datePatternLength + 3 and x[-4:] == '.xml') or \
                    (len(x) > self.__prefixLength + self.__datePatternLength + 5 and x[-7:] == '.xml.gz')), \
                os.listdir(os.path.dirname(ccpath)))
                builds = []
                for _mod in modlist:
                    build = self.createBuildInfo(_mod)
                    builds.append(build)
                    #print build
                     
                #builds.sort(cmp=lambda x,y: cmp(x['datetimeStr'], y['datetimeStr']))
                builds.sort()
                builds.reverse()
                req.hdf['cc.builds'] = builds
                template = req.hdf.parse(self.cc_cs)
                return template, None
            else:
                from trac import util
                raise util.TracError('The given cruisecontrol log path is invalid.');
        else:
            req.hdf['cc_id'] = cc_id

            try:
                import libxml2
                import libxslt
            except ImportError:
                from trac import util
                raise util.TracError('libxml and libxslt is not installed.');
            else:
                filename = 'log' + cc_id + '.xml' #TODO: compressed?
                build = self.createBuildInfo(filename)
                req.hdf['cc.build'] = build
                styledoc = libxml2.parseFile(self.config.get('cruisecontrol', 'xslfile'))
                style = libxslt.parseStylesheetDoc(styledoc)
                doc = libxml2.parseFile(ccpath + filename)
                result = style.applyStylesheet(doc, None)
                req.hdf['cc.html_result'] = style.saveResultToString(result)
                style.freeStylesheet()
                doc.freeDoc()
                result.freeDoc()

            template = req.hdf.parse(self.cc_details_cs)
            return template, None
