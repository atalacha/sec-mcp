# 1. Official Python Slim Image
FROM python:3.13-slim

# 2. Install UV (Fastest Package Manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# 3. Create App Directory and Copy Files
# Copy EVERYTHING to /app
COPY . /app
WORKDIR /app

# 4. Environment Variables
# Unbuffered output ensures logs appear immediately in Cloud Run console
ENV PYTHONUNBUFFERED=1

# 5. Install Dependencies
# Sync creates the .venv inside /app
RUN uv sync --frozen --no-dev

# 6. Expose the Port (Best Practice)
# Cloud Run sets PORT=8080 by default
EXPOSE 8080

# 7. Run the Server
# 'uv run' automatically finds the .venv and uses the correct python
CMD ["uv", "run", "python", "server.py"]

