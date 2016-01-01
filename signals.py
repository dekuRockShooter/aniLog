import enum


class Signal(enum.Enum):
    NEW_QUERY = 1
    ENTRY_DELETED = 2
    ENTRY_INSERTED = 3
    ENTRY_UPDATED = 4
    SCREEN_RESIZED = 5
    BROWSER_SWITCHED = 6


class Subject:
    def __init__(self):
        self._observers = set()

    def register(self, observer):
        self._observers.add(observer)

    def unregister(self, observer):
        self._observers.discard(observer)

    def emit(self, signal, args=None):
        for observer in self._observers:
            observer.receive_signal(signal, args)


class Observer:
    def receive_signal(self, signal, args=None):
        raise NotImplementedError('Subclasses must implement this.')
