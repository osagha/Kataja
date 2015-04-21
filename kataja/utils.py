# coding=utf-8
# ############################################################################
#
# *** Kataja - Biolinguistic Visualization tool ***
#
# Copyright 2013 Jukka Purma
#
# This file is part of Kataja.
#
# Kataja is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Kataja is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Kataja.  If not, see <http://www.gnu.org/licenses/>.
#
# ############################################################################
import importlib
import os

from types import FrameType
import gc
import string
import sys
import time
import traceback

from PyQt5 import QtWidgets

from PyQt5.QtCore import QPointF, QPoint
from kataja.debug import DEBUG_TIME_ME


def print_rect(rect):
    """

    :param rect:
    """
    print('x: %s y: %s width: %s height: %s' % (rect.x(), rect.y(), rect.width(), rect.height()))


def caller(function):
    """

    :param function:
    :return:
    """

    def wrap(*arg, **kwargs):
        """

        :param arg:
        :return:
        """
        if len(traceback.extract_stack()) > 1:
            mod, line, fun, cmd = traceback.extract_stack()[-2]
            print("%s was called by %s l.%s at %s" % (function.__name__, cmd, line, mod))
        return function(*arg, **kwargs)

    return wrap


def time_me(function):
    """

    :param function:
    :return:
    """
    if not DEBUG_TIME_ME:
        return function

    def wrap(*arg, **kwargs):
        """

        :param arg:
        :param kwargs:
        :return:
        """
        start = time.time()
        r = function(*arg, **kwargs)
        end = time.time()
        print("%s (%0.3f ms) at %s" % (function.__name__, (end - start) * 1000, function.__module__))
        return r

    return wrap


def to_tuple(p):
    """ PySide's to_tuple-helper method for PyQt
    :param p:
    """
    return p.x(), p.y()


# not used
def load_features(obj, key, d):
    """

    :param obj:
    :param key:
    :param d:
    :return:
    """
    if (isinstance(obj, str) or isinstance(obj, str)) and obj.startswith('_*'):
        if isinstance(d[obj], str) or isinstance(d[obj], str):
            classname = obj.split('_')[1][1:]  # _*[classname]_id
            obj = eval(classname + '()')
            d[obj] = load_features(obj, obj, d)
        obj = d[obj]
    setattr(obj, key, obj)
    return obj


# not used
def save_features(obj, saved, d):
    """

    :param obj:
    :param saved:
    :param d:
    :return:
    """

    def _save_feature(feat):
        """

        :param feat:
        :return:
        """
        fval = getattr(obj, feat)
        try:
            return fval.save(d)
        except AttributeError:
            if isinstance(fval, QPointF) or isinstance(fval, QPoint):
                return fval.x(), fval.y()
            if isinstance(fval, list):
                nval = []
                for item in fval:
                    try:
                        nval.append(item.save(d))
                    except AttributeError:
                        nval.append(item)
                return nval
            elif isinstance(fval, dict):
                nval = {}
                for ikey, item in fval.items():
                    try:
                        nval[ikey] = item.save(d)
                    except AttributeError:
                        nval[ikey] = item
                return nval
            else:
                return fval

    key = '_*%s_%s' % (obj.__class__.__name__, id(obj))
    if key in d:
        return key
    sob = {}
    d[key] = sob
    for feat in saved:
        sob[feat] = _save_feature(feat)
    d[key] = sob
    return key


# used only in syntax
def load_lexicon(filename, Constituent, Feature):
    """

    :param filename:
    :param Constituent:
    :param Feature:
    :return:
    """
    dict = {}
    try:
        file = open(filename, 'r')
    except IOError:
        print('FileNotFound: %s' % filename)
        return dict
    constituent = None
    constituent_id = ''
    for line in file.readlines():
        line = line.strip()
        if line.startswith('#'):
            continue

        split_char = ''
        for letter in line:
            if letter == '+' or letter == '-' or letter == '=':
                split_char = letter
                break
        if split_char and constituent:
            splitted = line.split(split_char, 1)
            key, value_list = splitted[0].strip(), splitted[1].strip().split(' ')
            base_value = split_char
            feature = Feature(key, base_value)
            constituent.set_feature(key, feature)
            # print "added feature %s:%s to '%s'" % (key, base_value, constituent.id)

        else:
            constituent_id = line.strip()
            if constituent_id:
                constituent = Constituent(constituent_id)
                dict[constituent_id] = constituent
    return dict


