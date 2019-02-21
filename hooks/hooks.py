#!/usr/bin/env python3

import hashlib
import json
import os
import sys

_path = os.path.dirname(os.path.realpath(__file__))
_root = os.path.abspath(os.path.join(_path, '..'))


def _add_path(path):
    if path not in sys.path:
        sys.path.insert(1, path)


_add_path(_root)

from subprocess import check_call

from charmhelpers.core import unitdata

from charmhelpers.core.hookenv import (
    config as config_get,
    Hooks,
    UnregisteredHookError,
    config,
    log,
    DEBUG,
    INFO,
    WARNING,
    relation_get,
    relation_ids,
    relation_set,
    related_units,
    status_set,
    open_port,
    is_leader,
    relation_id,
)

from charmhelpers.core.host import (
    service_pause,
    service_stop,
    service_start,
    service_restart,
)

from charmhelpers.payload.execd import execd_preinstall

from charmhelpers.fetch import (
    apt_install, apt_update,
    filter_installed_packages
)

from charmhelpers.contrib.openstack.ha.utils import (
    generate_ha_relation_data,
)

from jinja2 import Environment, FileSystemLoader


hooks = Hooks()
package_list=["ntp"]
NTP_CONF_FILE="/etc/ntp.conf"

@hooks.hook('install.real')
def install():
    status_set("maintenance", "Installing apt packages...")
    execd_preinstall()
    apt_update()
    apt_install(package_list, fatal=True)
    config_changed()


def build_conf_file():
    #if len(config_get("iburst_servers"))==0 and len(config_get("iburst_pools"))==0:
    #    block_service("No pools or NTP servers defined")
        
    iburst_srvs=config_get("iburst_servers").split(",")
    iburst_pools=config_get("iburst_pools").split(",")

    file_loader = FileSystemLoader("templates")
    env = Environment(loader=file_loader)
    fe_part = env.get_template("ntp.conf.templ")
    
    with open(NTP_CONF_FILE,"w") as f:
        cfg=[]
        res=[]
        pcount=0
        for i in iburst_srvs:
            cfg.append("server {} iburst".format(i))
        for i in iburst_pools:
            cfg.append("pool {} iburst".format(i))
        res.append(fe_part.render(servers_pools_config=cfg))
        f.write("".join(res))
        f.close()
        
    service_restart("ntp")
    
    
@hooks.hook('config-changed')
def config_changed():
    status_set("maintenance", "Resetting configs...")
    build_conf_file()
    update_status()

    
## TODO: check if NTP is not working correctly
#@hooks.hook('update-status')
def update_status():
    ## ALL GOOD, status = active
    ## ALL BAD, status = blocked/error
    status_set("active","Time is an illusion...")
    return
    

        
def main():
    try:
        hooks.execute(sys.argv)
    except UnregisteredHookError as e:
        log('Unknown hook {} - skipping.'.format(e))


if __name__ == '__main__':
    main()
