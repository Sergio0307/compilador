"""Pipeline de compilación de un archivo .ins (spec 1 y 2).

Encadena las tres fases en un único punto de entrada:

    texto -> [Lexer] -> tokens -> [Parser] -> SpeciesDef -> [Semántica] -> SpeciesDef

La aplicación y los tests llaman solo a compile_species(...) y no se
preocupan por las fases internas.
"""

from lang.lexer import Lexer
from lang.parser import Parser
from lang.semantics import SemanticAnalyzer
from lang.errors import SemanticErrors


def compile_species(source, filename="<input>"):
    """Compila un archivo .ins completo.

    Lanza LexError o ParseError en el primer fallo (no se puede continuar),
    y SemanticErrors con la lista completa si la fase semántica encuentra
    uno o más problemas. Si todo va bien, devuelve el SpeciesDef validado.
    """
    tokens = Lexer(source, filename).tokenize()             # Fase 1: léxica
    species = Parser(tokens, filename).parse_species()      # Fase 2: sintáctica
    errors = SemanticAnalyzer(filename).analyze(species)    # Fase 3: semántica
    if errors:
        raise SemanticErrors(errors)
    return species