# used only in syntax
def save_lexicon(lexicon, filename):
    """

    :param lexicon:
    :param filename:
    :return:
    """
    try:
        file = open(filename, 'w')
    except IOError:
        print('IOError: %s' % filename)
        return
    keys = list(lexicon.keys())
    keys.sort()
    for key in keys:
        constituent = lexicon[key]
        file.write('%s\n' % key)
        for feature in constituent.features.values():
            file.write('%s\n' % feature)
        file.write('\n')
    file.close()


# def linearize(node):
# res = []
# for n in node:
# if n not in res:
# res.append(n)
# return res

def next_free_index(indexes):
    """

    :param indexes:
    :return:
    """
    letters = [c for c in indexes if len(c) == 1 and c in string.ascii_letters]
    # 1 -- default i
    if not letters:
        return 'i'
    # 2 -- see if there is existing pattern and continue it
    letters.sort()
    last_index = string.ascii_letters.index(letters[-1])
    if len(string.ascii_letters) > last_index + 2:
        return string.ascii_letters[last_index + 1]
    else:
        # 3 -- try to find first free letter
        for c in string.ascii_letters:
            if c not in letters:
                return c
    # 4 -- return running number
    return len(indexes)


def print_derivation_steps(objects=gc.garbage, outstream=sys.stdout, show_progress=True):
    """



    :param objects:
    :param outstream:
    :param show_progress:
    objects:       A list of objects to find derivation_steps in.  It is often useful
                   to pass in gc.garbage to find the derivation_steps that are
                   preventing some objects from being garbage collected.
    outstream:     The stream for output.
    show_progress: If True, print the number of objects reached as they are
                   found.
    """

    def print_path(path):
        """

        :param path:
        """
        for i, step in enumerate(path):
            # next "wraps around"
            next = path[(i + 1) % len(path)]

            outstream.write("   %s -- " % str(type(step)))
            if isinstance(step, dict):
                for key, val in step.items():
                    if val is next:
                        outstream.write("[%s]" % repr(key))
                        break
                    if key is next:
                        outstream.write("[key] = %s" % repr(val))
                        break
            elif isinstance(step, list):
                outstream.write("[%d]" % step.index(next))
            elif isinstance(step, tuple):
                outstream.write("[%d]" % list(step).index(next))
            else:
                outstream.write(repr(step))
            outstream.write(" ->\n")
        outstream.write("\n")

    def recurse(obj, start, all, current_path):
        """

        :param obj:
        :param start:
        :param all:
        :param current_path:
        """
        if show_progress:
            outstream.write("%d\r" % len(all))

        all[id(obj)] = None

        referents = gc.get_referents(obj)
        for referent in referents:
            # If we've found our way back to the start, this is
            # a derivation_step, so print it out
            if referent is start:
                print_path(current_path)

            # Don't go back through the original list of objects, or
            # through temporary references to the object, since those
            # are just an artifact of the derivation_step detector itself.
            elif referent is objects or isinstance(referent, FrameType):
                continue

            # We haven't seen this object before, so recurse
            elif id(referent) not in all:
                recurse(referent, start, all, current_path + [obj])

    print('gc:', objects)
    for obj in objects:
        outstream.write("Examining: %r\n" % obj)
        recurse(obj, obj, {}, [])


def quit():
    """


    """
    sys.exit()


def create_shadow_effect(color):
    """


    :param color:
    :return:
    """
    effect = QtWidgets.QGraphicsDropShadowEffect()
    effect.setBlurRadius(20)
    effect.setColor(color)
    effect.setOffset(0, 5)
    effect.setEnabled(False)
    return effect


def print_transform(transform):
    """

    :param transform:
    """
    t = transform

    print('m11:%s m12:%s m13:%s | m21:%s m22:%s m23:%s | m31:%s m32:%s m33:%s | dx:%s dy:%s' % (
        t.m11(), t.m12(), t.m13(), t.m21(), t.m22(), t.m23(), t.m31(), t.m32(), t.m33(), t.dx(), t.dy()))
    print('isRotating:%s isScaling:%s isTranslating:%s' % (t.isRotating(), t.isScaling(), t.isTranslating()))



def import_plugins(prefs, plugins_path):
    """ Find the plugins dir for the running configuration and import all found modules to plugins -dict.
    :return: None
    """
    if not plugins_path:
        return
    plugins_dir = os.listdir(plugins_path)
    print('plugins dir:', plugins_dir)
    sys.path.append(plugins_path)
    for plugin_file in plugins_dir:
        if plugin_file.endswith('.py') and not plugin_file.startswith('__'):
            plugin_name = plugin_file[:-3]
            if plugin_name not in prefs.plugins:
                try:
                    prefs.plugins[plugin_name] = importlib.import_module(plugin_name)
                except:
                    print('import error with:', plugin_name)

    print('Modules imported from plugins: %s' % list(prefs.plugins.keys()))


















