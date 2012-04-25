#!/home/zhangcg/local/python/bin/python
# -*- coding:utf-8 -*-
'''MFEprimer-2.0


by Wubin Qu <quwubin@gmail.com>,
Copyright @ 2011-2012, All Rights Reserved.
'''

from wsgiref.handlers import CGIHandler
from MFEprimerWeb import app

CGIHandler().run(app)
