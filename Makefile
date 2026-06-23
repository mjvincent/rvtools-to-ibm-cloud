.PHONY: run test compile docker-build docker-run docker-health compose-up compose-pull compose-down sample-workbook validate-terraform

PORT ?= 8501
IMAGE ?= rvtools-to-ibm-cloud
APP_IMAGE ?= rvtools-to-ibm-cloud:local
PYTHON ?= $(shell if [ -x venv/bin/python ]; then echo venv/bin/python; else echo python3; fi)

run:
	$(PYTHON) -m streamlit run app.py

test:
	$(PYTHON) -m pytest

compile:
	$(PYTHON) -m py_compile app.py streamlit_app/*.py rvtools/*.py handoff/*.py models/*.py

docker-build:
	docker build -t $(IMAGE) .

docker-run:
	docker run --rm -p $(PORT):8501 $(IMAGE)

docker-health:
	for attempt in 1 2 3 4 5 6 7 8 9 10; do \
		if curl --fail --silent --show-error http://localhost:$(PORT)/_stcore/health; then \
			exit 0; \
		fi; \
		echo "Waiting for Streamlit health endpoint ($$attempt/10)..."; \
		sleep 2; \
	done; \
	exit 1

compose-up:
	APP_IMAGE=$(APP_IMAGE) docker compose up --build --detach

compose-pull:
	APP_IMAGE=ghcr.io/mjvincent/rvtools-to-ibm-cloud:latest docker compose up --detach

compose-down:
	docker compose down

sample-workbook:
	$(PYTHON) scripts/generate_sample_workbook.py

validate-terraform:
	$(PYTHON) scripts/validate_terraform_package.py --init-validate
