import os
from setuptools import setup

# bigorm
# A BigQuery ORM


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()


setup(
    name="bigorm",
    version="0.0.1",
    description="A BigQuery ORM",
    author="Johan Nestaas",
    author_email="johannestaas@gmail.com",
    license="PROPRIETARY",
    keywords="bigquery orm",
    url="https://github.com/johannestaas/bigorm",
    packages=['bigorm'],
    package_dir={'bigorm': 'bigorm'},
    long_description=read('README.md'),
    classifiers=[
        # 'Development Status :: 1 - Planning',
        # 'Development Status :: 2 - Pre-Alpha',
        'Development Status :: 3 - Alpha',
        # 'Development Status :: 4 - Beta',
        # 'Development Status :: 5 - Production/Stable',
        # 'Development Status :: 6 - Mature',
        # 'Development Status :: 7 - Inactive',
    ],
    install_requires=[
        "google-cloud-bigquery",
    ],
)
