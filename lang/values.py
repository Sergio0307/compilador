"""Reglas de valor del lenguaje Instinct (spec 2.5).

En la base solo existen dos tipos: enteros y texto. Aquí viven la noción
de verdad y los operadores. Cada operador es un objeto que sabe validarse
(`check`) y aplicarse (`apply`); las bases de categoría ajustan la
validación una sola vez, sin repetirla por operador (sección 5: nada de
cadenas de ifs). Ni estas clases ni las funciones conocen al intérprete
ni al mundo: reciben valores, devuelven valores, o lanzan RuntimeFault con
la línea del código que falló.
"""

from abc import ABC, abstractmethod

from lang.errors import RuntimeFault


# --------------------------------------------------------------------------
# Nociones comunes
# --------------------------------------------------------------------------

def is_truthy(value):
    """Verdad al estilo Instinct (spec 2.5): falso es el entero 0 y el texto
    vacío; todo lo demás es verdadero. No compara tipos, así que se traga
    cualquier valor (lo usan `and`, `or`, `not` y la condición de `if`)."""
    if isinstance(value, int):
        return value != 0
    if isinstance(value, str):
        return value != ""
    return True   # en la base no hay más tipos


def type_name(value):
    """Nombre del tipo para los mensajes de error."""
    return "texto" if isinstance(value, str) else "número"


def _check_same_type(op, a, b, line):
    """Todos los operadores salvo los lógicos exigen el mismo tipo a los dos
    lados (spec 2.5); si no, error en tiempo de ejecución."""
    if type(a) is not type(b):
        raise RuntimeFault(
            f"no se puede aplicar '{op}' a {type_name(a)} y {type_name(b)}",
            line=line,
        )


def _check_number(op, value, line):
    """La aritmética y las comparaciones de orden solo aceptan números."""
    if isinstance(value, str):
        raise RuntimeFault(f"el operador '{op}' no admite texto", line=line)


def _reject_zero(divisor, line):
    """La división y el resto rechazan el divisor 0 (spec 2.8)."""
    if divisor == 0:
        raise RuntimeFault("división por cero", line=line)


# --------------------------------------------------------------------------
# Operadores binarios
# --------------------------------------------------------------------------

class BinaryOperator(ABC):
    """Un operador de dos operandos. `symbol` es su nombre en el lenguaje."""

    symbol = ""

    def __call__(self, a, b, line=None):
        self.check(a, b, line)     # validación
        return self.apply(a, b)    # efecto

    def check(self, a, b, line):
        """Por defecto, mismo tipo a los dos lados; las categorías afinan."""
        _check_same_type(self.symbol, a, b, line)

    @abstractmethod
    def apply(self, a, b):
        """Aplica el operador (los tipos ya están validados)."""


class LogicalOperator(BinaryOperator):
    """and / or: no comparan nada, se tragan cualquier combinación de tipos."""
    def check(self, a, b, line):
        pass


class And(LogicalOperator):
    symbol = "and"

    def apply(self, a, b):
        return 1 if (is_truthy(a) and is_truthy(b)) else 0


class Or(LogicalOperator):
    symbol = "or"

    def apply(self, a, b):
        return 1 if (is_truthy(a) or is_truthy(b)) else 0


class EqualityOperator(BinaryOperator):
    """== / !=: mismo tipo requerido (heredan el check por defecto)."""


class Eq(EqualityOperator):
    symbol = "=="

    def apply(self, a, b):
        return 1 if a == b else 0


class Ne(EqualityOperator):
    symbol = "!="

    def apply(self, a, b):
        return 1 if a != b else 0


class NumericOperator(BinaryOperator):
    """Mismo tipo y además solo números (aritmética y comparaciones de orden)."""

    def check(self, a, b, line):
        super().check(a, b, line)
        _check_number(self.symbol, a, line)


class OrderOperator(NumericOperator):
    """<, <=, >, >=: devuelven 1/0."""


class Lt(OrderOperator):
    symbol = "<"

    def apply(self, a, b):
        return 1 if a < b else 0


class Le(OrderOperator):
    symbol = "<="

    def apply(self, a, b):
        return 1 if a <= b else 0


class Gt(OrderOperator):
    symbol = ">"

    def apply(self, a, b):
        return 1 if a > b else 0


class Ge(OrderOperator):
    symbol = ">="

    def apply(self, a, b):
        return 1 if a >= b else 0


class ArithmeticOperator(NumericOperator):
    """+ - * / %: enteros; '/' es división entera y '%' el resto de Python."""


class Add(ArithmeticOperator):
    symbol = "+"

    def apply(self, a, b):
        return a + b


class Sub(ArithmeticOperator):
    symbol = "-"

    def apply(self, a, b):
        return a - b


class Mul(ArithmeticOperator):
    symbol = "*"

    def apply(self, a, b):
        return a * b


class Div(ArithmeticOperator):
    symbol = "/"

    def check(self, a, b, line):
        super().check(a, b, line)
        _reject_zero(b, line)

    def apply(self, a, b):
        return a // b


class Mod(ArithmeticOperator):
    symbol = "%"

    def check(self, a, b, line):
        super().check(a, b, line)
        _reject_zero(b, line)

    def apply(self, a, b):
        return a % b


# --------------------------------------------------------------------------
# Operadores unarios
# --------------------------------------------------------------------------

class UnaryOperator(ABC):
    """Un operador de un solo operando: menos unario y not."""

    symbol = ""

    def __call__(self, value, line=None):
        self.check(value, line)
        return self.apply(value)

    def check(self, value, line):
        """Por defecto no valida nada; `Neg` exige número."""

    @abstractmethod
    def apply(self, value):
        """Aplica el operador (el tipo ya está validado)."""


class Neg(UnaryOperator):
    symbol = "-"

    def check(self, value, line):
        _check_number(self.symbol, value, line)

    def apply(self, value):
        return -value


class Not(UnaryOperator):
    symbol = "not"

    def apply(self, value):
        return 0 if is_truthy(value) else 1


# --------------------------------------------------------------------------
# Registros y puntos de entrada
# --------------------------------------------------------------------------

BINARY_OPERATORS = {op.symbol: op for op in (
    And(), Or(), Eq(), Ne(), Lt(), Le(), Gt(), Ge(),
    Add(), Sub(), Mul(), Div(), Mod(),
)}

UNARY_OPERATORS = {op.symbol: op for op in (Neg(), Not())}


def binary(op, a, b, line=None):
    """Aplica un operador binario a dos valores ya evaluados."""
    operator = BINARY_OPERATORS.get(op)
    if operator is None:
        raise RuntimeFault(f"operador desconocido '{op}'", line=line)
    return operator(a, b, line)


def unary(op, value, line=None):
    """Aplica un operador unario: '-x' y 'not x'."""
    operator = UNARY_OPERATORS.get(op)
    if operator is None:
        raise RuntimeFault(f"operador unario desconocido '{op}'", line=line)
    return operator(value, line)
