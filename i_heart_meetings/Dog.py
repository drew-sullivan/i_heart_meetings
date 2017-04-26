class Dog:

    kind = 'canine'

    def __init__(self, name):
        self.name = name


    def say_name(self):
        print("""
              *****woof*****
              {0}
              *****woof****
              """.format(self.name))
