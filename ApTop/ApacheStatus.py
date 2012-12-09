__author__ = "branko@toic.org (http://toic.org)"
__date__ = "Dec 8, 2012 09:00 PM$"
__version__ = "0.1.0"

import ConfigParser
import os
import re
import sys
from operator import itemgetter


"""
Now lets import some dependencies and check their versions
We need at least version 3.0.7a of BeautifulSoup
"""
try:
    import lxml.html
except:
    print "No lxml package found..."
    print "please install lxml >= 3.x.x"
    print "best way to install easy_install lxml"
    sys.exit(1)

class ApacheStatus(object):
    def __init__(self):
        """
        Try to detect config file location, trying to use user defined config
        in home path ~/.aptop.conf or /etc/aptop.conf then
        """
        homedir = os.path.expanduser('~')

        if os.path.isfile(os.path.join(homedir, '.aptop.conf')):
            self.configfile = os.path.join(homedir, '.aptop.conf')
        elif os.path.isfile('/etc/aptop.conf'):
            self.configfile = '/etc/aptop.conf'
        else:
            self.configfile = None

        """ 
        Let's populate some defaults if no config file is found
        """
        if not self.configfile:
            self.status_url = 'http://localhost/server-status'
            self.refresh = '5'
        else:
            config = ConfigParser.ConfigParser()
            config.readfp(open(self.configfile))
            try:
                self.status_url = config.get('aptop', 'status_url')
                self.refresh = config.get('aptop', 'refresh')
            except:
                self.status_url = 'http://localhost/server-status'
                self.refresh = '5'
        self.r = re.compile('<table border="0">(.*?)</table>')
        try:
            self.tree = lxml.html.parse(self.status_url)
        except:
            print "Apache not running?"
            sys.exit(1)

    def refresh_rate(self):
        """
        (NoneType) -> int
        
        Returns parsed refresh time interval as int
        """
        return int(self.refresh)

    def fetch_status(self):
        """
        (NoneType) -> NoneType
        
        Refetching of data
        """
        if self.tree:
            old_tree = self.tree
        try:

            self.tree = lxml.html.parse(self.status_url)
        except:
            self.tree = old_tree

    def verify_mod_status(self):
        """
        (str) -> boolean
        
        Checks the data string for Apache Status title and returns true or
        false
        """
        return self.tree.find('.//title').text == 'Apache Status'

    def count_by_vhost(self, data):
        """
        (str) -> list of tuple
        
        Counts the active concurent connections by vhosts and returns an ordered
        list of tuples containing vhost name and number of active connections
        """
        vstatus = {}
        for status in data:
            if status['M'] != '_' and status['M'] != '.':
                if status['VHost'] in vstatus:
                    vstatus[status['VHost']] += 1
                else:
                    vstatus[status['VHost']] = 1
        items = vstatus.items()
        items.sort(key=itemgetter(1), reverse=True)

        return items

    def parse_vhosts(self):
        """
        (str) -> list of dict
        
        Parses a apache status from internal class self.tree variable
        and returns list ofdict containing all vhost informations from 
        mod_status
        
        """
        m = self.r.search(lxml.html.tostring(self.tree).replace('\n', ''))
        s = '<table>' + m.group(1) + '</table>'
        tree = lxml.html.fromstring(s)
        vhost_status = []
        headers = tree.findall('.//th')
        h2 = [s.text for s in headers]
        for row in tree.findall('.//tr')[1:]: # this is header, excluding
            d = [s.text for s in row.findall('.//td')]
            vhost_status.append(dict(zip(h2, d)))
        return vhost_status

    def parse_header(self):
        """
        (NoneType) -> list
        
        Returns a list of header status variables from apache status page
        """

        headers = [h.text.replace('\n', '') for h in self.tree.findall('.//dt')]
        return headers
