FROM python:3.13-slim

# Set working directory
WORKDIR /app
ENV PYTHONPATH=/app

# Copia solo archivos necesarios
COPY devex_mcp/ devex_mcp/
COPY requirements.txt ./
COPY devex_mcp_setup/ devex_mcp_setup/

# Instala dependencias con pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 8000

# Run the server
CMD ["python", "devex_mcp/server.py"]
