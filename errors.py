"""Friendly errors for Memowrite."""


class MemoError(Exception):
    """An error in a Memowrite program, with the line it happened on."""

    def __init__(self, message, line=None, file=None, hint=None):
        super().__init__(message)
        self.message = message
        self.line = line
        self.file = file
        self.hint = hint

    def __str__(self):
        where = ""
        if self.file:
            where += f"{self.file}, "
        if self.line:
            where += f"line {self.line}: "
        text = f"Oops! {where}{self.message}"
        if self.hint:
            text += f"\n  Tip: {self.hint}"
        return text


class Complaint(MemoError):
    """Raised by the 'complain' statement; can be caught with try."""


class StopLoop(Exception):
    pass


class SkipLoop(Exception):
    pass


class GiveBack(Exception):
    def __init__(self, value):
        self.value = value


class StopProgram(Exception):
    pass


def suggest(name, choices, cutoff=0.72):
    import difflib
    match = difflib.get_close_matches(name, list(choices), n=1, cutoff=cutoff)
    return match[0] if match else None
