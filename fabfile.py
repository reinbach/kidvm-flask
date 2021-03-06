from __future__ import with_statement
from fabric.api import *

env.app = 'kidvm'
env.hosts = ['web1']
env.sites_dir = '/opt/sites/'
env.app_dir = env.sites_dir + env.app
env.repo = "https://github.com/reinbach/kidvm-flask.git"
env.nginx_conf_dir = "/opt/nginx/conf/sites/"
env.uwsgi_conf_dir = "/etc/uwsgi/apps/"
env.user = 'root'
env.key_filename = '/home/greg/.ssh/id_digitalocean'

def install():
    """Installs app on server"""
    with settings(user="root"):
        run("virtualenv --distribute --no-site-packages -p python2 {app_dir}".format(app_dir=env.app_dir))
        with cd(env.app_dir):
            # clone repo
            run("git clone {repo} master".format(repo=env.repo))
            with cd("master"):
                run("source {app_dir}/bin/activate && pip install -r requirements.txt".format(app_dir=env.app_dir))
                # setup config file
                run("cp {app_dir}/master/nginx.conf {nginx_conf_dir}{app}.conf".format(
                    app_dir=env.app_dir,
                    nginx_conf_dir=env.nginx_conf_dir,
                    app=env.app
                ))
                run("cp {app_dir}/master/uwsgi.ini {uwsgi_conf_dir}{app}.ini".format(
                    app_dir=env.app_dir,
                    uwsgi_conf_dir=env.uwsgi_conf_dir,
                    app=env.app
                ))
                run("cp config_default.py config.py")
        run("systemctl reload uwsgi")
        run("systemctl reload nginx")

def update():
    """Updates code base on server"""
    with settings(user="root"):
        with cd("{app_dir}/master".format(app_dir=env.app_dir)):
            with settings(warn_only=True):
                run("git pull")
            run("source {app_dir}/bin/activate && pip install -r requirements.txt".format(app_dir=env.app_dir))
            run("cp {app_dir}/master/nginx.conf {nginx_conf_dir}{app}.conf".format(
                app_dir=env.app_dir,
                nginx_conf_dir=env.nginx_conf_dir,
                app=env.app
            ))
            run("cp {app_dir}/master/uwsgi.ini {uwsgi_conf_dir}{app}.ini".format(
                app_dir=env.app_dir,
                uwsgi_conf_dir=env.uwsgi_conf_dir,
                app=env.app
            ))
        run("systemctl reload uwsgi")
        run("systemctl reload nginx")