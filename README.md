# 📚 API Biblioteca Digital (versión sencilla)

Este proyecto es una API para gestionar una biblioteca digital. La idea es simular cómo funciona una biblioteca real: puedes crear recursos (libros), prestarlos y devolverlos, siempre respetando algunas reglas básicas.

Repositorio de codigo: https://github.com/RodLozano/API_Biblioteca_digital_Monol.git

## 🎯 ¿Qué se quería conseguir?

El objetivo era crear un sistema simple pero realista para practicar el desarrollo de APIs con FastAPI. Las metas principales fueron:

Poder registrar libros o recursos digitales.

Permitir que un usuario pida prestado un recurso.

Devolver el recurso y que automáticamente esté disponible otra vez.

Tener una API limpia y fácil de probar

# 🔧 Tecnologías

Python

FastAPI

SQLite (base de datos local)

SQLAlchemy (manejo de base de datos)

Uvicorn (para ejecutar la API)



# Como usar el repositorio

1 Clonar el repositorio en local con git clone https://github.com/RodLozano/API_Biblioteca_digital_Monol.git

2 Se incluye un requirements.txt para configurar el entorno virtual con las dependencias necesarias, instalar con pip install -r requirements.txt

3 Levantar la aplicacion en local con uvicorn main:app --reload

4 Testear la funcionalidad con el script incluido api-test.py haciendo python api-test.py en la terminal
