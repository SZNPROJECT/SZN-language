class SZNExpception(Exception):
    def __init__(self, info : str, got = "Unknown",fix : str = None, expected = "Unknown"):
        self.info = info
        self.exp = expected 
        self.got = got
        self.fix = fix 

        super().__init__(f'\033[1;41m{self.__class__.__name__}: {self.info}\033[0m\n\033[14;44mFix: {self.fix}\033[0m')

class SyntaxException(SZNExpception):
    pass

class InternalException(SZNExpception):
    def __init__(self, info = "..."):
        super().__init__(info, fix="If you seeing this, please report the issue on GitHub page.")