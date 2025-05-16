#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标普500指数技术指标监控系统
监控多种技术指标包括均线交叉、MACD、RSI、VIX等，自动发送分析提醒
"""

import os
import time
import datetime
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.font_manager import FontProperties
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import requests

# 设置中文字体（MacOS可用"Arial Unicode MS"或"PingFang SC"）
try:
    # 尝试加载中文字体
    chinese_font = FontProperties(family='PingFang SC')
except:
    # 如果失败，使用系统默认字体
    chinese_font = FontProperties()