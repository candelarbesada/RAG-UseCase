# V.1 - BASE

La V.1 - BASE es la primera versión funcional de Gala Assistant: una aplicación local que presenta a Alfred, un asistente para una gala ficticia, mediante una interfaz de chat en Streamlit.

El usuario puede preguntar por los invitados incluidos en un dataset Parquet, material público del [Hugging Face AI Agents Course](https://huggingface.co/learn/agents-course). El agente recupera información relevante con BM25 y combina ese contexto con un modelo local `qwen2.5`, ejecutado mediante Ollama. También dispone de herramientas para buscar en la web, leer páginas y consultar el tiempo actual.

La versión incluye:

- Una interfaz Streamlit con preguntas sugeridas, entrada manual siempre disponible, conversación y traza operativa de la sesión.
- Las relaciones del dataset se interpretan desde el punto de vista del usuario del dashboard, Bruce Wayne.
- Memoria en proceso aislada por conversación: LangGraph conserva el estado y el agente recibe hasta seis mensajes previos de usuario/Alfred (máximo 1.000 caracteres por mensaje). El usuario del escenario es Bruce Wayne. Al limpiar el escritorio se borra ese checkpoint; la memoria no sobrevive al reinicio del proceso.
- Los nombres de invitados se detectan en cualquier posición de la pregunta, incluidas preguntas sobre relación. Las respuestas de relación se basan directamente en el campo `Relation` del registro, relativo a Bruce Wayne.
- Si Ollama rechaza la conexión, el dashboard muestra instrucciones para iniciar el servicio o descargar `qwen2.5`, en lugar de presentar la traza HTTP al usuario.
- Un flujo de agente construido con LangGraph.
- Recuperación de información de invitados desde `data/gala-invitees.parquet`.
- Herramientas de búsqueda web, lectura de páginas y consulta meteorológica.
- Instrucciones de instalación y ejecución local para Windows en el [README principal](../README.md).

Esta versión sirve como base para desarrollar y probar el caso de uso. Requiere Ollama y el modelo `qwen2.5` en la máquina local; las herramientas web y meteorológicas dependen de servicios externos. La memoria solo existe mientras el proceso de la aplicación está activo y no se conserva tras reiniciarlo. Antes de redistribuir el dataset, hay que comprobar la licencia y los requisitos de atribución del material del curso.
