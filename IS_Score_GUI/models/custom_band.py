class CustomBand:
    def __init__(self, bandIndex, ramanShift=None, leftEdge=None, rightEdge=None):
        self.bandIndex = bandIndex
        self.ramanShift = ramanShift
        self.leftEdge = leftEdge
        self.rightEdge = rightEdge

    def __eq__(self, other):
        if isinstance(other, CustomBand):
            return self.bandIndex == other.bandIndex
        return False