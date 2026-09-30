def Prepare(any):
    if not isinstance(any, str): any = any.__class__.__name__
    return any

def CWarninig(any, nt = False):
    print(fr"|||WRN||| {Prepare(any)}", end="" if nt else "\n")

def CInfo(any, nt = False):
    print(fr"///INF\\\ {Prepare(any)}", end="" if nt else "\n")

def CError(any, nt = False):
    print(fr"<<<ERR>>> {Prepare(any)}", end="" if nt else "\n")

class Error():
    def __init__(self, message : str):
        self.message = message

class BackendASMError(Error):
    def __init__(self, message):
        super().__init__(message)

class SyntaxError(Error):
    def __init__(self, message):
        super().__init__(message)

class TypeError(Error):
    def __init__(self, message):
        super().__init__(message)

def Abort(err : Error):
    print(f"        {err.__class__.__name__}:\n            {err.message}")
    exit()

def Exit():
    CInfo("[FATAL] Fatal error, quiting.")
    exit()