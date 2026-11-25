.PHONY: demo infra-demo test

demo:
	python3 -B se_factory.py demo

infra-demo:
	python3 -B demo.py

test:
	python3 -B -m unittest discover -s tests -v
