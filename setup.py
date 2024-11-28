from setuptools import setup, find_packages

setup(
    name="arcana-agent",
    version="0.1.0",
    description="A flexible, intelligent web automation framework for real-world tasks",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Codeium",
    author_email="support@codeium.com",
    url="https://github.com/codeium/arcana-agent",
    packages=find_packages(exclude=["tests*", "examples*"]),
    install_requires=[
        "aiohttp>=3.9.5",
        "asyncio>=3.4.3", 
        "python-dotenv>=1.0.1",
        "anthropic>=0.39.0",
        "selenium>=4.18.1",
        "webdriver-manager>=4.0.1",
        "python-dateutil>=2.8.2",
        "playwright>=1.49.0",
        "typing-extensions>=4.9.0"
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "black>=24.2.0",
            "isort>=5.13.2",
            "mypy>=1.8.0"
        ],
        "docs": [
            "sphinx>=7.2.6",
            "sphinx-rtd-theme>=2.0.0"
        ]
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Browsers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Testing :: Acceptance"
    ],
    python_requires=">=3.9",
    include_package_data=True,
    zip_safe=False
)
