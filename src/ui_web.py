import os
from bottle import Bottle, template, static_file, error, request, response, view
from Database import ACNTBootDatabase
from queues import ui_webq

class UIWeb(Bottle):
    _db = None
    _games = None

    def __init__(self, name, gameslist):
        super(UIWeb, self).__init__()
        self.name = name
        self._games = gameslist
        #set up routes
        self.route('/', method="GET", callback=self.index)
        self.route('/static/<filepath:path>', method="GET", callback=self.serve_static)

    def start(self):
        self.db = ACNTBootDatabase('db.sqlite')
        self.run(host='0.0.0.0', port=8000, debug=False)

    def serve_static(self, filepath):
        if 'images/' in filepath and not os.path.isfile('static/'+filepath):
            return static_file('images/0.jpg', 'static')

        return static_file(filepath, 'static')

    def index(self):
        #Get filter information from DB and format it all nice for the template
        filter_groups = self.db.getAttributes()
        filter_values = []
        filters = []
        if self._games != None:
            return template('index', games=self._games, filter_groups=filter_groups, filter_values=filter_values, activefilters=filters)
        else:
            return template('index')

    #TODO: other routes