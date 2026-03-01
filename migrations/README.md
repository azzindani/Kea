# 🗄️ Database Migrations

This directory contains the database migration scripts and configuration for Project's PostgreSQL database, managed by **Alembic**.

## 🚀 Usage

Migrations track changes to the database schema (tables, columns, indexes).

### Common Commands

```bash
# Apply all pending migrations (Upgrade to Head)
alembic upgrade head

# Revert the last migration
alembic downgrade -1

# Auto-generate a new migration based on SQLAlchemy model changes
alembic revision --autogenerate -m "verify_user_table_schema"
```

## 📁 Codebase Structure

- **`env.py`**: The Alembic environment script. It configures the database connection and imports the SQLAlchemy `Base` metadata so that Alembic can detect model changes.
- **`script.py.mako`**: The Mako template used to generate new migration files.
- **`versions/`**: Directory containing the individual migration scripts (e.g., `1a2b3c_create_users.py`).

## ⚙️ How It Works

1. **Model Definition**: Database models are defined in `shared/database/models.py` (or service-specific models).
2. **Detection**: When you run `--autogenerate`, Alembic compares the `Base.metadata` in your code against the current state of the database.
3. **Generation**: It generates a Python script in `versions/` with `upgrade()` and `downgrade()` functions.
4. **Execution**: Running `upgrade head` executes the SQL commands in the script.
