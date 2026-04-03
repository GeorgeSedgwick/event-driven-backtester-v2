import numpy as np
import pandas as pd
from queue import Queue

from abc import ABC, abstractmethod
from core.event import SignalEvent



class Strategy(ABC):
    """
    Abstract Base Class to define the required components that all future
    Strategy classes must have.
    """

    @abstractmethod
    def calc_signals(self):

        raise NotImplementedError("Should implement calc_signals()")

