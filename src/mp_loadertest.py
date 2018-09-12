from netloader import Loader
from multiprocessing import *

def subcb(*args, **kwargs):
    for x in args:
        print(x)

if __name__ == '__main__':
    q = Manager().Queue()
    p = Loader(q, "home/niggas.bin", "localhost")
    p.start()
    print("queueedsfskljfkdl")
    
    print(q.get())    # prints "[42, None, 'hello']"
    print(q.get())    # prints "[42, None, 'hello']"
    print(q.get())    # prints "[42, None, 'hello']"

