from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="weather-monitor",
    version="1.0.0",
    author="Weather Monitor Team",
    description="A weather monitoring system with Grafana integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.11",
    install_requires=[
        "requests>=2.31.0",
        "influxdb-client>=1.37.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.5.0",
        "loguru>=0.7.2",
        "click>=8.1.7",
        "schedule>=1.2.0",
    ],
    entry_points={
        "console_scripts": [
            "weather-monitor=weather_monitor.cli:cli",
        ],
    },
)