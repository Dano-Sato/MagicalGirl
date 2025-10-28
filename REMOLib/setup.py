from setuptools import setup, find_packages

setup(
    name='REMOLib',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'numpy',    # 필요한 라이브러리 목록
        'pandas',
        'pygame-ce',
        'moderngl',
        'screeninfo>=0.8.0'
        # 'other-package>=1.0.0',  # 특정 버전 이상이 필요할 때
    ],
    author='Dano Sato',
    author_email='uchang01@gmail.com',
    description='Python GUI & 2D Game Library, REMO Library (Real Mono Inc. presents)',
    url='https://github.com/Dano-Sato/REMO-Engine-with-100-Examples-Pygame-',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: Windows 10',
    ],
    python_requires='>=3.10',  # 최소 파이썬 버전
)
