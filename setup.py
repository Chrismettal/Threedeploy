import site
import sys
site.ENABLE_USER_SITE = "--user" in sys.argv[1:]

from setuptools import setup

if __name__ == "__main__":
    setup()