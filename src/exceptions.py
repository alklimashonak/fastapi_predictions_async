class UserAlreadyExists(Exception):
    pass


class InvalidEmailOrPassword(Exception):
    pass


class UserNotFound(Exception):
    pass


class EventNotFound(Exception):
    pass


class MatchNotFound(Exception):
    pass


class PredictionNotFound(Exception):
    pass


class UnexpectedEventStatus(Exception):
    pass


class UnexpectedMatchStatus(Exception):
    pass


class TooFewMatches(Exception):
    pass


class MatchesAreNotFinished(Exception):
    pass


class PredictionAlreadyExists(Exception):
    pass


class UserIsNotAllowed(Exception):
    pass
