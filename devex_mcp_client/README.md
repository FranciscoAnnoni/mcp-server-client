# Devex MCP Client

Bridge Client for Devex MCP.

## Arquitectura

Este proyecto está dividido en dos componentes, en esste caso estamos dentro del componente "cliente"

- **Cliente (`devex_mcp_client`)**: Administra las credenciales de usuario y el token de autenticación. Actúa como puente entre Claude Desktop y el servidor MCP.

## Configuración de Credenciales

El cliente utiliza [keyring](https://github.com/jaraco/keyring), una librería específica para garantizar el almacenamiento seguro de credenciales en el sistema operativo (Keychain en macOS, Credential Manager en Windows, Secret Service en Linux).

### Configurar credenciales (ejecutar una sola vez)

**Si tienes el proyecto clonado localmente:**

```bash
uv run --directory devex_mcp_client devex-mcp configure
```

**Si quieres usar el cliente desde el repositorio remoto (Recomendado):**

```bash
uvx --from "git+https://github.com/rappi-inc/devex-mcp.git@develop#subdirectory=devex_mcp_client" devex-mcp configure
```

Este comando te solicitará tu usuario y contraseña, los cuales se almacenarán de forma segura usando `keyring`.

## Configuración en Claude Desktop

Para usar el cliente en Claude Desktop sin clonar el repositorio, agrega lo siguiente a tu `claude_desktop_config.json`:

```json
"devex-mcp": {
  "command": "uvx",
  "args": [
    "--refresh",
    "--from",
    "git+https://github.com/rappi-inc/devex-mcp.git@develop#subdirectory=devex_mcp_client",
    "devex-mcp",
    "start"
  ]
}
```

Este comando te solicitará tu usuario y contraseña, los cuales se almacenarán de forma segura usando `keyring`. El cliente automáticamente gestionará la obtención y renovación del token de autenticación.
