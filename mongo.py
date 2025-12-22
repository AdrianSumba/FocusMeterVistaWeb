from pymongo import MongoClient
import streamlit as st

#@st.cache_resource
#def get_mongo_client():
#    uri = st.secrets["MONGO_URI"]
#    client = MongoClient(uri)
#    return client

def get_mongo_client():
    uri = "mongodb+srv://Adrian_bd:Administrador31.@base.f1r4j33.mongodb.net/Base?retryWrites=true&w=majority"
    client = MongoClient(uri)
    return client