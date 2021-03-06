from kataja.SavedObject import SavedObject
from kataja.KatajaFactory import KatajaFactory
from kataja.globals import FOREST
from kataja.singletons import ctrl, classes
from kataja.nodes_to_synobjs import nodes_to_synobjs


class SyntaxConnection(SavedObject):
    """ This class is the interface between syntax implementations and Kataja calls for them.
    Syntax implementations subclass this and overwrite methods as needed. It is assumed that each
    Forest will create its own SyntaxConnection -- it may save data specific for that structure, but
    if many forests e.g. use same lexicon, be wary that all SyntaxConnections point at the same
    object without making their own personal copies.

    """
    role = "SyntaxConnection"
    supports_editable_lexicon = False
    supports_secondary_labels = False
    display_modes = []

    options = {"merge_types": dict(options=["set_merge", "pair_merge"], default="set_merge"),
               "linearization_types": dict(options=["merge_asymmetry", "kayne"]),
               "binary_branching_for_constituents": dict(options=[True, False], default=True),
               "binary_branching_for_features": dict(options=[True, False], default=False),
               }
    # key : ("readable name", "optional help text")
    ui_strings = {"set_merge": ("Set Merge", ""),
                  "pair_merge": ("Pair Merge", ""),
                  "merge_types": ("Merge types", ""),
                  "binary_branching_for_constituents":
                      ("Allow only binary branching with constituents", ""),
                  "binary_branching_for_features":
                      ("Features are forced to binary trees", "")
                  }

    def __init__(self):
        super().__init__()
        self.Constituent = classes.get('Constituent')
        self.Feature = classes.get('Feature')
        self.trees = []
        self.constituents = {}
        self.features = {}
        self.lexicon = {}
        self.rules = {}
        self.sentence = ''
        for key, value in self.options.items():
            self.rules[key] = value.get('default')

    def get_trees(self):
        """ List the constituent structures of the workspace, represented by their topmost element
        """
        return self.trees

    def get_editable_lexicon(self):
        """ If it is possible to provide editable lexicon, where to get it
        :return:
        """
        print('old get_editable_lexicon')
        return repr(self.lexicon)

    def get_editable_sentence(self):
        """ If the current systems supports parsing, return the current parsed string. User can
        edit it and retry parsing.
        :return:
        """
        return ''

    def get_editable_semantics(self):
        """ If the current systems supports parsing, return the current parsed string. User can
        edit it and retry parsing.
        :return:
        """
        return ''

    def get_c_commanded_leaves(self, node):
        """ By default we cheat on c-command and do it on node level, where we have a reliable
        access to parent of node.
        :param node:
        :return:
        """
        def _pick_leaves(n):
            if n not in passed:
                passed.add(n)
                children = n.get_children(visible=False, similar=True)
                if children:
                    for c in children:
                        _pick_leaves(c)
                else:
                    leaves.append(n)
        leaves = []
        passed = set()
        #passed.add(node)
        for parent in node.get_parents():
            _pick_leaves(parent)
        return [l.syntactic_object for l in leaves]

    def get_dominated_nodes(self, node):
        """ General solution works on level of nodes, not constituents, so this shouldn't be used
        to determine how nodes relate to each others.
        :param node:
        :return:
        """
        def _pick_leaves(n):
            if n not in passed:
                passed.add(n)
                leaves.append(n)
                children = n.get_children(visible=False, similar=True)
                if children:
                    for c in children:
                        _pick_leaves(c)
        leaves = []
        passed = set()
        passed.add(node)
        for child in node.get_children(visible=False, similar=True):
            _pick_leaves(child)
        return [l.syntactic_object for l in leaves]

    def derive_from_editable_lexicon(self, sentence, lexdata, semantics=''):
        """ Take edited version of get_editable_lexicon output and try derivation with it.
        """
        raise NotImplementedError

    def nodes_to_synobjs(self, forest, roots):
        """ Wrapper for function to update all syntactic objects to correspond with the current
        node graph, if possible. It can be complicated and it is sensitive to modifications in
        syntax, so it is in its own file.

        :return:
        """
        syntax = self
        return nodes_to_synobjs(forest, syntax, roots)

    def create_derivation(self, forest):
        """ This is always called to initially turn syntax available here and some input into a
        structure. Resulting structures are used to populate a forest.
        :return:
        """
        text = self.sentence.strip()
        print('create derivation called w. sentence: ', text)
        roots = forest.parser.string_into_forest(text)
        forest.free_drawing.definitions_to_nodes(self.lexicon)
        self.nodes_to_synobjs(forest, roots)

    def get_constituent_from_lexicon(self, identifier):
        """ Fetch constituent from lexicon
        :param identifier:
        :return:
        """
        return self.lexicon.get(identifier)

    def get_feature_from_lexicon(self, identifier):
        """ Fetch the feature matching the key from workspace
        :param identifier:
        :return:
        """
        return self.lexicon.get(identifier)

    def merge(self, a, b, merge_type=None, c=None):
        """ Do Merge of given type, return result
        :param a:
        :param b:
        :param merge_type:
        :param c: result of merge if we are updating/redoing an existing merge (this
                  behavior isn't part of syntax)
        :return:
        """
        if not merge_type:
            merge_type = self.rules['merge_types']
        if merge_type == 'set_merge':
            if not c:
                c = self.create_constituent()
            c.features = []
            c.parts = [a, b]
            return c
        elif merge_type == 'pair_merge':
            if not c:
                c = self.create_constituent()
            c.features = []
            c.parts = [a, b]
            return c
        else:
            raise NotImplementedError

    def set_merge(self, A, B):
        """ Do set merge of two constituent.
        :param A:
        :param B:
        :return:
        """
        return self.merge(A, B, merge_type='set_merge')

    def pair_merge(self, A, B):
        """ Do pair merge of two constituent.
        :param A:
        :param B:
        :return:
        """
        return self.merge(A, B, merge_type='pair_merge')

    def merge_to_top(self, A, B, dir="<"):
        """
        :param A:
        :param B:
        :param dir:
        :return:
        """
        if dir == "<" or dir == "left":
            return self.merge(A, B)
        else:
            return self.merge(B, A)

    def use_labeling_algorithm(self, merged):
        """ Kind of basic labeling.
        Labeling and set_head are two ways of doing the same thing, I have not yet decided if both
        should be supported.
        :param merged:
        :return:
        """
        if len(merged.parts) == 0:
            # leaf should have label of its own
            pass
        elif len(merged.parts) == 1:
            # monobranches may exist temporarily because of free drawing
            merged.label = merged.parts[0].label
        elif len(merged.parts) == 2:
            # a common assumption is that in external merge the merged element is head and in
            # internal merge the element that is not raised is head. Raised element can be
            # recognised by being dominated by the other.
            # if both are leaves, there is no good way to yet decide which one is head. the left
            # one is head.
            a, b = merged.parts
            if (not a.parts) and (not b.parts):
                merged.label = a.label
            elif a.parts and not b.parts:
                merged.label = b.label
            elif b.parts and not a.parts:
                merged.label = a.label
            elif self.dominates(b, a):
                merged.label = b.label
            elif self.dominates(a, b):
                merged.label = a.label
            else:
                merged.label = a.label

    def linearize(self, a, linearization_type=None):
        """ Do linearisation for a structure, there may be various algorithms
        :param a:
        :param linearization_type: 'implicit', 'kayne' etc. if empty, use rules set for this FL
        :return: list of leaf constituents ?
        """
        def _implicit(const, result):
            """ Linearization that relies on parent-child nodes to be implicitly ordered by constituent
                implementation:
                constituent implements ordered_parts -method that can return [left, right] lists or
                even [first, second, third... ] lists. """
            o = const.ordered_parts()
            if not o:
                result.append(const)
            for child in o:
                _implicit(child, result)
            return result

        if not linearization_type:
            linearization_type = self.rules['linearization_types']
        if linearization_type == 'implicit':
            return _implicit(a, [])
        else:
            raise NotImplementedError

    def precedes(self, a, b, linearization_type=None):
        """
        :param a:
        :param b:
        :param linearization_type: 'implicit', 'kayne' etc. if empty, use rules set for this FL.
        :return: 1 if a precedes b, -1 if b precedes b, 0 if cannot say
        """
        def _implicit(const, i, j, found_i=None, found_j=None):
            """ Precedence that relies on parent-child nodes to be implicitly ordered by constituent
                implementation:
                constituent implements ordered_parts -method that can return [left, right] lists or
                even [first, second, third... ] lists. Precedence is computed by going through such
                trees from top down, left first and trying to match i and j. Once both are found from
                a same trees, their precedence can be stated. """
            o = const.ordered_parts()
            for c in o:
                result, found_i, found_j = _implicit(c, i, j, found_i, found_j)
                if result:
                    return result, found_i, found_j
            if not found_i and const is i:
                if found_j:
                    return -1, found_i, found_j
                else:
                    found_i = True
            if not found_j and const is j:
                if found_j:
                    return 1, found_i, found_j
                else:
                    found_j = True
            return 0, found_i, found_j

        if not linearization_type:
            linearization_type = self.rules['linearization_types']
        if linearization_type == 'implicit':
            found = 0
            for tree_top in self.trees:
                found, foo, bar = _implicit(tree_top, a, b, found_i=False, found_j=False)
                if found:
                    break
            return found
        else:
            raise NotImplementedError

    def feature_check(self, suitor, bride):
        """ Check if the features(?) match(?)
        :param suitor:
        :param bride:
        :return: bool
        """
        raise NotImplementedError

    def c_commands(self, A, B):
        """ Evaluate if A C-commands B
        :param A:
        :param B:
        :return: bool
        """
        raise NotImplementedError

    def parse(self, sentence, silent=False):
        """ Returns structure (constituent or list of constituents) if given sentence can be parsed. Not
        necessary to implement.
        :param sentence:
        :param silent:
        :return: :raise "Word '%s' missing from the lexicon" % word:
        """
        return None

    def dominates(self, higher, lower):
        if lower in higher.parts:
            return True
        for part in higher.parts:
            yes = self.dominates(part, lower)
            if yes:
                return True
        return False


    # Direct editing of FL constructs ##########################
    # these methods don't belong to assumed capabilities of FL, they are to allow Kataja editing
    # capabilities to directly create and modify FL structures.

    def create_constituent(self, **kw):
        """ Create constituent with provided values and return it
        :param kw:
        :return: Constituent
        """
        const = self.Constituent(**kw)
        self.constituents[const.uid] = const
        return const

    def get_constituent(self, key):
        """ Fetch the constituent matching the key from workspace
        :param key:
        :return:
        """
        return self.constituents.get(key, None)

    def get_feature(self, key):
        """ Fetch the feature matching the key from workspace
        :param key:
        :return:
        """
        return self.features.get(key, None)

    def construct(self, parent, children, purge_existing=True):
        """ Sets up connections between constituents without caring if there are syntactic
        operations to allow that
        :param parent:
        :param children:
        :param purge_existing:
        :return:
        """
        raise NotImplementedError

    def connect(self, parent, child, align=None):
        """ Tries to set a parent-child connection. It may be necessary to
        force parts to be in specific order, alignment can be used to give
        hints about the order
        :param parent:
        :param child:
        :param align: edge alignment
        :return:

        """
        if child not in parent.parts:
            if align is None:
                parent.add_part(child)
            elif align == g.LEFT:
                parent.insert_part(child)
            else:
                parent.add_part(child)

    def disconnect(self, parent, child):
        """ Tries to remove parent-child connection. Primitive: may leave binary trees to have empty
        branch.
        :param parent:
        :param child:
        :return:

        """
        if child in parent.parts:
            parent.remove_part(child)

    def replace(self, old_c, new_c, under_parent=None):
        """ Replace constituent with another, either in all occurences or only under specific parent
        :param old_c:
        :param new_c:
        :param under_parent:
        :return:
        """
        if under_parent:
            if old_c in under_parent.parts:
                under_parent.replace_part(old_c, new_c)
        else:
            parents = [x for x in self.constituents.values() if old_c in x.parts]
            for parent in parents:
                self.replace(old_c, new_c, under_parent=parent)

    def linearization_types(self):
        """ Return available options for linearization
        :return:
        """
        raise NotImplementedError

    def merge_types(self):
        """ Provide available merge types
        :return:
        """
        raise NotImplementedError

    def create_feature(self, **kw):
        """ Create feature with provided values and return it
        :param kw:
        :return: Feature
        """
        feature = self.Feature(**kw)
        self.features[feature.uid] = feature
        return feature
