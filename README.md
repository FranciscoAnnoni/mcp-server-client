# devex-mcp
**Team:** core-services  
**Entorno:** Shared Services (DevEX)

📚 **[Documentación completa en Confluence](https://rappidev.atlassian.net/wiki/spaces/SHS/pages/4864868376/MCP+DevEx)**

## 📖 Descripción

Este repositorio está compuesto principalmente por dos partes: el **cliente** y el **servidor**.

Sin embargo, cuenta con un tercer módulo llamado `devex_mcp_setup`, cuya función es gestionar la instalación y la configuración del entorno necesario para la correcta ejecución del MCP.

Aunque los módulos de cliente y servidor son los componentes centrales del sistema, `devex_mcp_setup` cumple un rol esencial al facilitar la preparación del ecosistema.

*En este documento analizaremos principalmente el servidor, ya que el cliente cuenta con su propia documentación.*

### Servidor:
Este MCP (Model Context Protocol) server permite a los LLMs (Large Language Models) consultar y analizar la documentación OpenAPI/Swagger de cualquier microservicio de Rappi de forma automática y estructurada.

**¿Para qué sirve?**  
Facilita que herramientas de IA (como GitHub Copilot, Claude, ChatGPT) puedan:
- 🤖 Obtener información actualizada sobre APIs de Rappi sin búsquedas manuales
- 📚 Entender contratos de servicios (endpoints, parámetros, schemas)
- 🔍 Ayudar a desarrolladores a integrar servicios correctamente
- ✅ Validar que la documentación OpenAPI esté disponible y sea válida

**Casos de uso:**
- Un desarrollador pregunta: *"¿Cómo uso el API de delayed-tasks?"* → El LLM consulta este MCP y obtiene toda la especificación OpenAPI
- Validación automática de que un microservicio exponga correctamente su documentación
- Análisis de dependencias entre servicios basándose en sus contratos

## Características

Este MCP server proporciona una herramienta (tool) para:
- 📋 Obtener la especificación OpenAPI/Swagger completa de cualquier microservicio
- 🔗 Ver todos los endpoints disponibles con sus métodos HTTP
- 📦 Explorar los schemas de datos (request/response)
- 🔧 Extraer información de autenticación y requisitos del API

## 🚀 Instalación y Configuración

### ⚡ Instalación Rápida (Usuarios)

1.  **Conéctate a la VPN de Rappi**. 🔒
2.  Ejecuta el siguiente comando en tu terminal (esto instalará el cliente y configurará el MCP para tu IDE):

**macOS:**
```bash
curl https://api.platform.rappi.com/v1/devex-mcp/install | bash
```

**Windows (PowerShell):**
```powershell
irm https://api.platform.rappi.com/v1/devex-mcp/install.ps1 | iex
```

### 🛠️ Configuración Manual / Desarrollo

### 1. Instalar dependencias

Desde la raíz del repositorio:

```bash
uv sync
```

### 2. Configurar variables de entorno

Crear un archivo `.env` en la raíz del repositorio (`/devex-mcp/.env`) con las siguientes variables:

#### Variables Requeridas

```bash
# Modo de transporte del MCP server
# Opciones: "stdio" (desarrollo local) | "streamable-http" (producción)
TRANSPORT=streamable-http

# Host donde se levanta el servidor (solo para streamable-http)
HOST=0.0.0.0

# Puerto del servidor (solo para streamable-http)
PORT=8000

# Path HTTP del endpoint MCP (solo para streamable-http)
HTTP_PATH=/api/devex-mcp

# URL del API de descriptors-analyzer (servicio que almacena los OpenAPI specs)
DESCRIPTORS_API_URL=https://api.platform.rappi.com/api/descriptors-analyzer

# Timeout en segundos para las peticiones al API
DESCRIPTORS_API_TIMEOUT=30
```

#### Ejemplo para Desarrollo Local (.env)

```bash
TRANSPORT=stdio
```

#### Ejemplo para Producción (.env)

```bash
TRANSPORT=streamable-http
HOST=0.0.0.0
PORT=8000
HTTP_PATH=/api/devex-mcp
DESCRIPTORS_API_URL=https://api.platform.rappi.com/api/descriptors-analyzer
DESCRIPTORS_API_TIMEOUT=30
```

## 🎯 Uso

**Importante:** Todos los comandos deben ejecutarse desde la raíz del repositorio (`/devex-mcp/`).

### Modo Desarrollo (Local con stdio)

```bash
uv run mcp dev devex_mcp/server.py
```

### Modo Producción (HTTP server)

```bash
uv run python devex_mcp/server.py
```

El servidor estará disponible en:
- **Health check:** `http://localhost:8000/api/devex-mcp/health`
- **MCP endpoint:** `http://localhost:8000/api/devex-mcp/`

### Con Docker Compose

#### Levantar el contenedor

```bash
# Build y levantar en background
docker-compose up --build -d

# Ver logs en tiempo real
docker-compose logs -f devex-mcp

# Ver estado del contenedor
docker-compose ps
```

#### Detener el contenedor

```bash
# Detener y eliminar contenedor (mantiene la imagen)
docker-compose down

# Detener, eliminar contenedor y eliminar volúmenes
docker-compose down -v
```

#### Health check

```bash
curl http://localhost:8000/api/devex-mcp/health
```

## 🔧 Tool Disponible

### `fetch_api_swagger`

Obtiene la especificación completa OpenAPI/Swagger de un microservicio de Rappi.

**Parámetros:**
- `microserviceName` (string, requerido): Nombre del microservicio en Rappi
  - Ejemplos: `"delayed-tasks-api"`, `"cms-gateway"`, `"etc.."`

**Retorna (JSON):**
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

## 🧪 Testing y Calidad de Código

Este proyecto cumple con los requisitos de producción de DevEX:

- **Tests unitarios**: 25 tests implementados
- **Coverage**: **100%** 🎯
- **Configuración SonarQube**: ✅

### Comandos

```bash
# 1. Sincronizar dependencias (incluyendo pytest)
uv sync --all-extras

# 2. Ejecutar tests
uv run pytest

# 3. Ejecutar tests con coverage
uv run pytest --cov=devex_mcp --cov-report=html --cov-report=term
# para ver el coverage
open htmlcov/index.html

# 4. Análisis de SonarQube (requiere sonar-scanner instalado)
uv run pytest --cov=devex_mcp --cov-report=xml
sonar-scanner
```

### Resultados

- **25 tests pasando** ✅
- **100% coverage** en todo el código productivo
- Los archivos generados (`htmlcov/`, `coverage.xml`, `.coverage`) están en `.gitignore`