try:
    from PoP.Lexicon import SHARED_FEAT_LABELS
    from PoP.Feature import FeatureSet, Feature
    from BaseConstituent import BaseConstituent as MyBase
    in_kataja = True
except ImportError:
    from Lexicon import SHARED_FEAT_LABELS
    from Feature import FeatureSet, Feature
    MyBase = object
    in_kataja = False


class Constituent(MyBase):  # collections.UserList):

    replaces = "ConfigurableConstituent"

    def __init__(self, label='', part1=None, part2=None, features=None):
        if in_kataja:
            if part1 and part2:
                super().__init__(label=label, parts=[part1, part2], features=features)
            else:
                super().__init__(label=label, features=features)
        self.label = label
        self.part1 = part1
        self.part2 = part2
        self.features = FeatureSet()
        self.stacked = False
        if features:
            for f in features:
                if isinstance(f, str):
                    self.features.add(Feature(f))
                elif isinstance(f, Feature):
                    self.features.add(f)

    def __repr__(self):
        parts = [self.label]
        if self.part1:
            parts.append(self.part1)
        if self.part2:
            parts.append(self.part2)
        if self.features:
            parts.append(self.features)
        return repr(parts)

    def __eq__(self, other):
        if not isinstance(other, Constituent):
            return False
        elif self.label != other.label:
            return False
        elif self.part1 != other.part1:
            return False
        elif self.part2 != other.part2:
            return False
        elif self.features != other.features:
            return False
        else:
            return True

    def __hash__(self):
        return hash(repr(self))

    def labelstring(self):
        if self.part1 and self.part2:
            return '[%s %s %s]' % (self.label, self.part1.labelstring(), self.part2.labelstring())
        else:
            return self.label

    def is_leaf(self):
        return not (self.part1 and self.part2)

    def get_head(self):
        if self.part1 and self.part1.label == self.label:
            return self.part1.get_head()
        elif self.part2 and self.part2.label == self.label:
            return self.part2.get_head()
        else:
            return self

    def shared_features(self, other):
        my_feats = self.get_head_features()
        other_feats = other.get_head_features()
        return FeatureSet(my_feats & other_feats)

    def add_feature(self, feat):
        if not isinstance(feat, Feature):
            feat = Feature(feat)
        self.features.add(feat)

    def remove_feature(self, feat):
        self.features.remove(feat)

    def replace_feature(self, old, new):
        if old in self.features:
            self.features.remove(old)
            self.features.add(new)

    def replace_feature_by_name(self, old_name, new):
        found = None
        for item in self.features:
            if item.name == old_name:
                found = item
                break
        if found is not None:
            self.features.remove(found)
            self.features.add(new)
        else:
            print('couldnt find ', old_name, self)

    def is_unlabeled(self):
        return self.label == '_'

    def is_labeled(self):
        return self.label != '_'

    def copy(self):
        if self.part1 and self.part2:
            return Constituent(label=self.label, part1=self.part1.copy(), part2=self.part2.copy())
        elif self.features:
            return Constituent(label=self.label, features=FeatureSet(self.features))
        else:
            raise TypeError

    def __contains__(self, item):
        if isinstance(item, Constituent):
            if self.part1 == item:
                return True
            elif self.part2 == item:
                return True
            if self.part1:
                if item in self.part1:
                    return True
            if self.part2:
                if item in self.part2:
                    return True
        elif isinstance(item, Feature):
            return item in self.features
        return False

    def tex_tree(self, stack):
        stacked = ''
        if self.stacked:
            stacked = '(S?)'
            for i, item in enumerate(reversed(stack)):
                if item is self:
                    stacked = '(S%s)' % i
                    break
        label = self.label.replace('_', '-')
        if self.part1 and self.part2:
            return '[.%s%s %s %s ]' % (label, stacked, self.part1.tex_tree(stack), self.part2.tex_tree(stack))
        else:
            return label + stacked

    def get_head_features(self):
        # if self.language == "Japanese":
        #    return self.get_head_features_head_final(merged)
        if self.is_leaf():
            return self.features
        if self.is_unlabeled():
            return self.part1.recursive_get_features()
        elif self.part2.is_unlabeled():
            f = self.part1.recursive_get_features()
            if f:
                return f
        return self.recursive_get_features()

    def recursive_get_features(self):
        if self.is_leaf():
            return self.features
        head = self.label
        if self.part1.label == head:
            return self.part1.get_head_features()
        if self.part2.label == head:
            return self.part2.get_head_features()
        if head in SHARED_FEAT_LABELS:
            elem1_feats = self.part1.get_head_features()
            elem2_feats = self.part2.get_head_features()
            shared_feats = FeatureSet(elem1_feats & elem2_feats)
            if shared_feats:
                return shared_feats
        if "Phi" in head:
            head_features = self.part1.get_head_features()
            return head_features
        assert False

    def replace_within(self, old_chunk, new_chunk, label=False):
        if self == old_chunk:
            self.label = new_chunk.label
            self.features = new_chunk.features
            self.part1 = new_chunk.part1
            self.part2 = new_chunk.part2
            return
        if label:
            self.recursive_replace_label(old_chunk, new_chunk)
        elif isinstance(old_chunk, Constituent):
            self.recursive_replace_constituent(old_chunk, new_chunk)
        elif isinstance(old_chunk, FeatureSet):
            self.recursive_replace_feature_set(old_chunk, new_chunk)
        elif isinstance(old_chunk, Feature):
            self.recursive_replace_feature(old_chunk, new_chunk)
        else:
            raise TypeError

    def recursive_replace_label(self, old_label, new_label):
        if self.part1:
            self.part1.recursive_replace_label(old_label, new_label)
        if self.part2:
            self.part2.recursive_replace_label(old_label, new_label)
        if self.label == old_label:
            self.label = new_label

    def recursive_replace_feature_set(self, old, new):
        for item in new:
            if not isinstance(item, Feature):
                print(new)
                raise TypeError
        if self.part1:
            self.part1.recursive_replace_feature_set(old, new)
        if self.part2:
            self.part2.recursive_replace_feature_set(old, new)
        if old == self.features:
            self.features = new

    def recursive_replace_feature(self, old, new):
        if new and not isinstance(new, Feature):
            print(new)
            raise TypeError
        if self.part1:
            self.part1.recursive_replace_feature(old, new)
        if self.part2:
            self.part2.recursive_replace_feature(old, new)
        if old in self.features:
            self.features.remove(old)
            if new:
                self.features.add(new)

    def recursive_replace_constituent(self, old, new):
        assert(self != old)
        if self.part1:
            if self.part1 == old:
                self.part1 = new
            else:
                self.part1.recursive_replace_constituent(old, new)
        if self.part2:
            if self.part2 == old:
                self.part2 = new
            else:
                self.part2.recursive_replace_constituent(old, new)