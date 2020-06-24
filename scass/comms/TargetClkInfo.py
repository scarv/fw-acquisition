
SCASS_CLK_SRC_EXTERNAL          = 0b00000001
SCASS_CLK_SRC_INTERNAL          = 0b00000010
SCASS_CLK_SRC_PLL               = 0b00000100

SCASS_CLK_SOURCES   = [
    SCASS_CLK_SRC_EXTERNAL, SCASS_CLK_SRC_INTERNAL, SCASS_CLK_SRC_PLL
]

class TargetClkInfo(object):
    """
    Contains information on the current system clock
    """

    def __init__(
        self            ,
        valid_rates     ,
        valid_sources   ,
        current_rate    ,
        current_src     ,
        ext_clk_rate
    ):
        """
        Create a new clock source description object.
        """

        for s in valid_sources:
            assert(s in SCASS_CLK_SOURCES)

        for r in valid_rates:
            assert(isinstance(r,int))

        assert(isinstance(current_rate, int))
        assert(current_src in SCASS_CLK_SOURCES)
        assert(isinstance(ext_clk_rate, int))

        self.__valid_rates  = valid_rates
        self.__valid_sources= valid_sources
        self.__current_rate = current_rate
        self.__current_src  = current_src
        self.__ext_clk_rate = ext_clk_rate

    def __str__(self):
        tr  ="- Target Clock Rate: %d\n" % self.current_rate
        tr +="- Valid Clock Rates: %s\n" % ", ".join([str(r) for r in self.rates])
        tr +="- External clock   : %d\n" % self.external_clk_rate
        tr +="- Clock Source     : %d" % self.current_src
        return tr

    @property
    def external_clk_rate(self):
        """Current rate of external clock source in hertz"""
        return self.__ext_clk_rate

    @property
    def rates(self):
        """Possible valid clock rates in hertz"""
        return self.__valid_rates

    @property
    def sources(self):
        """Possible valid clock sources"""
        return self.__valid_sources

    @property
    def current_src(self):
        """Current clock source"""
        return self.__current_src

    @property
    def current_rate(self):
        """Current clock rate in hertz"""
        return self.__current_rate

