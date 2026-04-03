import numpy as np
from abc import ABC, abstractmethod



class SlippageModel(ABC):

    @abstractmethod
    def calculate():

        raise NotImplementedError("Should implement calculate() func.")
    


class LogSlippageModel(SlippageModel):
    def __init__(self):
        pass
        
        

    def calculate(self, price, quantity, direction):
        
        slippage = price * 0.0001 * np.log10(2*float(quantity))

        

        if direction == "BUY":
            fill_price = price + slippage
        else:
            fill_price = price - slippage

        return fill_price