from setuptools import setup, find_packages

setup(
    name="session-memory",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "faiss-cpu>=1.7.4",
        "sentence-transformers>=2.2.2",
        "rank-bm25>=0.2.2",
        "mcp>=0.1.0",
        "click>=8.1.0",
        "pydantic>=2.0.0",
        "numpy>=1.20.0",
    ],
    entry_points={
        "console_scripts": [
            "session-memory=session_memory.cli.main:cli",
        ],
    },
    author="Yashaswi Hirekabbigere Vedamurthy",
    description="Session Memory for AI Coding Assistants",
    python_requires=">=3.9",
)
