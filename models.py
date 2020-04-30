from py2neo import Graph, Node, Relationship
from passlib.hash import bcrypt
from datetime import datetime
import os
import uuid

graph = Graph("bolt://localhost:7687", auth=("neo4j", "1234"))

class User:
    def __init__(self, username,password):
        self.username = username
        self.password = password

    def find(self):
        #user = graph.find_one('Login', 'name', self.username)
        #user = Graph.match('Login','name')
        #user = graph.match_one('Login','username')
        node1 = graph.evaluate('MATCH (x) WHERE x.name="admin" AND x.password="admin"  RETURN(x)')
        print('GİRDİ')
        print(node1)
        print(type(node1))
        return node1

    def verify_password(self, password):
        user = self.find()
        if user:
            return bcrypt.verify(password, user['password'])
        else:
            return False
