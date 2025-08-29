# Install UV

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

# Create virtual env

```sh
# uv supports creating virtual environments, e.g., to create a virtual environment at .venv
uv venv
# A specific name or path can be specified, e.g., to create a virtual environment at my-name
uv venv my-name
# A Python version can be requested, e.g., to create a virtual environment with Python 3.11
uv venv --python 3.11
```

# Install packages from pyproject.toml

```sh
#Install from a pyproject.toml file (recommended)
uv pip install -r pyproject.toml
#Install from a requirements.txt file
uv pip install -r requirements.txt
```

# Run the app

```sh
# Don't forget to activate virtual envirnoment
python main.py
```

# Adding Packages to pyproject.toml

```sh
uv add <package-name>
```

# Detect schema/ Generate migrations changes

```sh
alembic revision --autogenerate
```

# run migrations

```sh
alembic upgrade head
```

# Freeze env in requirments.txt file

```sh
uv pip compile pyproject.toml -o requirements.txt
```

# Download optional/dev deps

```sh
uv sync --extra dev
```

# run all tests

```sh
pytest
```
