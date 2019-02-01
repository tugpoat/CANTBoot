class PyBus (object):

    def __init__(self,):
        self.clear()
        
    def clear(self):
        self.subscriptions = {}
    
    def subscribe(self, subject, owner, func):
        if not self.subscriptions.has_key(owner):
            self.subscriptions[owner] = {}
        self.subscriptions[owner][subject] = func
        
    def has_subscription(self, owner, subject):
        return self.subscriptions.has_key(owner) and self.subscriptions[owner].has_key(subject)
        
    def publish(self, subject, *args, **kwargs):
        for owner in self.subscriptions.keys():
            if self.has_subscription(owner, subject):
                self.subscriptions[owner][subject](*args, **kwargs)
