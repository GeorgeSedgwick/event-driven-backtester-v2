import numpy as np
from abc import ABC, abstractmethod



class SlippageModel(ABC):

    @abstractmethod
    def calculate():

        raise NotImplementedError("Should implement calculate() func.")
    


class LogSlippageModel(SlippageModel):
    """
    Slippage model that logarithmically increases with order size.

    - Scaled by 0.01% of the asset's price.
    - Reflecting the diminishing marginal price impact of large orders.

    Limitations:

    This model is independant of key market microstructure factors and therefore lacks realims.
    In particular, it does not account for:
    - Market liquidity
    - Price volatility
    - Bid-ask spread

    As a result, the model may underestimate or overestimate true execution costs in live trading environments.


    reference: QuantConnect (Slippage Key Concepts) https://www.quantconnect.com/docs/v2/writing-algorithms/reality-modeling/slippage/key-concepts
    
    """




    def __init__(self):
        pass
        
        

    def calculate(self, price, quantity, direction):
        
        slippage = price * 0.0005 * np.log10(2*float(quantity))

        

        if direction == "BUY":
            fill_price = price + slippage
        else:
            fill_price = price - slippage

        return fill_price