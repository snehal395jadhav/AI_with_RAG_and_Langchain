import streamlit as st
import time
import datetime
import threading
import requests
import re

from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
DO IT YOURSELF THIS PROJECT IS FOR SHOWCASE 
