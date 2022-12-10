# TransiSHOW

> Your best partner to create your amaizing show!!

## Requirements

- `poetry`
- `python v3.10+`
- Postgress Library
  - Ubuntu: `sudo apt install libpq-dev python-dev`
  - Mac: `brew install postgresql`
  - Arch: `sudo pacman -S postgresql-libs`
- `pnpm`

## Installation

```sh
$ git clone git@github.com:pysan3/transishow.git
$ cd transishow
```

### Install Frontend

```sh
# Inside transishow/
$ pnpm install
```

### Install Backend

```sh
# Inside transishow/
$ poetry install
$ poetry shell
```

## Development

### Do Once

- `cp dotenv .env`
- Reconfigure the keys.

### Start Working

```sh
# Set the env vars
# INFO: Run this on every shell
$ set -a && source *.env; set +a

# Setup Database
$ alembic upgrade head

# Auto generate api definitions for frontend
$ pnpm run openapi-gen

# Run development server for frontend / backend
$ pnpm run dev & uvicorn main:app --reload
```
