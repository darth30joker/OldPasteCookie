#!/usr/bin/env python
"""

"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

def make_application():
    from pastecookie import app
    from pastecookie import db
    from pastecookie import oid
    from pastecookie import babel

    from pastecookie.application import config_app
    from pastecookie.application import dispatch_handlers
    from pastecookie.application import dispatch_views

    config_app(app, db, oid, babel,
               '/home/davidx/Sites/alpha.daimaduan.com/website/config.cfg')
    dispatch_handlers(app)
    dispatch_views(app)
    return app

application = make_application()

if __name__ == "__main__":
    application.run(host="0.0.0.0")
