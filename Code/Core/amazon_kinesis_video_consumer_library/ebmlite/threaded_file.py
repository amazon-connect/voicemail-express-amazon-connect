'''
A special-case, drop-in 'replacement' for a standard read-only file stream
that supports simultaneous access by multiple threads without (explicit)
blocking. Each thread actually gets its own stream, so it can perform its
own seeks without affecting other threads that may be reading the file. This
functionality is transparent.

@author: dstokes
'''
__author__ = "David Randall Stokes, Connor Flanigan"
__copyright__ = "Copyright 2021, Mide Technology Corporation"
__credits__ = "David Randall Stokes, Connor Flanigan, Becker Awqatty, Derek Witt"

__all__ = ['ThreadAwareFile']

import io
import platform
from threading import currentThread, Event

class ThreadAwareFile(io.FileIO):
    """ A 'replacement' for a standard read-only file stream that supports
        simultaneous access by multiple threads without (explicit) blocking.
        Each thread actually gets its own stream, so it can perform its own
        seeks without affecting other threads that may be reading the file.
        This functionality is transparent.

        ThreadAwareFile implements the standard `file` methods and has 
        the standard attributes and properties. Most of these affect only
        the current thread.
        
        @var timeout: A value (in seconds) for blocking operations to wait.
            Very few operations block; specifically, only those that do
            (or depend upon) internal housekeeping. Timeout should only occur
            in certain extreme conditions (e.g. filesystem-related file
            access issues).
    """

    def __init__(self, *args, **kwargs):
        """ ThreadAwareFile(name[, mode[, buffering]]) -> file object

            Open a read-only file that may already be open in other threads.
            Takes the standard `file` arguments, except `mode` can only be
            one of the "read" modes (``r``, ``rb``, ``rU``, etc.).
        """
        # Ensure the file mode, if specified, is "read."
        mode = args[1] if len(args) > 1 else 'r'
        if isinstance(mode, (str, bytes, bytearray)):
            if 'a' in mode or 'w' in mode or '+' in mode:
                raise IOError("%s is read-only" % self.__class__.__name__)

        # Undocumented keyword argument `_new` is used by `makeThreadAware()`
        # to prevent a new file for the current thread from being created.
        newFile = kwargs.pop('_new', True)
        
        # Blocking timeout. Not a `file` keyword argument; remove.
        self.timeout = kwargs.pop('timeout', 60.0)
        
        self.initArgs = args
        self.initKwargs = kwargs
        
        self._ready = Event()  # NOT a lock; some things block, others wait
        self._ready.set()

        self.threads = {}
        
        if newFile is True:
            # Getting the stream for the thread will open the file.
            self.getThreadStream()

        # For repr() on files closed by a thread.
        self._mode = mode


    def __repr__(self):
        # Format the object's ID appropriately for the architecture (32b/64b)
        if '32' in platform.architecture()[0]:
            fmt = "<%s %s %r, mode %r at 0x%08X>"
        else:
            fmt = "<%s %s %r, mode %r at 0x%016X>"
            
        return fmt % ("closed" if self.closed else "open",
                      self.__class__.__name__, 
                      self.initArgs[0],
                      self._mode, 
                      id(self))
        

    @classmethod
    def makeThreadAware(cls, fileStream):
        """ Create a new `ThreadAwareFile` from an already-open file. If the
            object is a `ThreadAwareFile`, it is returned verbatim.
        """
        if isinstance(fileStream, cls):
            return fileStream
        elif not isinstance(fileStream, io.IOBase):
            raise TypeError("Not a file: %r" % fileStream)

        f = cls(fileStream.name, fileStream.mode, _new=False)
        f.threads[currentThread().ident] = fileStream
        return f


    def getThreadStream(self):
        """ Get (or create) the file stream for the current thread.
        """
        self._ready.wait(self.timeout)

        ident = currentThread().ident
        if ident not in self.threads:
            # First access from this thread. Open the file.
            fp = io.FileIO(*self.initArgs, **self.initKwargs)
            self.threads[ident] = fp
            return fp
        return self.threads[ident]


    def closeAll(self):
        """ Close all open streams.

            Warning: May not be thread-safe in some situations!
        """
        try:
            self._ready.wait(self.timeout)
            self._ready.clear()
            for v in list(self.threads.values()):
                v.close()
        finally:
            self._ready.set()


    def cleanup(self):
        """ Delete all closed streams.
        """
        try:
            self._ready.wait(self.timeout)
            self._ready.clear()
            
            for i in self.threads.keys():
                if self.threads[i].closed:
                    del self.threads[i]
        finally:
            self._ready.set()


    @property
    def closed(self):
        """ Is the file not open? Note: A thread that never accessed the file
            will get `True`.
        """
        ident = currentThread().ident
        if ident in self.threads:
            return self.threads[ident].closed
        return True


    def close(self, *args, **kwargs):
        """ Close the file for the current thread. The file will remain
            open for other threads.
        """
        result = self.getThreadStream().close(*args, **kwargs)
        self.cleanup()
        return result


    # Standard file methods, overridden

    def __format__(self, *args, **kwargs):
        return self.getThreadStream().__format__(*args, **kwargs)

    def __hash__(self, *args, **kwargs):
        return self.getThreadStream().__hash__(*args, **kwargs)

    def __iter__(self, *args, **kwargs):
        return self.getThreadStream().__iter__(*args, **kwargs)

    def __reduce__(self, *args, **kwargs):
        return self.getThreadStream().__reduce__(*args, **kwargs)

    def __reduce_ex__(self, *args, **kwargs):
        return self.getThreadStream().__reduce_ex__(*args, **kwargs)

    def __sizeof__(self, *args, **kwargs):
        return self.getThreadStream().__sizeof__(*args, **kwargs)

    def __str__(self, *args, **kwargs):
        return self.getThreadStream().__str__(*args, **kwargs)

    def fileno(self, *args, **kwargs):
        return self.getThreadStream().fileno(*args, **kwargs)

    def flush(self, *args, **kwargs):
        return self.getThreadStream().flush(*args, **kwargs)

    def isatty(self, *args, **kwargs):
        return self.getThreadStream().isatty(*args, **kwargs)

    def next(self, *args, **kwargs):
        return self.getThreadStream().next(*args, **kwargs)

    def read(self, *args, **kwargs):
        return self.getThreadStream().read(*args, **kwargs)

    def readinto(self, *args, **kwargs):
        return self.getThreadStream().readinto(*args, **kwargs)

    def readline(self, *args, **kwargs):
        return self.getThreadStream().readline(*args, **kwargs)

    def readlines(self, *args, **kwargs):
        return self.getThreadStream().readlines(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self.getThreadStream().seek(*args, **kwargs)

    def tell(self, *args, **kwargs):
        return self.getThreadStream().tell(*args, **kwargs)

    def truncate(self, *args, **kwargs):
        raise IOError("Can't truncate(); %s is read-only" %
                      self.__class__.__name__)

    def write(self, *args, **kwargs):
        raise IOError("Can't write(); %s is read-only" %
                      self.__class__.__name__)

    def writelines(self, *args, **kwargs):
        raise IOError("Can't writelines(); %s is read-only" %
                      self.__class__.__name__)

    def xreadlines(self, *args, **kwargs):
        return self.getThreadStream().xreadlines(*args, **kwargs)

    def __enter__(self, *args, **kwargs):
        return self.getThreadStream().__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        return self.getThreadStream().__exit__(*args, **kwargs)


    # Standard file attributes, as properties for transparency with 'real'
    # file objects. Most are read-only.

    @property
    def encoding(self):
        return self.getThreadStream().encoding

    @property
    def errors(self):
        return self.getThreadStream().errors

    @property
    def mode(self):
        return self.getThreadStream().mode

    @property
    def name(self):
        return self.getThreadStream().name

    @property
    def newlines(self):
        return self.getThreadStream().newlines

    @property
    def softspace(self):
        return self.getThreadStream().softspace

    @softspace.setter
    def softspace(self, val):
        self.getThreadStream().softspace = val
