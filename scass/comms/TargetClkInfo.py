
from enum import Enum

class TargetClkSrc(Enum):
    EXTERNAL = 0b00000001
    INTERNAL = 0b00000010
    PLL_EXT  = 0b00000100
    PLL_INT  = 0b00001000

class TargetClkInfo(object):
    """
    Contains information on the current system clock
    """

    def __init__(
        self            ,
        sys_clk_rate    ,
        sys_clk_src
    ):
        """
        Create a new clock source description object.
        """
        self.__rate = sys_clk_rate
        self.__src  = sys_clk_src

    def __str__(self):
        return "Source: %8s, Rate: %8sHz" % (
            self.sys_clk_src.name, self.sys_clk_rate
        )

    @property
    def sys_clk_rate(self):
        """Current rate of system clock source in hertz"""
        return self.__rate

    @property
    def sys_clk_src(self):
        """System Clock source"""
        return self.__src
