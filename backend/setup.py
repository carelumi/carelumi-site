from setuptools import setup, find_packages
import src.commands

setup(
    name="BackendDemo",
    version="0.1",
    description="A FastAPI application with SQLAlchemy and S3 integration",
    author="Carelumi tech team",
    url="https://github.com/carelumi/carelumi-site",
    classifiers=[
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(where='src'), 
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,

    # Dependencies
    install_requires=[
        "fastapi>=0.68.0",
        "sqlalchemy>=1.4.0",
        "openai>=0.11.0",
        "boto3>=1.18.0",
        "python-dotenv>=0.19.0",
        "requests>=2.26.0",
        "pydantic>=1.8.0",
    ],

    # Command-line tools or scripts
    entry_points={
        'console_scripts': [
            'loading=commands:backend_successful',
        ],
    },

    python_requires='>=3.6',  # Minimum Python version required
)
