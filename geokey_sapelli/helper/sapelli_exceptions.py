class SapelliException(BaseException):
    pass

class SapelliSAPException(SapelliException):
    def __init__(self, message, java_stacktrace=None):
        super(SapelliSAPException, self).__init__(message)
        self.java_stacktrace = java_stacktrace

class SapelliXMLException(SapelliException):
    pass

class SapelliDuplicateException(SapelliException):
    pass

class SapelliCSVException(SapelliException):
    pass