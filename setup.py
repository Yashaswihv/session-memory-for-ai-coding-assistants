from setuptools import setup, find_packages

setup(
    name="session-memory",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # These aren't Python packages (hyphenated dir names, no __init__.py),
        # so find_packages() won't discover them -- they're assets that
        # `session-memory setup install` copies out into each assistant's own
        # global config location. Ship them explicitly.
        "session_memory": [
            "assistants/claude-code/commands/*.md",
            "assistants/claude-code/hooks/*.py",
            "assistants/agy/skills/*/*.md",
            "assistants/agy/hooks/*.py",
        ],
    },
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
