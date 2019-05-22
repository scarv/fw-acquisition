

class CPAModel(object):
    """
    A abstract class for describing power models.
    """

    def __init__(self):
        """
        Create the model.
        """

    def getEstimate(self,d,k):
        """
        Get a power estimate for the input data
        """
        count = 0.0
        
        for b in d:
            for i in range(0,8):
                count += float((b >> i) & 0x1)

        return count
