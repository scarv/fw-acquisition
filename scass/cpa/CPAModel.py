

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
        return 0.0

class CPAModelHammingWeightD(CPAModel):
    """
    A hamming weight based power model which returns the hamming weight
    of the input data array.
    """

    def getEstimate(self,d,k):
        """
        Get a power estimate for the input data.
        - Uses only the `d` parameters, and returns it's hamming weight.
        """
        count = 0.0
        
        for i in range(0,8):
            count += float((d >> i) & 0x1)

        return count

class CPAModelHammingDistance(CPAModel):
    """
    A hamming distance based power model which returns the hamming distance 
    between the input d and k arrays.
    """

    def getEstimate(self,d,k):
        """
        Get a power estimate for the input data.
        - Returns the hamming distance between d and k.
        """
        count = 0.0
        
        axb = d ^ k
        for i in range(0,8):
            count += float((axb >> i) & 0x1)

        return count
