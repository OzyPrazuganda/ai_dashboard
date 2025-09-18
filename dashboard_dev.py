import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import logging
import pyperclip
import datetime
import difflib
import json

# from backend.kula.chatbot_optimized import ChatbotOptimized
from utils_aggregation import aggregate_csat, aggregation_ratio, aggregate_sum, sidebar_filters, aggregate_table_with_granularity
from streamlit_chatbox import *
from st_aggrid import AgGrid
from st_aggrid.grid_options_builder import GridOptionsBuilder
from collections import defaultdict
from datetime import datetime, timedelta
logging.getLogger('streamlit.runtime.scriptrunner').setLevel(logging.ERROR)

CURRENT_THEME = "light" 
IS_DARK_THEME = False
st.set_page_config(layout="wide")

team = st.sidebar.radio('Team', ['QC'])

if team == 'QC':
    # st.markdown('#####')

    page = st.sidebar.selectbox("Pages", ['Validator'])

    if page == 'Validator':
        st.title("Validator Stats")