
# Mock simples para rodar testes sem o drive nativo Oracle
class Error(Exception):
    pass

class Connection:
    def cursor(self):
        return Cursor()
    def close(self):
        pass

class Cursor:
    def execute(self, sql, **kwargs):
        pass
    def fetchall(self):
        return []
    def fetchone(self):
        return None
    def close(self):
        pass
    def var(self, type):
        return Var()

class Var:
    def getvalue(self):
        return ""

STRING = "STRING"

def connect(*args, **kwargs):
    return Connection()

def makedsn(*args):
    return "DSN_MOCK"
