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

from trac.web.chrome import INavigationContributor, ITemplateProvider, add_stylesheet, Chrome
from trac.web.clearsilver import HDFWrapper

from trac.Timeline import ITimelineEventProvider
from trac.web.main import IRequestHandler
from trac.util import Markup
from trac.perm import IPermissionRequestor, PermissionSystem
from trac.util.text import to_unicode
from trac.util import pretty_timedelta, parse_date, format_datetime

from api import ICruiseControlLogRenderer
from xml.dom import minidom
from xml.parsers import expat
from xml.sax import make_parser
from xml.sax.handler import ContentHandler 

import urllib, os, time, pkg_resources

class CruiseControlPlugin(Component):
    """A plugin to integrate Cruise Control into Trac

    See [https://oss.werkbold.de/trac-cc/ http://oss.werkbold.de/trac-cc] for details.
    """
    implements(INavigationContributor, IRequestHandler, ITemplateProvider, ITimelineEventProvider, IPermissionRequestor)

    log_renderers = ExtensionPoint(ICruiseControlLogRenderer)
    
    __datePatternLength = 14
    __prefixLength = 3
    __labelSeparator = 'L'

    def get_build_info(self, filename):
        compressed = filename.endswith('.gz')
        if compressed:
            id = filename[self.__prefixLength:-7]
        else:
            id = filename[self.__prefixLength:-4]
        datetime = time.strptime(id[0:self.__datePatternLength],'%Y%m%d%H%M%S')
        successful = len(id) > self.__datePatternLength + len(self.__labelSeparator)
        build = {'id': '' + id,
            'filename': filename, 
            'datetime': time.mktime(datetime),
            'prettydate': pretty_timedelta(time.mktime(datetime)),
            'datetimeStr': time.strftime('%x %X', datetime),
            'label': id[self.__datePatternLength + len(self.__labelSeparator):],
            'successful': successful,
            'compressed': compressed}

        return build

    # INavigationContributor methods
    def get_active_navigation_item(self, req):
        if req.perm.has_permission('CRUISECONTROL_VIEW'): 
            return 'cruisecontrol'
    def get_navigation_items(self, req):
        if req.perm.has_permission('CRUISECONTROL_VIEW'): 
            yield 'mainnav', 'cruisecontrol', Markup('<a href="%s">CruiseControl</a>' % self.env.href.cruisecontrol())
    # ITemplateProvider methods
    def get_templates_dirs(self):
        """
        Return the absolute path of the directory containing the provided
        ClearSilver templates.
        """
        return [pkg_resources.resource_filename(__name__, 'templates')]

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
        return [('traccc', pkg_resources.resource_filename(__name__, 'htdocs'))]

    # IRequestHandler methods
    def match_request(self, req):
        import re
        match = re.match(r'/cruisecontrol(?:/?\?log=|/?)(.*)$', req.path_info)
        if match:
            if match.group(1):
                if match.group(1) != '':
                    req.args['log'] = match.group(1)
            if req.args.get('log','') == '':
                req.args['log'] = 'overview'
            return 1

    def getBuilds(self, projectpath, statusfile):
        if os.path.isdir(projectpath) & os.path.exists(projectpath + "/" + statusfile):
            modlist = filter(lambda x: x[0:3] == 'log' and (\
                (len(x) > self.__prefixLength + self.__datePatternLength + 3 and x[-4:] == '.xml') or \
                (len(x) > self.__prefixLength + self.__datePatternLength + 5 and x[-7:] == '.xml.gz')), \
            os.listdir(os.path.dirname(projectpath)))
            builds = []
            for _mod in modlist:
                build = self.createBuildInfo(_mod)
                builds.append(build)

            builds.sort()
            builds.reverse()
            return builds
        else:
            raise TracError('The given cruisecontrol log path is invalid.');

    def get_cc_config(self):
        if 'cruisecontrol' in self.config.sections():
            if self.config.get('cruisecontrol', 'logfiles') is None:
                if self.config.get('cruisecontrol', 'ccpath') is None:
                    raise TracError('TracCC is not properly configured. Please visit [https://oss.werkbold.de/trac-cc/ TracCC Website] for details.')
                else:
                    # backward compatibility
                    clogpaths = self.config.get('cruisecontrol', 'ccpath')
            else:
                clogpaths = self.config.get('cruisecontrol', 'logpaths') 

            statusfile = self.config.get('cruisecontrol', 'buildstatusfile')
            show_changesets = self.config.get('cruisecontrol', 'show_changesets')
            logpaths = map(lambda x: x.strip() + '/', clogpaths.strip().split(','))
            projectnames = []
            if self.config.get('cruisecontrol','projectnames') is not '':
                projectnames = map(lambda x: x.strip(), self.config.get('cruisecontrol','projectnames').split(','))
                
            return (logpaths, projectnames, statusfile, show_changesets)
        raise TracError('Please add the cruisecontrol section to your trac.ini')
        
    def get_all_builds(self):
        (logpaths, projectnames, statusfile, show_changesets) = self.get_cc_config()
        builds = []
        projects = []
        for i, logpath in enumerate(logpaths):
            f = urllib.urlopen(urllib.pathname2url(logpath + statusfile))
            pinfo = {'path': logpath,
                     'href': '%s/%d' % (self.env.href.cruisecontrol(), i),
                     'info': f.read().capitalize()}
            
            if i < len(projectnames) and projectnames[i] != '':
                pinfo.update({'name': projectnames[i]})
            else:
                pinfo.update({'name': 'Project %d' % (i + 1)})

            binfos = self.get_project_builds(logpath)
            lastbuild = {'datetime': 0}
            lastsuccess = 0
            for b in binfos:
                b['project'] = pinfo
                b['href'] = pinfo['href'] + '/' + b['id']
                if lastbuild['datetime'] < b['datetime']:
                    lastbuild = b
                if b['successful'] and lastsuccess < b['datetime']:
                    lastsuccess = b['datetime']
                    
            builds.extend(binfos)
            pinfo['status'] = lastbuild['successful']
            if lastsuccess == 0:
                pinfo['lastsuccess'] = 'None'
            else:
                pinfo['lastsuccess'] = format_datetime(lastsuccess)
            
            print str(pinfo)
            projects.append(pinfo)
        builds.sort(lambda x, y: cmp(y['datetime'], x['datetime']))
        return (builds, projects)
        
   # ITimelineEventProvider methods
    def get_timeline_filters(self, req):
        if req.perm.has_permission('CRUISECONTROL_VIEW'):
            yield ('ccbuild', 'CruiseControl Builds')

    def get_timeline_events(self, req, start, stop, filters):
        if 'ccbuild' in filters:
            (logpaths, projectnames, statusfile, show_changesets) = \
                       self.get_cc_config()

            add_stylesheet(req, 'traccc/traccc.css')

            (builds, projects) = self.get_all_builds()
            for b in builds:
                if b['datetime'] < start:
                    return
                if b['datetime'] < stop:
                    href = b['href']
                    title = 'Build of %s completed.' % b['project']['name']
                    date = b['datetime']
                    author = 'unknown'

                    if b['successful']:
                        message = 'Build %s was succesful.' % b['id']
                        kind = 'ccbuild-successful'
                    else:
                        message = 'Build %s failed.' % b['id']
                        kind = 'ccbuild-failed'
                        
                    if show_changesets:
                        revisions = self.parse_revisions(b['project']
                                                ['path'] + b['filename'])

                        if len(revisions) > 0:
                            message = Markup(message + \
                                    '<br/>Changesets since last build: ' + \
                                    ','.join(map(lambda x: \
                                    ' <a href="' + req.href.changeset(x) + \
                                    '">[r' + x +']</a>', revisions)))
                            
                    yield (kind, href, title, date, author, message)


    def process_request(self, req):
        req.perm.assert_permission('CRUISECONTROL_VIEW')
        
        add_stylesheet(req, 'traccc/traccc.css')
        add_stylesheet(req, 'common/css/code.css')

        action = req.args.get('log', 'overview').replace('log','',1)
        req.hdf['title'] = 'CruiseControl'
        req.hdf['cc.baseLink'] = self.env.href.cruisecontrol()


        if action == 'overview':
            req.hdf['cc.data'] = self.get_all_builds()
            return 'traccc_overview.cs', None
        else:
            (logpaths, projectnames, statusfile, show_changesets) = self.get_cc_config()
            (pid, cc_id) = action.split('/')
            projectpath = logpaths[int(pid)]
            req.hdf['cc_id'] = cc_id
            filename = 'log' + cc_id + '.xml' #TODO: compressed?
            build = self.get_build_info(filename)
            req.hdf['cc.build'] = build
            
            req.hdf['cc.html_result'] = Markup(to_unicode(self.parse_logfile(projectpath + filename)))
            return 'traccc_details.cs', None

        raise TracError('TracCC has not been properly configured.')

    def get_permission_actions(self): 
        return ['CRUISECONTROL_VIEW'] 


    def parse_logfile(self, file):
        """Parse a cruise control log file.

        Returns an HTML string that represents the log a human readable format.
        """

        renderers = {}
        for renderer in self.log_renderers:
            elements = renderer.get_supported_elements();
            for element in elements:
                if element not in renderers or renderers[element].get_priority < renderer:
                    renderers[element] = renderer

        res = "";
        try:
            dom = minidom.parse(file)
            root = dom.documentElement
            if root.tagName != 'cruisecontrol':
                raise TracError('Unknown log file format.')

            for element in [n for n in root.childNodes if n.nodeType == n.ELEMENT_NODE]:
                if element.tagName in renderers:
                    res += renderers[element.tagName].render(element)
                else:
                    self.log.warn("No log formatter for %s found. Ignoring this part of the log file.", element.tagName)

        except expat.error, e:
            raise ParseError, e

        return res

    def get_project_builds(self, projectpath):
        if os.path.isdir(projectpath):
            loglist = filter(lambda x: x[0:3] == 'log' and (\
                (len(x) > self.__prefixLength + self.__datePatternLength + 3 and x[-4:] == '.xml') or \
                (len(x) > self.__prefixLength + self.__datePatternLength + 5 and x[-7:] == '.xml.gz')), \
            os.listdir(os.path.dirname(projectpath)))
            builds = []
            for logfile in loglist:
                build = self.get_build_info(logfile)
                builds.append(build)

            return builds
        else:
            raise TracError('The given cruisecontrol log path is invalid.');

    def parse_revisions(self, logfile):
        parser = make_parser()
        handler = RevisionFinderSAXHandler()
        parser.setContentHandler(handler)
        parser.parse(logfile)
        return handler.revs


    def parse_infoblock(self, file):
        parser = make_parser()
        handler = InfoBlockSAXHandler()
        parser.setContentHandler(handler)
        parser.parse(file)
        return handler.props
        #try:
        #    dom = minidom.parse(file)
        #    root = dom.documentElement
        #    if root.tagName != 'cruisecontrol':
        #        raise TracError('Unknown log file format.')

        #    xinfo = root.getElementsByTagName('info')
        #    if len(xinfo) > 0:
        #        xproperties = xinfo[0].getElementsByTagName('property')
        #        props = {}
        #        for xprop in xproperties:
        #            props[xprop.getAttribute('value')] = xprop.getAttribute('value')
        #        return props
        #    else:
        #        raise TracError("Logfile does not contain a info block.")
            
        #except expat.error, e:
        #    raise ParseError, e

        #return ""

