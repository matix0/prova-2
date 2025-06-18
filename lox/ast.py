from abc import ABC
from dataclasses import dataclass
from typing import Callable, Optional

from lox.runtime import truthy

from .ctx import Ctx

# Declaramos nossa classe base num módulo separado para esconder um pouco de
# Python relativamente avançado de quem não se interessar pelo assunto.
#
# A classe Node implementa um método `pretty` que imprime as árvores de forma
# legível. Também possui funcionalidades para navegar na árvore usando cursores
# e métodos de visitação.
from .node import Node


#
# TIPOS BÁSICOS
#

# Tipos de valores que podem aparecer durante a execução do programa
Value = bool | str | float | None


class Expr(Node, ABC):
    """
    Classe base para expressões.

    Expressões são nós que podem ser avaliados para produzir um valor.
    Também podem ser atribuídos a variáveis, passados como argumentos para
    funções, etc.
    """


class Stmt(Node, ABC):
    """
    Classe base para comandos.

    Comandos são associdos a construtos sintáticos que alteram o fluxo de
    execução do código ou declaram elementos como classes, funções, etc.
    """


@dataclass
class Program(Node):
    """
    Representa um programa.

    Um programa é uma lista de comandos.
    """

    stmts: list[Stmt]

    def eval(self, ctx: Ctx):
        for stmt in self.stmts:
            stmt.eval(ctx)


#
# EXPRESSÕES
#
@dataclass
class BinOp(Expr):
    """
    Uma operação infixa com dois operandos.

    Ex.: x + y, 2 * x, 3.14 > 3 and 3.14 < 4
    """

    left: Expr
    right: Expr
    op: Callable[[Value, Value], Value]

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)
        right_value = self.right.eval(ctx)
        return self.op(left_value, right_value)


@dataclass
class Var(Expr):
    """
    Uma variável no código

    Ex.: x, y, z
    """

    name: str

    def eval(self, ctx: Ctx):
        try:
            return ctx[self.name]
        except KeyError:
            raise NameError(f"variável {self.name} não existe!")


@dataclass
class Literal(Expr):
    """
    Representa valores literais no código, ex.: strings, booleanos,
    números, etc.

    Ex.: "Hello, world!", 42, 3.14, true, nil
    """

    value: Value

    def eval(self, ctx: Ctx):
        return self.value


@dataclass
class And(Expr):
    """
    Uma operação infixa com dois operandos.

    Ex.: x and y
    """
    left: Expr
    right: Expr

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)
        if not truthy(left_value):
            return left_value
        return self.right.eval(ctx)

@dataclass
class Or(Expr):
    """
    Uma operação infixa com dois operandos.
    Ex.: x or y
    """
    left: Expr
    right: Expr

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)
        if truthy(left_value):
            return left_value
        return self.right.eval(ctx)

@dataclass
class UnaryOp(Expr):
    """
    Uma operação prefixa com um operando.

    Ex.: -x, !x
    """
    op: Callable
    expr: Expr

    def eval(self, ctx):
        return self.op(self.expr.eval(ctx))

@dataclass
class Call(Expr):
    """
    Uma chamada de função

    Ex.: fat(42)
    """
    callee: Expr
    params: list[Expr]
    
    def eval(self, ctx: Ctx):
        func = self.callee.eval(ctx)
        params = [param.eval(ctx) for param in self.params]
        if callable(func):
            return func(*params)
        raise TypeError(f"{self.callee} não é uma função!")


@dataclass
class This(Expr):
    """
    Acesso ao `this`.

    Ex.: this
    """


@dataclass
class Super(Expr):
    """
    Acesso a method ou atributo da superclasse.

    Ex.: super.x
    """


@dataclass
class Assign(Expr):
    """
    Atribuição de variável.

    Ex.: x = 42
    """
    name: str
    value: Expr

    def eval(self, ctx: Ctx):
        val = self.value.eval(ctx)
        if is_fortran_int(self.name):
            try:
                val = int(val)
            except Exception:
                pass
        ctx[self.name] = val
        return val

