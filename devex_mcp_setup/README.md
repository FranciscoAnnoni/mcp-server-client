# DevEx MCP Setup 🛠️

Este módulo es una herramienta auxiliar diseñada para simplificar la instalación y configuración del entorno necesario para utilizar el cliente **DevEx MCP**.

Su objetivo principal es automatizar tareas repetitivas como la gestión de credenciales y la configuración de los archivos JSON de los distintos IDEs compatibles.

## 📦 Contenido

El módulo consta de tres archivos principales:

1.  **`installer.py`**: El script principal escrito en Python. Contiene toda la lógica para:
    *   Detectar el sistema operativo (macOS, Windows, Linux).
    *   Gestionar credenciales de manera segura usando el llavero del sistema (Keyring) a través de `uvx`.
    *   Detectar y modificar los archivos de configuración de múltiples IDEs (Claude Desktop, VS Code, Antigravity, JetBrains).
    *   Realizar copias de seguridad (backups) de las configuraciones existentes antes de modificarlas.

2.  **`setup.sh`**: Script de entrada para sistemas **UNIX (macOS / Linux)**. Se encarga de:
    *   Verificar si `uv` está instalado.
    *   Instalar `uv` automáticamente si no se encuentra.
    *   Ejecutar `installer.py` en un entorno aislado.

3.  **`setup.bat`**: Script de entrada para sistemas **Windows**. Realiza las mismas funciones que `setup.sh` pero adaptado para la consola de Windows (CMD/PowerShell).

## 🚀 Uso

### ⚡ Instalación Rápida

1.  **Conéctate a la VPN de Rappi**. 🔒
2.  Ejecuta el siguiente comando en tu terminal:

**macOS:**
```bash
curl https://api.platform.rappi.com/v1/devex-mcp/install | bash
```

**Windows (PowerShell):**
```powershell
irm https://api.platform.rappi.com/v1/devex-mcp/install.ps1 | iex
```

### 📦 Instalación Manual (desde este repositorio)

### Prerrequisitos

*   Tener acceso a internet.
*   (Opcional) Tener instalado `uv`. Si no lo tienes, los scripts de setup lo instalarán por ti.

### Instalación en macOS / Linux

1.  Abre una terminar en este directorio:
    ```bash
    cd devex_mcp_setup
    ```
2.  Dale permisos de ejecución al script (solo la primera vez):
    ```bash
    chmod +x setup.sh
    ```
3.  Ejecuta el script:
    ```bash
    ./setup.sh
    ```

### Instalación en Windows

1.  Abre una terminal (CMD o PowerShell) en este directorio.
2.  Ejecuta el script:
    ```cmd
    setup.bat
    ```
    *O simplemente haz doble click sobre el archivo `setup.bat` desde el explorador de archivos.*

## ✨ Funcionalidades del Instalador

Una vez ejecutado, verás un menú interactivo con las siguientes opciones:

1.  **✨ Full Installation (Creds + IDE)**: Configura tanto las credenciales de Rappi como la integración con tu IDE favorito en un solo paso.
2.  **🔐 Credentials Only**: Solo configura las credenciales (guarda usuario y contraseña en el Keyring).
3.  **⚙️ IDE Config Only**: Solo inyecta la configuración del MCP server en el archivo JSON de tu IDE.
4.  **0. Exit**: Salir.

### IDEs Soportados

El instalador puede configurar automáticamente:
*   🟠 **Claude Desktop**
*   🔵 **VS Code** (extensión MCP)
*   🟣 **Antigravity**
*   🟢 **JetBrains** (IntelliJ, PyCharm, WebStorm, GoLand - vía GitHub Copilot)

> **Nota:** El instalador siempre crea una copia de respaldo (`.json.bak`) antes de modificar cualquier archivo de configuración.
