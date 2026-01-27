# DevEx-MCP
**Team:** core-services  
**Created by:** Francisco Annoni  
**Entorno:** Shared Services (DevEX)

📚 **[Documentación completa en Confluence](https://rappidev.atlassian.net/wiki/spaces/SHS/pages/4864868376/MCP+DevEx)**

## 📖 Descripción

**DevEx-MCP** es la herramienta que conecta tu agente de IA (GitHub Copilot, Claude, etc.) con la documentación de los microservicios de Rappi.

![DevEx-MCP Architecture](/Users/francisco.annoni/.gemini/antigravity/brain/6885a29f-ae1b-4a51-ae22-0d4ac78b98f9/uploaded_media_1769476623779.png)

Este MCP (Model Context Protocol) server permite a los LLMs (Large Language Models) consultar y analizar automáticamente:
- 📋 Especificaciones OpenAPI/Swagger de microservicios
- 📚 Catálogo de microservicios de Rappi
- 📖 READMEs de los servicios

## 🎯 Objetivo

**Ahorrarte tiempo.** Ya no necesitas buscar documentación manual ni copiar y pegar contexto. Esta herramienta permite que el LLM consulte automáticamente Swaggers, Contratos y READMEs de los microservicios para entender los requerimientos y generarte la función perfecta.

### ⚠️ Aclaración Importante

El MCP solo puede obtener información de microservicios que estén correctamente documentados.

**Tu documentación es clave:** Al mantenerla al día, permites mejorar el funcionamiento de este MCP y de futuras herramientas del ecosistema. Si tu microservicio no está documentado o simplemente no sabes cómo hacerlo, consulta la guía de documentación.

👉 **[Guía: Cómo documentar correctamente los microservicios](https://rappidev.atlassian.net/wiki/spaces/SHS/pages/4864868376/MCP+DevEx)**

## 🚀 Instalación

### Pasos para la Instalación

1. **Conectarse a la VPN de Rappi** 🔒 (dev/prod - da lo mismo)

2. **Ejecutar el siguiente comando** en la consola y seguir los pasos del instalador:

**macOS:**
```bash
curl https://api.platform.rappi.com/v1/devex-mcp/install | bash
```

**Windows (PowerShell):**
```powershell
irm https://api.platform.rappi.com/v1/devex-mcp/install.ps1 | iex
```

El instalador se encargará de:
- ✅ Instalar el cliente MCP
- ✅ Configurar automáticamente tu IDE (VS Code, Cursor, etc.)
- ✅ Establecer la conexión con el servidor

## 🏗️ Composición del Proyecto

Este repositorio está compuesto por **dos componentes principales** y un **módulo de instalación**:

### 1. 🖥️ Servidor (`devex_mcp/`)

El servidor MCP que expone las herramientas (tools) para que los LLMs puedan consultar información de los microservicios.

#### Herramientas Disponibles

El servidor proporciona **3 herramientas principales**:

##### 🔍 `search_microservices`
Busca microservicios en el Catálogo de Rappi basándose en un nombre, coincidencia parcial o descripción.

**Cuándo usar:**
- Como PRIMER paso cuando la solicitud es vaga (ej: "algo para pagos")
- Para encontrar el nombre exacto en kebab-case si el usuario proporciona un nombre legible

**Parámetros:**
- `possible_service_name` (string): Término de búsqueda (ej: 'order', 'payment', 'cms-gateway')

**Retorna:**
```json
{
  "service_name": "nombre-del-servicio",
  "repository": "https://github.com/rappi/...",
  "metadata": {
    "area": "...",
    "team": "...",
    "tier": "..."
  }
}
```

**🔐 Autenticación:** Requiere token de usuario (header `X-Rappi-Token`)

---

##### 📖 `fetch_readmes`
Obtiene los archivos README de una lista de microservicios para analizar su funcionalidad en profundidad.

**Cuándo usar:**
- Para desambiguar entre servicios similares encontrados en la búsqueda
- Cuando el usuario pregunta "¿Qué hace el servicio X?" o "¿Cómo usar X?"

**Parámetros:**
- `service_names` (List[str]): Lista de nombres exactos de microservicios

**Retorna:**
```json
[
  {
    "microservice": "nombre-del-servicio",
    "readme": "Contenido completo o truncado del README"
  }
]
```

**💡 Tip:** No obtener READMEs de TODOS los resultados de búsqueda. Seleccionar solo los 3-5 candidatos más prometedores.

**🔐 Autenticación:** No requiere token

---

##### 📋 `fetch_api_swagger`
Obtiene la especificación completa OpenAPI/Swagger de un microservicio específico de Rappi.

**Cuándo usar:**
- SOLO cuando se ha identificado el microservicio correcto
- Esencial para tareas que requieren endpoints específicos, estructuras de payload o métodos de autenticación

**Parámetros:**
- `microservice_name` (string): Nombre exacto del microservicio (ej: 'delayed-tasks-api')

**Retorna:**
```json
{
  "microservice": "Título del API",
  "version": "1.0.0",
  "last_updated": "2025-11-06T12:00:00.000Z",
  "openapi_spec": {
    "openapi": "3.0.0",
    "info": { ... },
    "paths": { ... },
    "components": {
      "schemas": { ... }
    }
  }
}
```

**Información incluida:**
- ✅ Título y versión del API
- ✅ Fecha de última actualización
- ✅ Lista completa de endpoints con métodos HTTP
- ✅ Parámetros de entrada (query, path, body)
- ✅ Schemas de request/response
- ✅ Códigos de respuesta (200, 400, 500, etc.)
- ✅ Modelos de datos (schemas)

**🔐 Autenticación:** No requiere token

---

### 2. 💻 Cliente (`devex_mcp_client/`)

El cliente MCP que se instala en tu máquina y se conecta con tu IDE para comunicarse con el servidor.

📚 **[Ver documentación completa del cliente](devex_mcp_client/README.md)**

El cliente se encarga de:
- Establecer la conexión con el servidor MCP
- Gestionar la autenticación del usuario
- Mantener la sesión activa
- Auto-actualizarse cuando hay nuevas versiones

---

### 3. ⚙️ Instalador (`devex_mcp_setup/`)

Componente de auto-instalación que configura automáticamente la herramienta en las computadoras de los usuarios.

**Archivos de instalación:**
- `setup.sh` - Script de instalación para macOS/Linux
- `setup.ps1` - Script de instalación para Windows (PowerShell)

Estos scripts se sirven automáticamente desde el servidor en:
- `https://api.platform.rappi.com/v1/devex-mcp/install` (macOS/Linux)
- `https://api.platform.rappi.com/v1/devex-mcp/install.ps1` (Windows)

## 🛠️ Desarrollo

### Requisitos Previos

- Python 3.10+
- `uv` (gestor de paquetes)
- Docker (opcional, para desarrollo con contenedores)

### Instalación para Desarrollo

```bash
# 1. Clonar el repositorio
git clone https://github.com/rappi-inc/devex-mcp.git
cd devex-mcp

# 2. Instalar dependencias
uv sync

# 3. Ejecutar en modo desarrollo
uv run mcp dev devex_mcp/server.py
```

### Variables de Entorno

Las variables de entorno están configuradas en el `docker-compose.yml` para producción. Para desarrollo local, puedes crear un archivo `.env`:

```bash
# Modo de transporte (stdio para desarrollo local)
TRANSPORT=stdio
```

### Ejecutar con Docker

```bash
# Levantar el contenedor
docker-compose up --build -d

# Ver logs
docker-compose logs -f devex-mcp

# Health check
curl http://localhost:8000/api/devex-mcp/health
```

## 🧪 Testing y Calidad de Código

Este proyecto cumple con los requisitos de producción de DevEX:

- **Tests unitarios**: 25 tests implementados
- **Coverage**: **100%** 🎯
- **Configuración SonarQube**: ✅

### Comandos de Testing

```bash
# Sincronizar dependencias (incluyendo pytest)
uv sync --all-extras

# Ejecutar tests
uv run pytest

# Ejecutar tests con coverage
uv run pytest --cov=devex_mcp --cov-report=html --cov-report=term

# Ver reporte de coverage
open htmlcov/index.html

# Análisis de SonarQube
uv run pytest --cov=devex_mcp --cov-report=xml
sonar-scanner
```

## 📞 ¿Necesitas Ayuda?

Como siempre, quedamos atentos a cualquier duda o feedback que puedan tener:
- 💬 Consulta en el canal de Slack del equipo
- 🏷️ Menciona a `@platform-product-guild`

---

**Creado con ❤️ por el equipo de DevEX**