@dataclass
class Getattr(Expr):
    """
    Acesso a atributo de um objeto.

    Ex.: x.y
    """
    obj: Expr
    attr: str

    def eval(self, ctx: Ctx):
        obj_value = self.obj.eval(ctx)
        try:
            return getattr(obj_value, self.attr)
        except AttributeError:
            obj_type = type(obj_value).__name__
            raise AttributeError(f"Objeto do tipo '{obj_type}' não possui o atributo '{self.attr}'")

@dataclass
class Setattr(Expr):
    """
    Atribuição de atributo de um objeto.

    Ex.: x.y = 42
    """
    obj: Expr
    attr: str
    value: Expr

    def eval(self, ctx: Ctx):
        obj_value = self.obj.eval(ctx)
        val = self.value.eval(ctx)
        if is_fortran_int(self.attr):
            try:
                val = int(val)
            except Exception:
                pass
        setattr(obj_value, self.attr, val)
        return val

#
# COMANDOS
#
@dataclass
class Print(Stmt):
    """
    Representa uma instrução de impressão.

    Ex.: print "Hello, world!";
    """
    expr: Expr
    
    def eval(self, ctx: Ctx):
        value = self.expr.eval(ctx)
        print(lox_str(value))


@dataclass
class Return(Stmt):
    """
    Representa uma instrução de retorno.

    Ex.: return x;
    """


@dataclass
class VarDef(Stmt):
    """
    Representa uma declaração de variável.

    Ex.: var x = 42;
    """
    name: str
    value: Expr
    type_hint: Optional[str] = None

    def eval(self, ctx: Ctx):
        val = self.value.eval(ctx)
        if is_fortran_int(self.name):
            try:
                val = int(val)
            except Exception:
                pass
        ctx.scope[self.name] = val


@dataclass
class If(Stmt):
    """
    Representa uma instrução condicional.

    Ex.: if (x > 0) { ... } else { ... }
    """
    condition: Expr
    then_stmt: Stmt
    else_stmt: Stmt

    def eval(self, ctx: Ctx):
        condition_value = self.condition.eval(ctx)
        if truthy(condition_value):
            self.then_stmt.eval(ctx)
        else:
            self.else_stmt.eval(ctx)


@dataclass
class While(Stmt):
    """
    Representa um laço de repetição.

    Ex.: while (x > 0) { ... }
    """
    condition: Expr
    body: Stmt

    def eval(self, ctx: Ctx):
        while truthy(self.condition.eval(ctx)):
            self.body.eval(ctx)


@dataclass
class Block(Stmt):
    """
    Representa bloco de comandos.

    Ex.: { var x = 42; print x;  }
    """
    declarations: list[Stmt]

    def eval(self, ctx: Ctx):
        for declaration in self.declarations:
            declaration.eval(ctx)


@dataclass
class Function(Stmt):
    """
    Representa uma função.

    Ex.: fun f(x, y) { ... }
    """
    name: str
    params: list[tuple[str, Optional[str]]]  # (nome, tipo)
    body: Block
    return_type: Optional[str] = None        # <-- Adicionado


@dataclass
class Class(Stmt):
    """
    Representa uma classe.

    Ex.: class B < A { ... }
    """


@dataclass
class ExprStmt(Stmt):
    """
    Representa uma expressão usada como statement.
    
    Ex.: x = 42; (quando usado como statement)
    """
    expr: Expr
    
    def eval(self, ctx: Ctx):
        self.expr.eval(ctx)


def lox_str(value):
    """
    Converte um valor Python para sua representação string no Lox.
    """
    if value is True:
        return "true"
    elif value is False:
        return "false"
    elif value is None:
        return "nil"
    elif isinstance(value, float) and value.is_integer():
        return str(int(value))
    elif isinstance(value, str):
        return value
    else:
        return str(value)

def is_fortran_int(name: str) -> bool:
    return name and name[0] in "ijklmn"