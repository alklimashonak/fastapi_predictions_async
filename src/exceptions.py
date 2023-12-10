class UserAlreadyExists(Exception):
    pass


class UserNotFound(Exception):
    pass


class InvalidEmailOrPassword(Exception):
    pass


class EventNotFound(Exception):
    pass


class EventAlreadyIsRunning(Exception):
    pass


class TooFewMatches(Exception):
    pass


class EventIsNotUpcoming(Exception):
    pass


class EventIsNotOngoing(Exception):
    pass


class EventIsNotClosed(Exception):
    pass


class MatchesAreNotFinished(Exception):
    pass


class MatchNotFound(Exception):
    pass


class MatchHasNotStarted(Exception):
    pass


class MatchAlreadyIsRunning(Exception):
    pass


class MatchAlreadyIsCompleted(Exception):
    pass


class PredictionNotFound(Exception):
    pass


class PredictionAlreadyExists(Exception):
    pass


class UserIsNotAllowed(Exception):
    pass
