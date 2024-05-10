do:
	export PYTHONDONTWRITEBYTECODE=1
	export PYTHONUNBUFFERED=1
	uvicorn main:app --port 80 --host 0.0.0.0