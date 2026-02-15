#!/bin/sh

prompt="$1"
case "$prompt" in
  *Username*)
    printf '%s\n' "${GIT_USERNAME:-x-access-token}"
    ;;
  *Password*)
    printf '%s\n' "$CMS_GIT_TOKEN"
    ;;
  *)
    printf '\n'
    ;;
esac
