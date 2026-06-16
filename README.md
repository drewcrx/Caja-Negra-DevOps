# Caja Negra DevOps

Proyecto Flask + Docker enfocado en DevOps. La aplicación simula incidentes de despliegue, genera un diagnóstico, propone acciones de rescate y sugiere un mensaje de commit.

## Ejecutar localmente con Python

```bash
pip install -r requirements.txt
python app.py
```

Abrir:

```text
http://localhost:5000
```

## Ejecutar con Docker

```bash
docker build -t caja-negra-devops .
docker run --rm -p 5000:5000 caja-negra-devops
```

## Ejecutar con Docker Compose

```bash
docker compose up --build
```

## GitHub Actions + Packages

El workflow ubicado en `.github/workflows/docker-publish.yml` construye la imagen Docker y la publica en GitHub Container Registry cuando hay un push a la rama `main`.

Publica dos tags:

- `latest`
- `${{ github.sha }}`

## Endpoint de salud

```text
GET /health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "service": "caja-negra-devops"
}
```
