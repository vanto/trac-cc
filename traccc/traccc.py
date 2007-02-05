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
from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet
from trac.Timeline import ITimelineEventProvider
from trac.web.main import IRequestHandler
#from trac.web.api import absolute_url
from trac.util import Markup
from trac.util.text import to_unicode

import urllib, os, time

class CruiseControlPlugin(Component):
    """A plugin to integrate Cruise Control into Trac"""
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, ITimelineEventProvider)

    cc_cs = """
<?cs include "header.cs"?>
<div id="ctxtnav" class="nav">
 <h2>About Navigation</h2>
 <ul>
  <li class="first last"><a href="<?cs
    var:cc.baseLink ?>">Overview</a></li>
 </ul>
</div>
<div id="content" class="cc<?cs if:cc.page ?>_<?cs var:cc.page ?><?cs /if ?>">
<h1>CruiseControl Status Page</h1>
<p><?cs var:cc.buildstatus ?></p>
<h2>Builds</h2>
<p>
<?cs each:build = cc.builds ?>
   <?cs if:build.successful ?><img src="<?cs var:chrome.href ?>/traccc/ccsuccess.gif" border="0"/> 
   <?cs else ?><img src="<?cs var:chrome.href ?>/traccc/ccerror.gif" border="0"/>
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
<div id="content" class="cc<?cs if:cc.page ?>_<?cs var:cc.page ?><?cs /if ?>">
<h1>CruiseControl Details Page</h1>
<p>
   <?cs if:cc.build.successful ?><img src="<?cs var:chrome.href ?>/traccc/ccsuccess.gif" border="0"/> 
   <?cs else ?><img src="<?cs var:chrome.href ?>/traccc/ccerror.gif" border="0"/>
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
        yield 'mainnav', 'cruisecontrol', Markup('<a href="%s">CruiseControl</a>' % self.env.href.cruisecontrol())
    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [self.env.get_templates_dir(),
                self.config.get('trac', 'templates_dir')]

    def get_htdocs_dirs(self):
        """
        Return a list of directories with static resources (such as style
        sheets, images, etc.)

        Each item in the list must be a `(prefix, abspath)` tuple. The
        `prefix` part defines the path in the URL that requests to these
        resources are prefixed with.
        
        The `abspath` is the absolute path to the directory containing the
        resources on the local file system.
        """
        from pkg_resources import resource_filename
        return [('traccc', resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods
    def match_request(self, req):
	import re
        #match = re.match(r'/cruisecontrol(?:/(.*))?$', req.path_info)
        #match = re.match(r'/cruisecontrol(?:/?\?log=|/?)(.*)$', req.path_info)
        match = re.match(r'/cruisecontrol(?:/?\?log=|/?)(.*)$', req.path_info)
        #match = re.match(r'/cruisecontrol(?:/?\?log=(.*))?$', req.path_info)
        if match:
            if match.group(1):
                if match.group(1) != '':
		    req.args['log'] = match.group(1)
	    if req.args.get('log','') == '':
	    	req.args['log'] = 'overview'
            return 1

    def getBuilds(self, ccpath, ccstatus):
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
            return builds
        else:
            from trac import util
            raise util.TracError('The given cruisecontrol log path is invalid.');

   # ITimelineEventProvider methods
    def get_timeline_filters(self, req):
        if req.perm.has_permission('CHANGESET_VIEW'):
            yield ('ccbuild', 'CruiseControl Builds')

    def get_timeline_events(self, req, start, stop, filters):
        if 'ccbuild' in filters:
            add_stylesheet(req, 'traccc/traccc.css')

            builds = self.getBuilds(self.config.get('cruisecontrol', 'ccpath') + '/', self.config.get('cruisecontrol', 'buildstatusfile'))
            for b in builds:
		if time.mktime(b['datetime']) < start:
			return
                if time.mktime(b['datetime']) < stop:
	               	href = 'cruisecontrol/' + b['id']
			title = 'CruiseControl Build:' + b['label']
			date = time.mktime(b['datetime'])
			author = 'unknown'
			from trac.util import format_datetime
			if b['successful']:
				message = 'Build was succesful on '
				kind = 'ccbuild-successful'
			else:
				message = 'Build failed on '
				kind = 'ccbuild-failed'
			message = message + format_datetime(b['datetime'])

       		       	yield (kind, href, title, date, author, message)


    def process_request(self, req):
        add_stylesheet(req, 'traccc/traccc.css')

        cc_id = req.args.get('log', 'overview').replace('log','',1)
	self.env.log.debug(cc_id)
        req.hdf['title'] = 'CruiseControl'
        req.hdf['cc.baseLink'] = self.env.href.cruisecontrol()

        ccpath = self.config.get('cruisecontrol', 'ccpath') + '/'
        ccstatus = self.config.get('cruisecontrol', 'buildstatusfile')

	if cc_id == 'overview':
                f = urllib.urlopen(urllib.pathname2url(ccpath + ccstatus))
                req.hdf['cc.buildstatus'] = f.read()
                req.hdf['cc.builds'] = self.getBuilds(ccpath, ccstatus)
                template = req.hdf.parse(self.cc_cs)
                return template, None
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
                req.hdf['cc.html_result'] = Markup(to_unicode(style.saveResultToString(result)))
                style.freeStylesheet()
                doc.freeDoc()
                result.freeDoc()

            template = req.hdf.parse(self.cc_details_cs)
            return template, None
