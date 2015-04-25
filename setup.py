"""
This is a setup.py script generated by py2applet

At the moment it supports building deployable standalone version for OS X. Requires Python3.4, setuptools,
Qt5.4 and PyQt5 on the build machine, but the created app doesn't need them.

Usage for OS X BUILD:
    python3 setup.py py2app

set create_dmg below False if you don't need it and adjust qt_mac to point your Qt installation.

The same script can be used for Windows build ...todo...

"""

import sys
import os
from setuptools import setup
from subprocess import call
import shutil

mainscript = 'Kataja.py'
create_dmg = True
qt_mac = '~/Qt5.4.1/'

DATA_FILES = ['resources']

version_file = open('resources/version.txt', 'r')
version = version_file.readlines()
version_file.close()
version_long = version[0].strip()
version_short = version_long.split('|')[1].strip()


if sys.platform == 'darwin':
    plist = {'CFBundleVersion':version_long,
    'CFBundleShortVersionString':version_short,
    'CFBundleIdentifier':'fi.aalto.jpurma.Kataja',
    'NSHumanReadableCopyright':'GPL 3'}
    OPTIONS = {'argv_emulation': False, 'includes': ['sip'], 'iconfile': 'resources/icons/Kataja.icns', 'plist': plist}
    extra_options = dict(setup_requires=['py2app'],
                         app=[mainscript],
                         data_files=DATA_FILES,
                         options={'py2app': OPTIONS})
    # Check that Qt is available before trying to do anything more:
    if not os.access(os.path.expanduser(qt_mac + '5.4/clang_64/'), os.F_OK):
        raise EnvironmentError(
            'Qt not found from given path ( "%s" => "%s" ).' % (
                qt_mac, os.path.expanduser(qt_mac + '5.4/clang_64/') +
                ' Edit qt_mac variable in setup.py to match your Qt directory.'))

else:
    extra_options = dict(  # Normally unix-like platforms will use "setup.py install"
                           # and install the main script as such
                           scripts=[mainscript], )

setup(name="Kataja", **extra_options)
################################################################
#                   Post-setup repairs                         #
################################################################

if sys.platform == 'darwin':
    print('------- Making OS X-specific fixes to application bundle --------')
    qt_base = os.path.expanduser(qt_mac + '5.4/clang_64/')
    setup_dir = os.path.realpath(__file__)
    filename = __file__.split('/')[-1]
    setup_dir = setup_dir[:-len(filename)]
    print('setup_dir:', setup_dir)
    app_contents = setup_dir + 'dist/Kataja.app/Contents/'
    print('qt_base:', qt_base)
    print('app_contents:', app_contents)
    print('-------deleting _debug -versions of frameworks, if they are included...')
    frameworks = ['QtCore', 'QtGui', 'QtPrintSupport', 'QtWidgets']
    debug_versions = ['%s.framework/%s_debug', '%s.framework/%s_debug.prl', '%s.framework/Versions/5/%s_debug']
    for framework in frameworks:
        for debug_version in debug_versions:
            path = '%sFrameworks/%s' % (app_contents, debug_version % (framework, framework))
            if os.access(path, os.F_OK):
                print('Deleting... ', path)
                os.remove(path)

    os.makedirs(app_contents + 'plugins/platforms', exist_ok=True)
    print('-------Copying libqcocoa.dylib to app...')
    print(shutil.copy(qt_base + 'plugins/platforms/libqcocoa.dylib', app_contents + 'plugins/platforms'))
    print('-------Copying libqcocoa.dylib to app...')
    os.makedirs(app_contents + 'plugins/imageformats', exist_ok=True)
    print(shutil.copy(qt_base + 'plugins/imageformats/libqgif.dylib', app_contents + 'plugins/imageformats'))

    print('-------Fixing libqcocoa.dylib dependencies')
    libq_relative = '@executable_path/../plugins/platforms/libqcocoa.dylib'
    libq_file = app_contents + 'plugins/platforms/libqcocoa.dylib'
    command = 'install_name_tool -id %s %s' % (libq_relative, libq_file)
    print(command)
    call(command, shell=True)

    qt_frameworks = qt_base + 'lib/%s.framework/Versions/5/%s'
    relative_frameworks = '@executable_path/../Frameworks/%s.framework/Versions/5/%s'
    for fr in frameworks:
        command = 'install_name_tool -change %s %s %s' % (
            qt_frameworks % (fr, fr), relative_frameworks % (fr, fr), libq_file)
        print(command)
        call(command, shell=True)

    print('-------Fixing libqgif.dylib dependencies')
    libq_relative = '@executable_path/../plugins/imageformats/libqgif.dylib'
    libq_file = app_contents + 'plugins/imageformats/libqgif.dylib'
    command = 'install_name_tool -id %s %s' % (libq_relative, libq_file)
    print(command)
    call(command, shell=True)
    qt_frameworks = qt_base + 'lib/%s.framework/Versions/5/%s'
    relative_frameworks = '@executable_path/../Frameworks/%s.framework/Versions/5/%s'
    for fr in ['QtCore', 'QtGui']:
        command = 'install_name_tool -change %s %s %s' % (
            qt_frameworks % (fr, fr), relative_frameworks % (fr, fr), libq_file)
        print(command)
        call(command, shell=True)

    print('------- Adding plugins dir inside Kataja.app to enable editable plugins')
    if not os.access(app_contents + 'Resources/lib/plugins', os.F_OK):
        shutil.copytree(setup_dir + 'kataja/plugins', app_contents + 'Resources/lib/plugins')
        print('copying ', setup_dir + 'kataja/plugins', ' to ', app_contents + 'Resources/lib/plugins')
    cache_path = app_contents + 'Resources/lib/plugins/__pycache__'
    if os.access(cache_path, os.F_OK):
        shutil.rmtree(cache_path)
        print('deleting __cache__:', cache_path)
    if create_dmg:
        print('-------- Creating Kataja.dmg --------------------')
        if os.access('Kataja.dmg', os.F_OK):
            os.remove('Kataja.dmg')
        call("hdiutil create -srcfolder dist/Kataja.app Kataja.dmg", shell=True)
    print('---- Done ----')
