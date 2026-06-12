from .GcAttributeContainer import GcAttributeContainer
from abc import abstractmethod, ABC

class GcAttributeTree(GcAttributeContainer, ABC):
        
    def __init__(self) -> None:
        super().__init__()


    @property
    @abstractmethod
    def children(self) -> list["GcAttributeTree"]:
        pass

    def augmentChildAttributesWithSelf(self):
        """Copys the Attributes from self to every Child, if the Child does not already have an Attribute with the same name"""
        for p in self.children:
            p.augmentAttributesSelf(self)

    def replaceChildAttributesWithSelf(self):
        """Removes all Attributes from Every Child - then Copys the Attributes from self to every Child"""
        for p in self.children:
            p.replaceAttributesSelf(self)

    def overwriteChildAttributesWithSelf(self):
        """Copys all Attributes form self to every Child, Overwriting Attributes of the Child with the same name"""
        for p in self.children:
            p.overwriteAttributesSelf(self)

    
    def childrenUntilDepth(self, depth = 0, ignore_leafs = False, _list = []) -> list["GcAttributeTree"]:
        """Recursively builds a list of all children until the specifyed depth is reached.
        If Depth is <= 0 the Whole tree is listed
        
        if ignore_leafs is true, the lowest level is not added to the list
        """
        for child in self.children:

            if ignore_leafs and len(child.children) == 0:
                continue

            _list.append(child)

            if depth != 1:
                child.childrenUntilDepth(depth - 1, ignore_leafs, _list)

        return _list



        