def getText(node):
    return ''.join([c.nodeValue.encode('utf-8')
                    for c in node.childNodes
                    if c.nodeType in (3,4)])

def getElementText(node, elementName):
    e = node.getElementsByTagName(elementName)
    if len(e) != 0:
        return getText(e[0])
    else:
        return None

def parse_cc_date(datestr):
    return time.mktime(time.strptime(datestr.strip(), '%m/%d/%Y %H:%M:%S'))

    
class ModificationLogRenderer(Component):
    implements(ICruiseControlLogRenderer)

    def get_supported_elements(self):
        return ['modifications']

    def render(self, element):
        modifications = []
        for mod in element.getElementsByTagName('modification'):

            mod_data = {'action': getElementText(mod, 'action'),
                        'user' : getElementText(mod, 'user'),
                        'date' : pretty_timedelta(parse_cc_date(
                getElementText(mod, 'date'))),
                        'comment' : getElementText(mod, 'comment')}


            fileel = mod.getElementsByTagName('file')
            if len(fileel) != 0:
                mod_data['action'] = fileel[0].getAttribute('action')
                filename = getElementText(fileel[0], 'filename')
                if filename is not None:
                    mod_data['filename'] = filename
                    mod_data['filename_href'] = self.env.href.browser(filename)
                rev = getElementText(fileel[0], 'revision')
            
                if rev is not None:
                    mod_data['revision'] = rev
                    mod_data['revision_href'] = self.env.href.changeset(rev)
                        
            modifications.append(mod_data)
            
        hdf = HDFWrapper(loadpaths=Chrome(self.env).get_all_templates_dirs())
        hdf['modifications'] = modifications
        return hdf.render('traccc_modifications.cs')

    def get_priority(self):
        return 1

