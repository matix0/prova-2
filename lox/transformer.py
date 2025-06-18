"""
Implementa o transformador da árvore sintática que converte entre as representações

    lark.Tree -> lox.ast.Node.

A resolução de vários exercícios requer a modificação ou implementação de vários
métodos desta classe.
"""

from typing import Callable
from lark import Transformer, v_args

from . import runtime as op
from .ast import *


def op_handler(op: Callable):
    """
    Fábrica de métodos que lidam com operações binárias na árvore sintática.

    Recebe a função que implementa a operação em tempo de execução.
    """

    def method(self, left, right):
        return BinOp(left, right, op)

    return method


@v_args(inline=True)
class LoxTransformer(Transformer):
    # Programa
    def program(self, *declarations):
        return Program(list(declarations))

    # Declarações
    def var_decl(self, name, value=None):
        # Se não há valor inicial, usa nil (None)
        if value is None:
            value = Literal(None)
        return VarDef(name.name if isinstance(name, Var) else str(name), value)

    # Comandos
    def print_cmd(self, expr):
        return Print(expr)

    def block(self, *declarations):
        return Block(list(declarations))

    def if_stmt(self, condition, then_stmt, else_stmt=None):
        # Se não há else, cria um bloco vazio
        if else_stmt is None:
            else_stmt = Block([])
        return If(condition, then_stmt, else_stmt)

    def while_stmt(self, condition, body):
        return While(condition, body)

    def for_stmt(self, init, condition, increment, body):
        """
        Converte for em while usando açúcar sintático:
        for (init; cond; incr) stmt => { init; while (cond) { stmt; incr; } }
        """
        # Se não há condição, usa true (loop infinito)
        if condition is None:
            condition = Literal(True)
        
        # Cria o corpo do while: { stmt; incr; }
        while_body_stmts = [body]
        if increment is not None:
            # Converte a expressão de incremento em um statement
            while_body_stmts.append(ExprStmt(increment))
        
        while_body = Block(while_body_stmts)
        while_loop = While(condition, while_body)
        
        # Cria o bloco externo: { init; while(...) }
        block_stmts = []
        if init is not None:
            block_stmts.append(init)
        block_stmts.append(while_loop)
        
        return Block(block_stmts)

    def for_init(self, init=None):
        """Processa a parte de inicialização do for"""
        return init

    def for_cond(self, condition=None):
        """Processa a condição do for"""
        return condition

    def for_incr(self, increment=None):
        """Processa o incremento do for"""
        return increment

    # Operações matemáticas básicas
    mul = op_handler(op.mul)
    div = op_handler(op.truediv)
    sub = op_handler(op.sub)
    add = op_handler(op.add)

    # Comparações
    gt = op_handler(op.gt)
    lt = op_handler(op.lt)
    ge = op_handler(op.ge)
    le = op_handler(op.le)
    eq = op_handler(op.eq)
    ne = op_handler(op.ne)

    # Outras expressões
    def call(self, callee, params):
        return Call(callee, params)
        
    def params(self, *args):
        params = list(args)
        return params

    def VAR(self, token):
        name = str(token)
        return Var(name)

    def NUMBER(self, token):
        num = float(token)
        return Literal(num)
    
    def STRING(self, token):
        text = str(token)[1:-1]
        return Literal(text)
    
    def NIL(self, _):
        return Literal(None)

    def BOOL(self, token):
        return Literal(token == "true")
    
    def getattr(self, obj, attr):
        return Getattr(obj, attr.name if isinstance(attr, Var) else str(attr))
    
    def not_(self, expr):
        return UnaryOp(op=lambda x: not truthy(x), expr=expr)

    def neg(self, expr):
        return UnaryOp(op=lambda x: -x, expr=expr)
    
    def and_(self, left, right):
        return And(left, right)

    def or_(self, left, right):
        return Or(left, right)
    
    def assign(self, var, value):
        return Assign(var.name, value)
    
    def setattr(self, obj, attr, value):
        return Setattr(obj, attr.name if isinstance(attr, Var) else str(attr), value)