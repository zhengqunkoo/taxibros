from setuptools import setup

setup(name='taxibros',
      version='0.0.1',
      description='Instantly query taxi arrival times',
      url='http://github.com/zhengqunkoo/taxibros',
      author='zhengqunkoo',
      author_email='zhengqun.koo@gmail.com',
      packages=['taxibros'],
      install_requires=[
          'bson',
      ],
      zip_safe=False)
