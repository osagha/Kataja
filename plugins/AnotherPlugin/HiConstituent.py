# coding=utf-8
from kataja.SavedField import SavedField
from syntax.BaseConstituent import BaseConstituent


class HiConstituent(BaseConstituent):
    """ HiConstituent is a slight modification from BaseConstituent.
    Everything that is not explicitly defined here is inherited from parent class."""


    def __init__(self, **kw):
        """
         """
        super().__init__(**kw)
        self.hi = 'hi'

    def __repr__(self):
        if self.is_leaf():
            return 'HiConstituent(id=%s)' % self.label
        else:
            return "[ %s ]" % (' '.join((x.__repr__() for x in self.parts)))

    def compose_html_for_viewing(self, node):
        """ This method builds the html to display in label. For convenience, syntactic objects
        can override this (going against the containment logic) by having their own
        'compose_html_for_viewing' -method. This is so that it is easier to create custom
        implementations for constituents without requiring custom constituentnodes.

        Note that synobj's compose_html_for_viewing receives the node object as parameter,
        so you can call the parent to do its part and then add your own to it.
        :return:
        """

        html, lower_html = node.compose_html_for_viewing(peek_into_synobj=False)
        html += ', hi: ' + self.hi
        return html, lower_html

    def copy(self):
        """ Make a deep copy of constituent. Useful for picking constituents from Lexicon.
        :return: BaseConstituent
        """
        nc = super().copy()
        nc.hi = self.hi
        return nc

    # ############## #
    #                #
    #  Save support  #
    #                #
    # ############## #

    hi = SavedField("hi")
