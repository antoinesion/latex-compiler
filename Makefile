# /!\ WARNING: you should not have spaces in the path to this directory for the following command to work
ROOT_DIR:=$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
TO_SVG_FUNC_PATH := $(ROOT_DIR)/to-svg
APP_NAME := compile-latex

build: build_to-svg

build_to-svg:
	cd $(TO_SVG_FUNC_PATH) && sudo fn -v build

deploy:
	sudo fn deploy --create-app --all --local --no-bump

