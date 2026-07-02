#!/usr/bin/env bash
set -e

uvicorn smartcoat.api.main:app --reload
