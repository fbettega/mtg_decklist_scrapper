# -*- coding: utf-8 -*-
"""
Created on Sun Nov 24 18:10:12 2024

@author: Francois
"""
import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime, timedelta, timezone
import os
import time
# import sys
from typing import List, Optional
# import html
from dataclasses import dataclass
# from models.Melee_model import *
from models.base_model import *
from comon_tools.tools import *


