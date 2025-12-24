from pymongo import MongoClient
import streamlit as st
from db.modelo import RegistroAtencion

def get_mongo_client():
    uri = "mongodb+srv://Adrian_bd:Administrador31.@base.f1r4j33.mongodb.net/Base?retryWrites=true&w=majority"
    client = MongoClient(uri)
    return client

def insertar_registro_atencion(registro_atencion:RegistroAtencion):
    pass