class BuildLogRenderer(Component):
    implements(ICruiseControlLogRenderer)

    def get_supported_elements(self):
        return ['build']

    def render(self, element):
        messages = []
        for xmsg in element.getElementsByTagName('message'):
            messages.append({'type': xmsg.getAttribute('priority'), 'msg':getText(xmsg)})

        hdf = HDFWrapper(loadpaths=Chrome(self.env).get_all_templates_dirs())
        hdf['cc.timetobuild'] = element.getAttribute('time');
        hdf['cc.messages'] = messages
        return hdf.render('traccc_buildmsgs.cs')

    def get_priority(self):
        return 1

class TestsuiteLogRenderer(Component):
    implements(ICruiseControlLogRenderer)

    def get_supported_elements(self):
        return ['testsuite']

    def render(self, element):
        tests = []
        for xtest in element.getElementsByTagName('testcase'):
            failure = xtest.getElementsByTagName('failure')
            data = {'name': xtest.getAttribute('name'), 'time':xtest.getAttribute('time')}
            if len(failure) == 0:
                data['failed'] = False
            else:
                data['failed'] = True
                data['msg'] = getText(failure[0])
            tests.append(data)

        hdf = HDFWrapper(loadpaths=Chrome(self.env).get_all_templates_dirs())
        hdf['cc.testtotaltime'] = element.getAttribute('time');
        hdf['cc.testtotalcount'] = element.getAttribute('tests');
        hdf['cc.testresults'] = tests
        hdf['cc.testsuite'] = element.getAttribute('name')
        
        return hdf.render('traccc_testresults.cs')

    def get_priority(self):
        return 1


class InfoBlockSAXHandler(ContentHandler):
    info_mode = False
    props = {}
    
    def startElement(self,name,attrs):
        if name == 'info' and not self.info_mode:
            self.info_mode = True
            return

        if self.info_mode and name == 'property':
            self.props[attrs['name']] = attrs['value']
            
    def endElement(self,name):
        if name == 'info' and self.info_mode:
            self.info_mode = False

class RevisionFinderSAXHandler(ContentHandler):

    def __init__(self):
        self.mod_mode = False
        self.rev_mode = False
        self.revs = []
        
    def startElement(self,name,attrs):
        if name == 'modification' and not self.mod_mode:
            self.mod_mode = True
            return

        if self.mod_mode and name == 'revision':
            self.rev_mode = True
            
    def endElement(self,name):
        if name == 'modification' and self.mod_mode:
            self.mod_mode = False

        if name == 'revision' and self.mod_mode and self.rev_mode:
            self.rev_mode = False


    def characters(self, data):
        if self.rev_mode:
            if data not in self.revs:
                print data
                self.revs.append(data)
