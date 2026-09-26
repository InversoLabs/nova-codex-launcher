"""Bounded interpreter, NOT Python exec/eval or a general repository sandbox.

Only pure expressions and simple function bodies are accepted. No imports,
filesystem, reflection, recursion, shell, network, or arbitrary call targets.
"""
import ast
import operator

class Rejected(ValueError):
    pass

class Returned(Exception):
    def __init__(self, value):
        self.value = value

BIN = {ast.Add:operator.add, ast.Sub:operator.sub, ast.Mult:operator.mul,
       ast.Div:operator.truediv, ast.FloorDiv:operator.floordiv, ast.Mod:operator.mod}
CMP = {ast.Eq:operator.eq, ast.NotEq:operator.ne, ast.Lt:operator.lt,
       ast.LtE:operator.le, ast.Gt:operator.gt, ast.GtE:operator.ge,
       ast.Is:operator.is_, ast.IsNot:operator.is_not}
FUNCS = {'min':min, 'max':max, 'sum':sum, 'len':len, 'abs':abs,
         'sorted':sorted, 'all':all, 'any':any, 'bool':bool}

def bounded(value):
    if type(value) not in (str, int, float, bool, list, tuple, type(None)):
        raise Rejected('Unsupported value type')
    if isinstance(value, (str,list,tuple)) and len(value) > 1000:
        raise Rejected('Value too large')
    if type(value) is int and value.bit_length() > 128:
        raise Rejected('Integer too large')
    return value

class Interpreter:
    def __init__(self):
        self.budget = 5000

    def expr(self, n, env):
        self.budget -= 1
        if self.budget < 0:
            raise Rejected('Step budget exceeded')
        return bounded(self._expr(n, env))

    def _expr(self, n, e):
        if isinstance(n, ast.Constant): return n.value
        if isinstance(n, ast.Name): return e[n.id]
        if isinstance(n, (ast.List,ast.Tuple)):
            return [self.expr(x,e) for x in n.elts]
        if isinstance(n, ast.BinOp) and type(n.op) in BIN:
            a,b = self.expr(n.left,e),self.expr(n.right,e)
            if isinstance(n.op, ast.Mult) and (isinstance(a,(str,list)) or isinstance(b,(str,list))):
                raise Rejected('Sequence multiplication disabled')
            if isinstance(n.op, ast.Mod) and isinstance(a,str):
                raise Rejected('String formatting disabled')
            return BIN[type(n.op)](a,b)
        if isinstance(n, ast.UnaryOp):
            f = {ast.Not:operator.not_, ast.USub:operator.neg, ast.UAdd:operator.pos}.get(type(n.op))
            if f: return f(self.expr(n.operand,e))
        if isinstance(n, ast.Compare):
            a=self.expr(n.left,e)
            for op,bnode in zip(n.ops,n.comparators):
                b=self.expr(bnode,e)
                if type(op) not in CMP: raise Rejected('Comparison disabled')
                if not CMP[type(op)](a,b): return False
                a=b
            return True
        if isinstance(n, ast.BoolOp):
            for sub in n.values:
                value=self.expr(sub,e)
                if isinstance(n.op,ast.And) and not value: return value
                if isinstance(n.op,ast.Or) and value: return value
            return value
        if isinstance(n, ast.IfExp):
            return self.expr(n.body if self.expr(n.test,e) else n.orelse,e)
        if isinstance(n, ast.Subscript):
            seq=self.expr(n.value,e)
            if isinstance(n.slice,ast.Slice):
                s=n.slice
                key=slice(*(self.expr(v,e) if v else None for v in (s.lower,s.upper,s.step)))
            else: key=self.expr(n.slice,e)
            return seq[key]
        if isinstance(n, ast.Call) and not n.keywords:
            args=[self.expr(v,e) for v in n.args]
            if isinstance(n.func,ast.Name) and n.func.id in FUNCS:
                return FUNCS[n.func.id](*args)
            if isinstance(n.func,ast.Attribute) and n.func.attr in ('strip','lower','upper') and not args:
                obj=self.expr(n.func.value,e)
                if type(obj) is str: return getattr(obj,n.func.attr)()
            raise Rejected('Call target disabled')
        if isinstance(n,ast.ListComp) and len(n.generators)==1:
            gen=n.generators[0]
            if gen.is_async or not isinstance(gen.target,ast.Name): raise Rejected('Comprehension disabled')
            out=[]
            for value in self.expr(gen.iter,e):
                scope={**e,gen.target.id:value}
                if all(self.expr(c,scope) for c in gen.ifs): out.append(self.expr(n.elt,scope))
            return out
        raise Rejected(f'Unsupported expression: {type(n).__name__}')

    def statements(self, nodes, env):
        for node in nodes:
            self.budget -= 1
            if self.budget < 0: raise Rejected('Step budget exceeded')
            if isinstance(node,ast.Return): raise Returned(self.expr(node.value,env) if node.value else None)
            elif isinstance(node,ast.If): self.statements(node.body if self.expr(node.test,env) else node.orelse, env)
            elif isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name):
                env[node.targets[0].id]=self.expr(node.value,env)
            elif isinstance(node,ast.Expr) and isinstance(node.value,ast.Constant) and isinstance(node.value.value,str): pass
            else: raise Rejected(f'Unsupported statement: {type(node).__name__}')

def run(code, name, args):
    if len(code)>12000: raise Rejected('Source too large')
    tree=ast.parse(code)
    if len(tree.body)!=1 or not isinstance(tree.body[0],ast.FunctionDef):
        raise Rejected('Exactly one function is required')
    fn=tree.body[0]
    if fn.name!=name or fn.decorator_list or fn.args.defaults or fn.args.kwonlyargs or fn.args.vararg or fn.args.kwarg or fn.args.posonlyargs:
        raise Rejected('Unsupported function signature')
    if len(fn.args.args)!=len(args): raise Rejected('Wrong arity')
    env=dict(zip((a.arg for a in fn.args.args),args))
    try: Interpreter().statements(fn.body,env)
    except Returned as result: return result.value
    return None
