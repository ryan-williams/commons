#!/bin/bash
# Script running for phabricator arcanist command-line tool.
# This checks to see if it's been installed. If not, it downloads and
# installs phabricator.
# In any case, it then runs the installed phabricator arc script.

PHAB_DIR=build-support/arc/phab

if [ ! -e "$PHAB_DIR" ]; then
  mkdir -p $PHAB_DIR
  cd $PHAB_DIR
  git clone git://github.com/facebook/libphutil.git
  git clone git://github.com/facebook/arcanist.git
  cd ../..
fi

if [ "$1" == "update" ]; then
  echo "Performing update"
  (cd $PHAB_DIR/libphutil ; git pull --rebase)
  (cd $PHAB_DIR/arcanist ; git pull --rebase)
elif [ "$1" == "push" ]; then
  ./arc.sh amend && git pull --rebase && git push origin master
elif [ "$1" == "audit" ]; then
  if [ -z "$2" ]; then
    echo -e "Too few arguments!\nList some auditors (comma separated, please)."
    exit 1
  fi
  if [ "$3" ]; then
    echo -e "Too many arguments!\nAuditors should be separated by a comma (i.e. no spaces)"
    exit 1
  fi
  old_msg=`git log -1 --pretty=format:%B`
  echo -e "${old_msg}" | grep '^Auditors:' &> /dev/null
  if [ $? == 0 ]; then
    echo "Commit message already had auditors, replacing"
    new_msg=`echo -e "${old_msg}" | sed "s/^Auditors:.*$/Auditors: ${2}/"`
    git commit --amend -m "${new_msg}"
  else
    git commit --amend -m "${old_msg}

Auditors: ${2}"
  fi
  git fpush origin master
else
  $PHAB_DIR/arcanist/bin/arc $*
fi
