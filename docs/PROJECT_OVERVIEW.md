# V.1 - BASE

La V.1 - BASE es la primera versión funcional de Gala Assistant: una aplicación local que presenta a Alfred, un asistente para una gala ficticia, mediante una interfaz de chat en Streamlit.

El usuario puede preguntar por los invitados incluidos en un dataset Parquet, material público del [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course). El agente recupera información relevante con BM25 y combina ese contexto con un modelo local `qwen2.5`, ejecutado mediante Ollama. También dispone de herramientas para buscar en la web, leer páginas y consultar el tiempo actual.

La versión incluye:

- Una interfaz Streamlit con preguntas sugeridas, conversación y traza operativa de la sesión.
- Un flujo de agente construido con LangGraph.
- Recuperación de información de invitados desde `data/gala-invitees.parquet`.
- Herramientas de búsqueda web, lectura de páginas y consulta meteorológica.
- Instrucciones de instalación y ejecución local para Windows en el [README principal](../README.md).

Esta versión sirve como base para desarrollar y probar el caso de uso. Requiere Ollama y el modelo `qwen2.5` en la máquina local; las herramientas web y meteorológicas dependen de servicios externos. La conversación no se conserva como memoria persistente entre sesiones. Antes de redistribuir el dataset, hay que comprobar la licencia y los requisitos de atribución del material del curso.
