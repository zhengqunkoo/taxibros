from setuptools import setup, find_packages
from taxibros import __version__

setup(
    name='taxibros',
    version=__version__,
    description='Instantly query taxi arrival times',

    url='http://github.com/zhengqunkoo/taxibros',
    author='zhengqunkoo',
    author_email='zhengqun.koo@gmail.com',

    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'coverage',
        'coverage-badge',
        'django',
        'django-dotenv',
        'django-background-tasks',
        'psutil',
        'requests',
    ],
    zip_safe=False
)
