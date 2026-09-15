class Extractor:

    storage = {}

    def RawExtractSingular(raw : str, *symbols : list[str]) -> list[str]:
        accumulated = ""
        result = []
        excpeted = ""

        shift = 0
        rawcopy = list(raw)
        for i, char in enumerate(raw):
            if char in symbols:
                if char == excpeted:
                    result += [accumulated]
                    accumulated = ''
                    excpeted = ""
                    rawcopy.pop(i+shift)
                    shift -= 1
                else:
                    excpeted = char
            else:
                if excpeted != "":
                    accumulated += char
                    rawcopy.pop(i+shift)
                    shift -= 1



        return result, ''.join(rawcopy)