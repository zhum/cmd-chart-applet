#!/usr/bin/env python3

from distutils.core import setup

setup(
    name='cmd-chart-applet',
    version='1.0.0',
    description='Custom Command Chart Applet',
    author='Sergey Zhumatiy',
    author_email='sergzhum@gmail.com',
    scripts=['cmd-chart-applet.py'],
    data_files=[
        ('/usr/lib/mate-applets/', ['cmd-chart-applet.py']),
        ('/usr/share/mate-panel/applets/',
         ['org.mate.panel.CmdChartApplet.mate-panel-applet']),
        ('/usr/share/applications/', ['cmd-chart-applet.desktop']),
    ],
)
