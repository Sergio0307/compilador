#para probar q funcione todo el lexer
from lang.lexer import Lexer                                  
from lang.tokens import TokenType
from .errors import LexError 

source = '''creature Uruk
faction isengard
health 80

start:
if health < 20 goto flee
if enemy_dist == 1 goto bite
say("meat is back")
goto start

'''

tokens = Lexer(source, "uruk.ins").tokenize()
for t in tokens:
    print(t)
