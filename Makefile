# /!\ WARNING: you should not have spaces in the path to this directory for the following command to work
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))

deploy:
	sudo fn deploy --create-app --all --local --no-bump

update:
	git fetch
	git pull