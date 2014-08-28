#!/usr/bin/python
#
# Copyright (C) 2014 eNovance SAS <licensing@enovance.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import config
import json
import os
import requests
import shutil
import yaml
import urllib

from utils import Base
from utils import create_random_str
from utils import ManageSfUtils
from utils import GerritUtil
from utils import RedmineUtil

class TestUserdata(Base):
    @classmethod
    def setUpClass(cls):
        cls.msu = ManageSfUtils(config.GATEWAY_HOST, 80)
        with open(os.environ['SF_ROOT'] + "/build/hiera/redmine.yaml") as f:
            ry = yaml.load(f)
        cls.redmine_api_key = ry['redmine']['issues_tracker_api_key']

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.projects = []
        self.rm = RedmineUtil(config.REDMINE_SERVER,
                              apiKey=self.redmine_api_key)
        self.gu = GerritUtil(config.GERRIT_SERVER,
                             username=config.ADMIN_USER)

    def tearDown(self):
        for name in self.projects:
            self.msu.deleteProject(name,
                                   config.ADMIN_USER)

    def createProject(self, name, user, options=None,
                      cookie=None):
        self.msu.createProject(name, user, options,
                               cookie)
        self.projects.append(name)

    def verify_userdata_gerrit(self, login, lastname, email):
        # Now check that the correct data was stored in Gerrit
        url = "http://gerrit.%s/api/accounts/%s" % (os.environ['SF_SUFFIX'],
                                                    login)
        resp=requests.get(url)
        data = json.loads(resp.content[4:])
        self.assertEqual(lastname, data.get('name'))
        self.assertEqual(email, data.get('email'))

    def verify_userdata_redmine(self, login, lastname, email):
        headers = {'X-Redmine-API-Key': self.redmine_api_key,
                   'Content-Type': 'application/json'}
        user = {}
        # We need to iterate over the existing users
        for i in range(15):  # check only the first 15 user ids
            url = 'http://api-redmine.%s/users/%d.json' % (os.environ['SF_SUFFIX'], i)
            resp=requests.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                u = data.get('user')
                if u.get('login') == login:
                    user = u
                    break
        self.assertEqual(lastname, user.get('lastname'))
        self.assertEqual(email, user.get('mail'))

    def test_userdata_ldap(self):
        """ Functional tests to verify the ldap user
        """
        self.user5_email = 'user5@%s' % os.environ['SF_SUFFIX']
        data = {'username': 'user5', 'password': 'userpass', 'back': '/'}
        # Trigger a login as user5, this should fetch the userdata from LDAP
        url = "http://%s/auth/login/" % config.GATEWAY_HOST
        resp=requests.post(url, data=data, allow_redirects=False)

        # verify if ldap user is created in gerrit and redmine
        self.verify_userdata_gerrit('user5', 'Demo user5', self.user5_email)
        self.verify_userdata_redmine('user5', 'Demo user5', self.user5_email)

    def test_userdata_github(self):
        """ Functional tests to verify the github user
        """
        self.user6_email = 'user6@%s' % os.environ['SF_SUFFIX']
        config.USERS['user6'] = {"password": "userpass",
                                 "email": "user6@tests.dom",
                                 "pubkey": config.USER_6_PUB_KEY,
                                 "privkey": config.USER_6_PRIV_KEY,
                                 "auth_cookie": "",
                                }
        # Trigger a oauth login as user6,
        # this should fetch the userdata from oauth mock
        # allow_redirects=False is not working for GET
        github_url = "http://%s/auth/login/github" % config.GATEWAY_HOST
        url = github_url + "?" + \
               urllib.urlencode({'username': 'user6',
                                  'password': 'userpass',
                                  'back': '/'})
        resp=requests.get(url)
        for r in resp.history:
            if r.cookies:
                for cookie in r.cookies:
                    if 'auth_pubtkt' == cookie.name:
                        config.USERS['user6']['auth_cookie'] = cookie.value
                        break
            if config.USERS['user6']['auth_cookie'] != "":
                break
            
        # verify if github user is created in gerrit and redmine
        self.verify_userdata_gerrit('user6', 'Demo user6', self.user6_email)
        self.verify_userdata_redmine('user6', 'Demo user6', self.user6_email)