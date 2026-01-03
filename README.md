# Seacom-App

An application to allow technicians to submit their reports and noc oporators to assign tasks to technicians.

## 1. Installation / Setup

1. Clone the repository into a folder

    ```bash
    git clone https://github.com/Caff-Core/seacom-app-backend.git
    ```

2. Install uv if you don't have it in your system [UV installation](https://docs.astral.sh/uv/getting-started/installation/)

3. Move into the project folder and run the following command:

    ```bash
    uv pip install -r pyproject.toml
    ```

## 2. Database setup

1. Install Postgresql 18 in your system [Postgresql Download](https://docs.astral.sh/uv/getting-started/installation/)

2. Install pgAdmin4 in your system [PgAdmin Download](https://www.pgadmin.org/download/)

3. After setting up your user password add the following file inside the project folder: `.env`

4. Inside the `.env` file add the following:

    ```bash
    # Database
    DB_HOST="localhost"
    DB_USER="postgres"
    DB_PASSWORD="use the password you set here"
    DB_PORT="5432"
    ```

## 3. Run the application

```bash
uv run uvicorn app.main:app --reload
```
