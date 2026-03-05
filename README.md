# Transcap ERP

Sistema de gestión empresarial multiempresa (Django + PostgreSQL).

## Requisitos
- Python 3.x
- PostgreSQL

## Ejecutar local
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver

