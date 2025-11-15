.PHONY: start stop restart rebuild status test

start:
	python3 scripts/ha_manager.py start

stop:
	python3 scripts/ha_manager.py stop

restart:
	python3 scripts/ha_manager.py restart

rebuild:
	python3 scripts/ha_manager.py rebuild

status:
	python3 scripts/ha_manager.py status

test:
	pytest
