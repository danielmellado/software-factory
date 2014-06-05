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

class zuul ($settings = hiera_hash('jenkins', ''), $gh = hiera('gerrit_url'), $hosts = hiera('hosts')){
  $gfqdn = "$gh.pub"
  $gip = $hosts[$gfqdn]['ip']
  package { 'apache2':
    ensure => present,
  }
  package {'libjs-jquery':
    ensure => present,
  }
  service {'apache2':
    ensure  => running,
    require => Package['apache2'],
  }
  user { 'zuul':
    ensure     => present,
    home       => '/home/zuul',
    shell      => '/bin/bash',
    gid        => 'zuul',
    managehome => true,
    require    => Group['zuul'],
  }

  group { 'zuul':
    ensure => present,
  }
  file {'/home/zuul/.ssh':
    ensure  => directory,
    mode    => '0777',
    owner   => 'zuul',
    group   => 'nogroup',
    require => [User['zuul'], Group['zuul']],
  }
  exec {'update_gerritip_knownhost':
    command => "/usr/bin/ssh-keyscan -p 29418 $gip >> /home/zuul/.ssh/known_hosts",
    logoutput => true,
    user => 'zuul',
    require => File['/home/zuul/.ssh']
  }

  exec {'update_gerrithost_knownhost':
    command => "/usr/bin/ssh-keyscan -p 29418 $gh >> /home/zuul/.ssh/known_hosts",
    logoutput => true,
    user => 'zuul',
    require => File['/home/zuul/.ssh']
  }
  file {'/usr/share/sf-zuul':
    ensure  => directory,
    mode    => '0640',
    owner   => 'root',
    group   => 'root',
  }
  file {'/usr/share/sf-zuul/layout.yaml':
    ensure => file,
    mode   => '0640',
    owner  => "root",
    group  => "root",
    require => File['/usr/share/sf-zuul'],
    source => 'puppet:///modules/zuul/layout.yaml',
  }
  file {'/var/log/zuul/':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'zuul',
    require => [User['zuul'], Group['zuul']],
  }
  file {'/etc/zuul':
    ensure  => directory,
    mode    => '0750',
    owner   => 'zuul',
    group   => 'zuul',
    require => [User['zuul'], Group['zuul']],
  }
  file {'/var/lib/zuul/':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'zuul',
    require => [User['zuul'], Group['zuul']],
  }
  file {'/var/lib/zuul/.ssh':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'nogroup',
    require => File['/var/lib/zuul/'],
  }
  file {'/var/lib/zuul/.ssh/id_rsa':
    ensure  => present,
    mode    => '0400',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/jenkins_rsa',
    require => File['/var/lib/zuul/.ssh'],
  }
  file {'/var/run/zuul/':
    ensure  => directory,
    mode    => '0755',
    owner   => 'zuul',
    group   => 'zuul',
    require => [User['zuul'], Group['zuul']],
  }
  file {'/etc/zuul/logging.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/logging.conf',
    require => File['/etc/zuul'],
  }
  file {'/etc/zuul/gearman-logging.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/gearman-logging.conf',
    require => File['/etc/zuul'],
  }
  file {'/etc/zuul/merger-logging.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    source  => 'puppet:///modules/zuul/merger-logging.conf',
    require => File['/etc/zuul'],
  }
  file {'/etc/zuul/zuul.conf':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    content => template('zuul/zuul.conf.erb'),
    require => [File['/etc/zuul/logging.conf'],
                File['/etc/zuul/gearman-logging.conf'],
                File['/etc/zuul/merger-logging.conf']],
  }
  file {'/etc/zuul/layout.yaml':
    ensure  => file,
    mode    => '0644',
    owner   => 'zuul',
    group   => 'zuul',
    require => [File['/etc/zuul'],
                Exec['init_config_repo']],
  }
  file {'/srv/zuul/etc/status/public_html/jquery.min.js':
    ensure => link,
    target => '/usr/share/javascript/jquery/jquery.min.js'
  }
  file {'/etc/init.d/zuul':
    ensure => present,
    mode   => '0555',
    owner  => 'root',
    group  => 'root',
    source => 'puppet:///modules/zuul/zuul.service'
  }
  file {'/etc/init.d/zuul-merger':
    ensure => present,
    mode   => '0555',
    group  => 'root',
    owner  => 'root',
    source => 'puppet:///modules/zuul/zuul-merger.service'
  }
  service {'zuul':
    ensure  => running,
    require => [File['/etc/init.d/zuul'],
                File['/etc/zuul/zuul.conf'],
                File['/srv/zuul/etc/status/public_html/jquery.min.js'],
                File['/etc/zuul/layout.yaml'],
                File['/var/log/zuul/'],
                File['/var/run/zuul/']]
  }
  service {'zuul-merger':
    ensure  => running,
    require => [File['/etc/init.d/zuul-merger'],
                File['/var/lib/zuul'],
                Service['zuul'],
                Exec['update_gerritip_knownhost'],
                Exec['update_gerrithost_knownhost']],
  }
  file {'/etc/apache2/sites-available/zuul':
    ensure => file,
    mode   => '0640',
    owner  => 'www-data',
    group  => 'www-data',
    source =>'puppet:///modules/zuul/zuul.site',
  }
  file { '/etc/apache2/sites-enabled/000-default':
    ensure => absent,
  }
  exec {'enable_zuul_site':
    command => 'a2ensite zuul',
    path    => '/usr/sbin/:/usr/bin/:/bin/',
    require => [File['/etc/apache2/sites-available/zuul'],
                Service['zuul'],
                Service['zuul-merger']],
    notify => Service[apache2],
  }
}
