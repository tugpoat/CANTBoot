from bottle import Bottle

class UI_Web(Bottle):
    def __init__(self, name):
        super(MyApp, self).__init__()
        self.name = name
        #set up routes
        self.route('/', callback=self.index)

    def index(self):
        return self.template('index')

    #TODO: other routes
