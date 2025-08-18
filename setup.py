from setuptools import setup, find_packages

setup(
    name="aes-cm",
    version="0.1",
    author="Eugene Chung",
    author_email="your_email@example.com",
    description="A script to install programs and generate Ansible playbooks.",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ycechungAI/SUP_CM",
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    python_requires='>=3.6',
    install_requires=[
        "python-dotenv",
        "openai",
    ],
    entry_points={
        'console_scripts': [
            'program-installer=program_installer.main:main',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
