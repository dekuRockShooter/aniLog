"""Define signals used throughout aniLog.

Classes:
    Signal: Enumerate the signals.
    Subject: Interface for a class that sends signals.
    Observer: Interace for a class that receives signals.
"""
import enum


# TODO: rename BROWSER_SWITCHED to TABLE_SWITCHED.
class Signal(enum.Enum):
    """Enumerate signals

    Enumerations:
        NEW_QUERY: A new set of rows has been queried and is ready to
            be displayed.
        ENTRY_DELETED: Some rows have been deleted.
        ENTRY_INSERTED: Some rows have been inserted.
        ENTRY_UPDATED: A cell's value has been changed.
        SCREEN_RESIZED: The screen has been resized.
        BROWSER_SWITCHED: The current Table has changed.
        ENTRIES_SELECTED: Rows have been selected.
        BROWSER_OPENED: A new Table has been created.
        SHOW_BUFFERS: Request to show the Table buffer.
    """
    NEW_QUERY = 1
    ENTRY_DELETED = 2
    ENTRY_INSERTED = 3
    ENTRY_UPDATED = 4
    SCREEN_RESIZED = 5
    BROWSER_SWITCHED = 6
    ENTRIES_SELECTED = 7
    BROWSER_OPENED = 8
    SHOW_BUFFERS = 9


class Subject:
    """Interface for a class that sends signals.

    Methods:
        register: Add an object to send signals to.
        unregister: Remove a registered object.
        emit: Send a signal to all registered objects.
    """
    def __init__(self):
        self._observers = set()

    def register(self, observer):
        """Add an object to send signals to.

        If the object is already registered, nothing happens.

        Args:
            observer: An object that subclasses Observer.
        """
        self._observers.add(observer)

    def unregister(self, observer):
        """Remove a registered object.

        If the object is not registered, nothing happens.

        Args:
            observer: An object that subclasses Observer.
        """
        self._observers.discard(observer)

    def emit(self, signal, args=None):
        """Send a signal to all registered objects.

        Args:
            signal: The signal to send.  This can be any one of the
                enumerations in Signal.
            args: The arguments to send to the observers.
        """
        for observer in self._observers:
            observer.receive_signal(signal, args)


class Observer:
    """Interace for a class that receives signals.

    Methods:
        receive_signal: Called by a Subject whenever it sends a signal.
    """
    def receive_signal(self, signal, args=None):
        """Called by a Subject whenever it sends a signal.

        This method must be overriden by the subclass.

        Args:
            signal: The signal sent by the Subject.
            args: The arguments sent by the Subject.
        """
        raise NotImplementedError('Subclasses must implement this.')
